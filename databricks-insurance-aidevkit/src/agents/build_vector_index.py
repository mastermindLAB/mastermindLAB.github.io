# Databricks notebook source
# MAGIC %md
# MAGIC # Build the policy-document vector index
# MAGIC Chunks policy wordings / endorsements, stores them in a Delta table with
# MAGIC Change Data Feed, and creates a Mosaic AI Vector Search delta-sync index
# MAGIC the Q&A agent retrieves from.

# COMMAND ----------
# MAGIC %pip install -U -qqq databricks-vectorsearch
# MAGIC dbutils.library.restartPython()

# COMMAND ----------
from databricks.vector_search.client import VectorSearchClient
from pyspark.sql import functions as F

dbutils.widgets.text("catalog", "insurance_dev")
dbutils.widgets.text("schema", "lakehouse")
dbutils.widgets.text("embedding_endpoint", "databricks-gte-large-en")
catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
embedding_endpoint = dbutils.widgets.get("embedding_endpoint")

ENDPOINT_NAME = "insurance-vs-endpoint"
SOURCE_TABLE = f"{catalog}.{schema}.policy_doc_chunks"
INDEX_NAME = f"{catalog}.{schema}.policy_doc_index"

# COMMAND ----------
# In production this reads parsed PDFs from a Volume; here we seed a few
# representative policy clauses so the kit is runnable end to end.
seed = [
    ("auto-001", "Auto Comprehensive", "Comprehensive coverage pays for damage to your vehicle from theft, fire, vandalism, hail and falling objects, less the deductible shown on your declarations page."),
    ("auto-002", "Auto Liability", "Bodily injury liability covers costs for which you are legally responsible when an at-fault accident injures another person, up to the policy limit."),
    ("home-001", "Home Water Damage", "Sudden and accidental water damage from burst pipes is covered. Damage from long-term seepage, flooding or lack of maintenance is excluded."),
    ("home-002", "Home Personal Property", "Personal property is covered worldwide up to 50% of the dwelling limit. High-value jewellery requires a scheduled endorsement."),
    ("life-001", "Life Contestability", "During the first two policy years, the insurer may contest a claim for material misrepresentation made on the application."),
    ("claims-001", "Claims Reporting", "Claims should be reported within 30 days of the incident. Late reporting may reduce or void the benefit if it prejudices the insurer's investigation."),
]
df = spark.createDataFrame(seed, ["doc_id", "title", "content"]).withColumn(
    "updated_at", F.current_timestamp()
)
(
    df.write.mode("overwrite")
    .option("delta.enableChangeDataFeed", "true")
    .saveAsTable(SOURCE_TABLE)
)

# COMMAND ----------
vsc = VectorSearchClient(disable_notice=True)

existing = [e["name"] for e in vsc.list_endpoints().get("endpoints", [])]
if ENDPOINT_NAME not in existing:
    vsc.create_endpoint_and_wait(ENDPOINT_NAME, endpoint_type="STANDARD")

try:
    vsc.get_index(ENDPOINT_NAME, INDEX_NAME).describe()
    print("Index already exists — syncing.")
    vsc.get_index(ENDPOINT_NAME, INDEX_NAME).sync()
except Exception:
    vsc.create_delta_sync_index_and_wait(
        endpoint_name=ENDPOINT_NAME,
        index_name=INDEX_NAME,
        source_table_name=SOURCE_TABLE,
        pipeline_type="TRIGGERED",
        primary_key="doc_id",
        embedding_source_column="content",
        embedding_model_endpoint_name=embedding_endpoint,
    )
print(f"Vector index ready: {INDEX_NAME}")
