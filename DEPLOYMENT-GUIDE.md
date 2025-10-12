# Complete Deployment Guide: Open WebUI with Traefik

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Domain Setup](#domain-setup)
3. [Traefik Overview](#traefik-overview)
4. [Deployment Options](#deployment-options)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### What You Need:
- ✅ VPS/Server (Ubuntu/Debian recommended)
- ✅ Domain name
- ✅ SSH access to your server
- ✅ Docker installed
- ✅ Basic Linux command knowledge

### Optional but Recommended:
- Cloudflare account (for easier SSL)
- Email for Let's Encrypt notifications

---

## Domain Setup

### Understanding Nameservers

Your friend's domain uses:
```
ns1.domainesia.net
ns2.domainesia.net
```

This means the domain is managed by **Domainesia** (Indonesian domain provider).

### What Your Friend Needs to Configure:

#### Option 1: Direct DNS Records (Recommended if NOT using Cloudflare)

Ask your friend to log into Domainesia and add these DNS records:

```
Type    Name        Value               TTL
----    ----        -----               ---
A       @           202.155.90.40       3600
A       www         202.155.90.40       3600
A       traefik     202.155.90.40       3600
```

**Explanation:**
- `@` = root domain (example.com)
- `www` = www subdomain (www.example.com)
- `traefik` = Traefik dashboard (traefik.example.com)
- `202.155.90.40` = Your VPS IP address
- `TTL 3600` = Cache time (1 hour)

#### Option 2: Using Cloudflare (Recommended for Better Performance + Easy SSL)

1. **Friend creates Cloudflare account** (free)
2. **Friend adds domain to Cloudflare**
3. **Friend changes nameservers at Domainesia from:**
   ```
   ns1.domainesia.net
   ns2.domainesia.net
   ```
   **To Cloudflare nameservers (example):**
   ```
   ns1.cloudflare.com
   ns2.cloudflare.com
   ```
4. **Friend adds DNS records in Cloudflare:**
   ```
   Type    Name        Value               Proxy
   ----    ----        -----               -----
   A       @           202.155.90.40       ✅ Proxied
   A       www         202.155.90.40       ✅ Proxied
   A       traefik     202.155.90.40       ⚠️ DNS Only
   ```

5. **Get Cloudflare API Token:**
   - Go to: https://dash.cloudflare.com/profile/api-tokens
   - Click "Create Token"
   - Use "Edit zone DNS" template
   - Select your domain
   - Create and copy the token

**Why Cloudflare?**
- ✅ Free SSL certificates
- ✅ DDoS protection
- ✅ CDN (faster loading)
- ✅ Easy DNS management
- ✅ Automatic SSL renewal

### Verifying Domain Setup

Wait 5-30 minutes after DNS changes, then check:

```bash
# Check if domain points to your IP
nslookup your-domain.com
dig your-domain.com

# Should show your IP: 202.155.90.40
```

---

## Traefik Overview

### What is Traefik?

**Traefik** is a modern reverse proxy that:
- ✅ Automatically gets SSL certificates (HTTPS)
- ✅ Routes traffic to your containers
- ✅ Handles multiple apps on one server
- ✅ Auto-discovers Docker containers
- ✅ Provides monitoring dashboard

### How Traefik Works (Simple Explanation)

```
Internet → Traefik (Port 80/443) → Your Docker Containers
            ↓
         Gets SSL
         Handles HTTPS
         Routes by domain
```

**Example:**
```
https://example.com          → Traefik → Open WebUI container
https://traefik.example.com  → Traefik → Traefik dashboard
https://api.example.com      → Traefik → API container (future)
```

### Traefik Components

1. **Entry Points** = Ports (80 for HTTP, 443 for HTTPS)
2. **Routers** = Rules (which domain goes where)
3. **Services** = Your containers
4. **Middlewares** = Security (redirect HTTP→HTTPS, headers, auth)
5. **Certificate Resolvers** = How to get SSL (Let's Encrypt, Cloudflare)

---

## Deployment Options

### Option A: Docker Compose + Traefik (Production - RECOMMENDED)

**When to use:**
- ✅ You have a domain name
- ✅ You want automatic HTTPS
- ✅ Professional production setup
- ✅ Planning to add more services later

**Files needed:**
- `docker-compose.yml` - Main configuration
- `.env` - Environment variables
- `traefik/traefik.yml` - Traefik config
- `traefik/config.yml` - Security middlewares

#### Step-by-Step:

**1. Prepare files on your server:**

```bash
cd /opt/open-webui
ls -la
# Should see:
# - docker-compose.yml
# - .env.example
# - traefik/traefik.yml
# - traefik/config.yml
```

**2. Configure environment:**

```bash
cp .env.example .env
nano .env
```

**Edit these values:**

```bash
# Your domain (ask your friend)
DOMAIN=example.com

# Your email for SSL certificates
CF_API_EMAIL=your-email@example.com

# Cloudflare API token (if using Cloudflare DNS challenge)
CF_DNS_API_TOKEN=your-cloudflare-api-token

# Traefik dashboard password
# Generate with: echo $(htpasswd -nb admin yourpassword) | sed -e s/\\$/\\$\\$/g
TRAEFIK_PASSWORD_HASH=$$apr1$$hash...

# API keys (already set from your .env)
DASHSCOPE_API_KEY=sk-1e4b4889461741d8b7022ee8fd7a15f2
# ... rest stays the same
```

**3. Update Traefik email in traefik.yml:**

```bash
nano traefik/traefik.yml
```

Change:
```yaml
certificatesResolvers:
  cloudflare:
    acme:
      email: your-email@example.com  # ← PUT YOUR REAL EMAIL HERE
```

**4. Create SSL storage file:**

```bash
touch traefik/acme.json
chmod 600 traefik/acme.json
```

**5. Create Docker network:**

```bash
docker network create web
```

**6. Start services:**

```bash
docker-compose up -d
```

**7. Monitor startup:**

```bash
# Watch all logs
docker-compose logs -f

# Just Open WebUI
docker-compose logs -f open-webui

# Just Traefik
docker-compose logs -f traefik
```

**8. Check SSL certificate:**

```bash
# After 2-3 minutes, check if cert was obtained
cat traefik/acme.json

# Should see certificate data
```

**9. Access your app:**

- **Main app:** https://example.com
- **Traefik dashboard:** https://traefik.example.com
  - Username: `admin` (or what you set)
  - Password: (what you generated)

---

### Option B: Simple Docker Run (No Domain - CURRENT SETUP)

**When to use:**
- ⚠️ No domain yet
- ⚠️ Testing/Development
- ⚠️ Quick deployment
- ⚠️ Temporary setup

**Current command:**

```bash
docker run -d \
  --name open-webui \
  --restart unless-stopped \
  -p 3000:8080 \
  --env-file .env \
  -v open-webui-data:/app/backend/data \
  haeryz/analisis-putusan:latest
```

**Access:** http://202.155.90.40:3000

**Issues:**
- ❌ No HTTPS (insecure)
- ❌ Must specify port :3000
- ❌ No automatic SSL
- ❌ IP address only

**To upgrade to Traefik later:**

```bash
# Stop simple container
docker stop open-webui
docker rm open-webui

# Keep your data (volume is preserved)
# Start with docker-compose instead
docker-compose up -d
```

---

## SSL Certificate Setup

### Method 1: Cloudflare DNS Challenge (RECOMMENDED)

**Pros:**
- ✅ Works even if port 80/443 blocked
- ✅ Can get wildcard certificates (*.example.com)
- ✅ More reliable
- ✅ Works behind firewalls/NAT

**Setup:**

1. **Get Cloudflare API token** (see Domain Setup section)

2. **Update .env:**
```bash
CF_API_EMAIL=your-email@cloudflare.com
CF_DNS_API_TOKEN=your-api-token-here
```

3. **Traefik will automatically:**
   - Create DNS TXT record
   - Verify domain ownership
   - Get SSL certificate
   - Renew every 90 days

**In traefik.yml:**
```yaml
certificatesResolvers:
  cloudflare:
    acme:
      email: your-email@example.com
      storage: acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "1.0.0.1:53"
```

### Method 2: HTTP Challenge (Simpler but Limited)

**Pros:**
- ✅ No DNS provider needed
- ✅ Simpler setup

**Cons:**
- ❌ Port 80 must be accessible from internet
- ❌ No wildcard certificates
- ❌ Doesn't work behind some firewalls

**Setup:**

1. **Remove Cloudflare config from .env:**
```bash
# Just comment out or remove
# CF_API_EMAIL=
# CF_DNS_API_TOKEN=
```

2. **Update traefik.yml:**
```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@example.com
      storage: acme.json
      httpChallenge:
        entryPoint: http
```

3. **Update docker-compose.yml labels:**
```yaml
# Change from:
- "traefik.http.routers.open-webui-secure.tls.certresolver=cloudflare"

# To:
- "traefik.http.routers.open-webui-secure.tls.certresolver=letsencrypt"
```

### Method 3: Manual Certificate (Advanced)

If you already have SSL certificate files:

```yaml
# In traefik/config.yml
tls:
  certificates:
    - certFile: /certs/example.com.crt
      keyFile: /certs/example.com.key
```

Add volume in docker-compose.yml:
```yaml
traefik:
  volumes:
    - ./certs:/certs:ro
```

---

## Traefik Configuration Explained

### traefik.yml (Main Config)

```yaml
# Enable dashboard
api:
  dashboard: true    # Enable web UI
  debug: true        # Show debug info

# Define ports
entryPoints:
  http:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: https           # Force HTTPS
          scheme: https

  https:
    address: ":443"

# Trust self-signed certs (for internal services)
serversTransport:
  insecureSkipVerify: true

# Watch Docker containers
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false    # Only expose labeled containers
  file:
    filename: /config.yml      # Load additional config

# SSL certificate provider
certificatesResolvers:
  cloudflare:
    acme:
      email: your-email@example.com
      storage: acme.json
      dnsChallenge:
        provider: cloudflare
```

### config.yml (Security & Middlewares)

```yaml
http:
  middlewares:
    # Force HTTPS
    https-redirect:
      redirectScheme:
        scheme: https

    # Security headers
    default-headers:
      headers:
        frameDeny: true                    # Prevent clickjacking
        browserXssFilter: true             # XSS protection
        contentTypeNosniff: true           # Prevent MIME sniffing
        forceSTSHeader: true               # Force HTTPS
        stsIncludeSubdomains: true         # Include subdomains
        stsPreload: true                   # HSTS preload
        stsSeconds: 15552000               # 180 days
        customFrameOptionsValue: SAMEORIGIN
        customRequestHeaders:
          X-Forwarded-Proto: https

    # IP whitelist (optional - for admin areas)
    default-whitelist:
      ipWhiteList:
        sourceRange:
        - "10.0.0.0/8"        # Private IPs
        - "192.168.0.0/16"
        - "172.16.0.0/12"

    # Combined security
    secured:
      chain:
        middlewares:
        - default-whitelist
        - default-headers
```

### docker-compose.yml Labels Explained

```yaml
labels:
  # Enable Traefik for this container
  - "traefik.enable=true"
  
  # HTTP router (port 80)
  - "traefik.http.routers.open-webui.entrypoints=http"
  - "traefik.http.routers.open-webui.rule=Host(`example.com`) || Host(`www.example.com`)"
  
  # Redirect HTTP to HTTPS
  - "traefik.http.middlewares.open-webui-https-redirect.redirectscheme.scheme=https"
  - "traefik.http.routers.open-webui.middlewares=open-webui-https-redirect"
  
  # HTTPS router (port 443)
  - "traefik.http.routers.open-webui-secure.entrypoints=https"
  - "traefik.http.routers.open-webui-secure.rule=Host(`example.com`) || Host(`www.example.com`)"
  - "traefik.http.routers.open-webui-secure.tls=true"
  - "traefik.http.routers.open-webui-secure.tls.certresolver=cloudflare"
  
  # Container port
  - "traefik.http.services.open-webui.loadbalancer.server.port=8080"
  
  # Network
  - "traefik.docker.network=web"
```

---

## Security Checklist

### Firewall (UFW)

```bash
# Install
apt install ufw -y

# Allow SSH (CRITICAL - Don't lock yourself out!)
ufw allow 22/tcp

# Allow HTTP/HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# If using simple Docker (no Traefik)
ufw allow 3000/tcp

# Enable
ufw --force enable

# Check status
ufw status verbose
```

### Fail2Ban (Protect SSH)

```bash
# Install
apt install fail2ban -y

# Start
systemctl enable fail2ban
systemctl start fail2ban

# Check status
fail2ban-client status sshd
```

### Docker Security

```bash
# Don't run as root inside container (already configured)
# Limit resources
docker update --memory="2g" --cpus="2" open-webui

# Regular updates
docker-compose pull
docker-compose up -d
```

### Traefik Dashboard Security

**Generate password hash:**
```bash
apt install apache2-utils -y
echo $(htpasswd -nb admin yourpassword) | sed -e s/\\$/\\$\\$/g
```

Put result in `.env`:
```bash
TRAEFIK_PASSWORD_HASH=$$apr1$$generated$$hash
```

### Environment Variables

```bash
# Protect .env file
chmod 600 .env

# Never commit to git
echo ".env" >> .gitignore
```

---

## Troubleshooting

### Domain not resolving

```bash
# Check DNS
nslookup your-domain.com
dig your-domain.com

# Wait 5-30 minutes for DNS propagation
# Use: https://dnschecker.org
```

### SSL certificate not obtained

```bash
# Check Traefik logs
docker-compose logs traefik | grep -i certificate

# Check acme.json
cat traefik/acme.json

# Common issues:
# - Email not set in traefik.yml
# - Cloudflare token invalid
# - Domain not pointing to server
# - Port 80/443 blocked
```

### Can't access Traefik dashboard

```bash
# Check if running
docker-compose ps

# Check logs
docker-compose logs traefik

# Verify password hash
echo "$TRAEFIK_PASSWORD_HASH"

# Test without auth
# Temporarily remove auth labels, restart
```

### App stuck at boot (downloading model)

```bash
# This is normal! First run takes 6-7 minutes
docker logs -f open-webui

# Look for:
# "Fetching 30 files: 100%|██████████| 30/30 [06:48<00:00, 13.61s/it]"

# Test if server is actually running:
docker exec open-webui curl http://localhost:8080/health
```

### Port already in use

```bash
# Find what's using port 80/443
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Stop conflicting service
systemctl stop apache2
systemctl stop nginx
```

### Container keeps restarting

```bash
# Check logs
docker-compose logs --tail=50 open-webui

# Check resources
docker stats

# Check disk space
df -h
```

---

## Useful Commands

### Docker Compose

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart service
docker-compose restart open-webui

# View logs
docker-compose logs -f
docker-compose logs -f open-webui
docker-compose logs -f traefik

# Pull updates
docker-compose pull
docker-compose up -d

# Check status
docker-compose ps
```

### Docker

```bash
# List containers
docker ps -a

# Container logs
docker logs -f open-webui
docker logs --tail 100 open-webui

# Execute command in container
docker exec open-webui ls /app
docker exec -it open-webui bash

# Container stats
docker stats

# Remove container
docker stop open-webui
docker rm open-webui

# Remove image
docker rmi haeryz/analisis-putusan:latest
```

### Backup & Restore

```bash
# Backup data volume
docker run --rm \
  -v open-webui-data:/data \
  -v $(pwd):/backup \
  ubuntu tar czf /backup/backup-$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm \
  -v open-webui-data:/data \
  -v $(pwd):/backup \
  ubuntu tar xzf /backup/backup-20241012.tar.gz -C /

# Backup .env and configs
tar czf config-backup.tar.gz .env traefik/

# List backups
ls -lh *.tar.gz
```

---

## Migration: Simple Docker → Traefik

When your friend gives you the domain:

```bash
# 1. Stop simple container (data is preserved in volume)
docker stop open-webui
docker rm open-webui

# 2. Update .env with domain
nano .env
# Set DOMAIN=your-domain.com

# 3. Update Traefik email
nano traefik/traefik.yml

# 4. Create SSL storage
touch traefik/acme.json
chmod 600 traefik/acme.json

# 5. Create network
docker network create web

# 6. Start with Traefik
docker-compose up -d

# 7. Monitor logs
docker-compose logs -f

# Your data from the simple deployment is automatically migrated!
```

---

## Next Steps

1. ✅ **Get domain from friend** - Ask for domain name and access
2. ✅ **Setup DNS** - Point domain to 202.155.90.40
3. ✅ **Configure Cloudflare** (optional but recommended)
4. ✅ **Update .env** - Add domain and API keys
5. ✅ **Deploy with Traefik** - Run docker-compose up -d
6. ✅ **Verify SSL** - Check https://your-domain.com
7. ✅ **Secure everything** - Firewall, fail2ban, strong passwords
8. ✅ **Setup backups** - Regular data backups
9. ✅ **Monitor** - Check logs regularly

---

## Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify DNS: `nslookup your-domain.com`
3. Check firewall: `ufw status`
4. Test ports: `netstat -tulpn | grep -E ':(80|443|3000)'`
5. Review Traefik dashboard: `https://traefik.your-domain.com`

---

**Created for: Open WebUI Production Deployment**  
**Server IP: 202.155.90.40**  
**Image: haeryz/analisis-putusan:latest**
