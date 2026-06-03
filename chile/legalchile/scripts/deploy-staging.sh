#!/bin/bash
set -e

echo "=== Deploying legalchile to STAGING ==="

# Build production images
docker compose -f docker-compose.staging.yml build

# Push images (adjust registry as needed)
# docker push your-registry/legalchile-backend:staging

echo "=== Staging deployment complete ==="
