# API Examples

All commands below are PowerShell (`Invoke-WebRequest`), tested against
a locally running server (`uvicorn app.main:app --reload`).

Node IDs shown (e.g. `7`, `15`) are examples from this project's actual
ingested data — run the `/browse/sections` command first to get your
own real IDs if your database differs.

---

## Browse API

### List top-level sections (latest version)
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/browse/sections?version=latest" -Method GET
```

### List top-level sections (explicit version)
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/browse/sections?version=v1" -Method GET
```

### Get a specific node's full detail
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/browse/nodes/7" -Method GET
```

### Search across headings/body text
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/browse/search?q=battery&version=latest" -Method GET
```

### Check a node's change status across versions (with diff)
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/browse/nodes/7/diff" -Method GET
```

---

## Selection API (version-pinned)

### Create a selection
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/selections" -Method POST -ContentType "application/json" -Body '{"name": "battery-and-alarms", "node_ids": [7, 15]}'
```
Response includes the new selection's `id` — use it below.

### Retrieve a selection (resolves to exact pinned text)
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/selections/1" -Method GET
```

---

## Generation API

### Generate test cases from a selection
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations/selections/1" -Method POST
```

### Submit the same selection again (duplicate-submission policy)
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations/selections/1" -Method POST
```
Returns `"status":"existing_generation_returned"` instead of calling the
LLM again — confirmed working.

### Force a fresh regeneration
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations/selections/1?force=true" -Method POST
```

---

## Retrieval API

### Fetch generations by selection ID
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations?selection_id=1" -Method GET
```

### Fetch generations by node ID
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations?node_id=7" -Method GET
```

Both include a `staleness` object: `{"is_stale": bool, "stale_nodes": [...]}`.

---

## Full End-to-End Versioning + Staleness Flow (as actually run and verified)

```powershell
# 1. Ingest v1
python -m app.services.run_ingest data/ct200_manual_v1.pdf v1

# 2. Browse v1, find "Battery Life Under Typical Use" node (id=7 in this run)
Invoke-WebRequest -Uri "http://127.0.0.1:8000/browse/sections?version=v1" -Method GET

# 3. Create a version-pinned selection
Invoke-WebRequest -Uri "http://127.0.0.1:8000/selections" -Method POST -ContentType "application/json" -Body '{"name": "battery-and-alarms", "node_ids": [7, 15]}'

# 4. Generate test cases
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations/selections/1" -Method POST

# 5. Confirm fresh (is_stale: false)
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations?selection_id=1" -Method GET

# 6. Ingest v2 — battery life text changes from
#    "300 cycles / 15%" to "250 cycles / 10%"
python -m app.services.run_ingest data/ct200_manual_v2.pdf v2

# 7. Re-check — staleness now correctly flips to true
Invoke-WebRequest -Uri "http://127.0.0.1:8000/generations?selection_id=1" -Method GET
# -> "staleness":{"is_stale":true,"stale_nodes":[{"node_id":7,"reason":"content_changed"}]}

# The original selection (step 3) still resolves to its exact v1 text,
# unaffected by v2's ingestion:
Invoke-WebRequest -Uri "http://127.0.0.1:8000/selections/1" -Method GET
```

This end-to-end flow was manually run and verified during development —
see `docs/approach.md`, Phase 5 Debugging Notes, for the staleness bug
found and fixed during this exact test.