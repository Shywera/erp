# Module: Skladište (WMS — warehouse / pallet management)

> **Status: Faze 1–4 izgrađene ✅ — gotovo osim go-live (pravi legacy ERP).**
> Faza 4 dovršena: multi-paletno zaprimanje, izdavanje po količini, prioriteti GUI, karta=tlocrt,
> sve-palete lista, **PDF ispisi** (stanje-tlocrt + lista zaprimanja). Detalji niže (Faza 4).
> - **Faza 1** — temelj: `REGALI` (20 regala, 1503 mjesta) + validacija pozicije, modeli +
>   migracija `da93a22079c1`, dashboard s metrikama i popunjenošću po zonama.
> - **Faza 2** — ERP adapter: `ErpAdapter` + `MockAdapter` + `LegacyErpAdapter` (REST/Basic,
>   `ERP_ADAPTER=mock|pauk` u `.env`), `GET /skladiste/lookup`.
> - **Faza 3** — glavni tok (`service.py`): **zaprimanje** (skener → mock lookup → algoritam
>   predloži poziciju s klasteriranjem → potvrdi), **FIFO/FEFO izdavanje**, **inventura**
>   (nedostaje/neočekivano). Zebra PDA UX: veliki inputi, Enter-submit, povrat fokusa,
>   in-flight lock. Dashboard funkcije sad linkovi.
> - Verificirano: validator, B3/B6 constraint, adapter, placement+klasteriranje, sva 3 toka
>   end-to-end (TestClient), **18/18 smoke + screenshot**.
> Sljedeće: go-live (spoj na pravi legacy ERP, `ERP_ADAPTER=pauk`) kad IT izloži REST API.
> Ported from the legacy standalone "Skladište" app v3.1 (see
> `Arhiva skripta/Skladište/3.1/SKLADISTE_KOMPLETNI_GUIDE.md`). We re-implement the
> proven domain model in our stack (SQLAlchemy 2.0 + Alembic + Jinja2/HTMX) and **fix the
> known legacy bugs by design** rather than copying the raw-sqlite code.

## Scope

Pallet-level warehouse management for the label-printing plant:
- **Zaprimanje** (receiving): create a plan, algorithm suggests positions, double-scan
  (pallet + position) to confirm, override allowed.
- **Izdavanje** (issuing): FIFO/FEFO, bulk scan session with rollback.
- **Inventura** (stocktake): scan, report missing / unexpected, reconcile.
- **Prioriteti** (placement rules per šifra): clustering + 4 placement modes.
- **Mapa skladišta** (2D/3D occupancy) — later phase.
- **Naljepnice** (QR labels) — later phase.

**Receiving reads pallet data from legacy ERP:** the worker scans the product **barcode**, the app
looks it up in the current ERP (legacy ERP) over REST and gets the article fields (šifra, naziv,
kolicina, rok, lot). The legacy ERP API will be ready **before go-live**, so the integration is
**in scope now** — built against a **mock** of the agreed REST contract until IT exposes the
real endpoints, then we just swap the URL. legacy ERP is called **only at receiving**; the scanned
barcode is stored as `qr_raw`, and later scans (izdaj/inventura) match the pallet in our own
DB (no legacy ERP call). Manual entry stays as a fallback for goods legacy ERP doesn't know.

Out of scope for v1: šifra↔Materijali linking, login / user tracking (both later via the
ERP), write-back to legacy ERP (read-only rule), ngrok/mobile tunnel (we have LAN via `dev-wifi.bat`).

## Hardware / scanning — Zebra PDA (DECIDED)
Target device is a **Zebra PDA**, not a phone. Its **hardware scanner acts as a keyboard
wedge** (scan → the barcode text is typed into the focused field + an Enter). Consequences:
- **No camera / JS barcode scanner** (legacy used the phone camera — dropped).
- Scan inputs are auto-focused `<input>`s that **submit on Enter** (`hx-trigger="keyup[key=='Enter']"`),
  with **focus returned** to the next expected field after each scan — fixes the legacy
  scan-rhythm bug (U4/U10), and an **in-flight lock** so a fast scan can't double-submit (B5).
- **PDA-optimized UI** for the scan flows: large tap targets + large type, single column,
  minimal typing. (Dashboard/map can stay denser.)
- Android Zebra runs Chrome/WebView → our Tailwind/HTMX/Alpine stack works as-is; the PDA
  reaches the app over warehouse **WiFi → local server (LAN)**.

## Design decisions (these are the legacy fixes — non-negotiable)

1. **ISO dates everywhere in the DB** (`Date` / `DateTime` columns, not `dd.mm.yyyy`
   strings). Legacy substring date-parsing is bug B7/B8 → FIFO issued the wrong pallet.
   Format to Croatian only in the template layer (we already have date filters elsewhere).
2. **`kolicina` is numeric** (`Numeric`/`Float`), not TEXT → enables sums and partial issue.
3. **Position validation is mandatory** on every store/edit. Legacy had a validator it
   never called (bug B2/B17 → phantom pallets on non-existent positions). A position is valid
   iff it parses and resolves against the `REGALI` constant (see #12).
4. **Racks are a fixed code constant, never rewritten from the UI** (see #12) — kills the
   legacy code-injection bug B14 (`/api/warehouse/save` rewrote `warehouse.py` from input).
5. **One active pallet per position** enforced by a **partial unique index**
   (`UNIQUE(pozicija) WHERE datum_out IS NULL`). Kills the double-booking race (B3) and the
   resurrect-onto-occupied rollback bug (B6) at the DB level.
6. **Transactions** wrap the multi-row flows (prijem confirm, bulk izdaj, inventura close)
   so a mid-flow failure can't leave orphan rows (B4).
7. **Indexes** on `qr_raw`, `sifra`, `pozicija`, `datum_out` (legacy had none → full scans).
8. **Placement algorithm returns exactly `n` or signals a shortage** — never a silent
   partial list (legacy B9: a short list passed the `if not prijedlozi` check).
9. **Position codes are stored EXACTLY as printed on the QR — no zero-padding**
   (`A1P1V1`, `A13P15V5`), never auto-padded. The numeric parts are **variable width**, so
   anything that orders/ranges positions must sort by the **parsed integers**
   `(regal#, pozicija#, visina#)`, never by the raw string (else `P10` sorts before `P2`).
   The validator and placement algorithm already operate on parsed ints, so this is free —
   it just must never regress to string comparison. (Legacy used padded `R1AP03V2`; our real
   warehouse uses unpadded — see "Stvarni raspored".)
10. **No login and no user tracking in v1** (DECIDED): no `korisnik` field anywhere. Who-did-
    what arrives later via the ERP-wide auth module. No secrets/tokens hardcoded.
11. **Pallet data comes from legacy ERP at receiving** (DECIDED): scan product barcode → legacy ERP REST
    lookup → article fields. **In scope**, built against a **mock** of the contract until IT
    delivers the real API (then swap the URL — already written and tested). We impose ISO dates
    + numeric kolicina in the contract (kills FIFO bug B7 at the source). legacy ERP is hit **only at
    receiving**; the barcode is stored as `qr_raw` and reused locally afterward. No Materijali
    link. Manual entry is the fallback for unknown barcodes.
12. **Racks are a FIXED code constant, NOT a DB table** (DECIDED): the 20 racks never change
    at runtime; if they ever change, a developer edits the constant. So there is **no `regal`
    table and no rack-editing UI** — which also fully kills legacy bug B14 (UI rewriting code).
    The validator, capacity totals, and map all read from this constant.

## Tables (SQLAlchemy 2.0)

### Regali — fixed config in code (no DB table, no CRUD)
Racks are defined once as a constant in the module (`warehouse.py`/`config.py`):

```python
# (naziv, zona, broj_pozicija, broj_visina) -- map layout coords added later if needed
REGALI = (
    [(f"A{i}", "A", 15, 5) for i in range(1, 14)] +  # A1..A13
    [(f"B{i}", "B", 15, 4) for i in range(1, 6)]  +  # B1..B5
    [("C1", "C", 30, 4)] +
    [("D1", "D", 27, 4)]
)
# 20 racks, 1503 positions total
```

**Position format:** `‹ZONA›‹REGAL#›P‹POZICIJA›V‹VISINA›`, unpadded — e.g. `A13P15V5` =
zona A, regal 13, pozicija 15, visina 5. A position is valid iff it parses and falls within
its rack's `broj_pozicija` / `broj_visina` (looked up in `REGALI`).

```
validator regex:  ^([A-D])(\d{1,2})P(\d{1,2})V(\d)$
bounds (per zone, all racks in a zone share dims):
  A -> regal 1..13, pozicija 1..15, visina 1..5
  B -> regal 1..5,  pozicija 1..15, visina 1..4
  C -> regal 1,     pozicija 1..30, visina 1..4
  D -> regal 1,     pozicija 1..27, visina 1..4
```
Implemented once in a `pozicija` helper, called on every pallet store/edit.

#### Stvarni raspored skladišta (mjerodavno — iz QR popisa)
Source: the real position-code ranges for this warehouse (4 zones, all racks within a zone
share dimensions).

| Zona | Regali | Pozicija/regal | Visina | Mjesta/regal | Ukupno zona |
|---|---|---|---|---|---|
| A | A1–A13 (13) | 15 | 5 | 75 | **975** |
| B | B1–B5 (5)   | 15 | 4 | 60 | **300** |
| C | C1 (1)      | 30 | 4 | 120 | **120** |
| D | D1 (1)      | 27 | 4 | 108 | **108** |
| **Σ** | **20 regala** | | | | **1503 mjesta** |

Zone A is the only one with 5 levels and is ~65% of capacity. C and D are single long racks
(likely horizontal). Ranges: `A1P1V1–A13P15V5`, `B1P1V1–B5P15V4`, `C1P1V1–C1P30V4`,
`D1P1V1–D1P27V4`. This table is the source for the `REGALI` constant above.

### `paleta` — active + historical pallets
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| qr_raw | text, indexed | the **scanned barcode** (used as the pallet key for later scans) |
| sifra | varchar, indexed | article code (from legacy ERP lookup) |
| naziv | varchar, nullable | article name (from legacy ERP; stored so display needs no re-lookup) |
| lot | varchar, nullable | from legacy ERP |
| kolicina | numeric, nullable | **numeric** (from legacy ERP); supports partial issue |
| jedinica | varchar, nullable | unit/JM (from legacy ERP) |
| datum_ulaza | date, nullable | **ISO**; production/entry date (from legacy ERP or set at receiving) |
| rok_trajanja | date, nullable, indexed | **ISO** (from legacy ERP); for FEFO |
| pozicija | varchar, indexed | validated against `REGALI` constant |
| datum_in | datetime | when stored |
| datum_out | datetime, nullable, indexed | **NULL = active**; set = issued (soft delete) |
| izvor | varchar, nullable | `pauk` / `rucno` — how the data was obtained |

At receiving, `sifra/naziv/lot/kolicina/jedinica/rok_trajanja` come from the **legacy ERP lookup**
of the scanned `qr_raw`; dates arrive ISO per our contract (or are normalized). Unknown
barcode → manual entry (`izvor=rucno`). Later scans (izdaj/inventura) find the pallet by
`qr_raw` in our DB — no legacy ERP call.

Partial unique index: `Index("uq_paleta_aktivna_pozicija", "pozicija", unique=True,
sqlite_where=text("datum_out IS NULL"), postgresql_where=text("datum_out IS NULL"))`.

### `prijem` — receiving plan header
`id` PK · `sifra` · `broj_paleta` int · `datum_plan` date · `status`
(`aktivan`/`zavrsen`/`odustao`). Relationship `stavke` → PrijemStavka.

### `prijem_stavka` — receiving plan line
`id` PK · `prijem_id` FK→prijem.id, indexed · `redni_broj` int · `pozicija` (validated) ·
`qr_raw` nullable (filled on confirm) · `datum_potvrda` datetime nullable (NULL=unconfirmed).

### `inventura` — stocktake header
`id` PK · `datum_pocetka` datetime · `datum_kraja` datetime nullable ·
`status` (`aktivan`/`zavrsen`/`ponistena`). Relationship `stavke` → InventuraStavka.

### `inventura_stavka`
`id` PK · `inventura_id` FK, indexed · `qr_raw` · `pozicija_skenirana` · `datum_skeniranja`.

### `prioritet` — placement rule per šifra
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| sifra | varchar, indexed | |
| mod | varchar | `standardno` / `puni_rupe` / `lijevi` / `strogo_lijevo` (legacy overloaded one int — we split it out) |
| rack_ids | text, nullable | CSV of allowed rack names (v1; a join table is the clean later option) |
| napomena | text, nullable | |
| aktivan | bool, default true | |

### `skladiste_event` — audit log
`id` PK · `timestamp` datetime · `tip` · `poruka` · `detalji` nullable.
(What happened + when; the "who" is added later with ERP auth. Could fold into an ERP-wide
audit log.)

## Placement algorithm (`predlozi_mjesta(n, sifra)`)
Port the v3.1 logic (it is the valuable IP), with the B9 fix:
1. **Clustering first** (when `sifra` given): free positions on racks already holding the
   same šifra; if it yields all `n`, return.
2. **By mode** (`prioritet.mod`, default `standardno`):
   - `standardno`: consecutive (same height, same rack) then any; respect `rack_ids`.
   - `puni_rupe`: partially-filled racks first (consolidate), then empty.
   - `lijevi`: racks sorted by `min_x` ascending (toward the exit first).
   - `strogo_lijevo`: left half only (by X median), **no fallback** — but return value
     **explicitly signals shortage** (`{found: k, of: n}`), callers must check.
Lower heights (V1) fill first (good for FIFO reach). Helpers: `_uzastopne`, `_bilo_koje`,
`_trazi`. "Consecutive" = same height within one rack (no cross-rack spanning).

## FIFO/FEFO issue
Sort candidate active pallets for a šifra by `datum_ulaza` (FIFO) or `rok_trajanja` (FEFO)
— now trivial and correct because both are real `Date` columns (no string parsing). Warn
when issuing a newer pallet while an older one exists. Bulk session: collect scans in a
transaction, "Završi i spremi" (commit) or "Završi bez spremanja" (rollback all).

## Routes (`/skladiste`, HTMX partials per our convention)
- `GET /skladiste` — dashboard (metrics: zauzeto/slobodno/ukupno/ističe-30d) + tab nav
  (capacity totals come from the `REGALI` constant — no regali routes/CRUD)
- Lookup (legacy ERP): `GET /skladiste/lookup?barkod=` — internal endpoint the receiving form calls
  on scan; returns the article fields from legacy ERP (or the mock) for confirmation
- Zaprimanje: `GET /skladiste/zaprimanje`, `POST .../plan` (calls `predlozi_mjesta`),
  `POST .../potvrdi`, `POST .../override`, `POST .../zatvori`, `POST .../odustani/{id}`,
  `GET .../plan/{id}/pdf`
- Izdavanje: `GET /skladiste/izdaj`, `GET .../sifra/{sifra}?metoda=fifo|fefo`,
  `POST .../izdaj`, `POST .../izdaj/ponisti`, `GET .../izdaj/pdf`
- Pregled: `GET /skladiste/pregled` (paginated — legacy returned whole tables),
  `POST .../paleta/ispravak`
- Rokovi: `GET /skladiste/rokovi?dani=90` (+ pdf)
- Inventura: `POST .../inventura/start`, `GET .../inventura/aktivna`,
  `POST .../inventura/skeniraj`, `POST .../inventura/zatvori`, `POST .../inventura/ponisti`,
  `+ reconciliation actions` (otpis/usvoji — new, legacy lacked these)
- Prioriteti: `GET/POST /skladiste/prioriteti`, `PUT/DELETE .../{id}`
- Mapa: `GET /skladiste/mapa` (zone overview), `GET /skladiste/mapa/{zona}` (zone grid,
  HTMX partial) — loads only the requested zone, never all 1503 at once
- Naljepnice (later): `POST .../naljepnice`

## Mapa skladišta (UI) — DECIDED: per-zone drill-down, CSS grid

Chosen for reliability + UX (1503 positions is too many to show readably at once). No
Canvas/Plotly — plain Tailwind CSS-grid cells: themeable (respects dark mode, legacy 2D
didn't), clickable (legacy canvas had no click handler), no build step, always rendered
(legacy hid the map by default — bug B8).

Three levels:
1. **Pregled (`/skladiste/mapa`)** — 4 zone cards (A/B/C/D) with occupancy % + counts
   (e.g. `Zona A 612/975, 63%`), color-coded. Click a zone to drill in.
2. **Zona (`/skladiste/mapa/{zona}`)** — each rack of the zone drawn as a
   **pozicija × visina** CSS grid (A7 = 15×5, C1 = 30×4 …). Cell = one position. **V1 at
   the bottom** (ground level), pozicije left→right. Rows/cols laid out by **parsed ints**
   (not string order). Cell color by status: free / occupied / rok ≤30d / expired /
   search-highlight.
3. **Ćelija** — hover = pallet tooltip (šifra, lot, rok, kolicina); click = detail +
   actions (izdaj / ispravak / premjesti).

Data: `GET /skladiste/mapa/{zona}` returns occupancy for that zone's racks only (one query
filtered to active pallets in those positions). Search (by QR or šifra) highlights matching
cells within the relevant zone. 3D view is explicitly **dropped** (not worth the Plotly
cost; the 2D grid covers the need).

## Templates (`app/templates/skladiste/`)
`list.html`/dashboard, `_table_body.html`, `zaprimanje.html`, `izdaj.html`, `pregled.html`,
`inventura.html`, `prioriteti.html`, `mapa.html` (+ zone partial), partials per HTMX section
— following CLAUDE.md conventions (slate card headers, HTMX search/partials, Alpine for scan
UI). No `regali.html` (racks are a code constant).

## Dual-mode architecture (standalone now + ERP module later)
Build `skladiste` as a **self-contained package**:
- **Core** (palete, pozicije, placement algo, FIFO/FEFO, inventura, mapa) is ERP-agnostic and
  talks to legacy ERP only through one seam: **`ErpAdapter.lookup_barcode(code) -> article fields`**.
- Adapter implementations: **`LegacyErpAdapter`** (REST + Basic to legacy ERP), **`MockAdapter`** (local
  fake used for dev/tests now), later **`NasErpAdapter`** (reads our own ERP) if it takes off.
- Which adapter is active is a config switch — core code never changes.
- Same package runs **standalone** (own `main.py` + own SQLite) OR mounts as a **module** in
  this ERP via `include_router(...)`.

## ERP (legacy ERP) integration — IN SCOPE, built against a mock
The legacy ERP API will be ready **before go-live**, so we build the integration now and are ready
when it lands. The API doesn't exist yet as a fixed contract — IT implements **to our spec**
(below) and generates Swagger afterward. **Dev approach: build `LegacyErpAdapter` to the contract,
run everything against `MockAdapter` (a local stub returning the same shape), then point at
the real `https://erp.interno/...` URL when IT delivers and re-verify.** So nothing waits on IT and
the integration is already tested.

Transport: **REST + HTTP Basic auth**, both apps on the **local network**. **Read-only**
(standing "legacy ERP = samo čitanje" rule); write-back only on explicit approval.

**Hard requirements we impose (to avoid the legacy bugs at the source):**
- All dates in the response as **ISO 8601 `yyyy-mm-dd`** (no `dd.mm.yyyy` — kills FIFO bug B7).
- `kolicina` as a **JSON number**, not a string.

**Endpoint 1 — article lookup by barcode (primary, what receiving uses):**
```
GET /api/skladiste/artikl?barkod={barcode}      Authorization: Basic
200 -> { "sifra":"12345", "naziv":"Etiketa X 100x50", "jedinica":"kom",
         "kolicina":5000, "rok_trajanja":"2027-03-15", "lot":"L2026-0042",
         "datum":"2026-06-20" }                 # rok_trajanja/datum ISO; kolicina numeric
404 -> not found
```
**Endpoint 2 — lookup by šifra (resolve/validate):** `GET /api/skladiste/artikl/{sifra}` (same shape).
**Endpoint 3 — write-back (DEFERRED, needs approval):** `POST /api/skladiste/primka`,
`POST /api/skladiste/izdavanje` — only if the read-only rule is lifted.

**Our connection config** lives in `.env` (`ERP_API_URL`, `ERP_API_USER`, `ERP_API_PASS`,
and an `ERP_ADAPTER=mock|pauk` switch) — same pattern as `DATABASE_URL`, never hardcoded
(legacy hardcoded its ngrok token, B15). No `erp_config` table / admin UI needed (single legacy ERP
on LAN, field mapping is fixed by our contract).

## Build phases (suggested)
1. **Foundation** ✅ DONE: `REGALI` constant + position validator; models + Alembic migration
   (`da93a22079c1`, FK, indexes, partial-unique active position) for
   paleta/prijem/inventura/prioritet/event; module skeleton + dashboard (capacity from
   `REGALI`). No regali table/CRUD, no auth.
2. **ERP adapter seam** ✅ DONE: `ErpAdapter` + `MockAdapter` (deterministic fake legacy ERP) +
   `GET /skladiste/lookup` + `_artikl.html`. `LegacyErpAdapter` (httpx, REST+Basic) written to the
   contract, switched via `.env` (`ERP_ADAPTER=mock|pauk`, `ERP_API_URL/USER/PASS`).
3. **Core flow** ✅ DONE (`service.py` + routes + Zebra templates): zaprimanje (scan → lookup
   → `predlozi_mjesta` s klasteriranjem → potvrdi pozicije) → FIFO/FEFO izdaj → inventura
   (nedostaje/neočekivano). Sve na mocku. (Reconcile akcije otpis/usvoji + plan-based
   multi-pallet receive + bulk-issue rollback = kasnija dorada.)
4. **Prioriteti** + placement modes.
5. **Mapa** ✅ DONE — per-zone drill-down, Tailwind CSS-grid (`/skladiste/mapa` + `/mapa/{zona}`):
   ćelija = pozicija, boja po statusu, hover tooltip. No Canvas/Plotly, no 3D.
6. **Naljepnice** (QR/label PDF — reportlab; prints an internal label after receiving).
7. **Go-live wiring**: point `LegacyErpAdapter` at the real `https://erp.interno/...` once IT exposes the
   endpoints; verify against live data. (Only step that waits on IT — everything else is done.)

## Faza 4 — u tijeku (workflow prema stvarnom procesu)
Stvarni tok (potvrđeno s korisnikom): roba = **papiri** (jed. = arak), šifra = legacy ERP kod.
- **Zaprimanje (glavno, više paleta):** skener 1 QR → API/mock vrati **šifru** → skladištar
  upiše **broj paleta** → algoritam po **prioritetima** generira **listu pozicija** → skenira
  paletu po paletu (ili uzme svoju poziciju uz upozorenje). Single paleta = pod-opcija.
- **Izdavanje (glavno, po količini araka):** upiše šifru + **broj araka** → FIFO/FEFO
  (redoslijed iz **API datuma**, ne lokalnog) → alocira **cijele palete** dok ne pokrije; zadnja
  premaši → izda se cijela, **ostatak se vrati kao nova paleta** (zasebno zaprimanje, bez
  editiranja količine). Single paleta = pod-opcija.
- **Prioriteti → po ŠIFRI** (više vrsta/dobavljača istog formata): mod (standardno/puni
  rupe/lijevi/strogo lijevo) + dozvoljeni regali. GUI za uređivanje.
- **Mock = stvarni papiri** iz tablice stanja (`_mock_papiri.json`, 165 papira), s formatom.
- **PDF:** stanje skladišta s kartama + lista pozicija za zaprimanje (reportlab).

Status Faze 4: ✅ mock-papiri, ✅ algoritam (port: clustering→mod+dozvoljeni regali+uzastopne),
✅ Prioriteti GUI (CRUD, algoritam ga koristi), ✅ **Karta = tlocrt** (`/skladiste/mapa` pogled
odozgo: ulaz dolje-desno, A1 do ulaza, P1 uvijek desno, Zapad/Istok okomito sa strane →
`/skladiste/mapa/{zona}` grid po visinama), ✅ **multi-paletno zaprimanje** (plan, dvostruko
skeniranje paleta→pozicija, vrati/otkaži), ✅ **izdavanje po količini** (FIFO/FEFO + ostatak),
✅ single zaprimanje/izdavanje (pod-opcije), ✅ **PDF ispisi** — sve gotovo osim go-live.

### PDF ispisi (`pdf.py`, reportlab + Arial TTF)
- `pdf_stanje(db)` → `GET /skladiste/stanje/pdf` — **stanje skladišta kao tlocrt** (ista
  orijentacija kao web karta), sažetak po zonama + legenda. Gumb "🖨 Ispiši (PDF)" na karti.
- `pdf_plan(db, pid)` → `GET /skladiste/zaprimanje/plan/{pid}/pdf` — **lista pozicija za
  zaprimanje** (Rb/pozicija/status/barkod + uputa + potpis). Gumb na stranici plana.
- Font: Arial TTF (`C:/Windows/Fonts/arial*.ttf`) registriran kao `F/FB` zbog hrvatskih znakova
  (fallback Helvetica). Isti pristup kao `reklamacije/utils.py`. Bez ✓/☐ glyphova (Arial ih nema).

## Dependencies / open questions
- **Auth:** DECIDED — no login and no user tracking in v1 (no `korisnik` anywhere). Comes
  later via ERP-wide auth. Admin-gating is moot (racks aren't editable; prioriteti stays open).
- **Šifra ↔ Materijal:** DECIDED — **no link in v1** (data comes from legacy ERP, not our catalog).
  May connect `paleta.sifra` ↔ `materijal` later if useful.
- **Map fidelity:** DECIDED — per-zone drill-down, Tailwind CSS-grid, no Canvas/Plotly,
  no 3D (see "Mapa skladišta (UI)").
- **Barcode source:** DECIDED — receiving scans the product barcode → legacy ERP lookup
  (`LegacyErpAdapter`, REST + Basic, read-only, ISO dates); built against `MockAdapter` until IT
  delivers. Manual entry is the fallback for unknown barcodes.
- **Deployment topology:** DECIDED — warehouse app runs on the **local server (LAN)**, same
  network as legacy ERP; it calls `https://erp.interno/...` over LAN with Basic auth (no public exposure).
