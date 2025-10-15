#!/bin/bash
# Quick API test script

BASE_URL="http://localhost:8000"

echo "🏥 Testing health endpoint..."
curl -s $BASE_URL/health | jq

echo -e "\n📝 Registering user..."
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}')
echo $REGISTER_RESPONSE | jq

TOKEN=$(echo $REGISTER_RESPONSE | jq -r '.token')

echo -e "\n👤 Getting current user..."
curl -s $BASE_URL/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n📱 Creating SMS verification..."
VERIFY_RESPONSE=$(curl -s -X POST $BASE_URL/verify/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "whatsapp"}')
echo $VERIFY_RESPONSE | jq

VERIFY_ID=$(echo $VERIFY_RESPONSE | jq -r '.id')

echo -e "\n🔍 Checking verification status..."
curl -s $BASE_URL/verify/$VERIFY_ID \
  -H "Authorization: Bearer $TOKEN" | jq

echo -e "\n✅ All tests complete!"
