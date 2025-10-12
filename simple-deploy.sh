#!/bin/bash

echo "=================================="
echo "Simple Open WebUI Deployment"
echo "=================================="

# Pull the image
echo "[1/5] Pulling Docker image..."
docker pull haeryz/analisis-putusan:latest

# Stop and remove old container if exists
echo "[2/5] Cleaning up old container..."
docker stop open-webui 2>/dev/null || true
docker rm open-webui 2>/dev/null || true

# Create .env file
echo "[3/5] Creating environment file..."
cat > /opt/open-webui/.env << 'EOF'
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_BASE_URL=
OPENAI_API_KEY=
DASHSCOPE_API_KEY=sk-1e4b4889461741d8b7022ee8fd7a15f2
DASHSCOPE_API_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions
VECTOR_DB=qdrant
QDRANT_URI=https://2c31c362-09d5-446d-96a9-c1abbaa86cc1.europe-west3-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzY4ODA1NTQzfQ.lZ4LU8eQX2TOCHE8_ymYqxbaklNRgpt2ZqjNQturnKM
QDRANT_PREFER_GRPC=false
QDRANT_TIMEOUT=15
CORS_ALLOW_ORIGIN=*
FORWARDED_ALLOW_IPS=*
SCARF_NO_ANALYTICS=true
DO_NOT_TRACK=true
ANONYMIZED_TELEMETRY=false
ENABLE_SIGNUP=true
EOF

# Setup firewall
echo "[4/5] Configuring firewall..."
apt-get update -qq
apt-get install -y ufw fail2ban -qq
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp

# Start fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Create volume and run container
echo "[5/5] Starting Open WebUI container..."
docker volume create open-webui-data 2>/dev/null || true

docker run -d \
  --name open-webui \
  --restart unless-stopped \
  -p 3000:8080 \
  --env-file /opt/open-webui/.env \
  -v open-webui-data:/app/backend/data \
  haeryz/analisis-putusan:latest

# Wait for container to start
echo ""
echo "Waiting for container to start..."
sleep 5

# Check status
echo ""
echo "=================================="
echo "Deployment Complete!"
echo "=================================="
echo ""
docker ps --filter name=open-webui
echo ""
echo "Your app is running at: http://202.155.90.40:3000"
echo ""
echo "To check logs: docker logs -f open-webui"
echo "To restart: docker restart open-webui"
echo "To stop: docker stop open-webui"
echo ""
