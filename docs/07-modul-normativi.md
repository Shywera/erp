# Module: Normativi (Throughput calculators)

Two **calculators** plus their parameter/data stores. This module is calculation-only —
**it has no database tables**. All inputs come from the form, machine parameters live in
a JSON file, paper formats live in another JSON file. Calculation logic is in
`calc.py` (kalkulator) and `montaza_calc.py` (montaža), ported from the legacy
`Arhiva skripta/Normativi/0.2/normativ_calc.py`.

Status: **implemented**. Calc bugs found in the test pass are fixed (montaža route name
shadowing that broke all montaža calcs; several division-by-zero guards).

## What is connected to what (important)

| Page | Uses | Data source |
|---|---|---|
| **Kalkulator** (`/normativi/kalkulator`) | `calc_layout`, `calc_strip_cut`, `calc_sc20`, `calc_mcs115`, `calc_stancanje`, `calc_tisak` | machine **params** (`params.json` via `ucitaj_params`/`spremi_params`) |
| **Parametri strojeva** (`/normativi/parametri`) | edits the machine params used by the Kalkulator | `params.json` |
| **Montaža etiketa** (`/normativi/montaza`) | `izracunaj`, `compute_ocjene`, `draw_montaza`, `export_montaza_pdf` | **baza papira** (paper-format list, `ucitaj_papire`/`spremi_papire`) |

- **Parametri strojeva feeds the Kalkulator, NOT montaža.** It is reachable as a side
  button on the Kalkulator page (`⚙ Parametri strojeva`) and is intentionally *not* a
  separate sidebar item.
- **Montaža is self-contained** — it has its own "Baza papira" sub-section
  (`/normativi/montaza/papiri`) and never touches machine params.

## Kalkulator
Computes per-machine throughput (sheets/h and labels/h), cutting/die-cutting/print times
for a given product (sheet format, label format, gramature, paper type, run size, colors).

- `GET /normativi/kalkulator` — full page (renders with `DEFAULTS`)
- `POST /normativi/kalkulator/izracunaj` — HTMX `_rezultati.html` partial (recalc on change)
- `_calc(p)` builds the result: layout + POLAR 137 strip cut + SC20 + MCS 115 +
  štancanje (POLAR DC 11, BLUMER 1110 DUAL, BLUMER 110) + tisak (CX 104, CX 102, CD 102).
- If `et_na_arku == 0` returns a friendly "label doesn't fit" error instead of dividing.

### Machine parameters (`params.json`)
Grouped (`_PARAM_GROUPS`) into Rezanje / Štancanje / Tisak. Each machine key (e.g.
`CX_104`, `POLAR_137`, `SC20_STRIP`) maps to a dict of times/speeds defined in
`DEFAULT_PARAMS`. ~60 labelled fields (`_LABELS`) — prep times, cut times, paper-pallet
counts, machine speeds (`brzina_metal`, `brzina_bijeli`), etc.

- `GET /normativi/parametri` — edit page (collapsible per machine, "Izmijenjeno" badge)
- `POST /normativi/parametri/{key}/spremi` — save one machine's params
- `POST /normativi/parametri/{key}/reset` — reset one machine to defaults
- `POST /normativi/parametri/reset-sve` — reset all

## Montaža etiketa
Label layout optimizer for label "kompleti" (sets of 1–3 different labels A/B/C). For
each candidate paper format it computes how many complete sets fit, scores them
(`compute_ocjene`, weighted by `k_ocjena`), and renders/exports the best layouts.

- `GET /normativi/montaza` — page (left: inputs, right: results + paper base)
- `POST /normativi/montaza/izracunaj` — HTMX `_montaza_rezultati.html` partial
- `POST /normativi/montaza/chart` — base64 PNG layout preview (matplotlib)
- `POST /normativi/montaza/pdf` — PDF export of a chosen layout (reportlab)

### Baza papira (paper formats)
- `GET /normativi/montaza/papiri` — `_papiri.html` partial (grouped by paper type)
- `POST /normativi/montaza/papiri/dodaj` — add `{naziv, v, s, tip}`
- `POST /normativi/montaza/papiri/{idx}/uredi` — edit
- `POST /normativi/montaza/papiri/{idx}/obrisi` — delete
- `POST /normativi/montaza/papiri/reset` — restore `DEFAULT_PAPIRI`

## Notes / decisions
- No DB tables on purpose: params and paper formats are small config-like data, stored as
  JSON next to the module. Could move to DB later if multi-user editing needs locking.
- `_PARAMS` is loaded once at import and updated in-place on save (single-process dev).
  For multi-worker production this needs reloading per-request or moving to DB.
