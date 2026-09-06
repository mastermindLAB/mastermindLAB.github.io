# Databricks notebook source
# MAGIC %md
# MAGIC # Silver layer — cleansed, conformed, quality-enforced
# MAGIC Applies expectations (DLT data-quality constraints) and standardises
# MAGIC types so downstream gold + ML can trust the data.

# COMMAND ----------
import dlt
from pyspark.sql import functions as F


@dlt.table(comment="Validated policies with conformed types.")
@dlt.expect_or_drop("valid_policy_id", "policy_id IS NOT NULL")
@dlt.expect_or_drop("positive_premium", "annual_premium >= 0")
def silver_policies():
    df = dlt.read_stream("bronze_policies")
    return (
        df.withColumn("annual_premium", F.col("annual_premium").cast("double"))
        .withColumn("policy_start_date", F.to_date("policy_start_date"))
        .withColumn("coverage_amount", F.col("coverage_amount").cast("double"))
        .dropDuplicates(["policy_id"])
    )


@dlt.table(comment="Validated claims with derived processing latency.")
@dlt.expect_or_drop("valid_claim_id", "claim_id IS NOT NULL")
@dlt.expect("non_negative_amount", "claim_amount >= 0")
def silver_claims():
    df = dlt.read_stream("bronze_claims")
    return (
        df.withColumn("claim_amount", F.col("claim_amount").cast("double"))
        .withColumn("claim_date", F.to_date("claim_date"))
        .withColumn("is_fraud", F.col("is_fraud").cast("int"))
        .withColumn(
            "days_to_report",
            F.datediff("claim_date", F.to_date("incident_date")),
        )
    )


@dlt.table(comment="Validated customer master.")
@dlt.expect_or_drop("valid_customer_id", "customer_id IS NOT NULL")
def silver_customers():
    df = dlt.read_stream("bronze_customers")
    return (
        df.withColumn("age", F.col("age").cast("int"))
        .withColumn("tenure_years", F.col("tenure_years").cast("double"))
        .dropDuplicates(["customer_id"])
    )
