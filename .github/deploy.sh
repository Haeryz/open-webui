#!/bin/bash
# Quick deployment script for Open WebUI CI/CD

echo "🚀 Open WebUI CI/CD Quick Deploy Script"
echo "========================================"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists git; then
    echo "❌ Git is not installed"
    exit 1
fi
echo "✅ Git installed"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"
echo ""

# Menu
echo "What would you like to do?"
echo "1) Push to main (triggers production build)"
echo "2) Push to dev (triggers development build)"
echo "3) Create a new release version (patch)"
echo "4) Create a new release version (minor)"
echo "5) Create a new release version (major)"
echo "6) Check CI/CD status"
echo "7) View recent images on DockerHub"
echo "8) Exit"
echo ""
read -p "Enter your choice [1-8]: " choice

case $choice in
    1)
        echo ""
        echo "🔄 Pushing to main branch..."
        git checkout main
        git pull origin main
        read -p "Enter commit message: " msg
        git add .
        git commit -m "$msg"
        git push origin main
        echo "✅ Pushed to main. Check GitHub Actions for build status."
        echo "🔗 https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
        ;;
    2)
        echo ""
        echo "🔄 Pushing to dev branch..."
        git checkout dev
        git pull origin dev
        read -p "Enter commit message: " msg
        git add .
        git commit -m "$msg"
        git push origin dev
        echo "✅ Pushed to dev. Check GitHub Actions for build status."
        ;;
    3)
        echo ""
        echo "📦 Creating PATCH release (0.0.x)..."
        git checkout main
        git pull origin main
        npm version patch
        VERSION=$(cat package.json | grep '"version"' | head -1 | awk -F: '{ print $2 }' | sed 's/[",]//g' | tr -d '[[:space:]]')
        git push origin main --tags
        echo "✅ Created version v$VERSION and pushed tag"
        echo "🔗 Check releases at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases"
        ;;
    4)
        echo ""
        echo "📦 Creating MINOR release (0.x.0)..."
        git checkout main
        git pull origin main
        npm version minor
        VERSION=$(cat package.json | grep '"version"' | head -1 | awk -F: '{ print $2 }' | sed 's/[",]//g' | tr -d '[[:space:]]')
        git push origin main --tags
        echo "✅ Created version v$VERSION and pushed tag"
        ;;
    5)
        echo ""
        echo "📦 Creating MAJOR release (x.0.0)..."
        git checkout main
        git pull origin main
        npm version major
        VERSION=$(cat package.json | grep '"version"' | head -1 | awk -F: '{ print $2 }' | sed 's/[",]//g' | tr -d '[[:space:]]')
        git push origin main --tags
        echo "✅ Created version v$VERSION and pushed tag"
        ;;
    6)
        echo ""
        echo "📊 Opening GitHub Actions..."
        REPO_URL=$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')
        echo "🔗 https://github.com/$REPO_URL/actions"
        if command_exists xdg-open; then
            xdg-open "https://github.com/$REPO_URL/actions"
        elif command_exists open; then
            open "https://github.com/$REPO_URL/actions"
        fi
        ;;
    7)
        echo ""
        echo "🐳 DockerHub images:"
        read -p "Enter your DockerHub username: " username
        echo "🔗 https://hub.docker.com/r/$username/open-webui/tags"
        if command_exists xdg-open; then
            xdg-open "https://hub.docker.com/r/$username/open-webui/tags"
        elif command_exists open; then
            open "https://hub.docker.com/r/$username/open-webui/tags"
        fi
        ;;
    8)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✨ Done!"
