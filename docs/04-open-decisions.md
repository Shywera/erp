# Open Decisions

Questions to resolve before committing to an architecture. Update this file as answers
come in — move resolved items to a "Decided" section with the date and rationale.

## Pending

1. **legacy ERP relationship** — does the new system replace legacy ERP, run alongside it
   (importing exports), or is this decided per-module? (User started answering "Stop for
   now, more info" — paused mid-decision on 2026-06-15.)
2. **Does legacy ERP expose an API** beyond server-rendered HTML pages? If yes, integration
   becomes much easier (read/write via API instead of HTML scraping or file exports).
4. **First module / starting point** — candidates: WMS (build on Skladište 3.1), core
   master data (articles/customers/machines shared backbone), Quality/CAPA (wrap
   Reklamacije 1.0), or Production/MES (normatives + scheduling + WorkOrderLog
   equivalent).
5. **Deployment model** — single user (Tehnolog) vs multi-user company-wide (Skladište
   3.1 already runs as a local network server, suggesting multi-user is the real need).
6. **"DOBAVLJAC-BOJA d.o.o."** — own company or supplier? Affects whether the cjenik
   updater logic belongs in "sales pricing" or "purchase pricing" module.
7. **Machine ID mapping** — legacy ERP machine IDs 23, 37, 52, 57, 142, 143 (shown on
   dashboard) need to be mapped to physical machine names (CX104, CX102, CD102, Polar,
   SC20, MCS115, Blumer Atlas, etc.)

## Decided

- **Tech stack** (2026-06-15): Python + FastAPI + SQLAlchemy + PostgreSQL backend,
  Jinja2 + HTMX + Alpine.js + Tailwind CSS frontend. Confirmed after reviewing
  "06 - Prijedlog tehnologije" (Python vs .NET + legacy ERP comparison). Hosted on RSERVER,
  accessed via pywebview desktop wrapper (office) and browser (warehouse/production
  tablets).
