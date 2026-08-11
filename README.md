# Citibike ETL Pipeline — Databricks Asset Bundles on GCP

A production-grade, end-to-end ETL pipeline for **Citibike trip data** built on **Databricks (GCP)** using the **Medallion Architecture**. The project demonstrates modern data engineering practices: modular Python packaging, multi-environment governance with Unity Catalog, CI/CD automation via GitHub Actions, and Delta Live Tables (DLT) orchestration — all managed as Infrastructure as Code with **Databricks Asset Bundles**.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
- [Multi-Environment Setup](#multi-environment-setup)
- [Local Development](#local-development)
- [CI/CD Pipeline](#cicd-pipeline)
- [Dashboards](#dashboards)
- [Getting Started](#getting-started)
- [Authentication](#authentication)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE FLOW                           │
│                                                                     │
│  GCS Volume                                                         │
│  (CSV Source)                                                       │
│      │                                                              │
│      ▼                                                              │
│  ┌──────────┐     ┌──────────────┐     ┌─────────────────────────┐ │
│  │  BRONZE  │────▶│    SILVER    │────▶│         GOLD            │ │
│  │          │     │              │     │                         │ │
│  │ Raw CSV  │     │  Cleaned &   │     │ daily_ride_summary      │ │
│  │ ingested │     │  enriched    │     │ daily_station_performa  │ │
│  │ w/ schema│     │  trip data   │     │                         │ │
│  └──────────┘     └──────────────┘     └─────────────────────────┘ │
│                                                   │                 │
│                                                   ▼                 │
│                                           Power BI Dashboards       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     DEPLOYMENT PIPELINE                             │
│                                                                     │
│  Feature Branch  ──▶  PR + Unit Tests (CI)  ──▶  main branch       │
│                                                       │             │
│                            ┌──────────────────────────┘             │
│                            ▼                                        │
│                     Deploy to TEST  ──▶  Deploy to PROD             │
│                     (CD Workflow)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Category | Technology |
|---|---|
| Data Platform | Databricks on GCP |
| Pipeline Framework | Delta Live Tables (DLT) |
| Language | Python 3.11+ |
| Distributed Processing | PySpark 3.5.0 |
| Storage Format | Delta Lake |
| Infrastructure as Code | Databricks Asset Bundles |
| Governance | Unity Catalog |
| Cloud Storage | Google Cloud Storage (GCS) |
| CI/CD | GitHub Actions |
| Compute | Classic cluster (DBR 15.4, `n2-highmem-4`) for jobs; serverless for DLT only |
| Local Dev | Databricks Connect (attached cluster) / PySpark local |
| Testing | pytest 8.3.5 + pytest-cov |
| Visualization | Power BI |

---

## Project Structure

```
citibike-etl-pipeline/
│
├── databricks.yml                  # Asset Bundle root config (dev/test/prod targets)
├── setup.py                        # Python package definition
├── pyproject.toml                  # Build system configuration
├── requirements-pyspark.txt        # Local dev dependencies
├── requirements-dbc.txt            # Databricks Connect dependencies
│
├── resources/                      # Bundle resource definitions (IaC)
│   ├── citibike_etl_pipeline.dlt.yml       # DLT pipeline config
│   ├── citibike_etl_pipeline_job.yml       # Multi-task job config
│   └── clusters.yml                        # Cluster specifications
│
├── citibike_etl/                   # Core ETL code
│   ├── notebooks/                  # Databricks notebooks (job tasks)
│   │   ├── 01_bronze_citibike.ipynb
│   │   ├── 02_silver_citibike.ipynb
│   │   ├── 03_gold_citibike_daily_ride_summary.ipynb
│   │   └── 03_gold_citibike_daily_station_performance.ipynb
│   ├── scripts/                    # Python script equivalents
│   └── dlt/                        # Delta Live Tables versions
│
├── src/                            # Reusable Python utilities (packaged as .whl)
│   ├── citibike/
│   │   └── citibike_utils.py       # Trip duration, station helpers
│   ├── utils/
│   │   └── datetime_utils.py       # Timestamp/date conversion helpers
│   └── citibike_project/
│       └── main.py                 # Package entry point
│
├── tests/                          # Unit tests
│   ├── conftest.py                 # Shared SparkSession fixtures
│   ├── test_citibike_utils.py
│   └── test_datetime_utils.py
│
├── dashboards/                     # Power BI assets
│   ├── citibike project.pbix
│   ├── daily ride summary.png
│   └── daily station performance.png
│
└── .github/workflows/
    ├── ci-workflow.yml             # Unit tests on PRs / feature branches
    └── cd-workflow.yml             # Deploy to TEST then PROD on main
```

---

## Data Pipeline

### Source Data

Raw Citibike trip CSV files loaded into a GCS-backed Unity Catalog volume:

```
/Volumes/{catalog}/00_landing/source_citibike_data/JC-202503-citibike-tripdata.csv
```

**Schema (13 fields):**

| Field | Type | Description |
|---|---|---|
| `ride_id` | string | Unique trip identifier |
| `rideable_type` | string | Bike type (classic, electric) |
| `started_at` | timestamp | Trip start time |
| `ended_at` | timestamp | Trip end time |
| `start_station_name` | string | Departure station |
| `start_station_id` | string | Departure station ID |
| `end_station_name` | string | Arrival station |
| `end_station_id` | string | Arrival station ID |
| `start_lat` / `start_lng` | double | Start coordinates |
| `end_lat` / `end_lng` | double | End coordinates |
| `member_casual` | string | Rider membership type |

---

### Bronze Layer — `{catalog}.01_bronze.jc_citibike`

Raw ingestion with full schema enforcement and pipeline metadata columns.

```python
# Metadata columns appended for lineage tracking
pipeline_id, run_id, task_id, processed_date
```

**Input:** CSV from GCS volume  
**Output:** Delta table with raw data + audit metadata

---

### Silver Layer — `{catalog}.02_silver.jc_citibike`

Data cleaning and business rule application using packaged utility functions.

**Transformations applied:**

| New Column | Logic |
|---|---|
| `trip_duration_mins` | `(ended_at - started_at)` in minutes |
| `trip_start_date` | Date extracted from `started_at` timestamp |

**Output columns:** `ride_id`, `trip_start_date`, `started_at`, `ended_at`, `start_station_name`, `end_station_name`, `trip_duration_mins`, `metadata`

---

### Gold Layer — Two curated analytics datasets

**`{catalog}.03_gold.daily_ride_summary`**

Aggregated daily metrics across all trips:

| Metric | Description |
|---|---|
| `total_trips` | Count of rides per day |
| `avg_trip_duration_mins` | Average ride duration |
| `max_trip_duration_mins` | Longest ride |
| `min_trip_duration_mins` | Shortest ride |

**`{catalog}.03_gold.daily_station_performance`**

Station-level daily performance breakdown:

| Metric | Description |
|---|---|
| `total_trips` | Trips originating from station per day |
| `avg_trip_duration_mins` | Average duration for station's trips |

---

### Two Orchestration Approaches

The project implements the same medallion pipeline two ways — demonstrating both DLT and traditional Databricks Jobs:

| Approach | Config File | When to Use |
|---|---|---|
| **Delta Live Tables** | `citibike_etl_pipeline.dlt.yml` | Managed pipelines, built-in retry/restart, auto-scaling |
| **Databricks Job** | `citibike_etl_pipeline_job.yml` | Fine-grained task control, custom cluster configs, mixed task types |

**DLT Pipeline** — 4 notebook libraries chained in order. This is the only part of the project on serverless compute (with Photon enabled).

**Traditional Job** — 5 tasks with explicit dependencies, all running on the classic `n2-highmem-4` cluster (DBR `15.4.x-scala2.12`) defined in `clusters.yml`:

```
00_whl_upload
    │
    ├──▶ 01_bronze_citibike
    │         │
    │         ▼
    │    02_silver_citibike
    │         │
    │    ┌────┴────┐
    │    ▼         ▼
    │  03_gold   03_gold
    │  _daily    _station
    │  _ride     _performa
    │  _summary  nce
```

---

## Multi-Environment Setup

The project uses **three isolated Databricks workspaces** backed by **Unity Catalog** for clean environment separation.

| Environment | Catalog | Mode | Purpose |
|---|---|---|---|
| `dev` | `citibike_development` | Development | Local iteration, feature work |
| `test` | `citibike_test` | Production | Integration testing, pre-release validation |
| `prod` | `citibike_production` | Production | Live, governed data |

Environment is selected at deploy time:

```bash
databricks bundle deploy --target dev
databricks bundle deploy --target test
databricks bundle deploy --target prod
```

**Unity Catalog** enforces consistent schema naming (`catalog.schema.table`) and access controls across all three environments.

---

## Local Development

### Prerequisites

- Python 3.11+
- Java 11+ (for local Spark)
- Databricks CLI

### Option 1 — Local PySpark (no cluster required)

```bash
pip install -r requirements-pyspark.txt
pytest tests/ --cov=src --cov-report=html
```

Uses a local `SparkSession` configured in `tests/conftest.py`.

### Option 2 — Databricks Connect (remote cluster)

```bash
pip install -r requirements-dbc.txt
databricks auth login
```

Connects your local IDE directly to a Databricks cluster via `databricks-connect`. This is the primary development path for this project — all pipeline code, including the DLT notebooks, was built against an attached DBR 15.4 cluster, since Databricks Connect needs a cluster to run against. The DLT pipeline only becomes serverless once deployed.

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_citibike_utils.py -v
```

Test coverage artifacts are generated in `htmlcov/`.

---

## CI/CD Pipeline

### CI — Continuous Integration (`ci-workflow.yml`)

Triggers on: **feature branches** and **pull requests to main**

```
Push to feature/* or PR opened
        │
        ▼
  Setup Python 3.11
        │
        ▼
  pip install dependencies
        │
        ▼
  pytest --cov (unit tests)
        │
        ▼
  Upload coverage artifacts
```

### CD — Continuous Deployment (`cd-workflow.yml`)

Triggers on: **push to main**

```
Merge to main
      │
      ▼
Deploy to TEST workspace
  (DATABRICKS_TEST_TOKEN)
      │
      ▼ (on success)
Deploy to PROD workspace
  (DATABRICKS_PROD_TOKEN)
```

**Required GitHub Secrets:**

| Secret | Environment |
|---|---|
| `DATABRICKS_TEST_TOKEN` | Test workspace PAT |
| `DATABRICKS_PROD_TOKEN` | Prod workspace PAT |

---

## Dashboards

Two Power BI dashboards consume the curated Gold layer tables for operational insights.

### Daily Ride Summary

High-level overview of daily Citibike operations — total trips, average/max/min duration, and usage trends over time.

![Daily Summary Dashboard](https://github.com/Uche-anya/citibike_project/blob/main/dashboards/daily%20ride%20summary.png?raw=true)

### Daily Station Performance

Station-level breakdown — top stations by total trip volume and average trip duration.

![Daily Station Performance Dashboard](https://github.com/Uche-anya/citibike_project/blob/main/dashboards/daily%20station%20performance.png?raw=true)

Both dashboards connect directly to Databricks Gold layer tables via **Power BI DirectQuery or Import mode**.

The Power BI source file is available at [dashboards/citibike project.pbix](dashboards/citibike%20project.pbix).

---

## Getting Started

### 1. Install the Databricks CLI

```bash
pip install databricks-cli
databricks configure --token
```

### 2. Clone and install dependencies

```bash
git clone <repo-url>
cd citibike-etl-pipeline
pip install -r requirements-pyspark.txt
```

### 3. Validate the bundle

```bash
databricks bundle validate
```

### 4. Deploy to dev

```bash
databricks bundle deploy --target dev
```

### 5. Run the pipeline

```bash
# Run the DLT pipeline
databricks bundle run citibike_etl_pipeline --target dev

# Or run the job version
databricks bundle run citibike_etl_pipeline_nb --target dev
```

---

## Authentication

### Current — Personal Access Tokens (PATs)

Configured as GitHub Actions secrets (`DATABRICKS_TEST_TOKEN`, `DATABRICKS_PROD_TOKEN`). Simple to set up, sufficient for most team workflows.

### Planned — GCP Service Account JSON

For enterprise-grade security:
- Native to GCP IAM
- Supports fine-grained permissions and audit logging
- Fully supported by Databricks CLI via `google-credentials` auth type
- Eliminates token rotation overhead

---

##KeyDesign Decisions

**Dual pipeline implementations** (DLT + traditional job) — demonstrates flexibility and lets teams choose the orchestration model that fits their use case without rewriting transformation logic.

**Python wheel packaging** — ETL utilities are packaged as `.whl` files and installed on the cluster, ensuring the same tested code runs locally and in all environments.

**Unity Catalog-first** — All tables use three-part naming (`catalog.schema.table`), making environment promotion


