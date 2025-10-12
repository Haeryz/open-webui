# Quick deployment script for Open WebUI CI/CD (Windows PowerShell)

Write-Host "🚀 Open WebUI CI/CD Quick Deploy Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git is not installed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Git installed" -ForegroundColor Green

# Get current branch
$currentBranch = git branch --show-current
Write-Host "📍 Current branch: $currentBranch" -ForegroundColor Yellow
Write-Host ""

# Menu
Write-Host "What would you like to do?" -ForegroundColor Cyan
Write-Host "1) Push to main (triggers production build)"
Write-Host "2) Push to dev (triggers development build)"
Write-Host "3) Create a new release version (patch)"
Write-Host "4) Create a new release version (minor)"
Write-Host "5) Create a new release version (major)"
Write-Host "6) Check CI/CD status"
Write-Host "7) View recent images on DockerHub"
Write-Host "8) Exit"
Write-Host ""

$choice = Read-Host "Enter your choice [1-8]"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "🔄 Pushing to main branch..." -ForegroundColor Yellow
        git checkout main
        git pull origin main
        $msg = Read-Host "Enter commit message"
        git add .
        git commit -m $msg
        git push origin main
        Write-Host "✅ Pushed to main. Check GitHub Actions for build status." -ForegroundColor Green
        $repoUrl = (git config --get remote.origin.url) -replace '.*github.com[:/](.*?)(.git)?$', '$1'
        Write-Host "🔗 https://github.com/$repoUrl/actions" -ForegroundColor Cyan
    }
    "2" {
        Write-Host ""
        Write-Host "🔄 Pushing to dev branch..." -ForegroundColor Yellow
        git checkout dev
        git pull origin dev
        $msg = Read-Host "Enter commit message"
        git add .
        git commit -m $msg
        git push origin dev
        Write-Host "✅ Pushed to dev. Check GitHub Actions for build status." -ForegroundColor Green
    }
    "3" {
        Write-Host ""
        Write-Host "📦 Creating PATCH release (0.0.x)..." -ForegroundColor Yellow
        git checkout main
        git pull origin main
        npm version patch
        $version = (Get-Content package.json | Select-String '"version"' | Select-Object -First 1) -replace '.*"version":\s*"([^"]+)".*', '$1'
        git push origin main --tags
        Write-Host "✅ Created version v$version and pushed tag" -ForegroundColor Green
        $repoUrl = (git config --get remote.origin.url) -replace '.*github.com[:/](.*?)(.git)?$', '$1'
        Write-Host "🔗 Check releases at: https://github.com/$repoUrl/releases" -ForegroundColor Cyan
    }
    "4" {
        Write-Host ""
        Write-Host "📦 Creating MINOR release (0.x.0)..." -ForegroundColor Yellow
        git checkout main
        git pull origin main
        npm version minor
        $version = (Get-Content package.json | Select-String '"version"' | Select-Object -First 1) -replace '.*"version":\s*"([^"]+)".*', '$1'
        git push origin main --tags
        Write-Host "✅ Created version v$version and pushed tag" -ForegroundColor Green
    }
    "5" {
        Write-Host ""
        Write-Host "📦 Creating MAJOR release (x.0.0)..." -ForegroundColor Yellow
        git checkout main
        git pull origin main
        npm version major
        $version = (Get-Content package.json | Select-String '"version"' | Select-Object -First 1) -replace '.*"version":\s*"([^"]+)".*', '$1'
        git push origin main --tags
        Write-Host "✅ Created version v$version and pushed tag" -ForegroundColor Green
    }
    "6" {
        Write-Host ""
        Write-Host "📊 Opening GitHub Actions..." -ForegroundColor Yellow
        $repoUrl = (git config --get remote.origin.url) -replace '.*github.com[:/](.*?)(.git)?$', '$1'
        $url = "https://github.com/$repoUrl/actions"
        Write-Host "🔗 $url" -ForegroundColor Cyan
        Start-Process $url
    }
    "7" {
        Write-Host ""
        Write-Host "🐳 DockerHub images:" -ForegroundColor Yellow
        $username = Read-Host "Enter your DockerHub username"
        $url = "https://hub.docker.com/r/$username/open-webui/tags"
        Write-Host "🔗 $url" -ForegroundColor Cyan
        Start-Process $url
    }
    "8" {
        Write-Host "👋 Goodbye!" -ForegroundColor Cyan
        exit 0
    }
    default {
        Write-Host "❌ Invalid choice" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✨ Done!" -ForegroundColor Green
