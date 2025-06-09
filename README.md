## 1. Project Overview

This repository provides a batch inference and prediction service for GitHub open issues, optimized for daily automated runs on AWS EC2, but also runnable locally.

> **Note:** This service is designed to work together with [MLOps-Sandbox-for-github-issues](https://github.com/Arsney091289421/MLOps-Sandbox-for-github-issues),  
> which handles issue collection, model training, and model upload to S3.  
> This repo focuses on scheduled prediction, result export, and serving inference APIs.

All core features (model download, prediction, API serving, CSV export) are available both in the cloud and locally, as long as environment variables and AWS credentials are configured.

## 2. Features

- Automated daily batch inference and prediction for GitHub open issues
- Scheduled workflow via local cron job (or Prefect)
- Model and result synchronization with S3
- Real-time prediction and CSV export via RESTful API (FastAPI)
- Built-in monitoring with Prometheus and Grafana
- Easy deployment with Docker and docker-compose
- Integrated CI/CD pipeline for EC2 auto-deployment

## 3. Tech Stack

- Python 3.9
- FastAPI
- XGBoost
- Docker & docker-compose
- AWS S3 / EC2 / SSM / IAM
- Prometheus, Pushgateway, Grafana

## 4. System Architecture

![System Architecture](docs/architecture.svg)

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
> Note:  
> - You do **not** need to specify `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` when running on EC2 with the correct IAM role attached.
> - The `MODEL_BUCKET` environment variable is still required, even when using IAM roles, to specify the target S3 bucket name.

### 5.2 Deployment

1. **Clone the repository**

   ```bash
   git clone https://github.com/Arsney091289421/mlops-serve.git
   cd mlops-serve
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env to match your S3 bucket and output directory settings
   ```

3. **Start all services with Docker Compose**

   ```bash
   docker compose up --build -d
   ```

4. **Check that services are running**

- FastAPI docs: `http://YOUR_EC2_IP:8000/docs`
- Prometheus: `http://YOUR_EC2_IP:9090/`
- Grafana: `http://YOUR_EC2_IP:3000/` (default password: `admin`)

## 6. Workflow & Automation

The full workflow is handled by `workflow.py` (downloads latest model → runs inference on open issues → uploads results to S3).

**Recommended:** Use cron on your EC2 instance to schedule daily automatic runs.

### 6.1 Example: Setting up a daily cron job

1. SSH into your EC2 instance:

   ```bash
   ssh ec2-user@YOUR_EC2_PUBLIC_IP
   ```

2. Edit your crontab:

   ```bash
   crontab -e
   ```

3. Add the following line to run `workflow.py` every day at 5:00 AM UTC:

   ```cron
   0 5 * * * cd /home/ec2-user/mlops-serve && /usr/bin/python3 workflow.py >> /home/ec2-user/mlops-serve/workflow_cron.log 2>&1
   ```
   
   - Logs will be saved to `workflow_cron.log` in the project directory

4. Check your current cron jobs:

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


