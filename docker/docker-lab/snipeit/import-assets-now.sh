#!/bin/bash

API_TOKEN=$(cat .snipeit-token)
API_URL="http://localhost:8000/api/v1"
ASSETS_FILE="assets-inventory.txt"

MODEL_ID=$(curl -s "${API_URL}/models" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')
STATUS_ID=$(curl -s "${API_URL}/statuslabels" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')

echo "Importing all assets..."
echo ""

while IFS= read -r line || [ -n "$line" ]; do
  [[ "$line" =~ ^#.*$ ]] && continue
  [[ -z "$line" ]] && continue
  
  IFS=':' read -r hostname ip os_type description <<< "$line"
  [ -z "$hostname" ] && continue
  
  printf "%-20s ... " "$hostname"
  
  RESPONSE=$(curl -s -X POST "${API_URL}/hardware" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"asset_tag\":\"$hostname\",\"status_id\":$STATUS_ID,\"model_id\":$MODEL_ID,\"name\":\"$hostname\",\"notes\":\"$description OS:$os_type IP:$ip\"}")
  
  if echo "$RESPONSE" | jq -e '.status == "success"' >/dev/null 2>&1; then
    echo "✅"
  else
    ERROR=$(echo "$RESPONSE" | jq -r '.messages // "error"')
    echo "❌ $ERROR"
  fi
done < "$ASSETS_FILE"
