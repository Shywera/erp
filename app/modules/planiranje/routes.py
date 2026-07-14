from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.planiranje import service as svc
from app.modules.planiranje.models import PlanStavka
from app.modules.planiranje.service import Nalog

router = APIRouter(prefix="/planiranje", tags=["planiranje"])
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["fmtmin"] = svc.fmt_min
templates.env.filters["fmtn"] = lambda n: f"{int(n):,}".replace(",", ".") if n is not None else "—"
templates.env.filters["fmtdt"] = lambda d: d.strftime("%d.%m. %H:%M") if d else "—"

EXCEL_PUTANJA = r"C:\Users\Tehnolog\Desktop\Planiranje\Raspored strojevi TISAK.xls"


def _slug(sifra: str) -> str:
    return sifra.replace("HD ", "").replace("-", "").replace(" ", "").lower()


def _presa_po_slugu(db: Session, slug: str):
    return next((s for s in svc.prese(db) if _slug(s.sifra) == slug), None)


def _tabovi(db: Session) -> list[dict]:
    out = []
    for s in svc.prese(db):
        opt = svc.opterecenje(db, s.sifra)
        out.append({"sifra": s.sifra, "slug": _slug(s.sifra),
                    "broj": opt["broj"], "sati_min": opt["sati_min"]})
    return out


def _tablica(request: Request, db: Session, presa):
    return templates.TemplateResponse(request, "planiranje/_tablica.html", {
        "presa": presa, "slug": _slug(presa.sifra),
        "stavke": svc.stavke_prese(db, presa.sifra),
        "opt": svc.opterecenje(db, presa.sifra)})


@router.get("", response_class=HTMLResponse)
def planiranje(request: Request):
    return templates.TemplateResponse(request, "planiranje/planiranje.html", {})


@router.post("/izracun", response_class=HTMLResponse)
def izracun(
    request: Request,
    naklada: int = Form(...),
    kontakata: int = Form(...),
    broj_boja: int = Form(...),
    format_x_cm: float = Form(...),
    format_y_cm: float = Form(...),
    materijal_sifra: str = Form(""),
    papir_naziv: str = Form(""),
    normativ: str = Form(""),
    papir_tip: str = Form(""),
    otpad: int = Form(0),
    priprema_min: int = Form(45),
    pranje_min: int = Form(15),
    treba_uv: str = Form(""),
    treba_lak: str = Form(""),
    db: Session = Depends(get_db),
):
    nalog = Nalog(
        naklada=naklada, kontakata=kontakata, broj_boja=broj_boja,
        format_x_mm=format_x_cm * 10, format_y_mm=format_y_cm * 10,
        treba_uv=(treba_uv == "on"), treba_lak=(treba_lak == "on"),
        materijal_sifra=materijal_sifra.strip() or None,
        papir_naziv=papir_naziv.strip() or None,
        normativ=int(normativ) if normativ.strip().isdigit() else None,
        papir_tip=papir_tip or None,
        otpad=otpad, priprema_min=priprema_min, pranje_min=pranje_min,
    )
    rez = svc.planiraj(db, nalog)
    return templates.TemplateResponse(request, "planiranje/_rezultat.html",
                                      {"rezultat": rez, "nalog": nalog})


# ─── Raspored po presi ────────────────────────────────────────────────────────

@router.get("/raspored", response_class=HTMLResponse)
def raspored(db: Session = Depends(get_db)):
    prese = svc.prese(db)
    prva = _slug(prese[0].sifra) if prese else "cd1"
    return RedirectResponse(f"/planiranje/raspored/{prva}", status_code=303)


@router.get("/raspored/{slug}", response_class=HTMLResponse)
def raspored_presa(request: Request, slug: str, db: Session = Depends(get_db)):
    presa = _presa_po_slugu(db, slug)
    if presa is None:
        return RedirectResponse("/planiranje/raspored", status_code=303)
    return templates.TemplateResponse(request, "planiranje/raspored.html", {
        "presa": presa, "slug": slug, "tabovi": _tabovi(db),
        "stavke": svc.stavke_prese(db, presa.sifra),
        "opt": svc.opterecenje(db, presa.sifra)})


@router.post("/uvoz", response_class=HTMLResponse)
def uvoz(db: Session = Depends(get_db)):
    svc.uvezi_excel(db, EXCEL_PUTANJA)
    return RedirectResponse("/planiranje/raspored", status_code=303)


@router.post("/raspored/{slug}/dodaj", response_class=HTMLResponse)
def dodaj(request: Request, slug: str, papir_naziv: str = Form(""), rn: str = Form(""),
          naklada: str = Form(""), kontakata: str = Form(""), normativ: str = Form(""),
          broj_boja: str = Form(""), format_cm: str = Form(""), rok: str = Form(""),
          priprema_min: int = Form(45), pranje_min: int = Form(15), otpad: int = Form(600),
          db: Session = Depends(get_db)):
    presa = _presa_po_slugu(db, slug)
    if presa is None:
        return RedirectResponse("/planiranje/raspored", status_code=303)
    n_int = lambda v: int(v) if str(v).strip().isdigit() else None
    s = PlanStavka(stroj_sifra=presa.sifra, redoslijed=9999, rn=rn.strip() or None,
                   papir_naziv=papir_naziv.strip() or None, format_cm=format_cm.strip() or None,
                   naklada=n_int(naklada), kontakata=n_int(kontakata), normativ=n_int(normativ),
                   broj_boja=n_int(broj_boja), otpad=otpad, priprema_min=priprema_min,
                   pranje_min=pranje_min, rok=rok.strip() or None)
    db.add(s); db.commit()
    svc.preracunaj_raspored(db, presa.sifra)
    return _tablica(request, db, presa)


_POLJA_INT = {"naklada", "kontakata", "normativ", "broj_boja", "otpad", "priprema_min", "pranje_min"}
_POLJA_STR = {"rn", "rok", "naziv", "papir_naziv", "format_cm"}


@router.post("/stavka/{sid}/uredi", response_class=HTMLResponse)
def uredi(request: Request, sid: int, polje: str = Form(""), vrijednost: str = Form(""),
          db: Session = Depends(get_db)):
    s = db.get(PlanStavka, sid)
    if s is None:
        return RedirectResponse("/planiranje/raspored", status_code=303)
    v = vrijednost.strip()
    if polje in _POLJA_INT:
        setattr(s, polje, int(v) if v.lstrip("-").isdigit() else None)
    elif polje in _POLJA_STR:
        setattr(s, polje, v or None)
    else:
        return RedirectResponse("/planiranje/raspored", status_code=303)
    db.commit()
    presa = next((p for p in svc.prese(db) if p.sifra == s.stroj_sifra), None)
    if presa:
        svc.preracunaj_raspored(db, presa.sifra)
        return _tablica(request, db, presa)
    return RedirectResponse("/planiranje/raspored", status_code=303)


@router.post("/stavka/{sid}/status", response_class=HTMLResponse)
def status(request: Request, sid: int, db: Session = Depends(get_db)):
    s = db.get(PlanStavka, sid)
    if s is None:
        return RedirectResponse("/planiranje/raspored", status_code=303)
    s.status = "plan" if s.status == "gotovo" else "gotovo"
    db.commit()
    presa = next((p for p in svc.prese(db) if p.sifra == s.stroj_sifra), None)
    return _tablica(request, db, presa) if presa else RedirectResponse("/planiranje/raspored", 303)


@router.post("/stavka/{sid}/obrisi", response_class=HTMLResponse)
def obrisi(request: Request, sid: int, db: Session = Depends(get_db)):
    s = db.get(PlanStavka, sid)
    if s is None:
        return RedirectResponse("/planiranje/raspored", status_code=303)
    presa = next((p for p in svc.prese(db) if p.sifra == s.stroj_sifra), None)
    db.delete(s); db.commit()
    if presa:
        svc.preracunaj_raspored(db, presa.sifra)
        return _tablica(request, db, presa)
    return RedirectResponse("/planiranje/raspored", status_code=303)


@router.post("/raspored/{slug}/redoslijed", response_class=HTMLResponse)
def redoslijed(request: Request, slug: str, ids: str = Form(""), db: Session = Depends(get_db)):
    presa = _presa_po_slugu(db, slug)
    if presa is None:
        return RedirectResponse("/planiranje/raspored", status_code=303)
    for i, sid in enumerate([int(x) for x in ids.split(",") if x.strip().isdigit()], 1):
        s = db.get(PlanStavka, sid)
        if s and s.stroj_sifra == presa.sifra:
            s.redoslijed = i
    db.commit()
    svc.preracunaj_raspored(db, presa.sifra)
    return _tablica(request, db, presa)
