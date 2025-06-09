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
