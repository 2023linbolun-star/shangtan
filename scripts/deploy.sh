#!/bin/bash
# Deployment script for 商探AI
# Usage: ssh into server, then run this script

set -e

PROJECT_DIR="/root/shangtanai"
cd "$PROJECT_DIR"

echo "[$(date)] Starting deployment..."

# Pull latest code
git pull origin main

# Backup database before deploy
echo "[$(date)] Backing up database..."
bash scripts/backup-db.sh || echo "Warning: backup failed, continuing deploy"

# Build and restart
echo "[$(date)] Building and restarting services..."
docker compose build
docker compose up -d

# Health check
echo "[$(date)] Waiting for services to start..."
sleep 5
if curl -sf http://localhost/health > /dev/null; then
    echo "[$(date)] Deployment successful! Health check passed."
else
    echo "[$(date)] WARNING: Health check failed. Check logs with: docker compose logs"
fi
