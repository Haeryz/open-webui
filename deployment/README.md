# Open WebUI Production Deployment

Complete production deployment setup with Docker Compose + Traefik for automatic SSL/HTTPS.

## Prerequisites

1. A VPS/Server with Ubuntu/Debian
2. A domain name pointing to your server
3. Cloudflare account (for DNS challenge and SSL)

## Files Structure

```
deployment/
├── docker-compose.yml       # Main orchestration file
├── .env.example            # Environment variables template
├── deploy.sh               # Automated deployment script
└── traefik/
    ├── traefik.yml         # Traefik main config
    └── config.yml          # Traefik middleware config
```

## Quick Deployment

### 1. Upload files to your server

```bash
# On your local machine
scp -r deployment root@202.155.90.40:/opt/open-webui
```

### 2. Connect to your server

```bash
ssh root@202.155.90.40
cd /opt/open-webui
```

### 3. Configure environment

```bash
# Copy and edit the environment file
cp .env.example .env
nano .env
```

Update these values:
- `DOMAIN=your-domain.com` - Your actual domain
- `CF_API_EMAIL=your-email@example.com` - Your Cloudflare email
- `CF_DNS_API_TOKEN=your-token` - Get from Cloudflare dashboard
- `TRAEFIK_PASSWORD_HASH` - Generate with: `echo $(htpasswd -nb admin yourpassword) | sed -e s/\\$/\\$\\$/g`

### 4. Run deployment script

```bash
chmod +x deploy.sh
./deploy.sh
```

### 5. Start services

```bash
docker-compose up -d
```

### 6. Check status

```bash
docker-compose ps
docker-compose logs -f open-webui
```

## Manual Deployment (if script fails)

```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 3. Create network
docker network create web

# 4. Create SSL cert storage
touch traefik/acme.json
chmod 600 traefik/acme.json

# 5. Setup firewall
apt install ufw -y
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# 6. Start services
docker-compose up -d
```

## Getting Cloudflare API Token

1. Go to https://dash.cloudflare.com/profile/api-tokens
2. Click "Create Token"
3. Use "Edit zone DNS" template
4. Select your domain under "Zone Resources"
5. Create token and copy it to `.env`

## DNS Configuration

Point your domain to your server IP at your DNS provider (Domainesia):

```
A     @           202.155.90.40
A     www         202.155.90.40
A     traefik     202.155.90.40
```

Or ask your friend who has access to configure:
- Main domain: `your-domain.com` → `202.155.90.40`
- WWW: `www.your-domain.com` → `202.155.90.40`
- Traefik: `traefik.your-domain.com` → `202.155.90.40`

## Accessing Your App

- Main app: `https://your-domain.com`
- Traefik dashboard: `https://traefik.your-domain.com`
  - Username: `admin` (or what you set in .env)
  - Password: (what you set in .env)

## Troubleshooting

### Check logs
```bash
docker-compose logs -f
docker-compose logs -f traefik
docker-compose logs -f open-webui
```

### Restart services
```bash
docker-compose restart
```

### Rebuild and restart
```bash
docker-compose down
docker-compose up -d
```

### Check SSL certificates
```bash
cat traefik/acme.json
```

## Security Features

✅ Automatic HTTPS with Let's Encrypt  
✅ HTTP to HTTPS redirect  
✅ Security headers (XSS, HSTS, etc.)  
✅ Firewall (UFW) configured  
✅ Fail2ban for SSH protection  
✅ Traefik dashboard protected with auth  

## Updating the App

```bash
docker-compose pull open-webui
docker-compose up -d open-webui
```

## Backup Data

```bash
# Backup volume
docker run --rm -v open-webui-data:/data -v $(pwd):/backup ubuntu tar czf /backup/open-webui-backup.tar.gz /data

# Restore volume
docker run --rm -v open-webui-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/open-webui-backup.tar.gz -C /
```
