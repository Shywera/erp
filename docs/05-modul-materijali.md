# Module: Materijali (Materials / Articles master data)

First module to build. Foundation for everything else — Strojevi (machines) and
Normativi (throughput norms) both reference materials (paper/foil type, label format,
gramature), and Skladište/WMS, Radni nalozi, Nabava etc. all key off `materijal.sifra`.

## Scope decisions

- Covers **all article types** in one core table (`materijal`): raw paper/foil, inks,
  packaging (boxes/pallets), and finished label products — matching how legacy ERP's
  `Product/Index/1` already lists everything together under Kategorija/Tip/Grupa/Podgrupa.
- Type-specific physical attributes (paper properties, label format) live in optional
  **1:1 extension tables**, not bolted onto the core table as nullable columns. Keeps
  the core table clean; a "boja" (ink) or "ambalaža" (packaging) row simply has no
  `materijal_papir` / `materijal_etiketa` row.
- Classification (Kategorija/Tip/Grupa/Podgrupa) stored as **plain strings** for v1,
  copied verbatim from legacy ERP once we get export/API access. Can be normalized into
  lookup tables later via migration if filtering/reporting needs it — not worth
  designing now without real data.
- **Price history** is its own table (`cijena_povijest`), matching the "Update cjenika
  boja" pattern (Šifra, Partner/Dobavljač, Datum važenja, J.c. DAP) — every price change
  is a new row, never an overwrite.

## Tables

### `materijal` — core article master
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| sifra | varchar, unique | legacy ERP "Šifra" |
| sipo_sifra | varchar, nullable | legacy ERP "Sipo šifra" |
| naziv | varchar | |
| jedinica | varchar | kg, arak, kom, m, rola... |
| kategorija | varchar | legacy ERP classification (free text, v1) |
| tip | varchar | |
| grupa | varchar | |
| podgrupa | varchar | legacy ERP "Podgrupa 1" |
| podgrupa2 | varchar, nullable | legacy ERP "Podgrupa 2" |
| podgrupa3 | varchar, nullable | legacy ERP "Podgrupa 3" |
| podgrupa4 | varchar, nullable | legacy ERP "Podgrupa 4" (almost never populated) |
| aktivno | bool, default true | |
| minimalna_kolicina | numeric, nullable | reorder threshold |
| minimalno_pakiranje | numeric, nullable | legacy ERP "Minimalno pakiranje" |
| dobavljac_id | int, nullable (soft link -> kontakt.id) | default/primary supplier; set via the Kontakt autocomplete on the material form (kontakt module is now implemented — see [09-modul-kontakt](09-modul-kontakt.md)) |
| dobavljac_naziv | varchar, nullable | supplier name copied alongside `dobavljac_id` so it survives contact edits; originally from the legacy ERP "Dobavljač" free-text import |
| tarifni_broj | varchar, nullable | legacy ERP "Tarifni broj" |
| zemlja_porijekla | varchar, nullable | legacy ERP "Zemlja porijekla" |
| rok_trajanja | varchar, nullable | legacy ERP "rok trajanja" (dobavljač/tvrtka) |
| rok_trajanja_godina | numeric, nullable | legacy ERP "rok trajanja godina" |
| rok_dobavljivosti | int, nullable | legacy ERP "ROK DOBAVLJIVOSTI" (days) |
| lokacija_skladiste | varchar, nullable | legacy ERP "Lokacija u skladištu" — placeholder, populated by WMS modul |
| pozicija | varchar, nullable | legacy ERP "Pozicija" — placeholder, populated by WMS modul |
| ulazno_skladiste_1, ulazno_skladiste_2 | varchar, nullable | legacy ERP "ULAZNO SKLADIŠTE 1/2" |
| prijelazno_skladiste_1..3 | varchar, nullable | legacy ERP "PRIJELAZNO SKLADIŠTE 1-3" |
| mjesto_troska_1..9 | varchar, nullable | legacy ERP "Mjesto troška 1-9" — machine cost centers, populated/used by Strojevi modul |
| datoteke | text, nullable | legacy ERP "Datoteke" — raw attachment metadata, unparsed |
| napomena | text, nullable | |
| promjer_mm, debljina_um, duljina_mm, sirina_mm, visina_mm | numeric, nullable | legacy ERP "Radius/Thickness/Length/Width/Height" — dimenzije |
| povrsina_mm2, volumen_mm3 | numeric, nullable | legacy ERP "Surface/Volumen" |
| gramatura_g_m2 | numeric, nullable | legacy ERP "ConvU1U2" |
| kvaliteta | varchar, nullable | legacy ERP "Quality" |
| kutija_na_paleti_z | numeric, nullable | legacy ERP "BoxesOnPaletteZ" |
| tezina_kg | numeric, nullable | legacy ERP "Weight" |
| hilzna | varchar, nullable | legacy ERP "Variant" |
| litraza | numeric, nullable | legacy ERP "Liter" |
| tehnicki_naziv | varchar, nullable | legacy ERP "Other" (Tehnički naziv robe) |
| raspored | varchar, nullable | legacy ERP "Description" (Raspored) |
| opis_en | text, nullable | legacy ERP "DescriptionEng" |
| posebna_napomena | text, nullable | legacy ERP "Remark" |
| napomena_dorada | text, nullable | legacy ERP "DoradaRemark" |
| oznaka | varchar, nullable | legacy ERP "Signature" |
| tehnika, tip_dorade, komplet, nacrt, sistem, namotaj, podloga, bazni_papir, materijal_tisak | varchar, nullable | legacy ERP "Technique/DoradaType/Complet/Drawing/System/Namotaj/SubSurface/BasePaper/Material" |
| boja | varchar, nullable | legacy ERP "Color" (free text) |
| pantone_id | FK -> pantone.id, nullable | legacy ERP "PantoneId" — see [[#pantone — pantone color lookup]] |
| coated, folija | bool, nullable | legacy ERP "Coated"/"Foil" |
| lugootporno, prehrana, jednokomp_dvokomp, svjetlostabilnost | varchar, nullable | legacy ERP "Lugootporno/Food/OneComponentTwoComponent/LightStability" |
| certifikati | varchar, nullable | legacy ERP "Certificates" |
| inventarni_broj, ura, proizvodni_broj, kljucni_broj_otpada | varchar, nullable | legacy ERP "InventoryNumber/Ura/ProductionNumber/JunkKeyNumber" |
| qr_nije_potreban | bool, default false | legacy ERP "QrNotNeeded" (Izdavanje bez QR koda) |
| zabranjeno_medjuskladiste | bool, default false | legacy ERP "IsMsExcluded" (Zabranjeno na međuskladištu) |
| created_at, updated_at | timestamp | |
| updated_by | varchar, nullable | from legacy ERP "Zadnje izmijenio" during migration |

### `pantone` — Pantone color lookup
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| kod | varchar, unique | Pantone code, e.g. "185 C" |
| naziv | varchar, nullable | optional name |
| hex_boja | varchar(7), nullable | hex color for swatch display, e.g. "#E4002B" |

Managed via `/pantoni` (simple list + add + delete). `materijal.pantone_id` references
this table; the materijal detail form shows a dropdown with a live color swatch
(Alpine.js). Intended to be referenced later by the Normativi modul (spot-color setup
on press).

### `materijal_papir` — paper/foil extension (1:1, optional)
| Field | Type | Notes |
|---|---|---|
| materijal_id | FK -> materijal.id, PK | |
| tip_papira | varchar | metalizirani / bijeli_pregani / bijeli_glatki / karton / folija / ostalo |
| gramatura_g_m2 | numeric | g/m² |
| sirina_mm | numeric | roll/sheet width |
| duljina_role_m | numeric, nullable | for rolls |
| format_arka_x_mm | numeric, nullable | for sheet-fed stock |
| format_arka_y_mm | numeric, nullable | |

### `materijal_etiketa` — finished label product extension (1:1, optional)
| Field | Type | Notes |
|---|---|---|
| materijal_id | FK -> materijal.id, PK | |
| kupac_id | FK -> kontakt.id, nullable | customer this label is made for |
| papir_materijal_id | FK -> materijal.id, nullable | which paper/foil stock it's printed on |
| format_netto_x_mm, format_netto_y_mm | numeric | label size, net |
| format_brutto_x_mm, format_brutto_y_mm | numeric | label size, gross (incl. bleed) |
| etiketa_u_kutiji | int, nullable | labels per box |
| kutija_tip | varchar, nullable | |
| paleta_tip | varchar, nullable | |
| kutija_na_paleti | int, nullable | boxes per pallet |

### `cijena_povijest` — price history
| Field | Type | Notes |
|---|---|---|
| id | int, PK | |
| materijal_id | FK -> materijal.id | |
| dobavljac_id | FK -> kontakt.id, nullable | |
| cijena | numeric(10,4) | matches cjenik updater's 4-decimal rounding |
| valuta | varchar(3), default 'EUR' | |
| datum_vazenja | date | "Datum važenja" |
| napomena | text, nullable | |

Current price for a material = row with latest `datum_vazenja` per `(materijal_id,
dobavljac_id)`.

## legacy ERP import (2026-06-15)

`app/modules/materijali/import_pauk.py` reads a legacy ERP "Product/Index/1" export
(`Resources/Materijali(1).xlsx`, Sheet1) and upserts `materijal` (by `sifra`) plus
`cijena_povijest` (one row per material with both a price and a price date).
**All 41 columns** of the export are imported into `materijal` (including
warehouse-location and machine-cost-center placeholders — see table above).

Run: `python -m app.modules.materijali.import_pauk Resources/Materijali(1).xlsx`

Imported 3108 materials and 2467 price history rows on first run; re-run is a
safe upsert by `sifra` (no duplicate price rows for identical date+amount).

**Not imported**:
- Sipo šifra (0/3108 populated in the export, but field exists in the model)
- `materijal_papir` / `materijal_etiketa` extension tables — legacy ERP export has no clean
  per-row structured fields for paper dimensions/gramature or label format; dimensions
  appear as free text inside `Naziv` (e.g. "700mm 1000mm"). Populating these tables
  needs separate per-row parsing, deferred.

## UI (2026-06-15)

- `/materijali` — search/browse table showing a curated subset of columns
  (sifra, naziv, jedinica, kategorija, tip, grupa, podgrupa, min. količina, aktivno).
  Clicking a row's šifra/naziv opens the detail page.
- `/materijali/{id}` — full detail page showing **every** field from the table above,
  grouped into sections (Osnovni podaci, Klasifikacija, Količine i nabava, Skladište,
  Mjesta troška, Napomena/privici), plus read-only Povijest cijena and metadata. Submits
  via POST to update; "Obriši materijal" deletes and returns to the list.
- `/materijali/novi` — same template with an empty form; POST creates and redirects
  to the new record's detail page.
- Old inline-row add/edit UI (`_row_edit.html`, `_row_new.html`, etc.) was removed in
  favor of this detail page.
- `/pantoni` — simple Pantone code list (kod, naziv, hex color swatch), add/delete.

## legacy ERP edit-form field expansion (2026-06-15, follow-up)

Added ~31 more fields to `materijal` (dimensions/technical, descriptions,
production/print, ink/color incl. `pantone_id`, misc identifiers, two checkboxes) plus
the new `pantone` lookup table — covering most of the fields found on legacy ERP's
`/Product/Edit/{id}` form (see `docs/03-pauk-erp-reference.md`). Migration
`90c84fcbe81a`. Detail page extended with "Dimenzije i tehnicka svojstva",
"Proizvodnja, tisak i boja" (incl. Pantone picker with color swatch via Alpine.js),
"Dodatni opisi" and "Ostalo" sections.

**Still not modeled** (need other modules first): entity-linked dropdowns
BuyerId/SupplierId/ProducerId/OriginCountryId/ContoId/KpdId/ColorId (need `kontakt`,
`zemlja`, `konto` lookups) and the repeatable lists ProductCategoryIds,
AllowedProducts, AllowedOperationIds, AllowedTransferIds, AllowedInputIds (need
Kategorije/Strojevi/Skladišta modules — these look like the structured source behind
our flat `mjesto_troska_1..9` / `*_skladiste_*` strings).

## Open for later
- `kontakt` (Kupci/Dobavljači) is referenced here (dobavljac_id, kupac_id) but is a
  separate module — needs to exist before `materijal` FKs can be enforced, or these FKs
  are added in a later migration once `kontakt` lands.
- Once legacy ERP data access is available, confirm actual Kategorija/Tip/Grupa/Podgrupa
  values to decide if/when to normalize into lookup tables.
- `materijal_papir.tip_papira` values (metalizirani/bijeli_pregani/bijeli_glatki/...)
  taken from Montaža Etiketa's 32 paper formats (3 groups) — confirm full list when
  building Normativi module.
