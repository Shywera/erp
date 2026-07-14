---
name: run-erp-mes-wms
description: Run, launch, start, smoke-test, or screenshot the ERP/MES/WMS FastAPI app (label-printing ERP/MES/WMS). Boots uvicorn against an isolated copy of the DB, checks every module endpoint, and screenshots the rendered UI via headless Edge. Use when asked to run/start/serve the app, verify it boots, or capture a screenshot.
---

# Run ERP/MES/WMS

FastAPI + SQLAlchemy 2.0 + SQLite + Jinja2 + HTMX + Tailwind (CDN) web app. Server-side
rendered HTML; no JS build step. Driven by **`.claude/skills/run-erp-mes-wms/driver.ps1`**
(Windows PowerShell): it isolates the DB, launches uvicorn, smoke-tests all module
endpoints, and screenshots the UI with headless Edge.

Environment: **Windows + Windows PowerShell 5.1**. Paths below are relative to the repo
root (`C:\Users\Tehnolog\Desktop\ERP-MES-WMS`).

## Prerequisites

- The repo ships a working `.venv`. Verify deps + DB are current (both safe to re-run):
  ```powershell
  .venv\Scripts\python -m pip install -r requirements.txt
  .venv\Scripts\python -m alembic upgrade head
  ```
- If `.venv` is missing, recreate everything with the project's bootstrap script
  `instalacija.bat` (creates venv, installs requirements, runs migrations).
- Microsoft Edge (preinstalled on Windows) is used for screenshots — no extra install.

## Run (agent path) — the driver

```powershell
powershell -ExecutionPolicy Bypass -File .claude\skills\run-erp-mes-wms\driver.ps1
```

What it does (all automatic, ~5s):
- Copies `dev.db` -> `test_driver.db` and points `DATABASE_URL` at the copy, so your real
  DB and any dev server on :8000 are never touched.
- Launches uvicorn on port 8799 (override with `-Port`), waits for readiness.
- Checks 13 endpoints (every module landing + a few HTMX partials), prints OK/FAIL per row.
- Scans the startup log for tracebacks.
- Screenshots `/materijali` to `driver_screenshot.png` (override page with `-Screenshot`).
- Stops the server and removes the test DB + logs (keeps the screenshot).
- **Exit 0 = all green; exit 1 = an endpoint failed or a traceback was found.**

Verified output this session: `== 13/13 endpoints OK ==`, screenshot ~157 KB.

Options:
```powershell
# screenshot a different page
powershell -ExecutionPolicy Bypass -File .claude\skills\run-erp-mes-wms\driver.ps1 -Screenshot /reklamacije

# leave the server running for manual poking (prints the stop command)
powershell -ExecutionPolicy Bypass -File .claude\skills\run-erp-mes-wms\driver.ps1 -KeepRunning
```

After `-KeepRunning`, drive it with `Invoke-WebRequest` against `http://localhost:8799`,
then stop it:
```powershell
Get-NetTCPConnection -LocalPort 8799 -State Listen | %{ Stop-Process -Id $_.OwningProcess -Force }
```

## Run (human path)

`pokreni.bat` opens the browser and runs `uvicorn app.main:app --reload` on
`http://127.0.0.1:8000`. For LAN access use `dev-wifi.bat` (binds `0.0.0.0:8000`).
Useless for automated checks (blocks, spawns a window) — use the driver instead.

## Gotchas

- **PowerShell 5.1 + non-ASCII = parse errors.** Keep `driver.ps1` ASCII-only; an em-dash
  or `c/c/z/s` in the script (saved without a BOM) makes PS 5.1 throw `Unexpected token`.
- **Edge stderr trips `ErrorActionPreference=Stop`.** Headless Edge writes a harmless
  `task_manager` ERROR line to stderr; a bare `& msedge ...` call escalates it to a
  terminating `NativeCommandError`. The driver runs Edge via `Start-Process` with
  redirected streams to dodge this. Don't "simplify" it back to a direct call.
- **`Start-Process -RedirectStandardOutput`/`-RedirectStandardError` must be different
  files** — pointing both at one path errors. The driver uses two.
- **Never stop uvicorn by name.** `Stop-Process -Name uvicorn` would kill every instance
  (incl. a real dev server / parallel runs). Always stop by port -> PID, as the driver does.
- **DB isolation via env var.** `app/core/config.py` reads `DATABASE_URL` (pydantic
  settings); setting it before launch overrides the `sqlite:///./dev.db` default. The
  driver relies on this to run against a throwaway copy.
- **SQLite = single writer.** Fine for one user / smoke tests; concurrent writers get
  "database is locked". Production swaps to Postgres via `DATABASE_URL` in `.env`.
- **`/` returns 307 -> `/materijali`.** `Invoke-WebRequest` follows it to 200; that's expected.
- **`tehnoloski-postupci` shows a permanent "U IZRADI" banner** by design — it's a
  work-in-progress module, not a bug.

## Troubleshooting

- **`SERVER DID NOT START`** + error-log tail printed: usually an import error or a missing
  migration. Run `.venv\Scripts\python -c "import app.main"` to see the traceback directly,
  and `.venv\Scripts\python -m alembic upgrade head`.
- **`uvicorn not found at ...`**: the venv is missing — run `instalacija.bat`.
- **Screenshot says FAILED / not produced**: Edge path differs; the driver checks the two
  standard install dirs. Confirm with `Get-Command msedge` or
  `Test-Path "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"`.
- **Port already in use**: another run/dev server holds 8799 — pass `-Port 8798`, or the
  driver auto-frees its own port at start.
