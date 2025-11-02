#!/bin/bash
# Quick setup for self-signed SSL certificate (TESTING ONLY)

echo "🔒 Creating self-signed SSL certificate for testing..."

# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -newkey rsa:4096 -nodes \
  -out ssl/cert.pem \
  -keyout ssl/key.pem \
  -days 365 \
  -subj "/CN=192.168.120.110"

echo "✅ Self-signed certificate created!"
echo ""
echo "📝 Certificate files:"
echo "  - ssl/cert.pem"
echo "  - ssl/key.pem"
echo ""
echo "⚠️  WARNING: Self-signed certificates will show security warnings in browser"
echo "⚠️  Users will need to click 'Proceed Anyway' or 'Accept Risk'"
echo ""
echo "🚀 To use with FastAPI, install uvicorn[standard]:"
echo "  pip install uvicorn[standard]"
echo ""
echo "Then start backend with SSL:"
echo "  uvicorn src.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile=ssl/key.pem --ssl-certfile=ssl/cert.pem"
