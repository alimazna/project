# TrendCipher — Backup & Recovery

**Applies to:** Docker Compose stack and plain-process deploys. Default store is
SQLite (single file). A Postgres option is documented at the end.

---

## What to back up

1. **The database** — everything a user owns lives in SQLite
   (`trendcipher-data` volume in Docker, or `backend/trendcipher.db` in-process).
2. **`.env`** — the configuration (secrets live only in your `.env`, never in
   the app container). Keep one encrypted copy per environment.
3. Nothing else is stateful: market/news data is re-fetchable from public
   providers; static bundles are reproducible from source.

## SQLite backup (recommended — `sqlite3 .backup`)

Backup while the app is **running** is safe with the online backup API; use
`.backup` rather than `cp`.

```bash
# Docker stack: exec into the backend container
docker compose -f deploy/docker-compose.yml exec backend \
  sqlite3 /app/data/trendcipher.db ".backup '/app/data/backup.db'"

# Plain process
cd backend && sqlite3 trendcipher.db ".backup 'backup/trendcipher-$(date +%F).bak'"

# Then move the backup file off-machine (S3, rsync, NAS…)
```

Consistency is guaranteed even without stopping services. To be extra safe with
WAL mode, also copy `trendcipher.db-wal`/`-shm` together with the file, or run
`.backup` (which handles WAL correctly).

## Automatic daily backup (cron on the host)

```cron
# 03:17 daily — backup SQLite from the running compose stack
17 3 * * * cd /opt/trendcipher && docker compose -f deploy/docker-compose.yml exec -T backend sqlite3 /app/data/trendcipher.db ".backup '/app/data/backup.db'" && cp deploy/tmp/backup.db 2>/dev/null; true
```

For off-host copies, point the `cp` at a mounted backup volume or use `rclone`.

## Restore (the whole flow)

```bash
# 1. Stop the stack so nobody writes during restore
docker compose -f deploy/docker-compose.yml stop backend worker

# 2. Copy the backup into the volume location
docker compose -f deploy/docker-compose.yml cp ./trendcipher.bak backend:/app/data/trendcipher-backup.db

# 3. Replace the live DB with the backup (use sqlite, not raw cp, to stay WAL-safe)
docker compose -f deploy/docker-compose.yml exec backend \
  sqlite3 /app/data/trendcipher.db ".restore '/app/data/trendcipher-backup.db'"

# 4. Start again and verify
docker compose -f deploy/docker-compose.yml start
curl -fsS http://localhost/healthz
docker compose -f deploy/docker-compose.yml exec backend \
  sqlite3 /app/data/trendcipher.db "SELECT count(*) FROM users;"
```

### Verify a restore before relying on it

```bash
sqlite3 /path/to/backup.db "PRAGMA integrity_check;"    # → ok
sqlite3 /path/to/backup.db ".tables"                    # → schema list
```

## Plain-process notes

- Default DB file: `backend/trendcipher.db` (created on first boot).
- Dump: `sqlite3 trendcipher.db ".backup 'backup/x.bak'"`.
- Restore: stop uvicorn and worker → `.restore` → start → verify via `/healthz`.

## PostgreSQL path (scale option)

Optional and documented-only in the codebase; switch with `DATABASE_URL`:

```bash
# compose override example (buyer-provided DB service):
#   db:  postgres:16 (volume postgres-data)
#   DATABASE_URL=postgresql+psycopg://trend@app-db:5432/trendcipher
```

- Dump: `pg_dump -Fc trendcipher > trendcipher.dump`
- Restore: `pg_restore -d trendcipher --clean trendcipher.dump`
- Incremental: point-in-time recovery via WAL archiving on the host RDS/VPS.

## Recovery time budget

| Failure | To restore | RTO/RPO guidance |
|---|---|---|
| Lost container | Rebuild image + volume intact | minutes; DB untouched |
| Corrupt/erased volume | Restore latest `backup.db` (above) | RPO = your schedule cadence |
| Whole machine | Restore backup file + `.env` on new host, `docker compose up -d` | hours |

## Checklist after any restore

1. `/healthz` returns `ok`.
2. A test login works (first registered user = super_admin already in DB).
3. Market data backfills automatically on the worker’s next tick (≤ `INGESTION_LOOP_SECONDS`).
4. `.env` secrets match the restored DB (JWT mismatch = re-login required).