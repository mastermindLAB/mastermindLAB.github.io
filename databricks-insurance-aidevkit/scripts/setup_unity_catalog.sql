-- One-time Unity Catalog scaffolding for the Insurance AI Dev Kit.
-- Run as a workspace/metastore admin, or let notebooks/00_seed_landing.py
-- create the dev objects automatically. Adjust catalog name per environment.

CREATE CATALOG IF NOT EXISTS insurance_dev
  COMMENT 'Insurance lakehouse (development)';

CREATE SCHEMA IF NOT EXISTS insurance_dev.lakehouse
  COMMENT 'Bronze/silver/gold + ML + agent assets';

CREATE VOLUME IF NOT EXISTS insurance_dev.lakehouse.landing
  COMMENT 'Raw policy/claims/customer file drops';

-- Governance: least-privilege grants for the analytics + data-science groups.
GRANT USE CATALOG ON CATALOG insurance_dev TO `data-analysts`;
GRANT USE SCHEMA, SELECT ON SCHEMA insurance_dev.lakehouse TO `data-analysts`;
GRANT USE SCHEMA, SELECT, CREATE TABLE, CREATE MODEL
  ON SCHEMA insurance_dev.lakehouse TO `data-scientists`;
