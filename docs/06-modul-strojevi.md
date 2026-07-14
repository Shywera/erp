# Module: Strojevi (Machines / cost centers)

Registry of production machines and cost centers. Referenced by Normativi (machine
speeds for throughput calc) and by Materijali (`mjesto_troska_1..9` keys off
`stroj.sifra`). Future: Radni nalozi (work orders) schedule onto machines, Održavanje
(maintenance) keys off them.

Status: **implemented**. Has a `seed.py` for initial machine list
(`python -m app.modules.strojevi.seed`).

## Table

### `stroj` — machine / cost center
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| sifra | varchar, unique, indexed | cost-center / machine code |
| naziv | varchar | |
| tip | varchar, nullable | tisak \| rezanje \| stancanje \| priprema \| ljepljenje \| ostalo |
| aktivno | bool, default true | |
| max_format_x_mm / max_format_y_mm | float, nullable | max sheet format |
| min_format_x_mm / min_format_y_mm | float, nullable | min sheet format |
| broj_boja | int, nullable | print units (tisak machines) |
| ima_lak | bool, default false | has varnish unit |
| ima_uv | bool, default false | has UV |
| brzina_metal_arh | int, nullable | speed metallic paper (sheets/h) |
| brzina_bijeli_arh | int, nullable | speed white paper (sheets/h) |
| brzina_arh | int, nullable | generic speed (sheets/h) for non-print machines |
| broj_osoba | int, nullable | operators required |
| napomena | text, nullable | |
| created_at / updated_at | datetime | |

## Routes (`/strojevi`)
- `GET /strojevi` — list
- `GET /strojevi/search?q=` — HTMX `_table_body` partial
- `GET /strojevi/novi` — new form
- `GET /strojevi/{id}` — detail/edit
- `POST /strojevi/novi`, `POST /strojevi/{id}` — create / update
- `POST /strojevi/{id}/obrisi` — delete (form, 303)
- `DELETE /strojevi/{id}` — delete (HTMX inline)

## Notes / decisions
- `sifra` is `unique`. Create/update catch `IntegrityError` and re-render the form with
  an error banner at HTTP 409 (instead of crashing) — fixed during module test pass.
- Speeds mirror the legacy `normativ_calc.py` constants (e.g. CD 102 metal/white =
  9000/10000, CX 104 = 9500/11000 sheets/h). These are *reference* values on the machine
  record; the actual throughput math lives in the Normativi calculator's `params.json`
  (see [07-modul-normativi](07-modul-normativi.md)).
