#!/bin/bash
set -e

# Paths (adjust if needed)
ISSUER_KEYPAIR="/home/arpit/issuer_keypair.json"
RECIPIENT_KEYPAIR="$HOME/recipient_keypair.json"
CERT_FILE="real_certificate.pdf"
CERT_BUNDLE="cert_bundle.json"
ANCHOR_RESP="anchor_resp.json"

# 1️⃣ Check issuer keypair
if [ ! -f "$ISSUER_KEYPAIR" ]; then
  echo "Issuer keypair not found at $ISSUER_KEYPAIR"
  exit 1
fi
echo "Issuer keypair found:"
solana-keygen pubkey "$ISSUER_KEYPAIR"

# 2️⃣ Check recipient keypair
if [ ! -f "$RECIPIENT_KEYPAIR" ]; then
  echo "Recipient keypair not found at $RECIPIENT_KEYPAIR"
  exit 1
fi
RECIPIENT_PUB=$(solana-keygen pubkey "$RECIPIENT_KEYPAIR")
echo "Recipient public key: $RECIPIENT_PUB"

# 3️⃣ Generate cert_bundle.json
echo "Generating cert_bundle.json..."
curl -s -X POST "http://127.0.0.1:8000/api/process" \
  -F "file=@$CERT_FILE" \
  -F "recipient_pub=$RECIPIENT_PUB" \
  -o "$CERT_BUNDLE"

if [ ! -f "$CERT_BUNDLE" ]; then
  echo "Failed to generate cert_bundle.json"
  exit 1
fi
echo "cert_bundle.json created successfully."
cat "$CERT_BUNDLE" | jq .

# 4️⃣ Call Anchor endpoint
echo "Sending transaction to Anchor..."
curl -s -X POST "http://127.0.0.1:8000/api/cert/anchor" \
  -F "core_hash=$(jq -r .core_hash $CERT_BUNDLE)" \
  -F "ipfs_cid=$(jq -r .ipfs_cid $CERT_BUNDLE)" \
  -F "metadata=$(jq -c .metadata $CERT_BUNDLE)" \
  -F "recipient_pub=$RECIPIENT_PUB" \
  -F "signer_keypair_path=$ISSUER_KEYPAIR" \
  -o "$ANCHOR_RESP"

echo "Anchor response:"
cat "$ANCHOR_RESP" | jq .
