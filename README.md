# Issue-Copilot — Batch Inference & API Serve

[![CI](https://github.com/Arsney091289421/mlops-serve/actions/workflows/ci.yml/badge.svg)](…)
[![Deploy](https://github.com/Arsney091289421/mlops-serve/actions/workflows/cd.yml/badge.svg)](…)

Predict whether a **new _transformers_ GitHub issue will close within 7 days**,  
with a fully-automated batch pipeline (EC2/cron) **or** one-shot local run.

> **Training repo:** [`MLOps-Sandbox-for-github-issues`](https://github.com/Arsney091289421/MLOps-Sandbox-for-github-issues)  
> collects data, hyper-tunes XGBoost, uploads `latest_model.json` to **S3**.  
> **This repo:** pulls the model, runs inference on open issues, exports CSV,  
> and serves real-time predictions via **FastAPI**.

---

## Features

| Category | What you get |
|----------|--------------|
| **Daily batch inference** | `cron` *(or Prefect)* job on EC2 |
| **Model sync** | auto-download newest model from **S3** (+ history keep) |
| **Real-time API** | `/predict` & `/export` endpoints (*FastAPI + Swagger*) |
| **Observability** | Prometheus metrics to Grafana dashboard (P95, error-rate) |
| **One-command deploy** | `docker compose up -d` ／ GitHub Actions - **SSM** Blue-Green |
| **Tested** | `pytest` + **moto** S3 mocks in CI |

---

## Tech Stack
`Python 3.9` · **FastAPI** · **XGBoost** · Docker / docker-compose  
**AWS S3 · EC2 · SSM · IAM**  
**Prometheus & Pushgateway • Grafana**  
**GitHub Actions** (CI + CD) • `pytest` · `moto`

---
## System Architecture

![System Architecture](docs/architecture.svg)

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Features](#2-features)
3. [Tech Stack](#3-tech-stack)
4. [System Architecture](#4-system-architecture)
5. [Quick Start](#5-quick-start)
    - [Prerequisites](#51-prerequisites)
    - [Deployment](#52-deployment)
6. [Workflow & Automation](#6-workflow--automation)
    - [Setting up a cron job](#61-example-setting-up-a-daily-cron-job)
    - [Prometheus Metrics](#62-prometheus-metrics)
    - [Why cron?](#63-why-cron)
7. [API Usage](#7-api-usage)
    - [Endpoints & Description](#71-endpoints--description)
    - [Example: Export & Predict API](#72-example-export--predict-api)
    - [Interactive API Docs](#73-interactive-api-docs-swagger-ui)
8. [Docker/Compose Configuration](#8-dockercompose-configuration)
    - [Services & Ports](#81-services--ports)
    - [Volume Mounts & Data Persistence](#82-volume-mounts--data-persistence)
    - [Directory Permissions](#83-directory-permissions-required-for-prometheus)
9. [Testing](#9-testing)
    - [How to run tests](#91-how-to-run-tests)
10. [FAQ](#10-faq)
11. [Maintainers & Contact](#11-maintainers--contact)

## 5. Quick Start

### 5.1 Prerequisites

- **AWS account**
  - An S3 bucket for storing models and prediction results
  - An EC2 instance (Amazon Linux, Python 3.9+ recommended)
    - EC2 instance must have [AWS SSM Agent](https://docs.aws.amazon.com/systems-manager/latest/userguide/ssm-agent.html) running
    - EC2 instance must be attached to an IAM role with at least:
      - `AmazonS3FullAccess` (for S3 access without explicit credentials)
      - `AmazonSSMManagedInstanceCore` (for SSM remote management)
- **Docker & docker-compose** installed on the EC2 instance
- **GitHub Actions CD**
  - A dedicated IAM user with `AmazonSSMFullAccess` to enable remote deployment via SSM in your GitHub Actions workflow
  - Store the following as GitHub repository secrets:
    - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `EC2_INSTANCE_ID`
- **Required environment variables** (see `.env.example` for details):
  - `MODEL_DIR`: Local path to store/download the model (default: `./model` if not specified)
  - `GITHUB_TOKEN`: Your GitHub Personal Access Token  
    - Only the `public_repo` scope is required (for reading public repositories and issues)
  - `MODEL_BUCKET`: Name of your S3 bucket for storing models and prediction outputs
> **Note**:  You do **not** need to specify `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` when running on EC2 with the correct IAM role attached.
> The `MODEL_BUCKET` environment variable is still required, even when using IAM roles, to specify the target S3 bucket name.

### 5.2 Deployment

1. **Clone the repository**

   ```bash
   git clone https://github.com/Arsney091289421/mlops-serve.git
   cd mlops-serve
   ```

2. **Install Python Dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

   * `requirements.txt` includes core dependencies needed to run the application.
   * The `-e .` flag installs the project in editable mode, allowing clean cross-module imports without modifying `sys.path`.

3. **(Optional) For Development and Testing**

   ```bash
   pip install -r requirements-dev.txt
   ```

   * Only needed for development and testing.
   * Includes tools like `pytest` and `moto[s3]` (for mocking AWS S3).
   * Not required in production, helping reduce unnecessary dependencies.

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env to match your S3 bucket, GitHub token, and output directory settings
   ```

5. **Start all services with Docker Compose**

   ```bash
   docker compose up --build -d
   ```

6. **Check that services are running**

   - FastAPI docs: `http://YOUR_EC2_IP_OR_LOCALHOST:8000/docs`
   - Prometheus: `http://YOUR_EC2_IP_OR_LOCALHOST:9090/`
   - Grafana: `http://YOUR_EC2_IP_OR_LOCALHOST:3000/` (default password: `admin`)

## 6. Workflow & Automation

The full workflow is handled by `workflow.py` (downloads latest model → runs inference on open issues → uploads results to S3).

**Recommended:** Use cron on your EC2 instance to schedule daily automatic runs.

### 6.1 Example: Setting up a daily cron job

1. **SSH into your EC2 instance**

   ```bash
   ssh ec2-user@YOUR_EC2_PUBLIC_IP
   ```

2. **Edit your crontab**

   ```bash
   crontab -e
   ```

3. **Add the following line to run `workflow.py` every day at 5:00 AM UTC**

   ```cron
   0 5 * * * cd /home/ec2-user/mlops-serve && /usr/bin/python3 workflow.py >> /home/ec2-user/mlops-serve/workflow_cron.log 2>&1
   ```
   
   - Logs will be saved to `workflow_cron.log` in the project directory

4. **Check your current cron jobs**

   ```bash
   crontab -l
   ```

### 6.2 Prometheus Metrics

Each workflow run pushes metrics to Prometheus Pushgateway for monitoring.  
Metrics sent:

```python
metric = f'workflow_status{{job="{job_name}"}} {status}\n'
metric += f'workflow_last_run{{job="{job_name}"}} {int(datetime.now().timestamp())}\n'
```

- `workflow_status{job="predict_upload"}`: 1 (success) or 0 (fail)
- `workflow_last_run{job="predict_upload"}`: UNIX timestamp of last run

### 6.3 Why cron?

- Cron is lightweight and reliable—ideal for always-on EC2 servers and simple batch jobs.
- If you need more advanced orchestration, `workflow.py` can be directly scheduled or integrated with Prefect, Airflow, or any other workflow scheduler.

## 7. API Usage

### 7.1 Endpoints & Description

By default, the API server runs in the Docker container on **port 8000**.

| Endpoint                      | Method | Description                                 | Parameters                         |
|-------------------------------|--------|---------------------------------------------|-------------------------------------|
| `/predict_recent_open_issues` | GET    | Predict open issues in the last N days      | `days` (query, int, default=1)      |
| `/predict_by_ids`             | POST   | Predict by specific GitHub issue numbers    | `ids` (body, List[int])             |
| `/export_predictions`         | GET    | Export CSV for open issues in last N days   | `days` (query, int, default=1)      |
| `/export_predictions_by_ids`  | POST   | Export CSV for specific issue numbers       | `ids` (body, List[int])             |

All responses (except CSV download) are in JSON format.

### 7.2 Example: Export & Predict API 

1. **Export Predictions for Recent 1 Day as CSV**

```bash
curl -O -J "http://localhost:8000/export_predictions?days=1"
```

---

2. **Predict by Issue IDs**

```bash
curl -X POST "http://localhost:8000/predict_by_ids" \
  -H "Content-Type: application/json" \
  -d '{"ids": [12345, 12346, 12347]}'
```

---

3. **Export Predictions by Issue IDs as CSV**

```bash
curl -X POST "http://localhost:8000/export_predictions_by_ids" \
  -H "Content-Type: application/json" \
  -d '{"ids": [12345, 12346, 12347]}' \
  -OJ
```


### 7.3 Interactive API Docs (Swagger UI)

You can browse and test all endpoints interactively via Swagger/OpenAPI UI:

- `http://YOUR_EC2_IP_OR_LOCALHOST:8000/docs` (Swagger UI)  
- `http://YOUR_EC2_IP_OR_LOCALHOST:8000/redoc` (ReDoc)

## 8. Docker/Compose Configuration

### 8.1 Services & Ports

| Service      | Description                  | Default Port |
|--------------|-----------------------------|--------------|
| serve        | Model inference API (FastAPI)| 8000         |
| prometheus   | Prometheus metrics           | 9090         |
| pushgateway  | Prometheus Pushgateway       | 9091         |
| grafana      | Grafana dashboard            | 3000         |

### 8.2 Volume Mounts & Data Persistence

| Service    | Local Path                  | Container Path / Notes           | Purpose                          |
|------------|-----------------------------|----------------------------------|-----------------------------------|
| serve      | `./model/`                  | `/app/model/`                    | Store/download model files        |
| serve      | `./predict_outputs/`        | `/app/predict_outputs/`          | Store prediction results (CSV, etc.) |
| prometheus | `./prometheus-data/`        | `/prometheus`                    | Persist Prometheus data           |
| prometheus | `./prometheus.yml`          | `/etc/prometheus/prometheus.yml` | Prometheus config                 |
| grafana    | `./grafana-data/`           | `/var/lib/grafana`               | Persist Grafana dashboards        |

- All prediction results and models are **persisted on the host machine** and accessible outside of Docker.
- If the output/model directories (`model/`, `predict_outputs/`) do not exist, Docker Compose will automatically create them when starting services.
- You can manually inspect or back up all data by accessing the corresponding local directories.

### 8.3 Directory Permissions (Required for Prometheus)

Before starting Docker Compose, set correct permissions for Prometheus data directory to allow container read/write access:

```bash
sudo chown -R 65534:65534 /home/ec2-user/mlops-serve/prometheus-data
sudo chmod -R 755 /home/ec2-user/mlops-serve/prometheus-data
```

- This ensures Prometheus can read and write its data files inside the container.

> **Note**: No need to manually mount extra volumes unless you want to store data elsewhere—by default, all important data is already persisted to the project directory.
> Ensure the host user running Docker has read/write permissions on these directories.
> API prediction/export endpoints will read and write from the same local directories, so both cron jobs and API share the latest data.

## 9. Testing

- All basic and smoke tests are located in the `tests/` directory.
  - Tests cover import checks, S3 mock upload/download, feature extraction with mocked issues, and model prediction logic.
- Most tests use `pytest` and `moto` to mock S3 operations, ensuring no real AWS charges or side effects.

### 9.1 How to run tests

1. **Install test dependencies (if not already installed):**
   ```bash
   pip install -r requirements-dev.txt
   # Or, at minimum:
   pip install pytest moto
   ```

2. **Run all tests:**
   ```bash
   pytest tests/
   ```

3. **Expected:**
   - All tests should pass (green).
   - No actual S3/AWS resources are created or billed.

> **Note**: The test suite is designed to ensure critical components can be imported and run, and that S3/model logic works as expected, even without real AWS credentials.
> You can add more tests under `tests/` as needed.

## 10. FAQ

**Workflow didn’t run as scheduled?**  
→ Check `crontab -l` to verify the schedule. Make sure your cron time matches the EC2 timezone (`date`), and confirm there are no typos or incorrect paths.

**S3 access denied or permission errors?**  
→ Ensure your EC2 instance has an IAM role with `AmazonS3FullAccess`, and that your `.env` has the correct `MODEL_BUCKET`.

**GitHub Actions CD failed, and nothing shows on the EC2 host?**  
→ Visit the [AWS SSM Console](https://console.aws.amazon.com/systems-manager/run-command/) to view Run Command logs.  
Use AWS Fleet Manager to inspect the instance and debug execution results.

## 11. Maintainers & Contact

- Maintainer: [Arsney091289421](https://github.com/Arsney091289421)
- Email: leearseny3@gmail.com
- Feedback and issues are welcome—please use [GitHub Issues](https://github.com/Arsney091289421/mlops-serve/issues)


