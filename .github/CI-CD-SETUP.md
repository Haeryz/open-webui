# CI/CD Pipeline Setup Guide

## Overview
This CI/CD pipeline automates the Docker image build and deployment process to DockerHub using GitHub Actions.

## Features
- ✅ Automatic Docker builds on code push
- ✅ Multi-architecture support (amd64, arm64)
- ✅ Auto-versioning from package.json
- ✅ Multiple image variants (main, cuda, ollama, slim)
- ✅ Push to DockerHub with proper tags
- ✅ Automatic GitHub releases for version tags
- ✅ Build caching for faster builds

## Setup Instructions

### 1. Create DockerHub Account
If you don't have one already:
1. Go to https://hub.docker.com/
2. Sign up for a free account
3. Create a repository named `open-webui`

### 2. Generate DockerHub Access Token
1. Log in to DockerHub
2. Go to Account Settings → Security
3. Click "New Access Token"
4. Name it "GitHub Actions CI/CD"
5. Set permissions to "Read & Write"
6. Copy the generated token (you won't see it again!)

### 3. Add GitHub Secrets
1. Go to your GitHub repository
2. Navigate to: Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add these two secrets:

   **Secret 1:**
   - Name: `DOCKERHUB_USERNAME`
   - Value: Your DockerHub username (e.g., `yourusername`)

   **Secret 2:**
   - Name: `DOCKERHUB_TOKEN`
   - Value: The access token you generated in step 2

### 4. Workflow Files
The pipeline is defined in: `.github/workflows/dockerhub-cicd.yaml`

## How It Works

### Trigger Events
The pipeline runs automatically when:
- Code is pushed to `main` branch
- Code is pushed to `dev` branch
- A version tag (v*.*.*) is created
- Manually triggered via workflow_dispatch

### Versioning Strategy

#### For Branch Pushes (main/dev)
- Version is extracted from `package.json`
- Appends short commit hash (e.g., `0.6.33-a1b2c3d`)

#### For Tag Pushes
- Uses the tag version (e.g., `v1.2.3` → `1.2.3`)
- Also tags as `latest`

### Image Variants Built

| Variant | Build Args | Tag Suffix | Description |
|---------|------------|------------|-------------|
| Main | None | (none) | Standard image |
| CUDA | `USE_CUDA=true` | `-cuda` | CUDA support |
| Ollama | `USE_OLLAMA=true` | `-ollama` | Ollama bundled |
| Slim | `USE_SLIM=true` | `-slim` | Minimal image |

### Tags Created

**On push to `main` branch:**
```
yourusername/open-webui:latest
yourusername/open-webui:0.6.33-a1b2c3d
yourusername/open-webui:latest-cuda
yourusername/open-webui:0.6.33-a1b2c3d-cuda
yourusername/open-webui:latest-ollama
yourusername/open-webui:0.6.33-a1b2c3d-ollama
yourusername/open-webui:latest-slim
yourusername/open-webui:0.6.33-a1b2c3d-slim
```

**On push to `dev` branch:**
```
yourusername/open-webui:dev
yourusername/open-webui:0.6.33-a1b2c3d
yourusername/open-webui:dev-cuda
yourusername/open-webui:0.6.33-a1b2c3d-cuda
... (and others)
```

**On tag push (e.g., v1.2.3):**
```
yourusername/open-webui:1.2.3
yourusername/open-webui:latest
yourusername/open-webui:1.2.3-cuda
yourusername/open-webui:latest-cuda
... (and others)
```

## Usage Examples

### 1. Push Code to Main Branch
```bash
git add .
git commit -m "Update feature"
git push origin main
```
This triggers a build and pushes images tagged as `latest` and version+hash.

### 2. Push Code to Dev Branch
```bash
git checkout dev
git add .
git commit -m "Development changes"
git push origin dev
```
This triggers a build and pushes images tagged as `dev` and version+hash.

### 3. Create a Release Version
```bash
# Update version in package.json first
npm version patch  # or minor, or major

# Push the tag
git push origin main --tags
```
This creates version tag images and a GitHub release.

### 4. Manual Trigger
1. Go to Actions tab in GitHub
2. Select "CI/CD Pipeline - Build and Push to DockerHub"
3. Click "Run workflow"
4. Choose the branch
5. Click "Run workflow" button

## Pulling Images

```bash
# Latest main branch build
docker pull yourusername/open-webui:latest

# Specific version
docker pull yourusername/open-webui:1.2.3

# Development version
docker pull yourusername/open-webui:dev

# CUDA variant
docker pull yourusername/open-webui:latest-cuda

# Ollama variant
docker pull yourusername/open-webui:latest-ollama

# Slim variant
docker pull yourusername/open-webui:latest-slim
```

## Running the Image

```bash
# Basic run
docker run -d -p 3000:8080 yourusername/open-webui:latest

# With volume mounts
docker run -d \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  yourusername/open-webui:latest

# CUDA variant
docker run -d \
  -p 3000:8080 \
  --gpus all \
  -v open-webui:/app/backend/data \
  --name open-webui \
  yourusername/open-webui:latest-cuda
```

## Monitoring Builds

### Check Build Status
1. Go to the Actions tab in your GitHub repository
2. Click on the latest workflow run
3. Monitor the progress of each job

### Build Times
- First build: ~30-45 minutes (no cache)
- Subsequent builds: ~10-20 minutes (with cache)

### Build Logs
Click on any job in the Actions tab to see detailed logs.

## Troubleshooting

### Issue: "Authentication failed"
**Solution:** Check that your DockerHub secrets are correctly set:
- Verify `DOCKERHUB_USERNAME` is your exact DockerHub username
- Verify `DOCKERHUB_TOKEN` is valid and has Read & Write permissions

### Issue: "manifest unknown"
**Solution:** The repository doesn't exist on DockerHub. Create it:
1. Log in to DockerHub
2. Click "Create Repository"
3. Name it `open-webui`
4. Set visibility (public/private)

### Issue: Build takes too long
**Solution:** The pipeline uses build cache. First builds are slow, subsequent builds are faster.

### Issue: Out of DockerHub storage
**Solution:** 
- Free tier: 5GB storage
- Delete old images or upgrade to Pro plan
- Use DockerHub's repository settings to set up auto-deletion policies

### Issue: Architecture not supported
**Solution:** The pipeline builds for both amd64 and arm64. If you only need one:
- Edit `.github/workflows/dockerhub-cicd.yaml`
- Change `platforms: linux/amd64,linux/arm64` to just `platforms: linux/amd64`

## Advanced Configuration

### Customize Image Name
Edit `.github/workflows/dockerhub-cicd.yaml`:
```yaml
env:
  IMAGE_NAME: ${{ secrets.DOCKERHUB_USERNAME }}/your-custom-name
```

### Add More Variants
Add to the matrix in the workflow file:
```yaml
- name: custom
  build_args: "USE_CUSTOM=true"
  suffix: "-custom"
```

### Change Build Platforms
Modify the platforms line:
```yaml
platforms: linux/amd64  # Remove arm64 for faster builds
```

### Skip Variants
Comment out unwanted variants in the matrix strategy.

## Costs

### GitHub Actions
- Public repositories: Unlimited free minutes
- Private repositories: 2,000 free minutes/month

### DockerHub
- Free tier: 1 repository, unlimited public repositories
- Storage: 5GB free
- Pull rate: 100 pulls per 6 hours for anonymous, 200 for authenticated

## Best Practices

1. **Version Management:**
   - Update `package.json` version before releases
   - Use semantic versioning (MAJOR.MINOR.PATCH)

2. **Testing:**
   - Test locally before pushing to main
   - Use dev branch for experimental features

3. **Security:**
   - Never commit DockerHub credentials
   - Rotate access tokens periodically
   - Use minimal permission tokens

4. **Optimization:**
   - Pipeline uses layer caching
   - Multi-stage builds reduce image size
   - Remove unused variants to speed up builds

## Next Steps

1. ✅ Set up DockerHub secrets in GitHub
2. ✅ Push code to trigger first build
3. ✅ Monitor the Actions tab
4. ✅ Pull and test your images
5. ✅ Set up auto-deployment to your servers (optional)

## Support

If you encounter issues:
1. Check the Actions logs in GitHub
2. Verify all secrets are correctly set
3. Ensure DockerHub repository exists
4. Check DockerHub token permissions

---

**Created:** October 12, 2025  
**Pipeline File:** `.github/workflows/dockerhub-cicd.yaml`
