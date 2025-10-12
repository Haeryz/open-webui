# CI/CD Pipeline Architecture

## 🏗️ Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DEVELOPER WORKFLOW                          │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
            ┌──────────┐   ┌──────────┐   ┌──────────┐
            │git push  │   │git push  │   │git tag   │
            │  main    │   │   dev    │   │ v1.2.3   │
            └──────────┘   └──────────┘   └──────────┘
                    │              │              │
                    └──────────────┼──────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB ACTIONS                               │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ STEP 1: Prepare                                             │   │
│  │ • Extract version from package.json                         │   │
│  │ • Append commit hash (for non-tags)                         │   │
│  │ • Determine tags to create                                  │   │
│  └────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ STEP 2: Build & Push (Parallel)                            │   │
│  │                                                              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │   │
│  │  │  Main    │  │  CUDA    │  │ Ollama   │  │  Slim    │  │   │
│  │  │  Image   │  │  Image   │  │  Image   │  │  Image   │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │   │
│  │       │             │             │             │          │   │
│  │       └─────────────┴─────────────┴─────────────┘          │   │
│  │                      │                                      │   │
│  │       Multi-architecture: AMD64 + ARM64                    │   │
│  └────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ STEP 3: Push to DockerHub                                  │   │
│  │ • Tag with version                                          │   │
│  │ • Tag with branch/latest                                    │   │
│  │ • Update manifest for multi-arch                            │   │
│  └────────────────────────────────────────────────────────────┘   │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ STEP 4: Create Release (if tag)                            │   │
│  │ • Generate release notes                                    │   │
│  │ • List all image tags                                       │   │
│  │ • Publish GitHub release                                    │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           DOCKERHUB                                  │
│                                                                      │
│  📦 username/open-webui:latest                                      │
│  📦 username/open-webui:0.6.33-a1b2c3d                             │
│  📦 username/open-webui:latest-cuda                                 │
│  📦 username/open-webui:latest-ollama                               │
│  📦 username/open-webui:latest-slim                                 │
│                                                                      │
│  Architectures: linux/amd64, linux/arm64                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DEPLOYMENT / USERS                            │
│                                                                      │
│  docker pull username/open-webui:latest                            │
│  docker run -d -p 3000:8080 username/open-webui:latest            │
└─────────────────────────────────────────────────────────────────────┘
```

## 📊 Version Tagging Strategy

### On Push to Main Branch
```
Source: main branch commit abc123
Version: 0.6.33 (from package.json)
Git Hash: abc123

Created Tags:
├── username/open-webui:latest
├── username/open-webui:0.6.33-abc123
├── username/open-webui:latest-cuda
├── username/open-webui:0.6.33-abc123-cuda
├── username/open-webui:latest-ollama
├── username/open-webui:0.6.33-abc123-ollama
├── username/open-webui:latest-slim
└── username/open-webui:0.6.33-abc123-slim
```

### On Push to Dev Branch
```
Source: dev branch commit def456
Version: 0.6.33 (from package.json)
Git Hash: def456

Created Tags:
├── username/open-webui:dev
├── username/open-webui:0.6.33-def456
├── username/open-webui:dev-cuda
├── username/open-webui:0.6.33-def456-cuda
├── username/open-webui:dev-ollama
├── username/open-webui:0.6.33-def456-ollama
├── username/open-webui:dev-slim
└── username/open-webui:0.6.33-def456-slim
```

### On Version Tag (v1.2.3)
```
Source: git tag v1.2.3
Version: 1.2.3

Created Tags:
├── username/open-webui:1.2.3
├── username/open-webui:latest
├── username/open-webui:1.2.3-cuda
├── username/open-webui:latest-cuda
├── username/open-webui:1.2.3-ollama
├── username/open-webui:latest-ollama
├── username/open-webui:1.2.3-slim
├── username/open-webui:latest-slim
└── GitHub Release: v1.2.3
```

## 🎯 Image Variants Matrix

| Variant | Build Arg | Use Case | Size | Tag Suffix |
|---------|-----------|----------|------|------------|
| **Main** | None | General purpose | ~2GB | (none) |
| **CUDA** | `USE_CUDA=true` | GPU acceleration | ~4GB | `-cuda` |
| **Ollama** | `USE_OLLAMA=true` | Bundled Ollama | ~3GB | `-ollama` |
| **Slim** | `USE_SLIM=true` | Minimal features | ~1GB | `-slim` |

## ⚡ Build Process Details

### Phase 1: Frontend Build
```
┌─────────────────────────────────────┐
│ Node.js 22 Alpine                   │
│ • Install dependencies (npm ci)     │
│ • Fetch Pyodide wheels             │
│ • Build SvelteKit app (vite build) │
│ • Output: /app/build                │
└─────────────────────────────────────┘
```

### Phase 2: Backend Build
```
┌─────────────────────────────────────┐
│ Python 3.11 Slim                    │
│ • Install Python dependencies       │
│ • Copy frontend build               │
│ • Install variant-specific packages │
│   - CUDA: Install torch with CUDA   │
│   - Ollama: Bundle Ollama binary    │
│   - Slim: Minimal dependencies      │
│ • Configure entrypoint              │
└─────────────────────────────────────┘
```

### Phase 3: Multi-Architecture
```
┌──────────────┐    ┌──────────────┐
│   AMD64      │    │    ARM64     │
│  (Intel/AMD) │    │ (Apple M1+)  │
│              │    │              │
│  Built in    │    │  Built in    │
│  parallel    │    │  parallel    │
└──────────────┘    └──────────────┘
        │                  │
        └────────┬─────────┘
                 │
         ┌───────▼────────┐
         │  Manifest      │
         │  Combined      │
         │  Multi-arch    │
         └────────────────┘
```

## 🔄 Pipeline Execution Times

### First Build (Cold Cache)
- **Checkout & Setup:** 1-2 min
- **Frontend Build:** 5-8 min
- **Backend Build (each variant):** 8-12 min
- **Multi-arch Build:** 15-20 min per variant
- **Push to DockerHub:** 3-5 min per variant
- **Total:** ~30-45 minutes

### Subsequent Builds (Warm Cache)
- **Checkout & Setup:** 1-2 min
- **Frontend Build:** 2-3 min (cached dependencies)
- **Backend Build (each variant):** 3-5 min (cached layers)
- **Multi-arch Build:** 5-8 min per variant
- **Push to DockerHub:** 2-3 min per variant
- **Total:** ~10-20 minutes

## 🔐 Security & Secrets

```
GitHub Repository Secrets:
├── DOCKERHUB_USERNAME
│   └── Your DockerHub username
└── DOCKERHUB_TOKEN
    └── Access token with Read & Write permissions

Not Stored in Code:
├── ✅ Credentials never in git history
├── ✅ Tokens rotatable without code changes
└── ✅ Scoped permissions (Read & Write only)
```

## 📈 Resource Usage

### GitHub Actions (Free Tier)
- **Public Repos:** Unlimited minutes
- **Private Repos:** 2,000 minutes/month
- **Concurrent Jobs:** 20 jobs
- **Storage:** 500 MB

### DockerHub (Free Tier)
- **Repositories:** Unlimited public
- **Storage:** 5 GB total
- **Bandwidth:** Unlimited
- **Pull Rate:** 200 pulls/6 hours (authenticated)

### Estimated Usage per Build
- **GitHub Actions:** ~60-90 minutes (across all jobs)
- **DockerHub Storage:** ~10-15 GB (all variants + architectures)

## 🎪 Parallel Execution

```
Job Timeline:
┌─────────┬──────────────────────────────────────┐
│ Prepare │ ████ (2 min)                         │
└─────────┴──────────────────────────────────────┘
                │
                ▼
┌──────────────┬───────────────────────────────────┐
│ Build Main   │ ████████████████████████ (20 min)│
├──────────────┼───────────────────────────────────┤
│ Build CUDA   │ ████████████████████████ (20 min)│
├──────────────┼───────────────────────────────────┤
│ Build Ollama │ ████████████████████████ (20 min)│
├──────────────┼───────────────────────────────────┤
│ Build Slim   │ ████████████████████████ (20 min)│
└──────────────┴───────────────────────────────────┘
                │ (All run in parallel)
                ▼
┌─────────────┬────────────────────────────────────┐
│ Release     │ ██ (2 min) (only for tags)        │
└─────────────┴────────────────────────────────────┘

Total Wall Time: ~24 minutes (with parallelization)
Total CPU Time: ~90 minutes (sum of all jobs)
```

## 📝 File Structure

```
.github/
├── workflows/
│   ├── docker-build.yaml      (Original GHCR workflow)
│   └── dockerhub-cicd.yaml    (New DockerHub CI/CD) ⭐
├── CI-CD-SETUP.md             (Detailed setup guide)
├── QUICKSTART.md              (Quick reference)
├── PIPELINE-ARCHITECTURE.md   (This file)
├── deploy.sh                  (Linux/Mac helper script)
└── deploy.ps1                 (Windows helper script)
```

## 🚀 Getting Started Checklist

- [ ] 1. Create DockerHub account
- [ ] 2. Create `open-webui` repository on DockerHub
- [ ] 3. Generate access token on DockerHub
- [ ] 4. Add `DOCKERHUB_USERNAME` secret to GitHub
- [ ] 5. Add `DOCKERHUB_TOKEN` secret to GitHub
- [ ] 6. Push code to trigger first build
- [ ] 7. Monitor Actions tab for build progress
- [ ] 8. Pull and test your images
- [ ] 9. Set up auto-deployment (optional)
- [ ] 10. Celebrate! 🎉

## 📚 Additional Resources

- **Workflow File:** `.github/workflows/dockerhub-cicd.yaml`
- **Setup Guide:** `.github/CI-CD-SETUP.md`
- **Quick Start:** `.github/QUICKSTART.md`
- **GitHub Actions Docs:** https://docs.github.com/actions
- **Docker Build Docs:** https://docs.docker.com/build/
- **DockerHub Docs:** https://docs.docker.com/docker-hub/

---

*Architecture documented: October 12, 2025*
