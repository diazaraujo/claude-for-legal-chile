#!/bin/bash
set -e

echo "=== Setting up legalchile local environment ==="

# Copy env files if they don't exist
cp -n .env.example .env 2>/dev/null || true
cp -n backend/.env.example backend/.env 2>/dev/null || true
cp -n frontend/.env.example frontend/.env 2>/dev/null || true

# Build and start
docker compose build
docker compose up -d

echo ""
echo "=== Setup complete ==="
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000/api/"
echo "Admin:    http://localhost:8000/admin/"
echo ""
echo "Create a superuser: make createsuperuser"
