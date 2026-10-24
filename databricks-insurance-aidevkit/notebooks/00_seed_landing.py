# Databricks notebook source
# MAGIC %md
# MAGIC # Seed the landing zone (demo bootstrap)
# MAGIC Creates the catalog / schema / volume if needed and drops synthetic
# MAGIC policy, claims and customer CSVs into the landing path so the medallion
# MAGIC pipeline has data to ingest. Safe to re-run.

# COMMAND ----------
import random
from datetime import date, timedelta

dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
dbutils.widgets.text("landing_volume", "landing")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
volume = dbutils.widgets.get("landing_volume")

spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.{volume}")
base = f"/Volumes/{catalog}/{schema}/{volume}"

# COMMAND ----------
random.seed(42)
regions = ["West", "Central", "East", "North"]
ctypes = ["Auto", "Home", "Life"]
N = 500

customers = [
    (f"C{i:04d}", random.randint(19, 85), round(random.uniform(0, 20), 1),
     random.choice(regions))
    for i in range(N)
]
policies = [
    (f"P{i:04d}", f"C{i:04d}", random.choice(ctypes),
     round(random.uniform(400, 3500), 2), round(random.uniform(10000, 500000), 2),
     str(date(2023, 1, 1) + timedelta(days=random.randint(0, 700))))
    for i in range(N)
]


def make_claim(i):
    fraud = 1 if random.random() < 0.08 else 0
    coverage = policies[i][4]
    amount = round(coverage * random.uniform(0.5 if fraud else 0.01, 0.9), 2)
    inc = date(2024, 1, 1) + timedelta(days=random.randint(0, 500))
    rep = inc + timedelta(days=random.randint(20 if fraud else 0, 45))
    return (f"CL{i:05d}", f"P{i:04d}", f"C{i:04d}",
            policies[i][2], amount, str(inc), str(rep), fraud)


claims = [make_claim(i) for i in range(N)]


def write_csv(rows, header, path):
    df = spark.createDataFrame(rows, header)
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(path)


write_csv(customers, ["customer_id", "age", "tenure_years", "region"],
          f"{base}/customers")
write_csv(policies, ["policy_id", "customer_id", "claim_type", "annual_premium",
                     "coverage_amount", "policy_start_date"], f"{base}/policies")
write_csv(claims, ["claim_id", "policy_id", "customer_id", "claim_type",
                   "claim_amount", "incident_date", "claim_date", "is_fraud"],
          f"{base}/claims")
print(f"Seeded {N} customers / policies / claims under {base}")
