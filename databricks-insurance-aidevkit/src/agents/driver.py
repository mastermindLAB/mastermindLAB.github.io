# Databricks notebook source
# MAGIC %md
# MAGIC # Log, evaluate and deploy the Policy Q&A agent
# MAGIC Logs `policy_qa_agent.py` with MLflow (models-from-code), runs Mosaic AI
# MAGIC Agent Evaluation on a small golden set, registers it to Unity Catalog and
# MAGIC deploys it to a review-app endpoint.

# COMMAND ----------
# MAGIC %pip install -U -qqq mlflow databricks-agents databricks-langchain langchain langchain-core
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
import os

import mlflow
import pandas as pd
from databricks import agents

dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
dbutils.widgets.text("llm_endpoint", "databricks-meta-llama-3-3-70b-instruct")
dbutils.widgets.text("model_name", "insurance_dev.lakehouse.policy_qa_agent")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
model_name = dbutils.widgets.get("model_name")

os.environ["INSURANCE_CATALOG"] = catalog
os.environ["INSURANCE_SCHEMA"] = schema
os.environ["LLM_ENDPOINT"] = dbutils.widgets.get("llm_endpoint")
mlflow.set_registry_uri("databricks-uc")

# COMMAND ----------
with mlflow.start_run(run_name="policy-qa-agent"):
    logged = mlflow.langchain.log_model(
        lc_model="./policy_qa_agent.py",   # models-from-code
        artifact_path="agent",
        registered_model_name=model_name,
        pip_requirements=[
            "mlflow", "databricks-langchain", "langchain", "langchain-core",
        ],
    )

    # --- Agent Evaluation: faithfulness + correctness on a golden set --------
    eval_df = pd.DataFrame(
        {
            "request": [
                "Does comprehensive auto cover hail damage?",
                "Is flood damage covered under my home water-damage clause?",
                "How long do I have to report a claim?",
            ],
            "expected_response": [
                "Yes, comprehensive covers hail damage less the deductible.",
                "No, flooding is excluded from the water-damage clause.",
                "Claims should be reported within 30 days of the incident.",
            ],
        }
    )
    results = mlflow.evaluate(
        model=logged.model_uri,
        data=eval_df,
        model_type="databricks-agent",
    )
    print("Agent eval metrics:", results.metrics)

# COMMAND ----------
# Deploy to a scale-to-zero serving endpoint with the built-in review app.
version = mlflow.MlflowClient().get_registered_model(model_name).latest_versions[0].version
deployment = agents.deploy(model_name, version, scale_to_zero=True)
print(f"Deployed {model_name} v{version}")
print("Review app:", deployment.review_app_url)
