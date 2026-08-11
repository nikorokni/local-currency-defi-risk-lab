"""Collateral solvency snapshots and Monte Carlo stress testing."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SolvencyInputs:
    collateral_usd: float
    debt_local: float
    fx_local_per_usd: float
    liquidation_ratio: float = 1.5
    collateral_shock: float = -0.25
    fx_depreciation: float = 0.30

    def validate(self) -> None:
        if min(self.collateral_usd, self.debt_local, self.fx_local_per_usd) <= 0:
            raise ValueError("collateral, debt, and FX must be positive")
        if self.liquidation_ratio <= 1.0:
            raise ValueError("liquidation_ratio must be greater than 1")
        if self.collateral_shock <= -1.0 or self.fx_depreciation <= -1.0:
            raise ValueError("shocks must be greater than -100%")


def solvency_snapshot(inputs: SolvencyInputs) -> dict[str, float | bool]:
    """Calculate a deterministic post-shock solvency snapshot."""

    inputs.validate()
    stressed_collateral = inputs.collateral_usd * (1.0 + inputs.collateral_shock)
    stressed_fx = inputs.fx_local_per_usd * (1.0 + inputs.fx_depreciation)
    stressed_debt_usd = inputs.debt_local / stressed_fx
    collateral_ratio = stressed_collateral / stressed_debt_usd
    liquidation_threshold_usd = stressed_debt_usd * inputs.liquidation_ratio
    liquidation_shortfall = max(0.0, liquidation_threshold_usd - stressed_collateral)
    bad_debt = max(0.0, stressed_debt_usd - stressed_collateral)
    return {
        "stressed_collateral_usd": stressed_collateral,
        "stressed_fx_local_per_usd": stressed_fx,
        "stressed_debt_usd": stressed_debt_usd,
        "collateral_ratio": collateral_ratio,
        "liquidation_shortfall_usd": liquidation_shortfall,
        "bad_debt_usd": bad_debt,
        "liquidatable": collateral_ratio < inputs.liquidation_ratio,
        "insolvent": collateral_ratio < 1.0,
    }


def monte_carlo_solvency(
    inputs: SolvencyInputs,
    simulations: int = 10_000,
    collateral_volatility: float = 0.55,
    fx_volatility: float = 0.35,
    horizon_years: float = 1.0,
    seed: int = 42,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Simulate correlated collateral and FX outcomes using lognormal shocks."""

    inputs.validate()
    if simulations < 100:
        raise ValueError("simulations must be at least 100")
    if min(collateral_volatility, fx_volatility, horizon_years) < 0:
        raise ValueError("volatilities and horizon must be non-negative")

    rng = np.random.default_rng(seed)
    correlation = -0.25
    covariance = np.array([[1.0, correlation], [correlation, 1.0]])
    z = rng.multivariate_normal([0.0, 0.0], covariance, size=simulations)
    sqrt_t = np.sqrt(horizon_years)

    collateral_drift = np.log1p(inputs.collateral_shock) / max(horizon_years, 1e-9)
    fx_drift = np.log1p(inputs.fx_depreciation) / max(horizon_years, 1e-9)
    collateral_factor = np.exp(
        (collateral_drift - 0.5 * collateral_volatility**2) * horizon_years
        + collateral_volatility * sqrt_t * z[:, 0]
    )
    fx_factor = np.exp(
        (fx_drift - 0.5 * fx_volatility**2) * horizon_years
        + fx_volatility * sqrt_t * z[:, 1]
    )

    collateral_usd = inputs.collateral_usd * collateral_factor
    fx = inputs.fx_local_per_usd * fx_factor
    debt_usd = inputs.debt_local / fx
    collateral_ratio = collateral_usd / debt_usd
    bad_debt = np.maximum(0.0, debt_usd - collateral_usd)

    frame = pd.DataFrame(
        {
            "collateral_usd": collateral_usd,
            "fx_local_per_usd": fx,
            "debt_usd": debt_usd,
            "collateral_ratio": collateral_ratio,
            "bad_debt_usd": bad_debt,
        }
    )
    summary = {
        "liquidation_probability": float(np.mean(collateral_ratio < inputs.liquidation_ratio)),
        "insolvency_probability": float(np.mean(collateral_ratio < 1.0)),
        "expected_bad_debt_usd": float(np.mean(bad_debt)),
        "var_95_bad_debt_usd": float(np.quantile(bad_debt, 0.95)),
        "median_collateral_ratio": float(np.median(collateral_ratio)),
    }
    return frame, summary
