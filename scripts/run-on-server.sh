#!/bin/bash
# Run on VPS after deploy. Usage: ./scripts/run-on-server.sh

set -e
cd "$(dirname "$0")/.."

echo "Starting Instagram Viral Bot..."
docker compose up -d --build

echo "Containers:"
docker compose ps

echo ""
echo "To view bot logs: docker compose logs -f bot"
