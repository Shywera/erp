# Module: Tehnološki postupci (Normativ — product production spec)

Full production specification per product, mirroring legacy ERP's `Product/Edit` page: header +
colors + materials + operations + cost totals. This is the "complete normativ card",
distinct from the Normativi *calculators* (see [07-modul-normativi](07-modul-normativi.md)).

Status: **U IZRADI / work-in-progress.** A permanent, non-dismissable sticky banner
("Modul u izradi — nije dovršen") is shown on the list and detail pages
(`_wip_banner.html`). Functional but several items still missing; not to be relied on for
real data yet. The 4 known bugs from the test pass are fixed (autocomplete `{TARGET}`
literal, empty sections on full page load, list-delete HTMX/redirect mismatch, auto
`et_po_arku = stupaca × redova`).

## Tables (4)

### `normativ` — header
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| naziv | varchar, indexed | |
| sifra | varchar, nullable | |
| kupac | varchar, nullable | customer |
| serija | int, nullable | nominal run, e.g. 10000 |
| koeficijent | int, nullable | e.g. 1000 = per-thousand basis |
| arka_x / arka_y | float, nullable | sheet format mm |
| podloga | varchar, nullable | substrate / paper name |
| gramatura | int, nullable | g/m² |
| stupaca / redova | int, nullable | label grid columns / rows |
| et_po_arku | int, nullable | auto = stupaca × redova (explicit value honored) |
| et_xn / et_yn | float, nullable | label netto width / height mm |
| et_xb / et_yb | float, nullable | label brutto width / height mm |
| napust | int, nullable | bleed mm |
| ukupno_araka | int, nullable | total sheets |
| broj_boja | int, nullable | colors |
| napomena | text, nullable | |
| created_at / updated_at | datetime | |

Relationships (all cascade delete-orphan, ordered by `redoslijed`):
`boje` → NormativBoja, `materijali` → NormativMaterijal, `operacije` → NormativOperacija.

### `normativ_boja` — colors / print passes
`id`, `normativ_id` (FK), `redoslijed`, `naziv_boje`, `pantone_naziv` (nullable),
`kolicina_kg_1000` (float, kg per 1000 sheets).

### `normativ_materijal` — materials cost lines
`id`, `normativ_id` (FK), `redoslijed`, `materijal_id` (**soft link**, nullable int, no FK
constraint), `naziv`, `sifra`, `kolicina`, `jedinica`, `cijena_eur` (per unit),
`ukupno_eur` (kolicina × cijena). Material is picked via autocomplete from the Materijali
table (`/tehnoloski-postupci/materijal-search?q=`), or typed manually.

### `normativ_operacija` — operations / labor lines
`id`, `normativ_id` (FK), `redoslijed`, `naziv_operacije`, `stroj_naziv`, `stroj_alias`,
`kolicina`, `norma_min` (**minutes, int**), `eur_h` (per hour), `ukupno_eur`
(= eur_h × norma_min/60). `norma_min` is stored as integer minutes; UI shows/parses
`hh:mm` via Jinja filters.

## Routes (`/tehnoloski-postupci`)
- `GET /` list, `GET /search?q=`, `GET /novi`, `GET /{id}` detail
- `POST /novi`, `POST /{id}/header` — create / update header
- `POST /{id}/obrisi` — delete normativ (HTMX → `HX-Redirect`; non-HTMX → 303)
- `POST /{id}/boje/dodaj`, `POST /{id}/boje/{boja_id}/obrisi`
- `POST /{id}/materijal/dodaj`, `POST /{id}/materijal/{mat_id}/obrisi`
- `POST /{id}/operacije/dodaj`, `POST /{id}/operacije/{op_id}/obrisi`
- `GET /materijal-search?q=` — autocomplete from Materijal table

Each sub-section (`#boje-sekcija`, `#mat-sekcija`, `#op-sekcija`) is an HTMX
`outerHTML`-swap target re-rendered on add/delete.

## Cost summary (`zbroj`)
`mat_total` = Σ material `ukupno_eur`; `op_total` = Σ `eur_h × norma_min/60`;
`grand` = mat_total + op_total; `per_1000` = grand / (serija × koeficijent / 1000) when
serija+koef set.

## Notes / decisions
- `materijal_id` is a **soft link** (no FK) to avoid SQLite batch-alter complexity; the
  name/sifra are copied onto the line so it survives material edits/deletes.
- Still missing / to refine: parity with full legacy ERP Product/Edit (packaging, dorada,
  storage fields), validation, and wiring the totals back into pricing.
