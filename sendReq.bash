PAYLOAD='{"event":"test_event","data":{"hello":"world"}}'
SECRET="helloworld"

# Calculate signature first and display it
SIGNATURE=$(echo -n "$PAYLOAD" | openssl sha256 -hmac "$SECRET" | awk '{print $2}')
echo "Calculated signature: $SIGNATURE"

# Send the request with the signature
curl -X POST http://localhost:5000/ingest/1 \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD" \
  -v  # Verbose output for debugging