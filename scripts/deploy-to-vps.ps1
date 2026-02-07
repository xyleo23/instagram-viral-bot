# Deploy Instagram Viral Bot to VPS
# Usage: edit $VPS_USER and $VPS_HOST below, then run:
#   .\scripts\deploy-to-vps.ps1
# Or with custom path: .\scripts\deploy-to-vps.ps1 -RemotePath "/home/user/instagram_bot"

param(
    [string]$RemotePath = "~/instagram_bot"
)

# ============ НАСТРОЙКИ — ЗАПОЛНИ СВОИ ДАННЫЕ ============
$VPS_USER = "root"          # или ubuntu, deploy и т.д.
$VPS_HOST = "YOUR_VPS_IP"   # IP или домен сервера, например 123.45.67.89
# ==========================================================

$REMOTE = "${VPS_USER}@${VPS_HOST}:$RemotePath"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

if ($VPS_HOST -eq "YOUR_VPS_IP") {
    Write-Host "ERROR: Edit the script and set VPS_USER and VPS_HOST (VPS IP or domain)." -ForegroundColor Red
    exit 1
}

Write-Host "Deploying to $REMOTE" -ForegroundColor Cyan
Set-Location $ProjectRoot

# 1. Create remote dir
Write-Host "Creating remote directory..." -ForegroundColor Yellow
ssh "${VPS_USER}@${VPS_HOST}" "mkdir -p $RemotePath"

# 2. Upload app, config files, Dockerfile, requirements
Write-Host "Uploading project files..." -ForegroundColor Yellow
scp -r app docker-compose.yml Dockerfile requirements.txt .dockerignore .env.example "${REMOTE}/"

# 3. Upload .env (secrets)
if (Test-Path ".env") {
    Write-Host "Uploading .env..." -ForegroundColor Yellow
    scp .env "${REMOTE}/"
} else {
    Write-Host "WARNING: .env not found. Create .env on server manually or copy from .env.example" -ForegroundColor Yellow
}

# 4. Run docker compose on server
Write-Host "Running docker compose on server..." -ForegroundColor Yellow
ssh "${VPS_USER}@${VPS_HOST}" "cd $RemotePath && docker compose up -d --build"

Write-Host "Done. Check logs: ssh ${VPS_USER}@${VPS_HOST} 'cd $RemotePath && docker compose logs -f bot'" -ForegroundColor Green
