# 🚀 CI/CD Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Get DockerHub Credentials (2 min)
1. Visit https://hub.docker.com/ and login/signup
2. Go to Account Settings → Security → New Access Token
3. Name: "GitHub Actions", Permissions: "Read & Write"
4. **Copy the token** (save it somewhere safe!)

### Step 2: Add GitHub Secrets (1 min)
1. Go to your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret" and add:
   - Name: `DOCKERHUB_USERNAME` | Value: `your-dockerhub-username`
   - Name: `DOCKERHUB_TOKEN` | Value: `paste-the-token-from-step1`

### Step 3: Create DockerHub Repository (1 min)
1. Go to https://hub.docker.com/
2. Click "Create Repository"
3. Name: `open-webui`
4. Visibility: Public (or Private if you have Pro)
5. Click "Create"

### Step 4: Test the Pipeline (1 min)
```bash
# Make a small change
echo "# CI/CD Test" >> README.md

# Commit and push
git add .
git commit -m "test: trigger CI/CD pipeline"
git push origin main
```

### Step 5: Watch It Build! 
Go to: `https://github.com/YOUR-USERNAME/open-webui/actions`

**That's it! Your images will be available at:**
`docker pull YOUR-DOCKERHUB-USERNAME/open-webui:latest`

---

## 📋 Common Commands

### Deploy to Main (Production)
```bash
git add .
git commit -m "feat: new feature"
git push origin main
```
**Result:** Builds and pushes with `:latest` tag

### Deploy to Dev (Testing)
```bash
git checkout dev
git add .
git commit -m "test: experimental feature"
git push origin dev
```
**Result:** Builds and pushes with `:dev` tag

### Create Release Version
```bash
npm version patch  # 0.6.33 → 0.6.34
# or
npm version minor  # 0.6.33 → 0.7.0
# or
npm version major  # 0.6.33 → 1.0.0

git push origin main --tags
```
**Result:** Creates versioned images + GitHub release

### Use Quick Deploy Script (Windows)
```powershell
.\.github\deploy.ps1
```

### Use Quick Deploy Script (Linux/Mac)
```bash
chmod +x .github/deploy.sh
./.github/deploy.sh
```

---

## 🐳 Image Variants

| Pull Command | Description |
|-------------|-------------|
| `docker pull username/open-webui:latest` | Latest stable |
| `docker pull username/open-webui:dev` | Development |
| `docker pull username/open-webui:0.6.33` | Specific version |
| `docker pull username/open-webui:latest-cuda` | CUDA support |
| `docker pull username/open-webui:latest-ollama` | Ollama bundled |
| `docker pull username/open-webui:latest-slim` | Minimal size |

---

## 🔧 Run Your Image

### Basic
```bash
docker run -d -p 3000:8080 username/open-webui:latest
```

### With Data Persistence
```bash
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  username/open-webui:latest
```

### With GPU (CUDA variant)
```bash
docker run -d \
  -p 3000:8080 \
  --gpus all \
  -v open-webui:/app/backend/data \
  username/open-webui:latest-cuda
```

---

## 🎯 Workflow Triggers

| Action | Trigger | Tags Created |
|--------|---------|--------------|
| Push to `main` | Automatic | `:latest`, `:version-hash` |
| Push to `dev` | Automatic | `:dev`, `:version-hash` |
| Push tag `v1.2.3` | Automatic | `:1.2.3`, `:latest` |
| Manual | Actions tab | Based on branch |

---

## ❗ Troubleshooting

### "Authentication failed"
- Check secrets: Settings → Secrets → Actions
- Verify token has "Read & Write" permissions
- Make sure username is exact (case-sensitive)

### "Repository not found"
- Create repository on DockerHub named `open-webui`
- Make sure it's not a typo

### Build is slow
- First build: ~30-45 min (normal)
- Next builds: ~10-20 min (cached)

### Want to test locally first?
```bash
# Build locally
docker build -t test-image .

# Run locally
docker run -d -p 3000:8080 test-image
```

---

## 📊 Monitor Your Pipeline

**GitHub Actions:** 
`https://github.com/YOUR-USERNAME/open-webui/actions`

**DockerHub Images:** 
`https://hub.docker.com/r/YOUR-USERNAME/open-webui/tags`

---

## 🎓 What Happens Behind the Scenes?

1. **You push code** → GitHub detects the push
2. **Workflow starts** → Reads `.github/workflows/dockerhub-cicd.yaml`
3. **Version extracted** → From `package.json`
4. **Docker builds** → 4 variants (main, cuda, ollama, slim)
5. **Multi-arch** → Both AMD64 and ARM64
6. **Push to DockerHub** → With proper tags
7. **Notification** → Check Actions tab for status

---

## 💡 Pro Tips

1. **Test on dev first:** Push to `dev` branch before `main`
2. **Use semantic versions:** `patch` for fixes, `minor` for features, `major` for breaking changes
3. **Check Actions logs:** Click on workflow runs to see detailed logs
4. **Cache saves time:** Subsequent builds are much faster
5. **Monitor DockerHub:** Keep an eye on storage usage

---

## 🆘 Need Help?

- **Full guide:** `.github/CI-CD-SETUP.md`
- **Workflow file:** `.github/workflows/dockerhub-cicd.yaml`
- **GitHub Actions Docs:** https://docs.github.com/actions
- **DockerHub Docs:** https://docs.docker.com/docker-hub/

---

**Ready to ship? 🚢**

```bash
git add .
git commit -m "feat: amazing new feature"
git push origin main
```

**Then watch the magic happen at:**  
`https://github.com/YOUR-USERNAME/open-webui/actions`

---

*Last updated: October 12, 2025*
