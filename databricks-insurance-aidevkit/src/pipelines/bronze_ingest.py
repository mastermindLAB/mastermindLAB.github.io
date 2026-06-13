# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze layer — raw ingestion with Auto Loader
# MAGIC Lands policy, claims and customer CSV drops into Delta with full schema
# MAGIC inference + rescue, plus ingestion lineage columns.

# COMMAND ----------
import dlt
from pyspark.sql import functions as F

LANDING = spark.conf.get("pipeline.landing_path")


def _autoload(subdir: str):
    """Stream a landing sub-folder into a bronze Delta table via Auto Loader."""
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "true")
        .option("cloudFiles.schemaEvolutionMode", "rescue")
        .option("header", "true")
        .load(f"{LANDING}/{subdir}")
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.col("_metadata.file_path"))
    )


@dlt.table(comment="Raw insurance policies as delivered by source systems.")
def bronze_policies():
    return _autoload("policies")


@dlt.table(comment="Raw claims events, one row per claim submission.")
def bronze_claims():
    return _autoload("claims")


@dlt.table(comment="Raw customer master records.")
def bronze_customers():
    return _autoload("customers")
