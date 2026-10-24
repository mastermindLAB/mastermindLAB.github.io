"""Pure, dependency-light feature logic for claims fraud detection.

Kept free of Spark/Databricks imports so it runs in plain CI (``pytest``)
and is reused by the Databricks ``featurize.py`` notebook. This is the
pattern the AI Dev Kit promotes: business logic in importable modules,
notebooks as thin orchestration shells.
"""
from __future__ import annotations

from dataclasses import dataclass

# Engineered feature columns, in the order the model expects them.
FEATURE_COLUMNS = [
    "claim_amount",
    "days_to_report",
    "amount_to_coverage_ratio",
    "claim_to_premium_ratio",
    "is_new_customer",
    "high_value_claim",
]


@dataclass(frozen=True)
class Claim:
    claim_amount: float
    coverage_amount: float
    annual_premium: float
    days_to_report: int
    tenure_years: float


def amount_to_coverage_ratio(claim_amount: float, coverage_amount: float) -> float:
    """Share of the policy limit a claim consumes (0 when no coverage)."""
    if coverage_amount <= 0:
        return 0.0
    return round(claim_amount / coverage_amount, 4)


def claim_to_premium_ratio(claim_amount: float, annual_premium: float) -> float:
    """How many years of premium a single claim represents."""
    if annual_premium <= 0:
        return 0.0
    return round(claim_amount / annual_premium, 4)


def engineer_features(claim: Claim) -> dict:
    """Turn a raw claim into the model-ready feature vector."""
    return {
        "claim_amount": float(claim.claim_amount),
        "days_to_report": int(claim.days_to_report),
        "amount_to_coverage_ratio": amount_to_coverage_ratio(
            claim.claim_amount, claim.coverage_amount
        ),
        "claim_to_premium_ratio": claim_to_premium_ratio(
            claim.claim_amount, claim.annual_premium
        ),
        "is_new_customer": int(claim.tenure_years < 1.0),
        "high_value_claim": int(claim.claim_amount >= 25_000),
    }


def risk_band(fraud_probability: float) -> str:
    """Map a model score to the operational triage band used by SIU."""
    if not 0.0 <= fraud_probability <= 1.0:
        raise ValueError("fraud_probability must be in [0, 1]")
    if fraud_probability >= 0.75:
        return "HIGH"
    if fraud_probability >= 0.40:
        return "MEDIUM"
    return "LOW"
