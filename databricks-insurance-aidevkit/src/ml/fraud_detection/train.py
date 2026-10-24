# Databricks notebook source
# MAGIC %md
# MAGIC # Train + register the fraud-detection model
# MAGIC Trains a gradient-boosted classifier, logs metrics/artifacts to MLflow,
# MAGIC and registers the model in Unity Catalog with an aliased "Champion".

# COMMAND ----------
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import train_test_split

dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
dbutils.widgets.text("model_name", "insurance_dev.lakehouse.fraud_detection_model")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
model_name = dbutils.widgets.get("model_name")

spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"USE SCHEMA {schema}")
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------
pdf = spark.table("fraud_features").toPandas()
feature_cols = [c for c in pdf.columns if c not in ("claim_id", "label")]
X, y = pdf[feature_cols], pdf["label"]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

# COMMAND ----------
mlflow.sklearn.autolog(log_models=False)
with mlflow.start_run(run_name="fraud-gbc") as run:
    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    auc = roc_auc_score(y_test, proba)
    f1 = f1_score(y_test, preds)
    mlflow.log_metrics({"test_auc": auc, "test_f1": f1})
    print(f"AUC={auc:.3f}  F1={f1:.3f}")

    signature = infer_signature(X_test, preds)
    mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        signature=signature,
        registered_model_name=model_name,
        input_example=X_test.head(3),
    )

# COMMAND ----------
# Alias the freshest version as Champion so serving + downstream jobs
# resolve it by name rather than a hard-coded version number.
client = mlflow.MlflowClient()
latest = max(int(v.version) for v in client.search_model_versions(f"name='{model_name}'"))
client.set_registered_model_alias(model_name, "Champion", latest)
print(f"Registered {model_name} v{latest} as @Champion")
