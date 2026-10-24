# Databricks notebook source
# MAGIC %md
# MAGIC # Policyholder churn model (retention use case)
# MAGIC Predicts non-renewal so the retention team can target outreach. Mirrors
# MAGIC the fraud pattern: gold table in, MLflow + Unity Catalog model out.

# COMMAND ----------
import mlflow
from pyspark.sql import functions as F
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------
df = (
    spark.table("gold_claims_enriched")
    .groupBy("customer_id", "age", "tenure_years", "annual_premium", "region")
    .agg(
        F.count("claim_id").alias("claim_count"),
        F.sum("claim_amount").alias("total_claimed"),
    )
    # synthetic label: long-tenure, low-claim customers tend to renew
    .withColumn(
        "churned",
        ((F.col("tenure_years") < 2) & (F.col("claim_count") >= 2)).cast("int"),
    )
).toPandas()

features = ["age", "tenure_years", "annual_premium", "claim_count", "total_claimed"]
X_train, X_test, y_train, y_test = train_test_split(
    df[features].fillna(0), df["churned"], test_size=0.25, random_state=7
)

# COMMAND ----------
mlflow.sklearn.autolog()
with mlflow.start_run(run_name="churn-logreg"):
    model = LogisticRegression(max_iter=500)
    model.fit(X_train, y_train)
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    mlflow.log_metric("test_auc", auc)
    mlflow.sklearn.log_model(
        model, "model",
        registered_model_name=f"{catalog}.{schema}.churn_model",
    )
    print(f"Churn model AUC={auc:.3f}")
