#!/bin/bash

mkdir -p certs

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout certs/key.pem -out certs/cert.pem \
  -subj "/CN=localhost" 2>/dev/null

docker compose up -d

echo ""
echo "Mattermost available at https://localhost"
echo "Wait ~30 seconds for it to fully start."
