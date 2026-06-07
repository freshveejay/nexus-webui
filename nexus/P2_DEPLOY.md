# P2 Deploy — Seed + Org-Map against the live aimsho-webui shell

Exact steps to (1) apply the NEXUS seed and (2) add the Org-Map entry point to
the running Open WebUI container.

> DO NOT run these automatically. They are written to be executed by a human
> after review. Nothing in this branch touches the live DB on its own.

- Container: `aimsho-webui`
- Host: `192.168.1.124` (UI on `:3080`)
- ORKY org-map: `http://192.168.1.115:9470/org-map`
- Branch: `claude/p2-orgmap-seed` (off `freshveejay/nexus-webui` default `main`)

---

## 0. Pre-flight (read-only, safe)

```bash
# Confirm the container is up
docker ps --filter name=aimsho-webui

# Locate the live DB inside the container (default path)
docker exec aimsho-webui ls -l /app/backend/data/webui.db

# Confirm ORKY org-map is reachable
curl -sS -o /dev/null -w '%{http_code}\n' http://192.168.1.115:9470/org-map
```

## 1. BACK UP the live DB before anything (required)

```bash
TS=$(date +%Y%m%d-%H%M%S)
docker exec aimsho-webui sh -c "cp /app/backend/data/webui.db /app/backend/data/webui.db.bak-$TS"
docker cp "aimsho-webui:/app/backend/data/webui.db.bak-$TS" "./webui.db.bak-$TS"
ls -l "./webui.db.bak-$TS"
```

## 2. Get this branch's nexus/ files into the container

If `nexus/` is bind-mounted, `git pull` on the host checkout is enough.
Otherwise copy the three files directly:

```bash
# from a checkout of branch claude/p2-orgmap-seed
docker cp nexus/seed.py                aimsho-webui:/app/nexus/seed.py
docker cp nexus/functions/org_map.py   aimsho-webui:/app/nexus/functions/org_map.py
```

## 3. DRY-RUN the seed (no writes — verify the plan)

```bash
docker exec aimsho-webui python /app/nexus/seed.py
```

Expected: a "DRY-RUN (no writes)" header, then `Would create ...` lines for any
missing models/groups/grants, and `already exists, skipping` for anything that
is already present. The script opens the DB **read-only** in this mode, so it
physically cannot write. Confirm the plan matches the catalog:

- 5 personas: NEXUS Base, Counsel, Muse, Quant, Dispatch (base
  `nvidia/nemotron-3-super-120b-a12b`)
- 5 groups: Creative, Analyst, Operator, Manager, Admin
- model grants per group + KB grants for Analyst/Manager/Admin (KB grants only
  appear for KBs that already exist in the DB)

## 4. APPLY the seed (writes; idempotent)

Only after the dry-run plan looks correct:

```bash
docker exec aimsho-webui python /app/nexus/seed.py --apply
```

Re-running `--apply` is safe: existing rows are skipped, nothing is duplicated.

### Verify

```bash
docker exec aimsho-webui sh -c "sqlite3 /app/backend/data/webui.db \
  'SELECT name FROM model WHERE id LIKE \"nexus-%\" ORDER BY name;'"
docker exec aimsho-webui sh -c "sqlite3 /app/backend/data/webui.db \
  'SELECT name FROM \"group\" ORDER BY name;'"
docker exec aimsho-webui sh -c "sqlite3 /app/backend/data/webui.db \
  'SELECT principal_id, resource_type, resource_id FROM access_grant;'"
```

Expect 5 models, 5 groups, and the model/KB grants from the dry-run plan.

## 5. Add the Org-Map entry point

See [`ORG_MAP.md`](ORG_MAP.md) for full detail. Quick path:

1. NEXUS UI (`http://192.168.1.124:3080`) → **Admin Panel → Functions → +**.
2. Import / paste `nexus/functions/org_map.py`, id `org_map`.
3. Toggle it **Enabled**.
4. Confirm Valves: `org_map_url = http://192.168.1.115:9470/org-map`.
5. In any chat, click the **Org-Map** toolbar button → it posts a link + iframe.

## 6. (Optional) restart

A restart is **not required** for the seed (Open WebUI reads these tables live).
Only restart if you changed env/config and your deployment caches it:

```bash
docker restart aimsho-webui   # optional — do NOT do this on prod without a maintenance window
```

---

## Rollback

```bash
# stop reads from the bad state, restore the backup taken in step 1
docker cp "./webui.db.bak-$TS" aimsho-webui:/app/backend/data/webui.db
docker restart aimsho-webui
```

Disable the Org-Map: Admin Panel → Functions → toggle `org_map` **off** (or
delete it).
