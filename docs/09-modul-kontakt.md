# Module: Kontakt (Kupci / Dobavljači — partners + addresses)

Unified contact registry covering legacy ERP's two sub-tabs under "Kupci/Dobavljači":
**Partneri** (the contacts) and **Adresar** (business units / addresses per partner).
Replaces the free-text `dobavljac_naziv` on Materijali — materials now pick a supplier via
autocomplete that keys off this table (`dobavljac_id`).

Status: **implemented**. ~1287 partners + 100 addresses imported from legacy ERP Excel exports.
Autocomplete HTML/JS injection bug (unescaped partner names breaking the `onclick`) fixed
during the test pass via a JS-safe escaping helper.

## Tables (2)

### `kontakt` — partner
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| sifra | varchar, unique, indexed | legacy ERP "Šifra"; auto `K0001…` if blank on create |
| naziv | varchar, indexed | legacy ERP "Naziv" |
| interni_naziv | varchar, nullable | legacy ERP "Interni naziv" |
| naziv_dodatni | varchar, nullable | legacy ERP col N "Naziv" (alt name) |
| tip | varchar, indexed | dobavljac \| kupac \| oba \| ostalo (from legacy ERP "Tip kupca": Supplier/Buyer/BuyerSupplier) |
| grupa | varchar, nullable | legacy ERP "Grupa" |
| oib | varchar, nullable | |
| maticni_broj | varchar, nullable | |
| adresa / postanski_broj / mjesto / drzava | varchar | drzava default "Hrvatska" |
| telefon / mobitel / email / web / referent | varchar, nullable | |
| valuta_placanja_dan | int, nullable | payment terms (days) |
| radno_vrijeme | varchar, nullable | |
| hbor_osiguranje | bool, default false | legacy ERP "HBOR osiguranje" |
| hbor_rok_placanja_dan | int, nullable | legacy ERP "HBOR ugovoreni rok plaćanja [dan]" |
| napomena | text, nullable | |
| aktivan | bool, default true | |
| created_at / updated_at | datetime | |

`tip_display` property maps the code to a Croatian label. `adrese` relationship →
Adresar (cascade delete-orphan, ordered by `naziv_pj`).

### `adresar` — business unit / address (legacy ERP "Adresar")
`id`, `kontakt_id` (FK, nullable, indexed), `partner_naziv` (raw legacy ERP name, for matching
on import), `naziv_pj` (business-unit name), `drzava`, `zupanija`, `opcina`, `grad`,
`adresa` (text), `kilometri` (float), `created_at`/`updated_at`. Multiple per partner.

## Routes (`/kupci`)
- `GET /kupci` — list (tip filter chips + HTMX search)
- `GET /kupci/search?q=&tip=` — `_table_body` partial
- `GET /kupci/autocomplete?q=&tip=` — dropdown HTML used by **Materijali** (and other
  modules) to pick a supplier; `tip` filter includes `oba`. Output is JS-escaped.
- `GET /kupci/novi`, `GET /kupci/{id}`, `POST /kupci/novi`, `POST /kupci/{id}`, `POST /kupci/{id}/obrisi`
- Adresar (inline HTMX on `#adresar-sekcija`):
  `POST /kupci/{id}/adresar/dodaj`, `POST /kupci/{id}/adresar/{adresa_id}/obrisi`

## Import (`python -m app.modules.kontakt.import_pauk "Resources/Kontakti(1).xlsx" "Resources/Adresar.xlsx"`)
- Reads xlsx **directly from the zip / raw OOXML** because the current openpyxl version
  crashes on these legacy ERP exports' stylesheet.
- Kontakti: upsert by `sifra`; maps Tip kupca → tip; parses HBOR fields.
- Adresar: full re-import (clears table first); links `Adresar.Partner` → `Kontakt.naziv`
  (case-insensitive, also matches `naziv_dodatni`), stores `partner_naziv` regardless.

## Notes / decisions
- `materijal_id`-style soft link the other way: Materijali store `dobavljac_id` +
  `dobavljac_naziv`; the name is copied so it survives even if the contact changes.
- `tip` is not validated against the allowed set on save (lenient); a bad value renders an
  empty badge rather than erroring. Could add validation if strictness is wanted.
