# 🚀 CI/CD Pipeline Documentation

This directory contains the complete CI/CD pipeline setup for Open WebUI, including GitHub Actions workflows and helper scripts.

## 📁 What's Inside

| File | Purpose | For |
|------|---------|-----|
| **QUICKSTART.md** | ⚡ 5-minute setup guide | Everyone |
| **CI-CD-SETUP.md** | 📖 Detailed documentation | Complete reference |
| **PIPELINE-ARCHITECTURE.md** | 🏗️ Technical architecture | Understanding flow |
| **deploy.ps1** | 🪟 Windows helper script | Windows users |
| **deploy.sh** | 🐧 Linux/Mac helper script | Unix users |
| **workflows/dockerhub-cicd.yaml** | ⚙️ GitHub Actions workflow | The actual pipeline |

## 🎯 Quick Navigation

### I want to...

#### 🆕 **Set up CI/CD for the first time**
→ Start with **[QUICKSTART.md](QUICKSTART.md)**
- 5-minute setup
- Step-by-step instructions
- No prior knowledge needed

#### 📚 **Learn everything about the pipeline**
→ Read **[CI-CD-SETUP.md](CI-CD-SETUP.md)**
- Complete documentation
- Troubleshooting guide
- Advanced configuration

#### 🏗️ **Understand how it works**
→ Check **[PIPELINE-ARCHITECTURE.md](PIPELINE-ARCHITECTURE.md)**
- Visual diagrams
- Technical details
- Execution flow

#### 💻 **Deploy changes quickly**
→ Use helper scripts
- Windows: `deploy.ps1`
- Linux/Mac: `deploy.sh`

## 🚦 Getting Started (30 seconds)

1. **DockerHub Setup** (if you haven't already):
   - Sign up at https://hub.docker.com
   - Create a repository named `open-webui`
   - Generate an access token

2. **Add GitHub Secrets**:
   - Go to: Settings → Secrets and variables → Actions
   - Add: `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`

3. **Push and Watch**:
   ```bash
   git push origin main
   ```
   - Go to Actions tab to see build progress
   - Images will be at: `docker pull your-username/open-webui:latest`

## 🎪 What the Pipeline Does

```
Code Push → GitHub Actions → Docker Build → DockerHub → Ready to Deploy!
```

**Automatically builds and pushes:**
- ✅ Multi-architecture images (AMD64 + ARM64)
- ✅ Multiple variants (main, cuda, ollama, slim)
- ✅ Auto-versioned tags
- ✅ GitHub releases for version tags

## 📦 Image Variants

| Variant | When to Use | Pull Command |
|---------|-------------|--------------|
| **Main** | General use | `docker pull username/open-webui:latest` |
| **CUDA** | GPU support | `docker pull username/open-webui:latest-cuda` |
| **Ollama** | Bundled Ollama | `docker pull username/open-webui:latest-ollama` |
| **Slim** | Minimal size | `docker pull username/open-webui:latest-slim` |

## 🔧 Helper Scripts

### Windows (PowerShell)
```powershell
.\.github\deploy.ps1
```

### Linux/Mac (Bash)
```bash
chmod +x .github/deploy.sh
./.github/deploy.sh
```

**Features:**
- Quick push to main/dev
- Create release versions
- Check build status
- View DockerHub images

## 📊 Pipeline Triggers

| Action | Trigger | Result |
|--------|---------|--------|
| `git push origin main` | Automatic | Builds `:latest` |
| `git push origin dev` | Automatic | Builds `:dev` |
| `npm version patch && git push --tags` | Automatic | Builds version + release |
| Manual (Actions tab) | Click "Run workflow" | Builds selected branch |

## 🎯 Common Tasks

### Deploy to Production
```bash
git checkout main
git pull
git add .
git commit -m "feat: new feature"
git push origin main
```

### Create a Release
```bash
npm version patch  # 0.6.33 → 0.6.34
git push origin main --tags
```

### Deploy to Development
```bash
git checkout dev
git add .
git commit -m "test: experimental feature"
git push origin dev
```

### Use Your Image
```bash
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  your-username/open-webui:latest
```

## ❗ Troubleshooting

| Problem | Solution |
|---------|----------|
| Authentication failed | Check GitHub secrets are set correctly |
| Repository not found | Create `open-webui` repo on DockerHub |
| Build is slow | First build takes ~30-45 min (normal) |
| Want to test locally | Run `docker build -t test .` first |

## 🔗 Important Links

- **GitHub Actions:** `https://github.com/YOUR-USERNAME/open-webui/actions`
- **DockerHub:** `https://hub.docker.com/r/YOUR-USERNAME/open-webui`
- **Workflow File:** `.github/workflows/dockerhub-cicd.yaml`

## 💡 Pro Tips

1. **Test on dev branch first** before pushing to main
2. **Use semantic versioning**: `patch` for fixes, `minor` for features, `major` for breaking changes
3. **Monitor Actions tab** to catch issues early
4. **Check DockerHub storage** to stay within limits
5. **Cache makes builds faster** - subsequent builds are much quicker

## 🆘 Need Help?

1. **Quick reference**: Read [QUICKSTART.md](QUICKSTART.md)
2. **Detailed help**: Check [CI-CD-SETUP.md](CI-CD-SETUP.md)
3. **Technical details**: See [PIPELINE-ARCHITECTURE.md](PIPELINE-ARCHITECTURE.md)
4. **GitHub Actions docs**: https://docs.github.com/actions
5. **Docker docs**: https://docs.docker.com/

## 🎓 Learning Path

```
1. QUICKSTART.md       → Get it working (5 min)
2. Use helper scripts  → Daily operations (30 sec)
3. CI-CD-SETUP.md      → Understand details (20 min)
4. PIPELINE-ARCHITECTURE.md → Deep dive (optional)
```

## 🔄 Workflow Comparison

### Old (docker-build.yaml) → GitHub Container Registry
```
Push → Build → ghcr.io/username/repo:tag
```

### New (dockerhub-cicd.yaml) → DockerHub
```
Push → Build → docker.io/username/open-webui:tag
```

**Both can coexist!** They target different registries.

## 📈 What Gets Built

### Every Push to Main:
- 4 variants × 2 architectures = 8 images
- Tags: `latest`, `version-hash`, with variant suffixes
- Time: ~20-45 minutes

### Every Version Tag:
- Same as above PLUS:
- GitHub Release with notes
- Version tags (e.g., `1.2.3`)

## 🎉 Success Indicators

✅ **Pipeline is working when:**
1. Actions tab shows green checkmarks
2. DockerHub shows new images
3. You can pull and run: `docker pull username/open-webui:latest`
4. Version tags match package.json

## 📝 Notes

- **Free tier limits**: GitHub Actions (2000 min/month private), DockerHub (5GB storage)
- **Build cache**: Stored on DockerHub as cache tags
- **Multi-arch**: Automatically builds for Intel/AMD and ARM (Apple M1+, Raspberry Pi)
- **Parallel builds**: All variants build simultaneously

## 🚀 Ready to Go?

1. Read [QUICKSTART.md](QUICKSTART.md) (5 min)
2. Set up secrets (2 min)
3. Push code (30 sec)
4. Watch the magic happen! ✨

---

**Questions?** Check the detailed guides above or visit GitHub Actions/Docker documentation.

**Found a bug?** Check the workflow logs in the Actions tab.

**Want to customize?** Edit `.github/workflows/dockerhub-cicd.yaml`

---

*Last updated: October 12, 2025*
