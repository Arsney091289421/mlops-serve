## Project Overview

This repository provides a batch inference and prediction service for GitHub open issues, optimized for daily automated runs on AWS EC2, but also runnable locally.

> **Note:** This service is designed to work together with [MLOps-Sandbox-for-github-issues](https://github.com/Arsney091289421/MLOps-Sandbox-for-github-issues),  
> which handles issue collection, model training, and model upload to S3.  
> This repo focuses on scheduled prediction, result export, and serving inference APIs.

All core features (model download, prediction, API serving, CSV export) are available both in the cloud and locally, as long as environment variables and AWS credentials are configured.

## Features

- Automated daily batch inference and prediction for GitHub open issues
- Scheduled workflow via local cron job (or Prefect)
- Model and result synchronization with S3
- Real-time prediction and CSV export via RESTful API (FastAPI)
- Built-in monitoring with Prometheus and Grafana
- Easy deployment with Docker and docker-compose
- Integrated CI/CD pipeline for EC2 auto-deployment

## Tech Stack

- Python 3.9
- FastAPI
- XGBoost
- Docker & docker-compose
- AWS S3 / EC2 / SSM / IAM
- Prometheus, Pushgateway, Grafana

## System Architecture

![System Architecture](docs/architecture.svg)

## Quick Start

### Prerequisites

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

### 4.2 Deployment

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

