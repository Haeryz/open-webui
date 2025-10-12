#!/bin/bash

echo "================================================"
echo "Open WebUI Deployment Script"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "[1/8] Updating system..."
apt update && apt upgrade -y

# Install Docker
echo "[2/8] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    echo "Docker installed successfully"
else
    echo "Docker already installed"
fi

# Install Docker Compose
echo "[3/8] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully"
else
    echo "Docker Compose already installed"
fi

# Create deployment directory
echo "[4/8] Creating deployment directory..."
mkdir -p /opt/open-webui/traefik
cd /opt/open-webui

# Copy files (you need to upload these manually or via SCP)
echo "[5/8] Setting up configuration files..."
echo "Please ensure you have uploaded:"
echo "  - docker-compose.yml"
echo "  - .env"
echo "  - traefik/traefik.yml"
echo "  - traefik/config.yml"
echo ""
read -p "Have you uploaded all files? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please upload files and run this script again"
    exit 1
fi

# Create acme.json for SSL certificates
echo "[6/8] Setting up SSL certificate storage..."
touch traefik/acme.json
chmod 600 traefik/acme.json

# Create Docker network
echo "[7/8] Creating Docker network..."
docker network create web 2>/dev/null || echo "Network already exists"

# Setup firewall
echo "[8/8] Configuring firewall..."
apt install ufw -y
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable

# Install fail2ban
echo "Installing fail2ban for security..."
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your domain and API keys"
echo "2. Run: docker-compose up -d"
echo "3. Check logs: docker-compose logs -f"
echo ""
echo "Your app will be available at: https://your-domain.com"
echo "Traefik dashboard: https://traefik.your-domain.com"
echo ""
