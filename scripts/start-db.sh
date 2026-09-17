#!/usr/bin/env bash
set -euo pipefail

echo "Starting PostgreSQL container..."
docker compose up -d db

echo "Waiting for PostgreSQL to be ready..."
until docker compose exec db pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done

echo "PostgreSQL is ready at localhost:5432 (database: cloudbox)"
