#!/bin/bash
# Quick deployment script

echo "🚀 Deploying Namaskah SMS updates..."

# Add all changes
git add .

# Commit with timestamp
timestamp=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "Deploy: Admin improvements, mobile features, CI/CD - $timestamp"

# Push to main (triggers auto-deploy on Render)
git push origin main

echo "✅ Pushed to main branch"
echo "⏳ Render will auto-deploy in ~5 minutes"
echo "📊 Monitor: https://dashboard.render.com"
