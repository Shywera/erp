# Domain Overview

## The company

A label printing company producing self-adhesive labels (etikete) on metallized and
white paper stock. Clients include:

- **kupac-pića** (e.g. "Tender kupac-pića") — barcode labels generated via legacy "Cola"
  tool (BARGEN)
- **kupac-moda** (apparel/logistics) — EDI ASN XML + shipping labels via legacy "Calz"
  tool (GENXML + BARGEN)
- Beer brands: Ožujsko pivo, 33 Export, Isenbeck
- **ponavljajući ino-kupci** — recurring tender/inquiry spreadsheets seen on
  desktop ("ino-kupac upiti", "Tender Paulaner", "Radna tablica ino-kupac_BENIN_ino-kupac")
- Switzerland WG Labels (pricing tenders)
- Somersby, Paulaner — tender folders present

## Materials

- Metallized paper (Alu) and white paper (Bijeli Pregani / Bijeli Glatki), various
  gramature (g/m²)
- Plastic foils (folije) — tracked by roll dimensions (width mm x length m), converted
  to kg via constant 0.01983 kg/m²
- Inks/colors — price list managed under "DOBAVLJAC-BOJA d.o.o." (need to confirm: own
  company or supplier)

## Production equipment

**Printing (offset, Heidelberg):**
- CX 104 6+LX (6 colors + lak/varnish)
- CX 102 5+LX (5 colors + lak)
- CD 102 6+LX (6 colors + UV lak)

**Finishing / cutting / die-cutting:**
- Polar 137 (guillotine cutter)
- SC20 (programmable cutter — strip-cut + finish-cut + packaging)
- MCS 115 (programmable cutter)
- Polar DC 11 (die-cutting/štancanje)
- Blumer Atlas 1110 Dual, Blumer Atlas 110 (die-cutting)

The legacy ERP ERP dashboard shows 6 "favorite" machines (IDs 23, 37, 52, 57, 142, 143) —
likely these core production machines. Need to map IDs -> machine names.

## Production flow (as understood so far)

1. Customer order / tender (Excel-based pricing & quoting, e.g. "Tender KUPAC.xlsx")
2. Work order created in legacy ERP (Radni nalog — "Narudžbe" / "Radni nalozi")
3. Production planning (legacy ERP: Planiranje, Planiranje nabave iz proizvodnje)
4. Printing on offset press, then finishing/die-cutting per production normatives
   (see legacy "Normativi" — sheets/h and labels/h formulas per machine)
5. Work logged per operation/machine/employee (legacy ERP: "Dnevnici rada" / WorkOrderLog) —
   this is the MES data: quantities, sensor counts, operation completion
6. Finished goods to warehouse (pallets, QR-coded, racked by position) — legacy
   "Skladište" WMS prototype
7. Delivery / shipping (legacy ERP: Otpremnice / Delivery) — with customer-specific
   requirements (e.g. kupac-moda EDI ASN XML, kupac-pića barcode labels)
8. Invoicing (legacy ERP: Računi / Order/Bill)
9. Quality issues tracked via complaints/CAPA (legacy "Reklamacije" Django app)

## Open naming questions

- Is "DOBAVLJAC-BOJA d.o.o." the user's own company, or an ink/color supplier whose price
  list is maintained as a courtesy/integration?
- What does korisničko ime u legacy ERP-u map to as a role — production/technology dept?
