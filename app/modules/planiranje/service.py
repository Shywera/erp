"""Planiranje tiska — eligibility resolver + izračun vremena (stateless kalkulator).

NE ovisi o normativi/proizvodi/radni-nalozi modulima (manual unos naloga). Koristi
samo `strojevi` (sposobnosti presa) i `materijali` (mjesto_troška = dopušteni strojevi).

Formula validirana na stvarnom rasporedu (`Raspored strojevi TISAK.xls`, ~1000 naloga):
  otisaka = ceil(naklada / kontakata) + otpad        (otpad = makeready araka)
  RAD     = ceil((otisaka / NORMATIV) * 60 / 15) * 15 min   (zaokruženo gore na 15 min, min 15)
  SATI    = PRIP + RAD + PRA
NORMATIV (brzina ar/h) ovisi o PAPIRU (npr. PROMET 68g=7250, MOSAICO=10000, PARADE PRO=9000);
ako nije zadan, fallback na brzinu stroja (metal/bijeli iz strojevi/seed).

Pravilo dopuštenosti (po presi): stroj ∈ mjesto_troška materijala (ako je zadano) ·
format ≤ max_format (uz rotaciju) · broj_boja ≤ broj_boja_stroja · UV→samo CD1 · lak→samo CX.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import ceil

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.materijali.models import Materijal
from app.modules.planiranje.models import PlanStavka
from app.modules.strojevi.models import Stroj


@dataclass
class Nalog:
    naklada: int                       # broj etiketa (naklada)
    kontakata: int                     # etiketa po arku
    broj_boja: int
    format_x_mm: float
    format_y_mm: float
    treba_uv: bool = False
    treba_lak: bool = False
    materijal_sifra: str | None = None
    papir_naziv: str | None = None
    normativ: int | None = None        # brzina ar/h (po papiru); None -> fallback na stroj
    papir_tip: str | None = None       # 'metal' | 'bijeli' (za fallback brzinu)
    otpad: int = 0                     # makeready araka
    priprema_min: int = 45
    pranje_min: int = 15


def prese(db: Session) -> list[Stroj]:
    """Aktivne tiskarske prese sa sposobnostima (broj_boja zadan) — CD1/CD2/CX104/CX1."""
    return list(db.scalars(
        select(Stroj).where(
            Stroj.aktivno.is_(True), Stroj.tip == "tisak", Stroj.broj_boja.is_not(None)
        ).order_by(Stroj.sifra)).all())


def mjesta_troska(materijal: Materijal | None) -> set[str]:
    if materijal is None:
        return set()
    return {v for i in range(1, 10)
            if (v := getattr(materijal, f"mjesto_troska_{i}"))}


def razlozi_nedopustenosti(stroj: Stroj, nalog: Nalog, mjesta: set[str]) -> list[str]:
    """Vrati razloge zašto nalog NE smije na ovaj stroj (prazna lista = smije)."""
    r: list[str] = []
    if mjesta and stroj.sifra not in mjesta:
        r.append("materijal ne dopušta ovaj stroj (mjesto troška)")
    mx, my = stroj.max_format_x_mm, stroj.max_format_y_mm
    if mx and my:
        fx, fy = nalog.format_x_mm, nalog.format_y_mm
        if not ((fx <= mx and fy <= my) or (fx <= my and fy <= mx)):
            r.append(f"format {fx:.0f}×{fy:.0f} > max {mx:.0f}×{my:.0f} mm")
    if stroj.broj_boja and nalog.broj_boja > stroj.broj_boja:
        r.append(f"{nalog.broj_boja} boja > {stroj.broj_boja} na stroju")
    if nalog.treba_uv and not stroj.ima_uv:
        r.append("treba UV (samo CD)")
    if nalog.treba_lak and not stroj.ima_lak:
        r.append("treba lak (samo CX)")
    return r


def brzina_arh(stroj: Stroj, nalog: Nalog) -> int | None:
    if nalog.normativ:
        return nalog.normativ
    if (nalog.papir_tip or "").lower().startswith("metal"):
        return stroj.brzina_metal_arh or stroj.brzina_arh
    return stroj.brzina_bijeli_arh or stroj.brzina_arh


def _zaokr15(minute: float) -> int:
    return max(15, ceil(minute / 15) * 15)


def vrijeme(stroj: Stroj, nalog: Nalog) -> dict:
    neto = ceil(nalog.naklada / nalog.kontakata) if nalog.kontakata else 0
    otisaka = neto + (nalog.otpad or 0)
    br = brzina_arh(stroj, nalog)
    rad_min = _zaokr15(otisaka / br * 60) if br else None
    sati_min = (nalog.priprema_min or 0) + (rad_min or 0) + (nalog.pranje_min or 0)
    return {
        "neto_araka": neto, "otisaka": otisaka, "brzina": br,
        "priprema_min": nalog.priprema_min or 0, "rad_min": rad_min,
        "pranje_min": nalog.pranje_min or 0, "sati_min": sati_min if rad_min is not None else None,
    }


def planiraj(db: Session, nalog: Nalog) -> dict:
    """Za nalog vrati dopuštene prese (s vremenom) + nedopuštene (s razlozima)."""
    materijal = None
    if nalog.materijal_sifra:
        materijal = db.scalar(select(Materijal).where(Materijal.sifra == nalog.materijal_sifra.strip()))
    mjesta = mjesta_troska(materijal)

    dopusteni, nedopusteni = [], []
    for s in prese(db):
        r = razlozi_nedopustenosti(s, nalog, mjesta)
        if r:
            nedopusteni.append({"stroj": s, "razlozi": r})
        else:
            dopusteni.append({"stroj": s, "vrijeme": vrijeme(s, nalog)})
    dopusteni.sort(key=lambda d: (d["vrijeme"]["sati_min"] is None, d["vrijeme"]["sati_min"] or 0))
    return {"materijal": materijal, "mjesta": sorted(mjesta),
            "dopusteni": dopusteni, "nedopusteni": nedopusteni}


def fmt_min(m: int | None) -> str:
    if m is None:
        return "—"
    return f"{int(m) // 60}:{int(m) % 60:02d}"


# ─── Raspored po presi (PlanStavka) ───────────────────────────────────────────

def izracun_stavku(s: PlanStavka) -> None:
    """Izračunaj otisaka/rad_min/sati_min iz baznih unosa. Ako fali normativ, zadrži
    uvezeni rad_min (graceful — npr. servisni nalozi bez naklade)."""
    if s.naklada and s.kontakata:
        s.otisaka = ceil(s.naklada / s.kontakata) + (s.otpad or 0)
    if s.otisaka and s.normativ:
        s.rad_min = _zaokr15(s.otisaka / s.normativ * 60)
    s.sati_min = (s.priprema_min or 0) + (s.rad_min or 0) + (s.pranje_min or 0)


def stavke_prese(db: Session, stroj_sifra: str) -> list[PlanStavka]:
    return list(db.scalars(
        select(PlanStavka).where(PlanStavka.stroj_sifra == stroj_sifra)
        .order_by(PlanStavka.redoslijed, PlanStavka.id)).all())


def preracunaj_raspored(db: Session, stroj_sifra: str, start_dt: datetime | None = None) -> None:
    """Ulančaj presu: normaliziraj redoslijed, izračunaj svaku stavku, POČETAK = ZAVRŠETAK
    prethodne (kontinuirano, kao Excel). start_dt = početak prve stavke (zadano: sada)."""
    stavke = stavke_prese(db, stroj_sifra)
    t = start_dt or datetime.now().replace(second=0, microsecond=0)
    for i, s in enumerate(stavke, 1):
        s.redoslijed = i
        izracun_stavku(s)
        s.pocetak = t
        s.zavrsetak = t + timedelta(minutes=s.sati_min or 0)
        t = s.zavrsetak
    db.commit()


def opterecenje(db: Session, stroj_sifra: str) -> dict:
    stavke = stavke_prese(db, stroj_sifra)
    uk = sum(s.sati_min or 0 for s in stavke)
    return {"broj": len(stavke), "sati_min": uk,
            "kraj": stavke[-1].zavrsetak if stavke else None}


# ─── Import postojećeg Excela ─────────────────────────────────────────────────

SHEET_STROJ = {"CD1": "HD CD-1", "CX 104": "HD CX-104", "CX1": "HD CX-1"}


def _na(v) -> bool:
    import pandas as pd
    try:
        return v is None or bool(pd.isna(v))
    except (ValueError, TypeError):
        return False


def _s(v) -> str | None:
    if _na(v):
        return None
    t = str(v).strip()
    return t or None


def _i(v) -> int | None:
    if _na(v):
        return None
    try:
        return int(float(v))
    except (ValueError, TypeError):
        return None


def _min(v) -> int | None:
    """Parsiraj vrijeme ('00:45:00', '0 days 00:15:00', timedelta) u minute."""
    if _na(v):
        return None
    if hasattr(v, "total_seconds"):
        return round(v.total_seconds() / 60)
    nums = [int(x) for x in re.findall(r"\d+", str(v))]
    if "days" in str(v) and len(nums) >= 4:
        return nums[1] * 60 + nums[2] + round(nums[3] / 60)
    if len(nums) >= 2:
        return nums[0] * 60 + nums[1]
    return None


def uvezi_excel(db: Session, putanja: str) -> int:
    """Učitaj `Raspored strojevi TISAK.xls` (3 lista = 3 prese) u PlanStavka. ZAMJENI
    postojeće stavke tih presa. Vrati broj uvezenih naloga."""
    import pandas as pd

    uvezeno = 0
    for sheet, stroj in SHEET_STROJ.items():
        try:
            df = pd.read_excel(putanja, sheet_name=sheet, engine="calamine", header=0)
        except Exception:
            continue
        db.query(PlanStavka).filter(PlanStavka.stroj_sifra == stroj).delete()
        red = 0
        for _, r in df.iterrows():
            rn_i = _i(r.get("RN") if "RN" in df.columns else None)
            if not rn_i:                              # samo numerički RN = pravi nalog
                continue
            rn = str(rn_i)
            red += 1
            s = PlanStavka(
                stroj_sifra=stroj, redoslijed=red, rn=rn,
                naziv=_s(r.get("NAZIV PROIZVODA")), papir_naziv=_s(r.get("PAPIR (naziv)")),
                format_cm=_s(r.get("format papira (cm)")),
                naklada=_i(r.get("NAKLADA")), kontakata=_i(r.get("kontakata")),
                normativ=_i(r.get("NORMATIV")), otisaka=_i(r.get("otisaka")),
                priprema_min=_min(r.get("PRIP.")) or 0, rad_min=_min(r.get("RAD")),
                pranje_min=_min(r.get("PRA.")) or 0, rok=_s(r.get("ROK")),
            )
            db.add(s)
            uvezeno += 1
        db.flush()
        preracunaj_raspored(db, stroj)
    return uvezeno
