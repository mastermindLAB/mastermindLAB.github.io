# Databricks notebook source
# MAGIC %md
# MAGIC # Fraud features → Feature table
# MAGIC Builds the model-ready feature table from the gold claims mart and
# MAGIC writes it to Unity Catalog so training + serving share one definition.

# COMMAND ----------
import sys

# Make the repo's src/ importable when run from the bundle workspace path.
sys.path.append("../../")
from pyspark.sql import functions as F  # noqa: E402

from ml.fraud_detection.features import FEATURE_COLUMNS  # noqa: E402

dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------
gold = spark.table("gold_claims_enriched")

features = (
    gold.withColumn(
        "amount_to_coverage_ratio",
        F.when(
            F.col("coverage_amount") > 0,
            F.col("claim_amount") / F.col("coverage_amount"),
        ).otherwise(0.0),
    )
    .withColumn(
        "claim_to_premium_ratio",
        F.when(
            F.col("annual_premium") > 0,
            F.col("claim_amount") / F.col("annual_premium"),
        ).otherwise(0.0),
    )
    .withColumn("is_new_customer", (F.col("tenure_years") < 1.0).cast("int"))
    .withColumn("high_value_claim", (F.col("claim_amount") >= 25000).cast("int"))
    .select("claim_id", *FEATURE_COLUMNS, F.col("is_fraud").alias("label"))
    .na.drop()
)

(
    features.write.mode("overwrite")
    .option("overwriteSchema", "true")
    .saveAsTable("fraud_features")
)
print(f"Wrote {features.count()} rows to {catalog}.{schema}.fraud_features")
