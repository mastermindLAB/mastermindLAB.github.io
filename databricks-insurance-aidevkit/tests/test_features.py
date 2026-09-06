"""Unit tests for the fraud feature logic. Run with: pytest -q"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ml.fraud_detection.features import (  # noqa: E402
    FEATURE_COLUMNS,
    Claim,
    amount_to_coverage_ratio,
    claim_to_premium_ratio,
    engineer_features,
    risk_band,
)


def test_ratios_handle_zero_denominator():
    assert amount_to_coverage_ratio(1000, 0) == 0.0
    assert claim_to_premium_ratio(1000, 0) == 0.0


def test_ratios_round_to_four_dp():
    assert amount_to_coverage_ratio(1, 3) == 0.3333
    assert claim_to_premium_ratio(500, 1000) == 0.5


def test_engineer_features_shape_and_flags():
    claim = Claim(
        claim_amount=30000, coverage_amount=100000,
        annual_premium=1200, days_to_report=40, tenure_years=0.5,
    )
    feats = engineer_features(claim)
    assert set(feats) == set(FEATURE_COLUMNS)
    assert feats["is_new_customer"] == 1      # tenure < 1
    assert feats["high_value_claim"] == 1     # >= 25k
    assert feats["amount_to_coverage_ratio"] == 0.3


@pytest.mark.parametrize(
    "prob,band",
    [(0.9, "HIGH"), (0.75, "HIGH"), (0.5, "MEDIUM"), (0.4, "MEDIUM"), (0.1, "LOW")],
)
def test_risk_band_thresholds(prob, band):
    assert risk_band(prob) == band


def test_risk_band_rejects_out_of_range():
    with pytest.raises(ValueError):
        risk_band(1.5)
