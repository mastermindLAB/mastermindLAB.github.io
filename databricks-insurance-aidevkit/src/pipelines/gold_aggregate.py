# Databricks notebook source
# MAGIC %md
# MAGIC # Gold layer — analytics + ML-ready marts
# MAGIC Business-level tables consumed by BI dashboards, the fraud model and
# MAGIC the loss-ratio KPIs the actuarial team reports on.

# COMMAND ----------
import dlt
from pyspark.sql import functions as F


@dlt.table(comment="One row per claim enriched with policy + customer context.")
def gold_claims_enriched():
    claims = dlt.read("silver_claims")
    policies = dlt.read("silver_policies")
    customers = dlt.read("silver_customers")
    return (
        claims.join(policies, "policy_id", "left")
        .join(customers, "customer_id", "left")
        .select(
            "claim_id",
            "policy_id",
            "customer_id",
            "claim_amount",
            "claim_type",
            "days_to_report",
            "is_fraud",
            "annual_premium",
            "coverage_amount",
            "age",
            "tenure_years",
            "region",
        )
    )


@dlt.table(comment="Loss ratio and claim frequency by product line and region.")
def gold_portfolio_kpis():
    enriched = dlt.read("gold_claims_enriched")
    return (
        enriched.groupBy("claim_type", "region")
        .agg(
            F.count("claim_id").alias("claim_count"),
            F.sum("claim_amount").alias("total_incurred"),
            F.sum("annual_premium").alias("total_premium"),
            F.avg("days_to_report").alias("avg_days_to_report"),
            F.avg("is_fraud").alias("fraud_rate"),
        )
        .withColumn(
            "loss_ratio",
            F.round(F.col("total_incurred") / F.col("total_premium"), 4),
        )
    )
