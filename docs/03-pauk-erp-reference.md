# legacy ERP ERP Reference

The company's current ERP, running on a local server at **`https://erp.interno`** (internal
network hostname, IIS/ASP.NET MVC 5.2, .NET 4.0.30319). Built by **Vanado**
(vanado.hr) — vendor name "legacy ERP Development". UI language: Croatian.

Login: `https://erp.interno/Account/Login` (form fields `UserName`, `Password`, ASP.NET
anti-forgery token + `.AspNet.ApplicationCookie`). Credentials for read-only exploration
are in `legacy ERP acc.txt` (gitignored, not reproduced here).

Explored 2026-06-15, read-only (GET requests only, no writes/changes made).

## Module map (left-hand nav menu)

| Croatian label | URL path | Likely English meaning |
|---|---|---|
| Planiranje nabave iz proizvodnje | `/Plan/Supply` | Procurement planning from production |
| Planiranje | `/Plan/Production` | Production planning |
| Materijal | `/Product/Index/1` | Materials / articles master data |
| upiti / Kalkulacije / šifrarnik | `/Product/Index2/4` | Inquiries / calculations / code registry |
| Knjiga izvoza | `/OutgoingBook` | Export book (customs/export records) |
| Knjiga uvoza | `/IncomingBook` | Import book |
| Cjenici | `/Catalog/Sales` | Sales price lists |
| Cjenik nabava | `/Catalog` | Purchase price list/catalog |
| Ponude | `/Offer` | Quotes/offers |
| Narudžbe | `/Order` | Orders |
| Analiza prodaje | `/Warehouse/AnalysisBuyer` | Sales analysis |
| Radni nalozi | `/WorkOrder/Launched` | Work orders (production) |
| Nabava | `/Request/Order` | Procurement requests |
| Primke i međuskladišnice | `/Purchase` | Goods receipts & inter-warehouse transfers |
| Ulazni računi | `/IncomeBill/Index` | Incoming invoices |
| Otpremnice | `/Delivery` | Delivery notes |
| Računi | `/Order/Bill` | Sales invoices |
| Proforma | `/Proforma/Bill` | Proforma invoices |
| Skladište | `/Warehouse/Index` | Warehouse / stock |
| Kategorije | `/Category` | Categories |
| Kupci / DOBAVLJAČI | `/Contact` | Customers / Suppliers |
| Dnevnici rada | `/WorkOrderLog` | **Work logs — the MES data** |
| Izvještaji planova | `/PlanReports` | Plan reports |
| Održavanje | `/Delay` | Maintenance |
| Inventura | `/InventoryDocument` | Stock-take / inventory count |

Other controllers seen but not in main menu: `Machine` (e.g. `/Machine/Details/{id}`),
`WorkOrder/CostDetails/{id}`, `WorkOrder/Details/{id}`, `Home/Prepare`.

Home dashboard ("Početna") shows 6 machines as quick links: `Machine/Details/23, 37, 52,
57, 142, 143` — need to identify which physical machines these IDs correspond to.

Dashboard also lists many `WorkOrder/Details/{id}` and `WorkOrder/CostDetails/{id}`
links for in-progress work orders (IDs observed in range ~64668-66328).

## Field schemas observed (table headers per page)

### Materijal (`/Product/Index/1`) — materials/articles master
RB, Vrijeme izrade, Kategorija, Tip, Grupa, Podgrupa, Naziv, Šifra, Sipo šifra, Jedinica,
Aktivno, Minimalna količina, Dobavljač, Datum zadnje izmjene, Zadnje izmjenio, Datoteke,
excel predložak

-> Matches the classification fields (Kategorija/Tip/Grupa/Podgrupa) used across legacy
scripts (Xgboost predikcije, Tjedna usklada, Utrošak vs stanje).

### Materijal — edit form (`/Product/Edit/{id}`), explored 2026-06-15

Opened a real material (id 5000, "folije SILVER KURZ SX 230mm 1800m", category path
1 -> 465 -> 466 -> 484 -> 665). This is the full per-article editor (opened by clicking
a row in `/Product/Index/1`). Far more fields than the Excel export's 41 columns.
Croatian label -> internal field name; **bold = dropdown / entity-linked**.

**Identifikacija (mostly hidden/read-only in edit mode)**
- Code (Šifra) — hidden, auto-generated, not directly editable
- CppID (Sipo šifra) — hidden
- Group — hidden, derived string from category path (e.g. "folije")
- Name (Naziv) — textarea
- Unit (Jedinica) — text
- IsActive (Aktivno) — checkbox

**Kategorija / klasifikacija — dropdowns**
- **CategoryId** (Kategorija) — cascading chain of dropdowns, one per level
  (`data-source="CategoryId"`, each level's `data-param-categoryId` = parent's value).
  For material 5000: 1 -> 465 -> 466 -> 484 -> 665.
- **ProductCategoryIds[]** (Kategorija, repeatable table "Proizvodi po kategoriji") —
  `data-source="CategoryId"`
- **KpdId** (KPD) — number/select-box

**Dimenzije i tehnička svojstva (plain number fields)**
Radius (Promjer [mm]), Thickness (Debljina [µm]), Length (Duljina [mm]),
Width (Širina [mm]), Height (Visina [mm]), Surface (Površina [mm2]),
Volumen (Volumen [mm3]), ConvU1U2 (Gramatura [g/m2]), Quality (Kvaliteta),
BoxesOnPaletteZ (Kutija na paleti Z-visina), Weight (Težina [kg]), Variant (Hilzna),
Liter (Litraža)

**Opis / napomene**
Other (Tehnički naziv robe), Description (Raspored), DescriptionEng (Opis En, textarea),
Remark (Posebna napomena, textarea), DoradaRemark (Napomena, textarea),
Signature (Oznaka)

**Skladište / lokacija**
- Location (Lokacija u skladištu) — textarea
- Position (Pozicija)
- MinumumStockQuantity (Minimalna vrijednost skladišta)
- **AllowedTransferIds[]** (Skladište, repeatable "Prijelazna skladišta") —
  `data-source="OrgUnitId"`, `data-param-isTransfer="True"`
- **AllowedInputIds[]** (Skladište, repeatable "Ulazna skladišta") —
  `data-source="OrgUnitId"`, `data-param-isInput="True"`

**Nabava / dobavljači**
- **BuyerId** (Kupac) — number/select-box
- **SupplierId** (Dobavljač) — `data-source="ContactId"`
- **ProducerId** (Proizvođač) — `data-source="ContactId"`
- **OriginCountryId** (Zemlja porijekla) — `data-source="CountryId"`
- ProducerProductName (Naziv proizvođača), ProducerProductCode (Šifra proizvođača),
  OtherCode (Šifra kupca)
- MinimumPackaging (Minimalno pakiranje), PackagingUnit (Jedinica mjere pakiranja)
- DeliveryInDays (Rok dobavljivosti [dan])
- DeliveryDeadlineType (Rok trajanja — free text, observed value "Supplier")
- **DeadlineYears** (Rok trajanja — godina) — real `<select>` with options 1-5 godina
- DeadlineText (Rok trajanja — free text)
- TariffNumber (Tarifni broj)

**Proizvodnja / strojevi**
- **AllowedOperationIds[]** (Stroj, repeatable "Mjesto troška") —
  `data-source="AliasOperationId"`, `data-id-field="Alias"` (e.g. "HD 105 CSF")
- **AllowedProducts[]** (Proizvod, repeatable — finished products this material can go
  into) — `data-source="ProductId"`
- Technique (Tehnika), DoradaType (Tip dorade), Complet (Komplet), Drawing (Nacrt),
  System (Sistem), Namotaj, SubSurface (Podloga), BasePaper (Bazni papir),
  Material (Materijal)

**Boja / tisak**
- Color (Boja) — free text
- **ColorId** (Šifra boje) — `data-source="ProductId"` (links to another material/product
  representing that ink/color)
- **PantoneId** (Pantone) — number/select-box
- Coated, Foil (Folija), Lugootporno, Food (Prehrana),
  OneComponentTwoComponent (Jednokomponentno/dvokomponentno),
  LightStability (Svjetlostabilnost LIGHT), Certificates (Certifikati)

**Ostalo**
- InventoryNumber (Inventarni broj), Ura, ProductionNumber (Serijski broj),
  JunkKeyNumber (Ključni broj otpada)
- **ContoId** (Konto prihoda) — number/select-box
- QrNotNeeded (Izdavanje bez QR koda) — checkbox
- IsMsExcluded (Zabranjeno na međuskladištu) — checkbox

**Privici**
- Annexes (Datoteke) — file upload widget

-> Coverage vs our `materijal` table (see `05-modul-materijali.md`): the Excel-imported
fields (kategorija/tip/grupa/podgrupa*, minimalna_kolicina, minimalno_pakiranje,
dobavljac_naziv, tarifni_broj, zemlja_porijekla, rok_trajanja*, rok_dobavljivosti,
lokacija_skladiste, pozicija, ulazno/prijelazno skladiste, mjesto_troska_1-9, datoteke,
napomena) cover roughly the "Skladište/lokacija" and "Nabava" groups above. **Not yet
modeled**: all dimension/technical fields (Radius..Liter), all
opis/napomene fields besides napomena, the ink/print-specific group (Color, ColorId,
PantoneId, Coated, Foil, Technique, Certificates, ...), the entity-linked dropdowns
(BuyerId/SupplierId/ProducerId/OriginCountryId/ContoId/KpdId — would need `kontakt`,
`zemlja`, `konto` lookup tables), the repeatable lists (ProductCategoryIds,
AllowedProducts, AllowedOperationIds, AllowedTransferIds, AllowedInputIds — these
look like the *real* source for "mjesto troška" / machine + warehouse linkage, more
structured than the flat `mjesto_troska_1..9` / `*_skladiste_*` strings we imported
from Excel), and the two checkboxes QrNotNeeded/IsMsExcluded.

### Skladište (`/Warehouse/Index`) — stock
RB, Šifra, Naziv proizvoda, Gramatura, Duljina [mm], Širina [mm], Skladište, Jedinica,
raspoloživo po lotu, broj pakiranja, Minimalna količina skladišta, Datum prvog ulaska,
Datum zadnjeg ulaska, Datum zadnjeg izlaska, lot, prosječna nabavna cijena, iznos,
ukupna količina po šifri, ukupan iznos po šifri

-> This is the live equivalent of the "IZVJEŠĆE STANJA MATERIJALA" export consumed by
Tjedna usklada, Utrošak vs stanje, Usklada metal, Xgboost predikcije. Confirms legacy ERP is
the **source system** for those exports.

### Radni nalozi (`/WorkOrder/Launched`) — work orders
RB, Godina, Vrijeme izrade, Rok isporuke, Kupac, Oznaka RN, Šifra kupca, Broj RN, Unio,
Napomena, Status, Datum završetka, Količina [kom], Proizvodi, Označi

### Dnevnici rada (`/WorkOrderLog`) — MES production logs
RB, Vrijeme izrade, Vrijeme završetka, Broj radnog naloga, Kalkulacija, Proces, Artikl,
Količina, Količina senzor, Djelatnik, Ime stroja, Operacija, Završi operaciju, Završi
proizvod, Završena faza na stroju, Završena faza na stroju napomena, Zadnje izmjenio,
Datum zadnje izmjene

-> **This is the closest existing thing to MES data**: per work-order, per-machine,
per-employee, per-operation log entries with both manual quantity and sensor-read
quantity ("Količina senzor"). Any new MES module should either integrate with this or
replace it with richer real-time tracking.

### Kupci / Dobavljači (`/Contact`)
RB, Šifra, Naziv, Interni naziv, Oib, Mjesto, Matični broj, Valuta plaćanja [dan],
Referent, Radno vrijeme, Grupa, Tip kupca, HBOR osiguranje, HBOR ugovoreni rok plaćanja
[dan], Naziv, excel predložak

## Implications for the new system

- legacy ERP already owns: materials master, customers/suppliers, work orders, work logs
  (basic MES), stock, pricing, invoicing, delivery notes, import/export books,
  maintenance, inventory counts.
- The legacy automation scripts exist precisely because legacy ERP's exports
  ("IZVJEŠĆE STANJA MATERIJALA", "RASPORED STROJEVI TISAK") need extra processing legacy ERP
  doesn't do natively (reorder alerts, forecasting, reconciliation, layout optimization,
  QR warehouse tracking, EDI/customer-specific labels, quality/CAPA).
- Two architecture directions (still open, see `04-open-decisions.md`):
  1. **Satellite system**: new app reads/writes legacy ERP via its exports or an API (if one
     exists — not yet checked) and focuses on the gaps (real WMS, quality, forecasting,
     advanced MES floor tracking).
  2. **Replacement**: new app becomes the system of record, with a migration path off
     legacy ERP module by module.
- Worth checking whether legacy ERP exposes a JSON/API layer beyond the server-rendered HTML
  (would change feasibility of "satellite" integration a lot). Not checked yet.
