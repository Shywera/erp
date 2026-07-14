# Legacy Tools Catalog

Inventory of standalone automation built over time at
`C:\Users\Tehnolog\Desktop\Arhiva skripta`. These encode years of domain logic and are
the main reference for what the new ERP/MES/WMS needs to cover. Source files were left
in place (not moved) — re-read them before reusing logic, this is a point-in-time
snapshot (2026-06-15).

## Quick map: legacy tool -> future module

| Legacy tool | Path | Maps to | Maturity |
|---|---|---|---|
| Skladište 3.1 | `Skladište/3.1` | **WMS core** | FastAPI+SQLite+web, QR pallets, ~2000 rack positions, FIFO/FEFO — most mature prototype |
| Reklamacije 1.0 | `Reklamacije 1.0` | **Quality/CAPA** | Full Django app — largely production-ready |
| Tjedna usklada | `Tjedna usklada/0.1.3` | WMS - reorder alerts | Script -> PDF |
| Utrošak vs stanje | `Utrošak vs stanje` (v3.1.4) | WMS/reporting | Script -> Excel, compiled .exe |
| Xgboost utrošak predikcije | `Xgboost utrošak predikcije` | MES/planning - forecasting | Script |
| Normativi | `Normativi` | MES - throughput norms | Excel workbook |
| Montaža Etiketa (Kompleti) | `Kompleti/0.2.1...` | MES/planning - layout optimizer | Streamlit |
| Cola (BARGEN) | `Cola` | Shipping/logistics | Script (tkinter+reportlab) |
| Calz (GENXML/BARGEN) | `Calz/0.3.1` | Shipping/logistics (EDI) | Script (customtkinter) |
| folije | `folije` | Inventory calc | Script/VBA |
| Certifikati i teh spec | `Certifikati i teh spec` | Quality - cert/spec docs | Prototype, mock API |
| Usklada metal | `Usklada metal` | WMS/Procurement | Script |
| Update cjenika boja | `Update cjenika boja` | Procurement - price lists | Script + .exe |

---

## Skladište (WMS core) — most mature

**Path:** `Skladište/3.1` (also 2.0, 3.0 — superseded)

FastAPI + Uvicorn + SQLite, web UI with Plotly floor-plan visualization. PyInstaller .exe
build exists (desktop has "Skladiste v3.0.lnk" shortcut, runs as local server).

- **Pallet record**: QR code, rack/position/height, entry/exit timestamps, šifra
  (article code), lot, quantity, expiry date
- QR format: `QRID|DATE_IN|EXPIRY|QTY|SIFRA|LOT` (pipe-separated)
- Manual position format: `[RackID]P[Pos#]V[Height]`, e.g. `R1AP01V01`
- ~2000 positions across 18 racks: L, R1A-R8B, D, G, B (9-30 slots x 4-5 heights)
- Reception workflow: create reception plan -> allocate positions -> scan each pallet ->
  confirm -> close batch
- Issuance: scan QR -> set datum_out -> log event
- Auto position assignment: 3-tier fallback (consecutive slots same rack lowest height
  -> same rack-pair group -> priority rack order)
- Auto-backup folder with timestamped DB copies

## Reklamacije 1.0 (Quality/CAPA) — most mature

**Path:** `Reklamacije 1.0` (also `Reklamacije 1.0.zip`, 31MB packaged build — don't
extract, and older `Reklamacije` folder superseded)

Django 6 + SQLite3, full complaint/CAPA workflow.

**Reklamacija (complaint) fields:**
`broj_predmeta` (RK-YYYY-NNNN), `vrsta` (INTERNA/KUPAC/DOBAVLJAC), `status`
(NOVO->U_OBRADI->CEKA->RIJESENO->ZATVORENO), `prioritet` (NIZAK/SREDNJI/VISOK/KRITICAN),
`kategorija` (MANJA/VECA), `naslov`, `opis`, `prijavitelj`, `email_obavijest`,
`kupac_dobavljac`, `referentni_broj`, `naziv_proizvoda`, `broj_radnog_naloga`, `stroj`,
`osoblje`, `datum_prijave/azuriranja/zatvaranja`, `rok_rjesavanja`, `korekcija`,
`analiza_uzroka`, `uzrok_kategorija`, `napomena`, `vezana_nesukladnost`,
`promjene_sustava`, `broj_promjene` (OB-21 system change tracking)

**CAPA fields:** `vrsta` (KOREKTIVNA/PREVENTIVNA), `opis_mjere`, `odgovorna_osoba`,
`rok_izvrsenja`, `status` (PLANIRANA/U_TIJEKU/IZVRSENA/ODGODENA), `datum_izvrsenja`,
`rezultat`, `provjerio`, `datum_provjere`

**Dokaz (evidence):** `datoteka`, `opis`, `datum_ucitavanja`

Outputs: PDF report (ReportLab, A4, Arial-embedded for Croatian diacritics), Excel export
(2 sheets, status color-coded), email notifications on new complaint / status change.

## Tjedna usklada (Weekly stock reorder alerts)

**Path:** `Tjedna usklada/0.1.3/UskaldaGEN.py`

Reads "IZVJEŠĆE STANJA MATERIJALA" Excel (18+ cols: šifra col0, naziv col1, skladište
col3, jedinica col4, stanje col13, classification cols 52-56). Compares against hardcoded
`PODACI_ARTIKALA` min thresholds (incl. special rules: `COMB_3` = sum of two related
items must be >=3, `POSITIVE` = stock must be >0). Outputs landscape A4 PDF
(`Usklada_V10_YYYY_MM_DD_HHMM.pdf`) with red-highlighted "NARUCITI?=DA" rows.

## Utrošak vs stanje (Consumption vs Stock snapshots)

**Path:** `Utrošak vs stanje/UsporedbaStanja.py` (v3.1.4, compiled to
"Provjera neaktivnog lagera.exe")

Compares two "IZVJEŠĆE STANJA MATERIJALA" snapshots (e.g. Jan 5 vs Apr 27). Filters to
real warehouse rows ("SKLADIŠTE MATERIJALA"), aggregates by šifra. Cross-references
"Ulaz na skladišta..." files (receipt dates) for days-since-last-output. Classifies each
article:
- `POVEĆANJE` — stock increased
- `TROŠI SE` — decreasing, still in stock
- `POTROŠENO` — depleted to zero
- `NEAKTIVNI LAGER` — no movement, still holds stock

Output: multi-sheet color-coded Excel. Desktop has recent outputs:
"Usporedba lagera_06.05.2026.xlsx", "..._boje_20.05.2026.xlsx",
"..._kartoni_29.04.2026.xlsx", "USPOREDBA_05_01_vs_27_04.xlsx".

## Xgboost utrošak predikcije (Consumption forecasting)

**Path:** `Xgboost utrošak predikcije`

XGBRegressor predicting 2026 monthly consumption per article from 2023-2025 history.

**Record fields:** Mjesec, Sifra, Artikl, Grupa/Kategorija/Vrsta, Sirina_mm, Duzina_mm,
Broj_kom, Kolicina, Jedinica, Jedinicna_cijena, Kolicina_kg, Kupac, Dobavljac, RN, LOT,
PRIMKA, NARUDZBA

**Approach:** target = ratio (Kolicina / lag_12), features = lag_1/2/3/6/12, rolling
mean/std (3/6/12mo), seasonal sin/cos(month), trend, article_mean_nonzero,
log_article_mean, active_share. Train 2023-2024, test 2025. Sample weights =
log1p(Kolicina)+1. Output: `xgboost_predikcije_2026.xlsx` (pivot, detail, validation,
group summary sheets) + feature importance plot. A `usporedba_2026.py` follow-up compares
actual 2026 (M1-M4) vs predictions.

## Normativi (Production throughput norms)

**Path:** `Normativi/normativ rada na rezacim strojevima 2025.xlsx`

Excel workbook calculating sheets/h and labels/h per machine. Two input sheets (UNOS
DORADA, UNOS TISAK) feed per-machine sheets: POLAR 137, SC20, MCS 115, POLAR DC 11,
BLUMER ATLAS 1110 DUAL/110 (finishing); CX 104 6+LX, CX 102 5+LX, CD 102 6+LX (printing).

**Key inputs per product:** naklada, gramatura, tip papira (metal/bijeli), format arka
X/Y, format etikete X/Y netto/brutto, strojni grajfer, rez po X/Y, etiketa u kutiji,
kutija/paleta tip, broj boja, lakirano DA/NE, broj prolaza.

**Key formulas:** labels/sheet = INT(arak_X/etiketa_brutto_X) * INT(arak_Y/etiketa_brutto_Y);
gross sheets = netto x (1+waste%) + fixed setup; cutting time = setup + iterations x
time_per_1000 + transport.

## Montaža Etiketa (Label layout optimizer)

**Path:** `Kompleti/0.2.1 Dodaj odabir papira, custom napust ovisno o vrsti, gui`

Streamlit app. Given two label types A+B with dimensions, iterates column counts for A,
fills remaining width with B, picks layout maximizing `min(total_A, total_B)` (complete
sets). 32 paper formats across 3 paper types (Bijeli Pregani, Bijeli Glatki, Alu), each
with v/s dims + margins (top/bottom/left/right; Alu has bottom margin 15 vs 12 for
others).

## Cola / BARGEN (kupac-pića barcode labels)

**Path:** `Cola` (versions 0.1 -> 0.2 -> 1.0)

tkinter/customtkinter + pandas + reportlab. Reads 2-sheet Excel: "Deklaracije" (selected
Serial IDs in col B) + "Background" (master: Serial, Lot, Quantity, Production date,
Final-barcode-string). Generates PDF labels (15x5.5cm): LOT/DATE/QTY + Code128 barcode,
dynamic scaling to fit width. Output: `DD-MM-YYYY-N.pdf` in DEKLARACIJE folder.

## Calz / GENXML + BARGEN (kupac-moda EDI)

**Path:** `Calz/0.3.1` (latest seen; versions 0.1.0-0.1.4 + 0.3.1)

customtkinter + pandas + reportlab/lxml. Reads "Deklaracije i xml.xlsx":
- Sheet "Background": ASN, ASN delivery/doc date, HU supplier, PO from Calz, item nums,
  SKU, color, quantity, lot, unit, HU Final, production date, reels, net/gross weight
- Sheet "Bar kodovi": item, lot, net weight, quantity, barcode, status (OK/not)

**GENXML.py**: generates ASN_*.xml (namespace `urn:it:kupac-moda:snr:pp:ipp12`) — Header
(DeliveryNote, dates, VendorCode) + Items (PO, SKU, quantities, weights, production
dates). Dates formatted YYYYMMDD.

**BARGEN.py**: PDF labels (15x5.5cm, 2/page) with item/lot/net weight/qty + Code128,
filters rows with status "OK".

Also `read_log.py` parses `usage_log.txt`.

## folije (Foil consumption calculator)

**Path:** `folije`

Parses roll dimensions from product names via regex (`(\d+[.,]?\d*)\s*mm` for width,
`(\d+[.,]?\d*)\s*m(?!m)` for length). m² = (width_mm/1000) x length_m. kg = m² x
**0.01983** (conversion constant). Implemented both as VBA UDFs (`FolijeMakro.bas`:
FoilWidth_mm, FoilLength_m, FoilM2PerRola) and Python/openpyxl formula injection. Handles
European decimal/thousands separators.

## Certifikati i teh spec (Certificate/spec generator)

**Path:** `Certifikati i teh spec`

win32com (Word automation) + python-docx + threading. Currently driven by **mock API**
(`api_mock.py`) simulating ERP work-order data (customer, brand, material, production
code, dimensions, colors, analysis number). Templates (`Cer_template.docx`,
`Teh_template.docx`) use `<<TOKEN>>` placeholders; tech specs pull property tables from
`Spec papira/*.docx` (one per paper type: Property | Unit | Value | Range | Method).
Output per work order: `Certifikat_*.docx/.pdf` + `Tehnicka specifikacija_*.docx/.pdf`.
**This mock API is the integration point for the real ERP (legacy ERP) once schema is known.**

## Usklada metal (Metallized paper reconciliation)

**Path:** `Usklada metal`

pandas + xlrd + openpyxl. Reconciles 3 sources:
1. "PODLOGA NABAVE" (purchase orders) — pivots arci by vrsta (V/S) x kupac
   (KINEZI/ROTOFLEX) x format
2. "IZVJEŠĆE STANJA MATERIJALA" — stock by format, filtered gsm==68, supplier mapped via
   name substrings (nissha / protec|wenzhuo|haisen|promet -> Kinezi)
3. "RASPORED STROJEVI TISAK" (.xls, press schedule) — kg = (w_mm/1000)x(h_mm/1000)x68x
   impressions/1000, grouped by format+month

Output `USKLADA_output.xlsx`: 4 sheets (Podloga pivoti, Stanje po formatu, Plan tiska,
Tablica vrijednosti), optional auto-update of master table.

## Update cjenika boja (Price list updater)

**Path:** `Update cjenika boja` — see memory `project_cjenik_updater.md` for full detail.

GUI (customtkinter) bulk-updates "Cjenici DOBAVLJAC-BOJA d.o.o..xlsx" (1630 rows, 29 cols).
Groups by Šifra, finds latest-dated row, applies fixed-EUR or % increase to
`J.c. DAP` (col 8, always) and `J.c. 1` (col 15, if DAP exists), prepends new dated rows,
preserves full history. v2 adds preview table + partner filter. Croatian UI, EUR, ISO
dates.

---

## Other relevant files seen on Desktop (not yet cataloged as tools, but data sources)

- `Pivot - podloga za naručivanje iz legacy ERP 03.02.2026.xlsx` — pivot exported **from
  legacy ERP** for ordering basis
- `Copy of PODLOGA ZA NARUČIVANJE - GLAVNA ...xlsx` — master ordering basis (5MB)
- `IZVJEŠĆE NARUDŽBI I UTROŠKA 05.01.2026. ...xlsx` — order & consumption report (51MB,
  likely a legacy ERP export)
- `Raspored strojevi TISAK.xls - Shortcut.lnk` — shortcut to press schedule file (network
  share?)
- `QR_Generator/` — separate folder, not yet explored
- `Tjedne usklade/`, `Tender cola/`, `ino-kupac upiti/`, `Slike za Vanadoo/` — not yet explored
