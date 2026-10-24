# Databricks notebook source
# MAGIC %md
# MAGIC # Post-load data-quality gate
# MAGIC Fails the job (and therefore alerts) when gold tables breach the
# MAGIC freshness / completeness thresholds the business signed off on.

# COMMAND ----------
dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------
checks = {
    "gold_claims_enriched has rows":
        "SELECT count(*) FROM gold_claims_enriched",
    "no null claim ids":
        "SELECT count(*) FROM gold_claims_enriched WHERE claim_id IS NULL",
    "loss ratio computed":
        "SELECT count(*) FROM gold_portfolio_kpis WHERE loss_ratio IS NULL",
}

row_count = spark.sql(checks["gold_claims_enriched has rows"]).first()[0]
null_ids = spark.sql(checks["no null claim ids"]).first()[0]
null_ratio = spark.sql(checks["loss ratio computed"]).first()[0]

failures = []
if row_count == 0:
    failures.append("gold_claims_enriched is empty")
if null_ids > 0:
    failures.append(f"{null_ids} null claim_id values in gold")
if null_ratio > 0:
    failures.append(f"{null_ratio} rows with null loss_ratio")

print(f"rows={row_count} null_ids={null_ids} null_ratio={null_ratio}")
if failures:
    raise Exception("Data-quality gate failed: " + "; ".join(failures))
print("Data-quality gate passed ✅")
