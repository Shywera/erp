"""
Uvoz materijala iz legacy ERP exporta (Excel).

Ocekuje datoteku "Materijali(1).xlsx" (Sheet1) s kolonama u istom redoslijedu kao
legacy ERP Product/Index/1 export. Upisuje/azurira `materijal` po sifri (upsert) i dodaje
`cijena_povijest` zapis ako materijal jos nema cijenu s istim datumom.

Uvozi se SVE kolone iz exporta. Lokacija u skladistu/Pozicija/ULAZNO/PRIJELAZNO
SKLADISTE i Mjesto troska 1-9 su trenutno samo "sirovi" podaci iz legacy ERP -
WMS i Strojevi moduli ce ih kasnije aktivno koristiti/azurirati.

NIJE uvezeno:
- Sipo sifra (0 redaka popunjeno u exportu - polje postoji u modelu za buducnost)

Pokrenuti: python -m app.modules.materijali.import_pauk <putanja_do_xlsx>
"""

import datetime as dt
import sys
from pathlib import Path

import openpyxl

from app.core.database import SessionLocal
from app.modules.materijali.models import CijenaPovijest, Materijal

COL = {
    "vrijeme_izrade": 0,
    "kategorija": 1,
    "tip": 2,
    "grupa": 3,
    "podgrupa": 4,
    "podgrupa2": 5,
    "podgrupa3": 6,
    "podgrupa4": 7,
    "naziv": 8,
    "sifra": 9,
    "jedinica": 11,
    "aktivno": 12,
    "minimalna_kolicina": 13,
    "dobavljac_naziv": 14,
    "updated_by": 15,
    "datoteke": 16,
    "rok_trajanja": 17,
    "rok_trajanja_godina": 18,
    "lokacija_skladiste": 19,
    "pozicija": 20,
    "minimalno_pakiranje": 21,
    "tarifni_broj": 22,
    "cijena": 23,
    "datum_cijene": 24,
    "rok_dobavljivosti": 25,
    "zemlja_porijekla": 26,
    "ulazno_skladiste_1": 27,
    "ulazno_skladiste_2": 28,
    "prijelazno_skladiste_1": 29,
    "prijelazno_skladiste_2": 30,
    "prijelazno_skladiste_3": 31,
    "mjesto_troska_1": 32,
    "mjesto_troska_2": 33,
    "mjesto_troska_3": 34,
    "mjesto_troska_4": 35,
    "mjesto_troska_5": 36,
    "mjesto_troska_6": 37,
    "mjesto_troska_7": 38,
    "mjesto_troska_8": 39,
    "mjesto_troska_9": 40,
}


def _str(row, key):
    v = row[COL[key]]
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def _num(row, key):
    v = row[COL[key]]
    if v is None or v == "":
        return None
    return float(v)


def run(path: str):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb["Sheet1"]
    rows = list(ws.iter_rows(min_row=2, values_only=True))

    db = SessionLocal()
    created = updated = prices_added = 0
    try:
        for row in rows:
            sifra = _str(row, "sifra")
            if not sifra:
                continue

            m = db.query(Materijal).filter(Materijal.sifra == sifra).one_or_none()
            is_new = m is None
            if is_new:
                m = Materijal(sifra=sifra)
                db.add(m)

            m.naziv = _str(row, "naziv") or m.naziv
            m.jedinica = _str(row, "jedinica") or "kom"
            m.kategorija = _str(row, "kategorija")
            m.tip = _str(row, "tip")
            m.grupa = _str(row, "grupa")
            m.podgrupa = _str(row, "podgrupa")
            m.podgrupa2 = _str(row, "podgrupa2")
            m.podgrupa3 = _str(row, "podgrupa3")
            m.podgrupa4 = _str(row, "podgrupa4")
            m.aktivno = _str(row, "aktivno") == "DA"
            m.minimalna_kolicina = _num(row, "minimalna_kolicina")
            m.minimalno_pakiranje = _num(row, "minimalno_pakiranje")
            m.dobavljac_naziv = _str(row, "dobavljac_naziv")
            m.tarifni_broj = _str(row, "tarifni_broj")
            m.zemlja_porijekla = _str(row, "zemlja_porijekla")
            m.rok_trajanja = _str(row, "rok_trajanja")
            m.rok_trajanja_godina = _num(row, "rok_trajanja_godina")
            rok_dobavljivosti = _num(row, "rok_dobavljivosti")
            m.rok_dobavljivosti = int(rok_dobavljivosti) if rok_dobavljivosti is not None else None
            m.updated_by = _str(row, "updated_by")
            m.datoteke = _str(row, "datoteke")

            m.lokacija_skladiste = _str(row, "lokacija_skladiste")
            m.pozicija = _str(row, "pozicija")
            m.ulazno_skladiste_1 = _str(row, "ulazno_skladiste_1")
            m.ulazno_skladiste_2 = _str(row, "ulazno_skladiste_2")
            m.prijelazno_skladiste_1 = _str(row, "prijelazno_skladiste_1")
            m.prijelazno_skladiste_2 = _str(row, "prijelazno_skladiste_2")
            m.prijelazno_skladiste_3 = _str(row, "prijelazno_skladiste_3")

            for i in range(1, 10):
                setattr(m, f"mjesto_troska_{i}", _str(row, f"mjesto_troska_{i}"))

            vrijeme_izrade = row[COL["vrijeme_izrade"]]
            if is_new and isinstance(vrijeme_izrade, dt.datetime):
                m.created_at = vrijeme_izrade

            if is_new:
                created += 1
            else:
                updated += 1

            db.flush()  # ensure m.id is available for cijena_povijest FK

            cijena = _num(row, "cijena")
            datum_cijene = row[COL["datum_cijene"]]
            if isinstance(datum_cijene, dt.datetime):
                datum = datum_cijene.date()
            elif isinstance(datum_cijene, dt.date):
                datum = datum_cijene
            else:
                datum = None
            if cijena is not None and datum is not None:
                postoji = (
                    db.query(CijenaPovijest)
                    .filter(
                        CijenaPovijest.materijal_id == m.id,
                        CijenaPovijest.datum_vazenja == datum,
                        CijenaPovijest.cijena == cijena,
                    )
                    .first()
                )
                if not postoji:
                    db.add(
                        CijenaPovijest(
                            materijal_id=m.id,
                            cijena=cijena,
                            valuta="EUR",
                            datum_vazenja=datum,
                        )
                    )
                    prices_added += 1

        db.commit()
    finally:
        db.close()

    print(f"Novih materijala: {created}")
    print(f"Azuriranih materijala: {updated}")
    print(f"Novih zapisa cijena: {prices_added}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "Resources/Materijali(1).xlsx"
    if not Path(path).exists():
        print(f"Datoteka ne postoji: {path}")
        sys.exit(1)
    run(path)
