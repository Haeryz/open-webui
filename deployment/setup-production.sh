#!/bin/bash

echo "=========================================="
echo "Legal-Verse.id Deployment with Cloudflare"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo ./setup-production.sh"
    exit 1
fi

# Navigate to deployment directory
cd /opt/open-webui || exit

echo "[Step 1/10] Stopping existing simple deployment..."
docker stop open-webui 2>/dev/null || true
docker rm open-webui 2>/dev/null || true

echo "[Step 2/10] Installing required packages..."
apt-get update -qq
apt-get install -y apache2-utils ufw fail2ban -qq

echo "[Step 3/10] Configuring environment..."
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env from .env.production template"
    exit 1
fi

# Check if domain is set
if grep -q "legal-verse.id" .env; then
    echo "✓ Domain configured: legal-verse.id"
else
    echo "ERROR: Domain not set in .env!"
    exit 1
fi

# Check if Cloudflare token is set
if grep -q "YOUR_CLOUDFLARE_API_TOKEN_HERE" .env; then
    echo "ERROR: Please set your Cloudflare API token in .env!"
    exit 1
fi

echo "[Step 4/10] Setting up Traefik..."
mkdir -p traefik
touch traefik/acme.json
chmod 600 traefik/acme.json

echo "[Step 5/10] Creating Docker network..."
docker network create web 2>/dev/null && echo "✓ Network created" || echo "✓ Network already exists"

echo "[Step 6/10] Setting up firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable

echo "[Step 7/10] Configuring Fail2Ban..."
systemctl enable fail2ban
systemctl restart fail2ban

echo "[Step 8/10] Pulling latest Docker image..."
docker pull haeryz/analisis-putusan:latest

echo "[Step 9/10] Starting services with Docker Compose..."
docker-compose up -d

echo "[Step 10/10] Waiting for services to start..."
sleep 10

echo ""
echo "=========================================="
echo "Deployment Status"
echo "=========================================="
docker-compose ps
echo ""

echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Your applications:"
echo "  • Main App:         https://legal-verse.id"
echo "  • WWW:              https://www.legal-verse.id"
echo "  • Traefik Dashboard: https://traefik.legal-verse.id"
echo ""
echo "SSL certificates will be obtained automatically."
echo "This may take 2-3 minutes on first run."
echo ""
echo "Useful commands:"
echo "  • View logs:        docker-compose logs -f"
echo "  • View app logs:    docker-compose logs -f open-webui"
echo "  • View Traefik:     docker-compose logs -f traefik"
echo "  • Restart:          docker-compose restart"
echo "  • Stop:             docker-compose down"
echo "  • Update app:       docker-compose pull && docker-compose up -d"
echo ""
echo "Check SSL status: cat traefik/acme.json"
echo ""
