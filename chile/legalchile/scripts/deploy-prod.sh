#!/bin/bash
set -e

echo "=== Deploying legalchile to PRODUCTION ==="

# Safety check
read -p "Are you sure you want to deploy to PRODUCTION? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 1
fi

# Build production images
docker compose -f docker-compose.prod.yml build

# Push images (adjust registry as needed)
# docker push your-registry/legalchile-backend:latest

echo "=== Production deployment complete ==="
