# legalchile

Prototype application scaffold.

## Stack

| Layer      | Technology |
|------------|------------|
| Frontend   | React + Vite + TypeScript + Tailwind CSS + shadcn/ui |
| Backend    | Django + Django Ninja |
| Database   | PostgreSQL |
| Hosting    | Frontend: Vercel · Backend: Docker container |
| CI/CD      | GitHub Actions |

## Quick Start

```bash
# 1. Copy environment variables
cp .env.example .env

# 2. Build and start everything
make setup
make run
```

| Service  | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| Backend  | http://localhost:8000/api/ |
| API Docs | http://localhost:8000/api/docs || Admin    | http://localhost:8000/admin/ |

## Common Commands

```bash
make run              # Start all services
make stop             # Stop all services
make logs             # Tail logs
make test             # Run all tests
make lint             # Run linters
make migrate          # Run Django migrations
make createsuperuser  # Create admin user
make shell            # Django shell
make fe-add-component # Add a shadcn/ui component
```

## Deploy

```bash
make deploy-staging   # Deploy to staging
make deploy-prod      # Deploy to production
```

## Project Structure

```
legalchile/
├── frontend/         # React + Vite app
├── backend/          # Django API
├── scripts/          # Deploy and setup scripts
├── .github/          # CI/CD workflows
└── docker-compose.*  # Docker configs per environment
```
