"""Oracle latency and automated governance response model."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GovernanceInputs:
    initial_collateral_price: float
    shock_pct: float
    oracle_delay_steps: int
    oracle_smoothing: float
    initial_debt_ceiling_usd: float
    initial_liquidation_ratio: float
    policy_aggressiveness: float
    steps: int = 48

    def validate(self) -> None:
        if self.initial_collateral_price <= 0 or self.initial_debt_ceiling_usd <= 0:
            raise ValueError("price and debt ceiling must be positive")
        if self.shock_pct <= -100:
            raise ValueError("shock_pct must be greater than -100")
        if self.oracle_delay_steps < 0 or self.steps < 2:
            raise ValueError("delay must be non-negative and steps at least 2")
        if not 0 < self.oracle_smoothing <= 1:
            raise ValueError("oracle_smoothing must be in (0, 1]")
        if self.initial_liquidation_ratio <= 1:
            raise ValueError("initial_liquidation_ratio must be greater than 1")
        if not 0 <= self.policy_aggressiveness <= 1:
            raise ValueError("policy_aggressiveness must be in [0, 1]")


def governance_oracle_path(inputs: GovernanceInputs) -> tuple[pd.DataFrame, dict[str, float]]:
    """Simulate a delayed oracle and an automated parameter response."""

    inputs.validate()
    step = np.arange(inputs.steps + 1)
    shock_time = max(1, inputs.steps // 6)
    true_price = np.full(inputs.steps + 1, inputs.initial_collateral_price, dtype=float)
    post_shock = inputs.initial_collateral_price * (1.0 + inputs.shock_pct / 100.0)
    true_price[shock_time:] = post_shock

    oracle_price = np.empty_like(true_price)
    oracle_price[0] = true_price[0]
    debt_ceiling = np.empty_like(true_price)
    liquidation_ratio = np.empty_like(true_price)
    debt_ceiling[0] = inputs.initial_debt_ceiling_usd
    liquidation_ratio[0] = inputs.initial_liquidation_ratio

    for t in range(1, len(step)):
        observed_index = max(0, t - inputs.oracle_delay_steps)
        observed = true_price[observed_index]
        oracle_price[t] = (
            inputs.oracle_smoothing * observed
            + (1.0 - inputs.oracle_smoothing) * oracle_price[t - 1]
        )
        oracle_drawdown = max(0.0, 1.0 - oracle_price[t] / inputs.initial_collateral_price)
        target_ceiling = inputs.initial_debt_ceiling_usd * (
            1.0 - inputs.policy_aggressiveness * min(0.9, oracle_drawdown * 1.6)
        )
        target_ratio = inputs.initial_liquidation_ratio + (
            inputs.policy_aggressiveness * oracle_drawdown * 0.75
        )
        debt_ceiling[t] = 0.65 * debt_ceiling[t - 1] + 0.35 * target_ceiling
        liquidation_ratio[t] = 0.65 * liquidation_ratio[t - 1] + 0.35 * target_ratio

    pricing_error_pct = (oracle_price - true_price) / true_price * 100.0
    unprotected_exposure = debt_ceiling * np.maximum(0.0, oracle_price - true_price) / oracle_price
    risk_score = np.clip(
        np.abs(pricing_error_pct) * 2.0
        + 25.0 * (debt_ceiling / inputs.initial_debt_ceiling_usd)
        - 10.0 * (liquidation_ratio - inputs.initial_liquidation_ratio),
        0.0,
        100.0,
    )

    frame = pd.DataFrame(
        {
            "step": step,
            "true_price": true_price,
            "oracle_price": oracle_price,
            "pricing_error_pct": pricing_error_pct,
            "debt_ceiling_usd": debt_ceiling,
            "liquidation_ratio": liquidation_ratio,
            "unprotected_exposure_usd": unprotected_exposure,
            "risk_score": risk_score,
        }
    )
    summary = {
        "max_pricing_error_pct": float(np.max(np.abs(pricing_error_pct))),
        "peak_unprotected_exposure_usd": float(np.max(unprotected_exposure)),
        "final_debt_ceiling_usd": float(debt_ceiling[-1]),
        "final_liquidation_ratio": float(liquidation_ratio[-1]),
        "peak_risk_score": float(np.max(risk_score)),
    }
    return frame, summary
