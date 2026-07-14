# Module: Pantoni (Pantone color reference)

Small CRUD registry of Pantone colors. Referenced by Materijali (a material's `pantone_id`
points here) and conceptually by Normativ colors (`pantone_naziv`). Reuses the `Pantone`
model that lives in the Materijali module (`app/modules/materijali/models.py`).

Status: **implemented**. Two fixes during the consolidation pass:
- Duplicate `kod` crashed with a 500 (IntegrityError) → now caught, rolled back, redirects.
- Router was **not registered** in `main.py` (so `/pantoni` 404'd) → now registered and
  added to the sidebar under "Matični podaci".

## Table

### `pantone` (defined in materijali/models.py)
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| kod | varchar(30), unique, indexed | Pantone code, e.g. "185 C" |
| naziv | varchar(100), nullable | display name |
| hex_boja | varchar(7), nullable | "#rrggbb" (from `<input type="color">`, default #ffffff) |

## Routes (`/pantoni`)
- `GET /pantoni` — list + add form
- `POST /pantoni` — create (duplicate `kod` is rolled back silently and redirects)
- `POST /pantoni/{pantone_id}/obrisi` — delete

## Notes / decisions
- Not an autocomplete endpoint — it's a full list/create/delete page. Materijali links to
  Pantone via the `pantone_id` hidden field on the material form.
- Duplicate-`kod` is currently silent (no flash message) — safe but gives no feedback;
  a user-facing message would need a messaging mechanism this module doesn't have yet.
