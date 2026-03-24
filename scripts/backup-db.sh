#!/bin/bash
# PostgreSQL daily backup script
# Usage: Add to crontab: 0 3 * * * /path/to/backup-db.sh

set -e

BACKUP_DIR="/backups/postgres"
CONTAINER="shangtanai-postgres-1"
DB_NAME="shangtanai"
DB_USER="shangtanai"
DATE=$(date +%Y%m%d_%H%M%S)
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."
docker exec "$CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/shangtanai_${DATE}.sql.gz"

echo "[$(date)] Backup saved: shangtanai_${DATE}.sql.gz"

# Remove backups older than KEEP_DAYS
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -delete
echo "[$(date)] Cleaned up backups older than ${KEEP_DAYS} days"
