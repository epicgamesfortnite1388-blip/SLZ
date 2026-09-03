#!/usr/bin/env bash
# backup-erp.sh — nightly backup for the SLZ ERP stack.
#
#   ./scripts/backup-erp.sh              # run one backup now
#   ./scripts/backup-erp.sh --install-cron   # install /etc/cron.d/slz-erp-backup
#
# What it does:
#   * pg_dump of the ERP database (via docker compose exec, no host port needed)
#   * tar.gz of the docker media volume (attachments/uploads)
#   * verifies both archives (gzip -t) and records sizes/SHA256
#   * keeps the newest BACKUP_RETENTION daily archives (default 30)
#   * optional off-box copy when OFFBOX_TARGET=user@host:/path is set (rsync)
#
# Run as root (docker access). Safe to run while the stack is up — pg_dump
# takes a consistent snapshot; no downtime.
set -euo pipefail
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ERP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE="docker compose --project-directory "$ERP_DIR" -f "$ERP_DIR/docker-compose.yml""
[ -f "$ERP_DIR/docker-compose.prod.yml" ] && \
    COMPOSE="docker compose --project-directory "$ERP_DIR" -f "$ERP_DIR/docker-compose.yml" -f "$ERP_DIR/docker-compose.prod.yml""

BACKUP_ROOT="${BACKUP_ROOT:-/root/slz-erp-backups}"
RETENTION="${BACKUP_RETENTION:-30}"
LOG="/var/log/slz-erp-backup.log"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="$BACKUP_ROOT/$STAMP"
mkdir -p "$DEST"

# Database credentials (same defaults the compose file uses).
pg_val() { # pg_val <key>
    local v
    v="$(grep -E "^$1=" "$ERP_DIR/.env" 2>/dev/null | head -1 | cut -d= -f2- || true)"
    printf '%s' "${v:-$2}"
}
PG_USER="$(pg_val POSTGRES_USER slz_erp)"
PG_DB="$(pg_val POSTGRES_DB slz_erp)"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "[$(ts)] $*" | tee -a "$LOG"; }
die() { log "ERROR: $*"; exit 1; }

if [ "${1:-}" = "--install-cron" ]; then
    CRON_FILE=/etc/cron.d/slz-erp-backup
    # 3:15 a.m. — after the host-level VPS backup (3:00) so disk writes are spread.
    printf 'SHELL=/bin/bash\nPATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n15 3 * * * root %s >> %s 2>&1\n' \
        "$SCRIPT_DIR/backup-erp.sh" "$LOG" > "$CRON_FILE"
    chmod 644 "$CRON_FILE"
    log "installed $CRON_FILE (runs daily at 03:15)"
    exit 0
fi

log "starting ERP backup -> $DEST"

# 1. Database
log "pg_dump ${PG_DB} ..."
if $COMPOSE exec -T postgres pg_dump -U "$PG_USER" "$PG_DB" 2>/dev/null \
        | gzip -1 > "$DEST/db.sql.gz"; then
    gzip -t "$DEST/db.sql.gz" && log "OK db.sql.gz ($(du -h "$DEST/db.sql.gz" | cut -f1))" \
        || die "db.sql.gz failed verification"
else
    die "pg_dump failed (is the stack up? 'docker compose ps')"
fi

# 2. Media volume (attachments/uploads)
MEDIA_VOL="$(docker volume ls -q | grep -E '(^|_)media_data$' | head -1 || true)"
if [ -n "$MEDIA_VOL" ]; then
    log "archiving media volume $MEDIA_VOL ..."
    if docker run --rm -v "$MEDIA_VOL:/data:ro" -v "$DEST:/backup" alpine:3 \
            tar czf "/backup/media.tgz" -C /data . 2>/dev/null \
            && gzip -t "$DEST/media.tgz"; then
        log "OK media.tgz ($(du -h "$DEST/media.tgz" | cut -f1))"
    else
        die "media volume archive failed"
    fi
else
    log "WARN: no media volume found — skipping (uploads not backed up)"
fi

# 3. Manifest + integrity record
( cd "$DEST" && sha256sum ./* > SHA256SUMS 2>/dev/null || true )

# 4. Retention — keep the newest N archive directories
ls -1dt "$BACKUP_ROOT"/20* 2>/dev/null | tail -n +$((RETENTION + 1)) | while read -r old; do
    log "pruning old backup $old"
    rm -rf "$old"
done

# 5. Optional off-box copy (e.g. OFFBOX_TARGET=backup@nas:/srv/backups/slz)
if [ -n "${OFFBOX_TARGET:-}" ]; then
    log "rsync to ${OFFBOX_TARGET} ..."
    rsync -a --delete "$BACKUP_ROOT/" "${OFFBOX_TARGET%/}/" && log "OK off-box rsync" \
        || log "WARN: off-box rsync failed (see above)"
fi

log "backup complete. retained: $(ls -1dt "$BACKUP_ROOT"/20* 2>/dev/null | wc -l) daily archives"
