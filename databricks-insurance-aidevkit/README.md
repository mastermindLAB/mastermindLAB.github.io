# 🏛️ Insurance AI Dev Kit — Databricks Asset Bundle

An opinionated, end-to-end **Databricks** starter project for an insurance
company. It ships a governed lakehouse, three ML/GenAI use cases, and the
CI/CD wiring to deploy them across environments with a single command — the
**AI Dev Kit** pattern: business logic in importable modules, notebooks as thin
orchestration shells, everything declared as code in a
[Databricks Asset Bundle](https://docs.databricks.com/dev-tools/bundles/index.html).

## What's inside

| Capability | Tech | Path |
|---|---|---|
| **Medallion lakehouse** (bronze → silver → gold) | Lakeflow Declarative Pipelines / DLT + Auto Loader | `src/pipelines/` |
| **Claims fraud detection** | scikit-learn + MLflow + Unity Catalog model + Model Serving | `src/ml/fraud_detection/` |
| **Policyholder churn** | scikit-learn + MLflow | `src/ml/churn/` |
| **Policy Q&A GenAI agent** | Mosaic AI Vector Search + Foundation Model APIs + Agent Framework | `src/agents/` |
| **Databricks App** (claims UI) | Databricks Apps + Streamlit (fraud triage, Q&A, KPIs) | `app/` |
| **Orchestration** | Databricks Jobs (scheduled + dependency DAGs) | `resources/` |
| **Governance** | Unity Catalog catalog/schema/volume + grants | `scripts/setup_unity_catalog.sql` |
| **Quality gates** | DLT expectations + post-load checks + pytest | `src/pipelines/quality_checks.py`, `tests/` |

## Architecture

```
 landing volume (CSV drops)
        │  Auto Loader
        ▼
   ┌─────────┐   expectations   ┌─────────┐   joins/aggs   ┌────────┐
   │ bronze  │ ───────────────▶ │ silver  │ ─────────────▶ │  gold  │
   └─────────┘                  └─────────┘                └────────┘
                                                       │           │
                                   feature table ◀─────┘           ▼
                                        │                    BI / KPIs
                       ┌────────────────┼─────────────────┐
                       ▼                ▼                  ▼
                 fraud model       churn model      policy Q&A agent
                 (Serving EP)      (UC model)       (Vector Search + LLM)
                       └──────────────┬──────────────────┘
                                      ▼
                          Databricks App (Streamlit)
                       fraud triage · Q&A · KPI dashboard
```

## Repo layout

```
databricks-insurance-aidevkit/
├── databricks.yml              # bundle: vars + dev/prod targets
├── resources/                  # jobs, pipeline & serving endpoint as code
├── src/
│   ├── pipelines/              # DLT bronze/silver/gold + DQ gate
│   ├── ml/                     # fraud + churn (pure logic in features.py)
│   └── agents/                 # RAG agent, vector index build, deploy driver
├── app/                        # Databricks App (Streamlit claims UI)
├── notebooks/                  # seed data + exploration
├── tests/                      # pytest for the pure feature logic
├── data/sample/                # tiny reference CSVs
├── scripts/                    # Unity Catalog setup SQL
└── .github/workflows/ci.yml    # lint + test + bundle validate
```

## Quick start

### 0. Prerequisites
- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/install.html) `>= 0.230`
- A Databricks workspace with **Unity Catalog** and **serverless** enabled
- Authenticate: `databricks auth login --host https://<your-workspace>`

### 1. Point the bundle at your workspace
Edit the `host` (and, if you like, the default `catalog`) in `databricks.yml`,
or override on the CLI:

```bash
cd databricks-insurance-aidevkit
databricks bundle validate -t dev
```

### 2. Deploy everything
```bash
databricks bundle deploy -t dev
```
This creates the jobs, the DLT pipeline and the serving endpoint in your
workspace, prefixed with your username (development mode).

### 3. Run it end to end
```bash
# 1) seed data + build the medallion + run the DQ gate
databricks bundle run claims_ingestion -t dev

# 2) train + register + (re)deploy the fraud model
databricks bundle run fraud_detection_training -t dev

# 3) build the vector index + log/evaluate/deploy the Q&A agent
databricks bundle run policy_qa_agent -t dev
```

### 4. Open the Databricks App
Set `warehouse_id` in `databricks.yml` (a running SQL Warehouse ID), then the
`databricks bundle deploy` already created the App. Start it and grab its URL:
```bash
databricks bundle run insurance_app -t dev
```
The **Insurance AI Dev Kit** App (`app/`) gives claims staff a Streamlit UI with
three tabs — fraud triage (calls the fraud serving endpoint), policy Q&A (calls
the agent endpoint) and portfolio KPIs (reads the gold table over the warehouse).
The App authenticates as its own service principal; `resources/insurance_app.app.yml`
grants it least-privilege `CAN_QUERY` / `CAN_USE` on exactly those backends.

### 5. Promote to prod
```bash
databricks bundle deploy -t prod
```
Production mode enforces a clean source tree, `run_as` identity, unpaused
schedules and the `insurance_prod` catalog.

## Local development

```bash
pip install -r requirements-dev.txt
ruff check src tests
pytest
```
The fraud feature logic lives in `src/ml/fraud_detection/features.py` with **no
Spark dependency**, so it is fully unit-tested in plain CI.

## CI/CD

`/.github/workflows/ci.yml` lints, runs `pytest`, and runs
`databricks bundle validate` on every push/PR. For the bundle-validate job, set
the repo secrets `DATABRICKS_HOST` and `DATABRICKS_TOKEN`.

> ⚠️ GitHub only runs workflows from `.github/workflows/` at the **repository
> root**. If this project is nested in a subdirectory, copy
> `databricks-insurance-aidevkit/.github/workflows/ci.yml` to the repo root.

## Customising

- **Cloud**: set `node_type_id` in `databricks.yml` (`i3.xlarge` on AWS,
  `n2-standard-4` on GCP).
- **Models**: swap `llm_endpoint` / `embedding_endpoint` for any Foundation
  Model or external model endpoint.
- **Real documents**: replace the seed clauses in `build_vector_index.py` with a
  parse-from-Volume step over your actual policy PDFs.

---
Built as a reusable kit — fork it, point it at your workspace, and ship.
