#!/bin/bash
set -e

# 1. Force the script to switch to the directory where this file is located
# This ensures 'docker compose' finds your yaml file, even if you run the script from elsewhere.
cd "$(dirname "$0")"

echo "=== Updating n8n ==="
# 2. Rebuild and restart containers
docker compose build --no-cache --pull
docker compose down
docker compose up -d

echo ""
echo "=== Waiting for n8n to start... ==="
# We wait 10s to ensure the database is ready for the import command
sleep 10

echo "=== Checking Versions ==="
docker exec n8n n8n --version
docker exec n8n npm list n8n-nodes-checkmk 2>/dev/null | grep checkmk || true

echo ""
echo "=== Importing Workflows ==="
# 3. execute the import command INSIDE the running container
# 'docker exec' sends the command into the container named 'n8n'
docker exec n8n n8n import:workflow --input=/opt/n8n-examples/example-workflow.json
docker exec n8n n8n import:workflow --input=/opt/n8n-examples/monitoring-workflow.json
docker exec n8n n8n import:workflow --input=/opt/n8n-examples/snipeit-to-checkmk-sync.json

echo ""
echo "Done! Access at http://localhost:5678"
