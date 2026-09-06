# Databricks notebook source
# MAGIC %md
# MAGIC # Portfolio exploration
# MAGIC Quick look at the gold KPIs once the pipeline has run. Use this to sanity
# MAGIC check loss ratios and fraud rates before sharing dashboards.

# COMMAND ----------
dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")

# COMMAND ----------
display(
    spark.sql(
        """
        SELECT claim_type, region, claim_count, loss_ratio, fraud_rate
        FROM gold_portfolio_kpis
        ORDER BY loss_ratio DESC
        """
    )
)

# COMMAND ----------
# MAGIC %md Ask the Policy Q&A agent a question (after the agent job has deployed):
# MAGIC ```python
# MAGIC from mlflow.deployments import get_deploy_client
# MAGIC client = get_deploy_client("databricks")
# MAGIC client.predict(endpoint="policy-qa-agent-dev",
# MAGIC                inputs={"messages": [{"role": "user",
# MAGIC                "content": "Does comprehensive auto cover hail?"}]})
# MAGIC ```
