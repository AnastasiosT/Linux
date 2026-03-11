#!/bin/bash
set -e

ASSETS_FILE="${1:-assets-inventory.txt}"
API_TOKEN=$(cat .snipeit-token 2>/dev/null || echo "")

if [ -z "$API_TOKEN" ]; then
  echo "Error: No API token found in .snipeit-token"
  echo "Please run complete-snipeit-setup.sh first or create .snipeit-token"
  exit 1
fi

if [ ! -f "$ASSETS_FILE" ]; then
  echo "Error: Assets file not found: $ASSETS_FILE"
  echo "Usage: $0 [assets-file.txt]"
  exit 1
fi

API_URL="http://localhost:8000/api/v1"

echo "========================================="
echo "  Adding Assets from: $ASSETS_FILE"
echo "========================================="
echo ""

# Get required IDs
MODEL_ID=$(curl -s "${API_URL}/models" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')
STATUS_ID=$(curl -s "${API_URL}/statuslabels" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')

echo "Using Model ID: ${MODEL_ID}, Status ID: ${STATUS_ID}"
echo ""

SUCCESS=0
FAILED=0
SKIPPED=0

# Read file line by line
while IFS= read -r line || [ -n "$line" ]; do
  # Skip comments and empty lines
  [[ "$line" =~ ^#.*$ ]] && continue
  [[ -z "$line" ]] && continue
  
  # Parse line
  IFS=':' read -r hostname ip os_type description <<< "$line"
  
  # Skip if missing required fields
  if [ -z "$hostname" ] || [ -z "$ip" ]; then
    echo "⚠ Skipping invalid line: $line"
    ((SKIPPED++))
    continue
  fi
  
  printf "%-20s %-15s %-10s ... " "${hostname}" "${ip}" "[${os_type}]"
  
  # Create asset
  RESPONSE=$(curl -s -X POST "${API_URL}/hardware" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "{
      \"asset_tag\":\"${hostname}\",
      \"status_id\":${STATUS_ID},
      \"model_id\":${MODEL_ID},
      \"name\":\"${hostname}\",
      \"notes\":\"${description}\nOS: ${os_type}\nIP: ${ip}\"
    }")
  
  if echo "$RESPONSE" | jq -e '.status == "success"' > /dev/null 2>&1; then
    ASSET_ID=$(echo "$RESPONSE" | jq -r '.payload.id')
    echo "✓ (ID: ${ASSET_ID})"
    ((SUCCESS++))
  else
    ERROR=$(echo "$RESPONSE" | jq -r '.messages // "Unknown error"' 2>/dev/null | head -1)
    echo "✗ ${ERROR}"
    ((FAILED++))
  fi
done < "$ASSETS_FILE"

echo ""
echo "========================================="
echo "  Summary"
echo "========================================="
echo "Success:  ${SUCCESS}"
echo "Failed:   ${FAILED}"
echo "Skipped:  ${SKIPPED}"
echo ""
echo "View assets: http://localhost:8000/hardware"
