import numpy as np
import pytest

from risk_lab.debt_erosion import DebtErosionInputs, debt_erosion_path
from risk_lab.governance import GovernanceInputs, governance_oracle_path
from risk_lab.peg import PegInputs, peg_recovery_path
from risk_lab.solvency import SolvencyInputs, monte_carlo_solvency, solvency_snapshot


def test_debt_erosion_reduces_usd_debt_when_depreciation_dominates():
    inputs = DebtErosionInputs(1_000_000, 1_000, 0.50, 0.20, 1.0)
    path = debt_erosion_path(inputs)
    assert path.iloc[-1]["debt_usd"] < path.iloc[0]["debt_usd"]
    assert path.iloc[-1]["equity_usd"] > 0


def test_debt_erosion_rejects_invalid_principal():
    with pytest.raises(ValueError):
        debt_erosion_path(DebtErosionInputs(0, 1_000, 0.3, 0.2, 1.0))


def test_solvency_snapshot_flags_bad_debt_after_severe_shock():
    inputs = SolvencyInputs(100_000, 100_000_000, 1_000, 1.5, -0.60, 0.0)
    result = solvency_snapshot(inputs)
    assert result["insolvent"] is True
    assert result["bad_debt_usd"] > 0


def test_monte_carlo_summary_is_bounded_and_reproducible():
    inputs = SolvencyInputs(150_000, 100_000_000, 1_000, 1.5, -0.25, 0.30)
    first, summary_one = monte_carlo_solvency(inputs, simulations=2_000, seed=7)
    second, summary_two = monte_carlo_solvency(inputs, simulations=2_000, seed=7)
    assert summary_one == summary_two
    assert np.allclose(first["collateral_ratio"], second["collateral_ratio"])
    assert 0 <= summary_one["insolvency_probability"] <= 1
    assert 0 <= summary_one["liquidation_probability"] <= 1


def test_peg_recovery_waits_for_delay_then_converges():
    path = peg_recovery_path(PegInputs(-10, 5_000_000, 1_000_000, 0.3, 3, 48))
    assert path.loc[0, "deviation_pct"] == pytest.approx(-10)
    assert path.loc[2, "deviation_pct"] == pytest.approx(-10)
    assert abs(path.iloc[-1]["deviation_pct"]) < abs(path.iloc[0]["deviation_pct"])


def test_zero_initial_peg_deviation_is_stable():
    path = peg_recovery_path(PegInputs(0, 5_000_000, 500_000, 0.3, 1, 24))
    assert np.allclose(path["stablecoin_price"], 1.0)
    assert np.allclose(path["recovered_share_pct"], 100.0)


def test_governance_oracle_lags_and_policy_reduces_ceiling():
    inputs = GovernanceInputs(2_500, -40, 4, 0.35, 50_000_000, 1.5, 0.7, 48)
    path, summary = governance_oracle_path(inputs)
    assert summary["max_pricing_error_pct"] > 0
    assert path.iloc[-1]["debt_ceiling_usd"] < path.iloc[0]["debt_ceiling_usd"]
    assert path.iloc[-1]["liquidation_ratio"] > path.iloc[0]["liquidation_ratio"]


def test_governance_rejects_invalid_smoothing():
    with pytest.raises(ValueError):
        governance_oracle_path(GovernanceInputs(100, -20, 1, 0, 1_000_000, 1.5, 0.5))
