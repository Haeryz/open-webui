# Legal-Verse.id Deployment Checklist

## ✅ Pre-Deployment (Do This First)

### 1. Cloudflare Setup (30 minutes)
- [ ] Create Cloudflare account at https://dash.cloudflare.com/sign-up
- [ ] Add site: legal-verse.id
- [ ] Choose FREE plan
- [ ] Add DNS records:
  ```
  A    @         202.155.90.40    Proxied ON
  A    www       202.155.90.40    Proxied ON
  A    traefik   202.155.90.40    DNS Only (grey cloud)
  ```
- [ ] Note down Cloudflare nameservers (e.g., ns1.cloudflare.com)

### 2. Change Nameservers at Domainesia (Friend does this)
- [ ] Login to https://my.domainesia.com
- [ ] Go to Domain Management → legal-verse.id
- [ ] Change nameservers from:
  ```
  ns1.domainesia.net → ns1.cloudflare.com
  ns2.domainesia.net → ns2.cloudflare.com
  ```
- [ ] Save changes
- [ ] Wait 30 minutes to 24 hours for propagation

### 3. Get Cloudflare API Token
- [ ] Go to https://dash.cloudflare.com/profile/api-tokens
- [ ] Click "Create Token"
- [ ] Use "Edit zone DNS" template
- [ ] Zone Resources: legal-verse.id
- [ ] Create and COPY the token

### 4. Verify DNS Propagation (After 30+ minutes)
Open terminal and run:
```bash
nslookup legal-verse.id
# Should show: 202.155.90.40

# Or use online tool:
# https://dnschecker.org/#A/legal-verse.id
```
- [ ] legal-verse.id points to 202.155.90.40
- [ ] www.legal-verse.id points to 202.155.90.40
- [ ] traefik.legal-verse.id points to 202.155.90.40

---

## 🚀 Deployment (VPS Setup)

### 5. Upload Production Files to VPS

From your local machine (PowerShell):
```powershell
cd D:\Side\KY-Web\open-webui
scp deployment/.env.production root@202.155.90.40:/opt/open-webui/.env.production
scp deployment/setup-production.sh root@202.155.90.40:/opt/open-webui/setup-production.sh
```

- [ ] Files uploaded successfully

### 6. Connect to VPS via SSH

```powershell
ssh root@202.155.90.40
```

- [ ] Connected to VPS

### 7. Configure Environment Variables

```bash
cd /opt/open-webui
cp .env.production .env
nano .env
```

**Edit these values:**

1. **Your Email** (for SSL notifications):
```bash
CF_API_EMAIL=your-actual-email@example.com
```

2. **Cloudflare API Token** (from Step 3):
```bash
CF_DNS_API_TOKEN=paste-your-token-here
```

3. **Traefik Password** (generate new one):
```bash
# Generate on VPS:
apt install apache2-utils -y
echo $(htpasswd -nb admin YourStrongPassword) | sed -e s/\\$/\\$\\$/g

# Copy the output and paste in .env:
TRAEFIK_PASSWORD_HASH=$$apr1$$generated$$hash
```

4. **Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

- [ ] Email configured
- [ ] Cloudflare token set
- [ ] Traefik password generated
- [ ] File saved

### 8. Update Traefik Email

```bash
nano traefik/traefik.yml
```

Find line with `email: your-email@example.com` and change to your real email.

Save: `Ctrl+X`, `Y`, `Enter`

- [ ] Email updated in traefik.yml

### 9. Run Production Deployment

```bash
chmod +x setup-production.sh
./setup-production.sh
```

This will:
- Stop simple Docker deployment (preserves data)
- Configure firewall
- Setup Fail2ban
- Create Docker network
- Start Traefik + Open WebUI
- Configure SSL automatically

- [ ] Script completed successfully
- [ ] No errors shown

### 10. Monitor Deployment

```bash
# Watch all logs
docker-compose logs -f

# Watch just Traefik (SSL certificate)
docker-compose logs -f traefik

# Watch just Open WebUI
docker-compose logs -f open-webui
```

**What to look for:**
1. Traefik: `"msg"="Configuration loaded from file: /traefik.yml"`
2. SSL: `"Domains"=["legal-verse.id","www.legal-verse.id"]`
3. Open WebUI: `Started server process` and the ASCII banner

- [ ] Traefik started
- [ ] SSL certificate obtained (check after 2-3 minutes)
- [ ] Open WebUI started

### 11. Verify SSL Certificate

```bash
# After 2-3 minutes, check:
cat traefik/acme.json

# Should see certificate data (long JSON)
# If empty, check logs: docker-compose logs traefik
```

- [ ] Certificate obtained successfully

---

## 🎯 Testing (Access Your App)

### 12. Access Applications

Open your browser:

1. **Main App**: https://legal-verse.id
   - [ ] Loads successfully
   - [ ] Shows HTTPS (lock icon)
   - [ ] Can signup/login

2. **WWW**: https://www.legal-verse.id
   - [ ] Redirects to main domain
   - [ ] HTTPS working

3. **Traefik Dashboard**: https://traefik.legal-verse.id
   - [ ] Shows login prompt
   - [ ] Login with username: `admin`
   - [ ] Password: (what you set in .env)
   - [ ] Dashboard loads

### 13. Test SSL Certificate

```bash
# From local machine:
curl -I https://legal-verse.id

# Should show:
# HTTP/2 200
# server: traefik
```

Or use: https://www.ssllabs.com/ssltest/analyze.html?d=legal-verse.id

- [ ] SSL grade A or higher
- [ ] Certificate valid

### 14. Check Container Status

On VPS:
```bash
docker-compose ps

# Both should show "Up"
# traefik       Up      0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
# open-webui    Up      8080/tcp
```

- [ ] All containers running
- [ ] No restart loops

---

## 🔒 Security Verification

### 15. Verify Firewall

```bash
ufw status

# Should show:
# Status: active
# 22/tcp    ALLOW
# 80/tcp    ALLOW
# 443/tcp   ALLOW
```

- [ ] Firewall enabled
- [ ] Only necessary ports open

### 16. Verify Fail2Ban

```bash
systemctl status fail2ban

# Should show: active (running)
```

- [ ] Fail2ban running

### 17. Test HTTP → HTTPS Redirect

```bash
curl -I http://legal-verse.id

# Should show:
# HTTP/1.1 308 Permanent Redirect
# Location: https://legal-verse.id/
```

- [ ] HTTP redirects to HTTPS

---

## 📊 Post-Deployment

### 18. Create First Admin Account

1. Go to https://legal-verse.id
2. Click "Sign Up"
3. Create your admin account (first user is auto-admin)
4. Login and verify everything works

- [ ] Admin account created
- [ ] Can chat with AI
- [ ] Dashboard accessible

### 19. Disable Public Signup (Optional - After creating admin)

If you want to prevent public signups:

```bash
# On VPS
cd /opt/open-webui
nano .env

# Change:
ENABLE_SIGNUP=false

# Restart:
docker-compose restart open-webui
```

- [ ] Signup settings configured as desired

### 20. Setup Monitoring

```bash
# Create monitoring script
cat > /root/check-legal-verse.sh << 'EOF'
#!/bin/bash
if ! curl -f https://legal-verse.id/health > /dev/null 2>&1; then
    echo "legal-verse.id is DOWN!" | mail -s "Alert: Site Down" your-email@example.com
    docker-compose -f /opt/open-webui/docker-compose.yml restart
fi
EOF

chmod +x /root/check-legal-verse.sh

# Add to crontab (check every 5 minutes)
echo "*/5 * * * * /root/check-legal-verse.sh" | crontab -
```

- [ ] Monitoring script created
- [ ] Cron job configured

---

## 🎉 Deployment Complete!

### Your URLs:
- **Main App**: https://legal-verse.id
- **WWW**: https://www.legal-verse.id  
- **Traefik Dashboard**: https://traefik.legal-verse.id

### Important Files:
- Config: `/opt/open-webui/.env`
- Docker Compose: `/opt/open-webui/docker-compose.yml`
- SSL Certificates: `/opt/open-webui/traefik/acme.json`
- Logs: `docker-compose logs -f`

### Common Commands:
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update app
docker-compose pull
docker-compose up -d

# Backup data
docker run --rm -v open-webui-data:/data -v $(pwd):/backup ubuntu tar czf /backup/backup-$(date +%Y%m%d).tar.gz /data

# Check SSL renewal (auto every 90 days)
cat traefik/acme.json
```

---

## 🐛 Troubleshooting

### If SSL not obtained:
```bash
# Check logs
docker-compose logs traefik | grep -i certificate

# Common fixes:
# 1. Check DNS propagation (nslookup legal-verse.id)
# 2. Verify Cloudflare token is correct
# 3. Check email in traefik.yml
# 4. Wait 5 more minutes (sometimes slow)

# Force retry
docker-compose down
rm traefik/acme.json
touch traefik/acme.json
chmod 600 traefik/acme.json
docker-compose up -d
```

### If app won't start:
```bash
# Check logs
docker-compose logs open-webui

# Look for "Fetching 30 files" - this takes 6-7 minutes first time
# Check health after model downloads:
docker exec open-webui curl http://localhost:8080/health
```

### If Traefik dashboard won't load:
```bash
# Verify password hash
echo "$TRAEFIK_PASSWORD_HASH"

# Regenerate if needed:
echo $(htpasswd -nb admin newpassword) | sed -e s/\\$/\\$\\$/g
```

---

**Need Help?** Check logs first: `docker-compose logs -f`

**Everything Working?** ✅ Congratulations! Your Legal-Verse.id is live! 🎉
