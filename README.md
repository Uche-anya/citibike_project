# Citibike ETL Pipeline – CI/CD on Databricks (GCP)

This project implements a **production-ready ETL pipeline** for the **Citibike dataset** on **Databricks (GCP)**, showcasing:

- **Medallion architecture** (Bronze → Silver → Gold) using Delta Live Tables (DLT)  
- **Environment separation** (Dev, Test, Prod) with Unity Catalog governance  
- **CI/CD automation** to deploy transformations across environments  
- **Local development & testing** with PySpark + Pytest  
- **Power BI dashboards** for actionable insights  

---

## Key Features

### 🔹 Multi-Environment Setup
- Separate **Databricks Workspaces** for Dev, Test, and Prod  
- **Unity Catalog** ensures consistent governance & security across environments  
- Shared **GCS Buckets** for managed and external storage  

### 🔹 Medallion ETL Architecture
- **Bronze Layer** → Raw Citibike data ingestion (DLT pipeline)  
- **Silver Layer** → Cleaned & enriched data (applied business rules)  
- **Gold Layer** → Curated analytics-ready datasets  

### 🔹 Code Packaging & Distribution
- ETL transformations modularized into **Python packages**  
- Packaged as **Wheels (.whl)** and installed on Databricks clusters  
- Ensures **reproducibility and versioning** across environments  

### 🔹 Local Development & Testing
- Local **SparkSession** for development without cluster costs  
- **Pytest** for unit tests  
- **`conftest.py`** centralizes fixtures for consistent test setup  

### 🔹 CI/CD Deployment
- **GitHub Actions workflow** (`cd-workflow.yml`)  
- Deploys code and pipelines to **Dev → Test → Prod**  
- **Current authentication**: Personal Access Tokens (PATs) for Test/Prod  
- **Future plan**: Service Account JSON auth (more secure & GCP-native)  

---

## 🔹 Visualization / Dashboards

To make the Citibike data actionable, the project includes two **Power BI dashboards** built on the curated Gold layer:

1. **Daily Summary Dashboard**  
   - Provides a high-level overview of Citibike operations each day  
   - Key metrics: total trips, average trip duration, and active stations  
   - Trend charts for usage over time  

2. **Daily Station Performance Dashboard**  
   - Analyzes performance per station  
   - Top stations by total trips or average duration   

💡 **Integration**:  
- Both dashboards use **Power BI DirectQuery or imported Gold layer tables** from Databricks    

---

## Authentication

### Current (Short-Term)
- **Personal Access Tokens (PATs)** for Test & Prod deployments  
- Simple to configure but **not ideal for long-term**  

### Future (Long-Term)
- **Service Account JSON authentication**  
- Native to GCP, secure, and fully supported by Databricks CLI  
- Recommended for **enterprise-grade CI/CD**  

---

## ✅ Benefits
- Reliable data pipeline with **Medallion layers** (Bronze → Silver → Gold)  
- Governed **multi-environment setup** with Unity Catalog  
- **Reproducible deployments** using GitHub Actions + Wheels  
- Confidence in changes with **local PySpark + pytest** workflow  
- Actionable insights via **Power BI dashboards**  
- Future-proofed security by migrating to **service account–based auth**  

---

👉 This README tells the story of your **Citibike pipeline**, emphasizes the **Medallion architecture**, incorporates **CI/CD + governance**, and highlights **dashboards for visualization**.
