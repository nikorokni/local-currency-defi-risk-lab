"""Reduced-form stablecoin peg recovery model."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PegInputs:
    initial_deviation_pct: float
    pool_liquidity_usd: float
    arbitrage_capital_usd: float
    trading_fee_pct: float = 0.30
    oracle_delay_hours: float = 1.0
    horizon_hours: int = 72

    def validate(self) -> None:
        if self.pool_liquidity_usd <= 0 or self.arbitrage_capital_usd < 0:
            raise ValueError("liquidity must be positive and arbitrage capital non-negative")
        if self.trading_fee_pct < 0 or self.oracle_delay_hours < 0:
            raise ValueError("fee and delay must be non-negative")
        if self.horizon_hours < 1:
            raise ValueError("horizon_hours must be at least 1")


def peg_recovery_path(inputs: PegInputs) -> pd.DataFrame:
    """Simulate how liquidity, arbitrage capacity, fees, and delay affect recovery."""

    inputs.validate()
    hours = np.arange(0, inputs.horizon_hours + 1, dtype=float)
    deviation = np.empty_like(hours)

    capital_ratio = inputs.arbitrage_capital_usd / inputs.pool_liquidity_usd
    fee_drag = max(0.05, 1.0 - inputs.trading_fee_pct / 2.0)
    recovery_speed = max(0.0025, min(1.25, capital_ratio * 3.5 * fee_drag))

    active_time = np.maximum(0.0, hours - inputs.oracle_delay_hours)
    deviation[:] = inputs.initial_deviation_pct * np.exp(-recovery_speed * active_time)
    deviation[hours < inputs.oracle_delay_hours] = inputs.initial_deviation_pct

    price = 1.0 + deviation / 100.0
    cumulative_arbitrage = inputs.arbitrage_capital_usd * (
        1.0 - np.exp(-recovery_speed * active_time)
    )
    if abs(inputs.initial_deviation_pct) > 1e-12:
        recovered_share = 1.0 - np.abs(deviation / inputs.initial_deviation_pct)
    else:
        recovered_share = np.ones_like(deviation)

    return pd.DataFrame(
        {
            "hour": hours,
            "stablecoin_price": price,
            "deviation_pct": deviation,
            "recovered_share_pct": recovered_share * 100.0,
            "cumulative_arbitrage_usd": cumulative_arbitrage,
        }
    )
