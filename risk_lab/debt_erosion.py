"""Inflation and FX-driven local-currency debt erosion model."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DebtErosionInputs:
    """Parameters for a local-currency loan converted into a USD asset."""

    principal_local: float
    initial_fx_local_per_usd: float
    annual_depreciation: float
    annual_loan_rate: float
    horizon_years: float
    asset_annual_return: float = 0.0
    compounding_periods: int = 12

    def validate(self) -> None:
        if self.principal_local <= 0:
            raise ValueError("principal_local must be positive")
        if self.initial_fx_local_per_usd <= 0:
            raise ValueError("initial_fx_local_per_usd must be positive")
        if self.horizon_years <= 0:
            raise ValueError("horizon_years must be positive")
        if self.compounding_periods < 1:
            raise ValueError("compounding_periods must be at least 1")
        if min(self.annual_depreciation, self.annual_loan_rate, self.asset_annual_return) <= -1:
            raise ValueError("annual rates must be greater than -100%")


def debt_erosion_path(inputs: DebtErosionInputs) -> pd.DataFrame:
    """Return the debt, FX, asset, and borrower-equity path.

    Rates are decimal values. FX is expressed as local-currency units per USD,
    so an increase in FX represents depreciation of the local currency.
    """

    inputs.validate()
    steps = max(2, int(round(inputs.horizon_years * inputs.compounding_periods)) + 1)
    years = np.linspace(0.0, inputs.horizon_years, steps)

    debt_local = inputs.principal_local * np.power(1.0 + inputs.annual_loan_rate, years)
    fx_local_per_usd = inputs.initial_fx_local_per_usd * np.power(
        1.0 + inputs.annual_depreciation, years
    )
    debt_usd = debt_local / fx_local_per_usd

    initial_asset_usd = inputs.principal_local / inputs.initial_fx_local_per_usd
    asset_usd = initial_asset_usd * np.power(1.0 + inputs.asset_annual_return, years)
    equity_usd = asset_usd - debt_usd
    roi_on_initial_capital = equity_usd / initial_asset_usd

    return pd.DataFrame(
        {
            "year": years,
            "fx_local_per_usd": fx_local_per_usd,
            "debt_local": debt_local,
            "debt_usd": debt_usd,
            "asset_usd": asset_usd,
            "equity_usd": equity_usd,
            "roi_pct": roi_on_initial_capital * 100.0,
        }
    )
