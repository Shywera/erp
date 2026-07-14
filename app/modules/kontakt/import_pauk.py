"""
Uvoz partnera (Kontakti) i adresa (Adresar) iz legacy ERP Excel exporta.

legacy ERP polje "Kupci/Dobavljači" ima dvije pod-tablice:
  - Partneri  →  Kontakti(1).xlsx
  - Adresar   →  Adresar.xlsx  (više poslovnih jedinica po partneru, vezano po Naziv)

xlsx se čita direktno iz ZIP-a (sirovi OOXML) jer trenutna verzija openpyxl
puca na stylesheetu ovih exporta. Ćelije su cp1250/win-1250 pa ih dekodiramo.

Pokretanje:
    python -m app.modules.kontakt.import_pauk Resources/Kontakti(1).xlsx Resources/Adresar.xlsx
"""
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.kontakt.models import Adresar, Kontakt

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

# legacy ERP export je cp1250 ali zapisan kao UTF-8 bytes s krivim kodiranjem;
# znakovi Š/č/ć/ž stignu kao U+FFFD. Pokušavamo popraviti najčešće.
_FIX = {
    "�ifra": "Šifra", "Mati�ni": "Matični", "pla�anja": "plaćanja",
    "Dr�ava": "Država", "�upanija": "Županija", "Op�ina": "Općina",
    "PODUZE�E": "PODUZEĆE",
}


def _clean(v):
    if v is None:
        return None
    s = str(v).strip().lstrip("'")
    return s or None


def _read_sheet(path):
    """Vrati listu dict-ova {kolona_slovo: vrijednost} po retku."""
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        t = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in t.findall(f"{NS}si"):
            shared.append("".join(n.text or "" for n in si.iter(f"{NS}t")))
    root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in root.iter(f"{NS}row"):
        cells = {}
        for c in row.findall(f"{NS}c"):
            col = re.match(r"[A-Z]+", c.get("r")).group()
            t = c.get("t")
            v = c.find(f"{NS}v")
            iss = c.find(f"{NS}is")
            val = ""
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif iss is not None:
                val = "".join(n.text or "" for n in iss.iter(f"{NS}t"))
            elif v is not None:
                val = v.text
            cells[col] = val
        rows.append(cells)
    return rows


def _to_int(v):
    v = _clean(v)
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def _to_float(v):
    v = _clean(v)
    if not v:
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


_TIP_MAP = {
    "Buyer": "kupac",
    "Supplier": "dobavljac",
    "BuyerSupplier": "oba",
}


def import_kontakti(db, path):
    rows = _read_sheet(path)
    if not rows:
        return 0, 0
    # rows[0] = header
    novih = azuriranih = 0
    for r in rows[1:]:
        sifra = _clean(r.get("A"))
        naziv = _clean(r.get("B"))
        if not sifra and not naziv:
            continue
        if not sifra:
            sifra = f"AUTO-{naziv[:20]}"

        k = db.scalar(select(Kontakt).where(Kontakt.sifra == sifra))
        nova = k is None
        if nova:
            k = Kontakt(sifra=sifra, naziv=naziv or "Bez naziva")
            db.add(k)

        k.naziv = naziv or k.naziv
        k.interni_naziv = _clean(r.get("C"))
        k.oib = _clean(r.get("D"))
        k.mjesto = _clean(r.get("E"))
        k.maticni_broj = _clean(r.get("F"))
        k.valuta_placanja_dan = _to_int(r.get("G"))
        k.referent = _clean(r.get("H"))
        k.radno_vrijeme = _clean(r.get("I"))
        k.grupa = _clean(r.get("J"))
        k.tip = _TIP_MAP.get(_clean(r.get("K")) or "", "ostalo")
        k.hbor_osiguranje = (_clean(r.get("L")) or "").lower() in ("da", "yes", "1", "true")
        k.hbor_rok_placanja_dan = _to_int(r.get("M"))
        k.naziv_dodatni = _clean(r.get("N"))
        k.aktivan = True

        if nova:
            novih += 1
        else:
            azuriranih += 1
    db.commit()
    return novih, azuriranih


def import_adresar(db, path):
    rows = _read_sheet(path)
    if not rows:
        return 0, 0
    # Mapa naziv → kontakt (case-insensitive)
    svi = db.scalars(select(Kontakt)).all()
    by_naziv = {}
    for k in svi:
        if k.naziv:
            by_naziv.setdefault(k.naziv.strip().lower(), k)
        if k.naziv_dodatni:
            by_naziv.setdefault(k.naziv_dodatni.strip().lower(), k)

    # Očisti postojeći adresar (puni re-import)
    for a in db.scalars(select(Adresar)).all():
        db.delete(a)
    db.flush()

    dodano = povezano = 0
    for r in rows[1:]:
        partner = _clean(r.get("A"))
        if not partner:
            continue
        k = by_naziv.get(partner.strip().lower())
        a = Adresar(
            kontakt_id=k.id if k else None,
            partner_naziv=partner,
            drzava=_clean(r.get("B")),
            zupanija=_clean(r.get("C")),
            opcina=_clean(r.get("D")),
            grad=_clean(r.get("E")),
            naziv_pj=_clean(r.get("F")),
            adresa=_clean(r.get("G")),
            kilometri=_to_float(r.get("H")),
        )
        db.add(a)
        dodano += 1
        if k:
            povezano += 1
    db.commit()
    return dodano, povezano


def main():
    args = sys.argv[1:]
    kontakti_path = args[0] if len(args) > 0 else "Resources/Kontakti(1).xlsx"
    adresar_path = args[1] if len(args) > 1 else "Resources/Adresar.xlsx"

    db = SessionLocal()
    try:
        if Path(kontakti_path).exists():
            n, a = import_kontakti(db, kontakti_path)
            print(f"Kontakti:  {n} novih, {a} ažuriranih")
        else:
            print(f"!! Nije pronađen: {kontakti_path}")

        if Path(adresar_path).exists():
            d, p = import_adresar(db, adresar_path)
            print(f"Adresar:   {d} adresa uvezeno, {p} povezano s partnerom ({d - p} nepovezano)")
        else:
            print(f"!! Nije pronađen: {adresar_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
