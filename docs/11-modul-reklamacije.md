# Module: Reklamacije (Complaints / nonconformities — QMS)

Quality management: customer complaints, internal nonconformities, and supplier
nonconformities, each with CAPA (corrective/preventive) measures. Ported from a standalone
Django project (`Arhiva skripta/Reklamacije`). Includes PDF (reportlab) and Excel
(openpyxl) export.

Status: **implemented**, clean in the test pass (PDF + Excel verified). Auto case number
`RK-YYYY-NNNN`.

## Tables (2)

### `reklamacija` — case
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| broj_predmeta | varchar, unique, indexed | auto `RK-2026-0001` |
| vrsta | varchar, indexed | INTERNA \| KUPAC \| DOBAVLJAC |
| status | varchar, indexed | NOVO \| U_OBRADI \| CEKA \| RIJESENO \| ZATVORENO |
| prioritet | varchar, indexed | NIZAK \| SREDNJI \| VISOK \| KRITICAN |
| kategorija | varchar, nullable | MANJA \| VECA |
| naslov | varchar | |
| opis | text | |
| prijavitelj | varchar | |
| kupac_dobavljac | varchar, nullable | |
| referentni_broj / naziv_proizvoda / broj_radnog_naloga / stroj / osoblje | varchar, nullable | links to order/product/machine (free text for now) |
| datum_prijave / datum_azuriranja | datetime | |
| datum_zatvaranja | datetime, nullable | auto-set when status → RIJESENO/ZATVORENO |
| rok_rjesavanja | date, nullable | due date |
| korekcija | text, nullable | immediate correction |
| analiza_uzroka | text, nullable | root cause (5-Why) |
| uzrok_kategorija | varchar, nullable | |
| napomena | text, nullable | |
| vezana_nesukladnost / promjene_sustava / broj_promjene | varchar, nullable | |

Enums + Croatian labels are class dicts (`VRSTA`/`STATUS`/`PRIORITET`/`KATEGORIJA`) with
`*_display` properties. Computed properties: `je_zatvorena`, `rok_prekoracen`,
`broj_capa`, `broj_otvorenih_capa`. `capa` relationship (cascade delete-orphan, ordered by
`rok_izvrsenja`).

### `capa` — corrective / preventive measure
`id`, `reklamacija_id` (FK, indexed), `vrsta` (KOREKTIVNA \| PREVENTIVNA), `opis_mjere`,
`odgovorna_osoba`, `rok_izvrsenja` (date), `status` (PLANIRANA \| U_TIJEKU \| IZVRSENA \|
ODGODENA), `datum_izvrsenja`, `rezultat`, `provjerio`, `datum_provjere`.
`je_prekoracen` property = past due and not IZVRSENA.

## Routes (`/reklamacije`)
- `GET /reklamacije` — dashboard (KPIs)
- `GET /reklamacije/lista` — list
- `GET /reklamacije/search?status=&vrsta=&prioritet=&q=&page=` — filtered partial
- `GET /reklamacije/nova`, `POST` create, `POST /reklamacije/{id}` edit, `POST /reklamacije/{id}/obrisi`
- CAPA (inline HTMX): `POST /reklamacije/{id}/capa/dodaj`,
  `POST /reklamacije/{id}/capa/{capa_id}/status`, `POST /reklamacije/{id}/capa/{capa_id}/obrisi`
- `GET /reklamacije/{id}/pdf` — single-case PDF (reportlab; Croatian chars + XML-escaped)
- `GET /reklamacije/excel/izvoz` — Excel export (openpyxl), honors list filters

## Notes / decisions
- PDF/Excel generation lives in `utils.py`. Croatian/XML escaping is handled (`_x()` helper)
  so special chars in naslov/opis don't break the PDF.
- Cross-links (kupac/dobavljač, radni nalog, stroj, proizvod) are free text for now; will
  become real FKs to Kontakt / Radni nalozi / Strojevi / Materijali as those mature.
