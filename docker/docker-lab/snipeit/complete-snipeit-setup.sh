#!/bin/bash
set +e

ASSETS_FILE="${1:-assets-inventory.txt}"

echo "========================================="
echo "  Complete Snipe-IT Setup"
echo "========================================="
echo ""

# Step 1: Docker Setup
echo "Step 1: Docker Setup"
echo "  Fresh start? (deletes all data) [y/N]:"
read -r FRESH_START

if [[ "$FRESH_START" =~ ^[Yy]$ ]]; then
  echo "  🗑️  Removing all data..."
  docker compose down -v
else
  docker compose down
fi

echo "  🚀 Starting containers..."
docker compose up -d

echo "  ⏳ Waiting for services (90s)..."
sleep 90

# Wait for Snipe-IT to be ready
MAX_RETRIES=10
for i in $(seq 1 $MAX_RETRIES); do
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 || echo "000")
  if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "302" ]; then
    echo "  ✅ Snipe-IT is ready!"
    break
  fi
  echo "  ⏳ Waiting... ($i/$MAX_RETRIES)"
  sleep 10
done
echo ""

# Step 2: Manual Setup
echo "========================================="
echo "  📋 MANUAL STEPS (2-3 minutes)"
echo "========================================="
echo ""
echo "1. Open: http://localhost:8000"
echo "2. Click 'Next: Create Database Tables'"
echo "3. Create admin user:"
echo "     Username: admin"
echo "     Password: admin"
echo "     (fill in other fields)"
echo "4. Complete setup"
echo "5. Create API Token:"
echo "     Click your name → Manage API Keys"
echo "     → Create New Token → Copy it!"
echo ""
read -p "Press Enter when done and you have your token..."
echo ""

# Step 3: Get Token
echo "Paste your API token:"
read -r API_TOKEN

if [ -z "$API_TOKEN" ]; then
  echo "❌ No token provided"
  exit 1
fi

echo "$API_TOKEN" > .snipeit-token
#that part is necessary as I run docker with sudo
sudo chmod 644 .snipeit-token
sudo chown $USER:$USER .snipeit-token

# Verify token
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  "http://localhost:8000/api/v1/statuslabels" \
  -H "Authorization: Bearer ${API_TOKEN}")

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Token verification failed"
  exit 1
fi
echo "✅ Token verified"
echo ""

# Step 4: Create Base Data
echo "========================================="
echo "  🏗️  Creating Base Data"
echo "========================================="
echo ""

API_URL="http://localhost:8000/api/v1"

api_call() {
  curl -s -X "$1" "${API_URL}$2" \
    -H "Authorization: Bearer ${API_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d "$3"
}

# Category
echo "Creating category..."
CATEGORY_RESPONSE=$(api_call POST "/categories" '{"name":"Servers","category_type":"asset"}')
CATEGORY_ID=$(echo "$CATEGORY_RESPONSE" | jq -r '.payload.id // .id // empty')
[ -z "$CATEGORY_ID" ] && CATEGORY_ID=$(curl -s "${API_URL}/categories" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')
echo "  ✅ Category: $CATEGORY_ID"

# Manufacturer
echo "Creating manufacturer..."
MANUFACTURER_RESPONSE=$(api_call POST "/manufacturers" '{"name":"Generic"}')
MANUFACTURER_ID=$(echo "$MANUFACTURER_RESPONSE" | jq -r '.payload.id // .id // empty')
[ -z "$MANUFACTURER_ID" ] && MANUFACTURER_ID=$(curl -s "${API_URL}/manufacturers" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')
echo "  ✅ Manufacturer: $MANUFACTURER_ID"

# Model
echo "Creating model..."
MODEL_RESPONSE=$(api_call POST "/models" "{\"name\":\"Generic Server\",\"model_number\":\"GEN-001\",\"category_id\":$CATEGORY_ID,\"manufacturer_id\":$MANUFACTURER_ID}")
MODEL_ID=$(echo "$MODEL_RESPONSE" | jq -r '.payload.id // .id // empty')
[ -z "$MODEL_ID" ] && MODEL_ID=$(curl -s "${API_URL}/models" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')
echo "  ✅ Model: $MODEL_ID"

# Status
STATUS_ID=$(curl -s "${API_URL}/statuslabels" -H "Authorization: Bearer ${API_TOKEN}" | jq -r '.rows[0].id')
echo "  ✅ Status: $STATUS_ID"
echo ""

# Step 5: Add Assets
if [ ! -f "$ASSETS_FILE" ]; then
  echo "⚠️  No assets file found: $ASSETS_FILE"
  echo "Skipping asset import"
else
  echo "========================================="
  echo "  📦 Adding Assets from: $ASSETS_FILE"
  echo "========================================="
  echo ""
  
  SUCCESS=0
  FAILED=0
  
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^#.*$ ]] && continue
    [[ -z "$line" ]] && continue
    
    IFS=':' read -r hostname ip os_type description <<< "$line"
    [ -z "$hostname" ] && continue
    
    printf "  %-20s %-15s ... " "$hostname" "$ip"
    
    RESPONSE=$(api_call POST "/hardware" "{\"asset_tag\":\"$hostname\",\"status_id\":$STATUS_ID,\"model_id\":$MODEL_ID,\"name\":\"$hostname\",\"notes\":\"$description\\nOS: $os_type\\nIP: $ip\"}")
    
    if echo "$RESPONSE" | jq -e '.status == "success"' >/dev/null 2>&1; then
      echo "✅"
      ((SUCCESS++))
    else
      echo "❌"
      ((FAILED++))
    fi
  done < "$ASSETS_FILE"
  
  echo ""
  echo "Results: ✅ $SUCCESS  ❌ $FAILED"
fi

echo ""
echo "========================================="
echo "  🎉 Setup Complete!"
echo "========================================="
echo ""
echo "Snipe-IT:  http://localhost:8000"
echo "Username:  admin"
echo "Password:  admin"
echo "Token:     .snipeit-token"
echo ""
echo "Commands:"
echo "  docker compose ps        # Status"
echo "  docker compose logs -f   # Logs"
echo "  docker compose down      # Stop"
echo ""
