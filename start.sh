#!/bin/bash

# Start all Docker Compose services in detached mode
docker compose up -d

# Print access URLs for your services
echo ""
echo "Access your services:"
echo "- Grafana:     http://localhost:3000"
echo "- Prometheus:  http://localhost:9090"
echo "- Swagger UI:  http://localhost:8000/docs"
echo ""
