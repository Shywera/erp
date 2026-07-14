"""
Seed script: populates the strojevi table with known machines.
Speed data for printing machines sourced from normativ_calc.py (CX_104, CX_102, CD_102 params).
Run from project root: python -m app.modules.strojevi.seed
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.strojevi.models import Stroj

MACHINES = [
    # ── Tisak (offset printing) ─────────────────────────────────────────────
    # Brzine iz normativ_calc.py: CD_102 metal=9000, bijeli=10000
    dict(sifra="HD CD-1", naziv="Heidelberg CD 102 — 6+UV",
         tip="tisak", aktivno=True,
         max_format_x_mm=720, max_format_y_mm=1020,
         broj_boja=6, ima_lak=False, ima_uv=True,
         brzina_metal_arh=9000, brzina_bijeli_arh=10000,
         broj_osoba=2),
    dict(sifra="HD CD-2", naziv="Heidelberg CD 102 — 6+UV",
         tip="tisak", aktivno=True,
         max_format_x_mm=720, max_format_y_mm=1020,
         broj_boja=6, ima_lak=False, ima_uv=True,
         brzina_metal_arh=9000, brzina_bijeli_arh=10000,
         broj_osoba=2),
    # Brzine iz normativ_calc.py: CX_104 metal=9500, bijeli=11000
    dict(sifra="HD CX-104", naziv="Heidelberg CX 104 — 6+lak",
         tip="tisak", aktivno=True,
         max_format_x_mm=720, max_format_y_mm=1040,
         broj_boja=6, ima_lak=True, ima_uv=False,
         brzina_metal_arh=9500, brzina_bijeli_arh=11000,
         broj_osoba=2),
    # Brzine iz normativ_calc.py: CX_102 metal=9200, bijeli=10500
    dict(sifra="HD CX-1", naziv="Heidelberg CX 102 — 5+lak",
         tip="tisak", aktivno=True,
         max_format_x_mm=720, max_format_y_mm=1020,
         broj_boja=5, ima_lak=True, ima_uv=False,
         brzina_metal_arh=9200, brzina_bijeli_arh=10500,
         broj_osoba=2),
    dict(sifra="HD 105 CSF", naziv="Heidelberg 105 CS Formate",
         tip="tisak", aktivno=True,
         max_format_x_mm=740, max_format_y_mm=1050,
         broj_osoba=2),
    dict(sifra="HD 105 CS", naziv="Heidelberg 105 CS",
         tip="tisak", aktivno=True,
         max_format_x_mm=740, max_format_y_mm=1050,
         broj_osoba=2),
    dict(sifra="SBL 105 CF", naziv="SBL 105 CF",
         tip="tisak", aktivno=True,
         max_format_x_mm=740, max_format_y_mm=1050,
         broj_osoba=2),

    # ── Rezanje / guillotine ────────────────────────────────────────────────
    dict(sifra="POLAR137", naziv="Polar 137 guillotine",
         tip="rezanje", aktivno=True,
         max_format_x_mm=1370, max_format_y_mm=None,
         broj_osoba=1,
         napomena="Strip-cut + finish-cut parametri u normativ_calc.py: POLAR_137"),
    dict(sifra="SC20", naziv="SC20 — programabilni rezač",
         tip="rezanje", aktivno=True,
         max_format_x_mm=None, max_format_y_mm=None,
         broj_osoba=1,
         napomena="Strip-cut + finish-cut parametri u normativ_calc.py: SC20_STRIP / SC20_FINISH"),
    dict(sifra="MCS 115-1", naziv="MCS 115 — rezač #1",
         tip="rezanje", aktivno=True,
         max_format_x_mm=1150, max_format_y_mm=None,
         broj_osoba=1,
         napomena="Strip-cut + finish-cut parametri u normativ_calc.py: MCS_115_STRIP / MCS_115_FINISH"),
    dict(sifra="MCS 115-2", naziv="MCS 115 — rezač #2",
         tip="rezanje", aktivno=True,
         max_format_x_mm=1150, max_format_y_mm=None,
         broj_osoba=1,
         napomena="Strip-cut + finish-cut parametri u normativ_calc.py: MCS_115_STRIP / MCS_115_FINISH"),
    dict(sifra="MCS 115-3", naziv="MCS 115 — rezač #3",
         tip="rezanje", aktivno=True,
         max_format_x_mm=1150, max_format_y_mm=None,
         broj_osoba=1,
         napomena="Strip-cut + finish-cut parametri u normativ_calc.py: MCS_115_STRIP / MCS_115_FINISH"),
    dict(sifra="WOHL-115-1", naziv="Wohlenberg 115 — rezač #1",
         tip="rezanje", aktivno=True,
         max_format_x_mm=1150, max_format_y_mm=None,
         broj_osoba=1),
    dict(sifra="WOHL-115-2", naziv="Wohlenberg 115 — rezač #2",
         tip="rezanje", aktivno=True,
         max_format_x_mm=1150, max_format_y_mm=None,
         broj_osoba=1),
    dict(sifra="WOHL-115-3", naziv="Wohlenberg 115 — rezač #3",
         tip="rezanje", aktivno=True,
         max_format_x_mm=1150, max_format_y_mm=None,
         broj_osoba=1),

    # ── Štancanje / die-cutting ──────────────────────────────────────────────
    dict(sifra="BL-1110", naziv="Blumer Atlas 1110 Dual — štancanje",
         tip="stancanje", aktivno=True,
         max_format_x_mm=1100, max_format_y_mm=None,
         broj_osoba=2,
         napomena="Parametri u normativ_calc.py: BLUMER_1110_DUAL"),
    dict(sifra="BL-110-1", naziv="Blumer Atlas 110 — štancanje #1",
         tip="stancanje", aktivno=True,
         max_format_x_mm=1100, max_format_y_mm=None,
         broj_osoba=2,
         napomena="Parametri u normativ_calc.py: BLUMER_110"),
    dict(sifra="BL-110-2", naziv="Blumer Atlas 110 — štancanje #2",
         tip="stancanje", aktivno=True,
         max_format_x_mm=1100, max_format_y_mm=None,
         broj_osoba=2,
         napomena="Parametri u normativ_calc.py: BLUMER_110"),
    dict(sifra="DC-11", naziv="Polar DC 11 — štancanje",
         tip="stancanje", aktivno=True,
         max_format_x_mm=None, max_format_y_mm=None,
         broj_osoba=1,
         napomena="Parametri u normativ_calc.py: POLAR_DC_11"),

    # ── Priprema / prepress ──────────────────────────────────────────────────
    dict(sifra="CTP", naziv="CTP — osvjetljivač ploča",
         tip="priprema", aktivno=True, broj_osoba=1),
    dict(sifra="RRM", naziv="RRM — priprema",
         tip="priprema", aktivno=True, broj_osoba=1),

    # ── Ljepljenje ───────────────────────────────────────────────────────────
    dict(sifra="LJEP-VEGA", naziv="Vega — stroj za ljepljenje",
         tip="ljepljenje", aktivno=True, broj_osoba=1),
    dict(sifra="LJEP-BOBST", naziv="Bobst — stroj za ljepljenje",
         tip="ljepljenje", aktivno=True, broj_osoba=1),

    # ── Ostalo ───────────────────────────────────────────────────────────────
    dict(sifra="VAK-1", naziv="VAK-1 — vakuumski stroj",
         tip="ostalo", aktivno=True),
    dict(sifra="DEMINERALIZATOR", naziv="Demineralizator",
         tip="ostalo", aktivno=True),
    dict(sifra="FUT-1", naziv="FUT-1",
         tip="ostalo", aktivno=True),
    dict(sifra="SEN-1", naziv="SEN-1",
         tip="ostalo", aktivno=True),
]


def run():
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    with Session(engine) as db:
        added = 0
        skipped = 0
        for m in MACHINES:
            existing = db.query(Stroj).filter(Stroj.sifra == m["sifra"]).first()
            if existing:
                skipped += 1
                continue
            db.add(Stroj(**m))
            added += 1
        db.commit()
        print(f"Seed done: {added} dodano, {skipped} preskočeno (već postoje).")


if __name__ == "__main__":
    run()
