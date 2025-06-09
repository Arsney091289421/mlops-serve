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
- **Required environment variables** configured (`.env`, see `.env.example`)
  - You do **not** need to specify `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` in `.env` when running on EC2 with the correct IAM role
- **GitHub Actions CD**
  - A dedicated IAM user with `AmazonSSMFullAccess` to enable remote deployment via SSM in your GitHub Actions workflow
  - Store the following as GitHub repository secrets:
    - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `EC2_INSTANCE_ID`

