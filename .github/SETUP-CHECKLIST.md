# ✅ CI/CD Setup Checklist

Use this checklist to ensure your CI/CD pipeline is properly configured.

## 📋 Pre-Setup (Before Starting)

- [ ] Have a GitHub account
- [ ] Have repository access with push permissions
- [ ] Have a DockerHub account (or create one at https://hub.docker.com)

---

## 🔧 DockerHub Configuration

### Step 1: DockerHub Repository
- [ ] Logged into DockerHub
- [ ] Created repository named `open-webui`
- [ ] Set repository visibility (Public/Private)
- [ ] Noted your DockerHub username: `________________`

### Step 2: Access Token
- [ ] Went to DockerHub → Account Settings → Security
- [ ] Clicked "New Access Token"
- [ ] Named token: "GitHub Actions CI/CD"
- [ ] Set permissions to "Read & Write"
- [ ] **Saved token in secure location** (you won't see it again!)

---

## 🔐 GitHub Secrets Configuration

### Step 3: Add GitHub Secrets
Go to: `https://github.com/YOUR-USERNAME/open-webui/settings/secrets/actions`

- [ ] Clicked "New repository secret"
- [ ] Added secret #1:
  - Name: `DOCKERHUB_USERNAME`
  - Value: `________________` (your DockerHub username)
- [ ] Added secret #2:
  - Name: `DOCKERHUB_TOKEN`
  - Value: `________________` (paste the token from Step 2)
- [ ] Both secrets show as saved in GitHub

---

## 📁 Workflow Files

### Step 4: Verify Files Exist
- [ ] `.github/workflows/dockerhub-cicd.yaml` exists
- [ ] `.github/QUICKSTART.md` exists
- [ ] `.github/CI-CD-SETUP.md` exists
- [ ] `.github/PIPELINE-ARCHITECTURE.md` exists
- [ ] `.github/deploy.ps1` exists (Windows)
- [ ] `.github/deploy.sh` exists (Linux/Mac)

---

## 🧪 Initial Test

### Step 5: First Pipeline Run
- [ ] Made a small test change (e.g., updated README)
- [ ] Committed changes: `git commit -m "test: CI/CD pipeline"`
- [ ] Pushed to main: `git push origin main`
- [ ] Went to Actions tab: `https://github.com/YOUR-USERNAME/open-webui/actions`
- [ ] Workflow "CI/CD Pipeline - Build and Push to DockerHub" started
- [ ] All jobs show as queued or running (not failed)

### Step 6: Monitor Build Progress
- [ ] Clicked on the running workflow
- [ ] "prepare" job completed successfully
- [ ] "build-and-push" jobs are running (4 variants in parallel)
- [ ] No authentication errors
- [ ] No "repository not found" errors

### Step 7: Wait for Completion
- [ ] All jobs completed with green checkmarks ✅
- [ ] Total time: ______ minutes (first build: 30-45 min is normal)
- [ ] No red X's or failures

---

## 🐳 Verify DockerHub

### Step 8: Check Images on DockerHub
Go to: `https://hub.docker.com/r/YOUR-USERNAME/open-webui/tags`

- [ ] Can see tags for main images:
  - [ ] `latest`
  - [ ] `0.6.33-XXXXXX` (version + git hash)
- [ ] Can see tags for variants:
  - [ ] `latest-cuda`
  - [ ] `latest-ollama`
  - [ ] `latest-slim`
  - [ ] Variant tags with version (e.g., `0.6.33-XXXXXX-cuda`)

### Step 9: Verify Multi-Architecture
Click on one of the tags on DockerHub:
- [ ] Shows "OS/ARCH" column
- [ ] Lists `linux/amd64`
- [ ] Lists `linux/arm64`

---

## 🚀 Test Pulling Images

### Step 10: Pull and Test Image
```bash
docker pull YOUR-USERNAME/open-webui:latest
docker run -d -p 3000:8080 --name test-webui YOUR-USERNAME/open-webui:latest
```

- [ ] Image pulled successfully
- [ ] Container started without errors
- [ ] Can access at http://localhost:3000
- [ ] Application loads correctly
- [ ] Stopped test container: `docker stop test-webui && docker rm test-webui`

---

## 📊 Test Different Triggers

### Step 11: Test Dev Branch (Optional)
```bash
git checkout -b dev
echo "# Dev test" >> README.md
git add . && git commit -m "test: dev branch"
git push origin dev
```

- [ ] Workflow triggered for dev branch
- [ ] Images tagged with `:dev` created
- [ ] Can pull: `docker pull YOUR-USERNAME/open-webui:dev`

### Step 12: Test Version Release (Optional)
```bash
git checkout main
npm version patch
git push origin main --tags
```

- [ ] Workflow triggered for version tag
- [ ] GitHub Release created
- [ ] Version-specific tags created (e.g., `1.2.3`)
- [ ] `:latest` tag updated

---

## 🛠️ Helper Scripts

### Step 13: Test Helper Scripts

**Windows PowerShell:**
```powershell
.\.github\deploy.ps1
```
- [ ] Script runs without errors
- [ ] Menu displays correctly
- [ ] Can choose option 6 (Check CI/CD status)
- [ ] Browser opens to Actions page

**Linux/Mac Bash:**
```bash
chmod +x .github/deploy.sh
./.github/deploy.sh
```
- [ ] Script runs without errors
- [ ] Menu displays correctly
- [ ] Can choose option 6 (Check CI/CD status)

---

## 📚 Documentation

### Step 14: Review Documentation
- [ ] Read [QUICKSTART.md](.github/QUICKSTART.md)
- [ ] Bookmarked [CI-CD-SETUP.md](.github/CI-CD-SETUP.md) for reference
- [ ] Reviewed [PIPELINE-ARCHITECTURE.md](.github/PIPELINE-ARCHITECTURE.md) (optional)

---

## ✅ Final Verification

### Step 15: Complete Health Check
- [ ] No errors in latest workflow run
- [ ] Images exist on DockerHub
- [ ] Can pull and run images locally
- [ ] Understand how to trigger builds
- [ ] Know where to find documentation
- [ ] Have helper scripts ready to use

---

## 🎉 Success Criteria

Your CI/CD pipeline is fully operational when:

✅ **GitHub Actions:**
- Workflows run without errors
- All jobs complete successfully
- Build time is reasonable (30-45 min first, 10-20 min subsequent)

✅ **DockerHub:**
- Images appear with correct tags
- Multi-architecture support confirmed
- Images are pullable

✅ **Local Testing:**
- Can pull images
- Can run containers
- Application works correctly

✅ **Documentation:**
- Understand how to use pipeline
- Know how to troubleshoot issues
- Have quick reference guides

---

## ❌ Common Issues & Solutions

### Issue: "Authentication failed"
- [ ] Verified `DOCKERHUB_USERNAME` matches DockerHub exactly (case-sensitive)
- [ ] Verified `DOCKERHUB_TOKEN` is correct and has Read & Write permissions
- [ ] Regenerated token if needed
- [ ] Updated GitHub secret with new token

### Issue: "Repository not found"
- [ ] Created `open-webui` repository on DockerHub
- [ ] Verified repository name is exactly `open-webui` (no typos)
- [ ] Checked repository is not private (or have Pro account)

### Issue: "Workflow file not found"
- [ ] Confirmed `.github/workflows/dockerhub-cicd.yaml` exists
- [ ] File is in correct directory structure
- [ ] File is committed and pushed to repository

### Issue: Build times out or fails
- [ ] Checked GitHub Actions logs for specific errors
- [ ] Verified DockerHub has enough storage (5GB free tier)
- [ ] Tried re-running the workflow
- [ ] Checked if DockerHub service is operational

---

## 📝 Notes Section

**First Build Completed:**
- Date: __________
- Time taken: ______ minutes
- Image tags created: _____________________________

**DockerHub Information:**
- Username: __________
- Repository URL: https://hub.docker.com/r/__________/open-webui

**GitHub Actions:**
- Repository URL: https://github.com/__________/open-webui
- Actions URL: https://github.com/__________/open-webui/actions

**Common Commands (Fill in your username):**
```bash
# Pull latest
docker pull __________/open-webui:latest

# Pull specific version
docker pull __________/open-webui:0.6.33-XXXXXX

# Pull CUDA variant
docker pull __________/open-webui:latest-cuda

# Run container
docker run -d -p 3000:8080 -v open-webui:/app/backend/data __________/open-webui:latest
```

---

## 🎓 Next Steps

After completing this checklist:

1. **Daily Operations:**
   - Use helper scripts for common tasks
   - Test changes on dev branch first
   - Deploy to main when ready

2. **Version Management:**
   - Update package.json version before releases
   - Use `npm version` commands for consistency
   - Tag releases for versioned images

3. **Monitoring:**
   - Check Actions tab after each push
   - Monitor DockerHub storage usage
   - Review build logs for optimization opportunities

4. **Advanced:**
   - Customize workflow for your needs
   - Add deployment automation
   - Set up notifications

---

## ✍️ Sign-Off

Setup completed by: ________________  
Date: ________________  
Pipeline Status: ✅ Operational / ❌ Needs Work

Notes:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

*Checklist Version: 1.0 | Created: October 12, 2025*

**Need help?** Refer to [CI-CD-SETUP.md](.github/CI-CD-SETUP.md) for detailed troubleshooting.
