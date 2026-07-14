from datetime import date, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.modules.reklamacije.models import CAPA, Reklamacija
from app.modules.reklamacije.utils import generiraj_excel, generiraj_pdf

router = APIRouter(prefix="/reklamacije", tags=["reklamacije"])
templates = Jinja2Templates(directory="app/templates")

PER_PAGE = 50

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _auto_broj(db: Session) -> str:
    godina = datetime.now().year
    prefix = f"RK-{godina}-"
    count = db.scalar(
        select(func.count(Reklamacija.id))
        .where(Reklamacija.broj_predmeta.like(f"{prefix}%"))
    ) or 0
    return f"{prefix}{count + 1:04d}"


def _parse_rek(form) -> dict:
    def s(k): return str(form.get(k, "")).strip() or None
    def d(k):
        v = str(form.get(k, "")).strip()
        try: return date.fromisoformat(v)
        except: return None

    return dict(
        vrsta=str(form.get("vrsta", "INTERNA")),
        status=str(form.get("status", "NOVO")),
        prioritet=str(form.get("prioritet", "SREDNJI")),
        kategorija=s("kategorija"),
        naslov=str(form.get("naslov", "")).strip() or "Bez naslova",
        opis=str(form.get("opis", "")).strip(),
        prijavitelj=str(form.get("prijavitelj", "")).strip(),
        kupac_dobavljac=s("kupac_dobavljac"),
        referentni_broj=s("referentni_broj"),
        naziv_proizvoda=s("naziv_proizvoda"),
        broj_radnog_naloga=s("broj_radnog_naloga"),
        stroj=s("stroj"),
        osoblje=s("osoblje"),
        rok_rjesavanja=d("rok_rjesavanja"),
        korekcija=s("korekcija"),
        analiza_uzroka=s("analiza_uzroka"),
        uzrok_kategorija=s("uzrok_kategorija"),
        napomena=s("napomena"),
        vezana_nesukladnost=s("vezana_nesukladnost"),
        promjene_sustava=s("promjene_sustava"),
        broj_promjene=s("broj_promjene"),
    )


def _load(db: Session, id: int) -> Reklamacija | None:
    return db.scalar(
        select(Reklamacija)
        .where(Reklamacija.id == id)
        .options(selectinload(Reklamacija.capa))
    )


def _ctx():
    return {
        "vrsta_choices": list(Reklamacija.VRSTA.items()),
        "status_choices": list(Reklamacija.STATUS.items()),
        "prioritet_choices": list(Reklamacija.PRIORITET.items()),
        "kategorija_choices": list(Reklamacija.KATEGORIJA.items()),
        "capa_vrsta_choices": list(CAPA.VRSTA.items()),
        "capa_status_choices": list(CAPA.STATUS.items()),
        "today": date.today(),
    }


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    ukupno       = db.scalar(select(func.count(Reklamacija.id))) or 0
    otvorene     = db.scalar(select(func.count(Reklamacija.id))
                             .where(Reklamacija.status.notin_(["RIJESENO","ZATVORENO"]))) or 0
    prekoraceni  = db.scalar(select(func.count(Reklamacija.id))
                             .where(Reklamacija.rok_rjesavanja < date.today())
                             .where(Reklamacija.status.notin_(["RIJESENO","ZATVORENO"]))) or 0
    capa_otv     = db.scalar(select(func.count(CAPA.id)).where(CAPA.status != "IZVRSENA")) or 0

    po_statusu = db.execute(
        select(Reklamacija.status, func.count(Reklamacija.id).label("n"))
        .group_by(Reklamacija.status)
    ).all()
    po_vrsti = db.execute(
        select(Reklamacija.vrsta, func.count(Reklamacija.id).label("n"))
        .group_by(Reklamacija.vrsta)
    ).all()

    zadnjih = db.scalars(
        select(Reklamacija).options(selectinload(Reklamacija.capa))
        .order_by(Reklamacija.datum_prijave.desc()).limit(10)
    ).all()
    kriticne = db.scalars(
        select(Reklamacija).where(Reklamacija.prioritet == "KRITICAN")
        .where(Reklamacija.status.notin_(["RIJESENO","ZATVORENO"]))
        .options(selectinload(Reklamacija.capa))
    ).all()

    return templates.TemplateResponse(request, "reklamacije/dashboard.html", {
        **_ctx(),
        "ukupno": ukupno, "otvorene": otvorene,
        "prekoraceni": prekoraceni, "capa_otv": capa_otv,
        "po_statusu": [(s, Reklamacija.STATUS.get(s,s), n) for s,n in po_statusu],
        "po_vrsti":   [(v, Reklamacija.VRSTA.get(v,v),  n) for v,n in po_vrsti],
        "zadnjih": zadnjih, "kriticne": kriticne,
    })


# ─── Lista ────────────────────────────────────────────────────────────────────

@router.get("/lista", response_class=HTMLResponse)
def lista(request: Request):
    return templates.TemplateResponse(request, "reklamacije/list.html", _ctx())


@router.get("/search", response_class=HTMLResponse)
def search(request: Request, q: str = "", status: str = "", vrsta: str = "",
           prioritet: str = "", page: int = 1, db: Session = Depends(get_db)):
    conds = []
    if q:
        like = f"%{q}%"
        conds.append(or_(
            Reklamacija.broj_predmeta.ilike(like),
            Reklamacija.naslov.ilike(like),
            Reklamacija.prijavitelj.ilike(like),
            Reklamacija.kupac_dobavljac.ilike(like),
            Reklamacija.naziv_proizvoda.ilike(like),
            Reklamacija.opis.ilike(like),
        ))
    if status:  conds.append(Reklamacija.status == status)
    if vrsta:   conds.append(Reklamacija.vrsta == vrsta)
    if prioritet: conds.append(Reklamacija.prioritet == prioritet)

    total = db.scalar(select(func.count(Reklamacija.id)).where(*conds)) or 0
    page  = max(1, page)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page  = min(page, total_pages)

    rows = db.scalars(
        select(Reklamacija).where(*conds)
        .options(selectinload(Reklamacija.capa))
        .order_by(Reklamacija.datum_prijave.desc())
        .offset((page-1)*PER_PAGE).limit(PER_PAGE)
    ).all()

    return templates.TemplateResponse(request, "reklamacije/_table_body.html", {
        **_ctx(), "reklamacije": rows, "q": q,
        "filter_status": status, "filter_vrsta": vrsta, "filter_prioritet": prioritet,
        "page": page, "total": total, "total_pages": total_pages, "per_page": PER_PAGE,
    })


# ─── Nova ─────────────────────────────────────────────────────────────────────

@router.get("/nova", response_class=HTMLResponse)
def nova_get(request: Request):
    return templates.TemplateResponse(request, "reklamacije/detail.html", {**_ctx(), "r": None})


@router.post("/nova", response_class=RedirectResponse)
async def nova_post(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    data = _parse_rek(form)
    r = Reklamacija(**data, broj_predmeta=_auto_broj(db))
    db.add(r); db.commit(); db.refresh(r)
    return RedirectResponse(f"/reklamacije/{r.id}", status_code=303)


# ─── Detail ───────────────────────────────────────────────────────────────────

@router.get("/{id}", response_class=HTMLResponse)
def detail(request: Request, id: int, db: Session = Depends(get_db)):
    r = _load(db, id)
    if not r: return HTMLResponse("Nije pronađeno.", status_code=404)
    return templates.TemplateResponse(request, "reklamacije/detail.html", {**_ctx(), "r": r})


@router.post("/{id}", response_class=RedirectResponse)
async def update(request: Request, id: int, db: Session = Depends(get_db)):
    r = _load(db, id)
    if not r: return RedirectResponse("/reklamacije/lista", status_code=303)
    form  = await request.form()
    data  = _parse_rek(form)
    # Auto datum zatvaranja
    if data["status"] == "ZATVORENO" and not r.datum_zatvaranja:
        r.datum_zatvaranja = datetime.now()
    elif data["status"] not in ("ZATVORENO", "RIJESENO"):
        r.datum_zatvaranja = None
    for k, v in data.items():
        setattr(r, k, v)
    db.commit()
    return RedirectResponse(f"/reklamacije/{id}", status_code=303)


@router.post("/{id}/obrisi", response_class=RedirectResponse)
async def obrisi(request: Request, id: int, db: Session = Depends(get_db)):
    r = db.get(Reklamacija, id)
    if r: db.delete(r); db.commit()
    return RedirectResponse("/reklamacije/lista", status_code=303)


# ─── CAPA ─────────────────────────────────────────────────────────────────────

def _render_capa(request, r, db):
    return templates.TemplateResponse(request, "reklamacije/_capa.html", {
        **_ctx(), "r": r,
        "capa_list": r.capa,
    })


@router.post("/{id}/capa/dodaj", response_class=HTMLResponse)
async def capa_dodaj(request: Request, id: int, db: Session = Depends(get_db)):
    r = _load(db, id)
    if not r: return HTMLResponse("", status_code=404)
    form = await request.form()
    def s(k): return str(form.get(k,"")).strip() or None
    def d(k):
        v = str(form.get(k,"")).strip()
        try: return date.fromisoformat(v)
        except: return None
    c = CAPA(
        reklamacija_id=id,
        vrsta=str(form.get("vrsta","KOREKTIVNA")),
        opis_mjere=str(form.get("opis_mjere","")).strip(),
        odgovorna_osoba=str(form.get("odgovorna_osoba","")).strip(),
        rok_izvrsenja=d("rok_izvrsenja"),
        status=str(form.get("status","PLANIRANA")),
    )
    db.add(c); db.commit()
    db.refresh(r)
    r = _load(db, id)
    return _render_capa(request, r, db)


@router.post("/{id}/capa/{capa_id}/status", response_class=HTMLResponse)
async def capa_status(request: Request, id: int, capa_id: int, db: Session = Depends(get_db)):
    c = db.get(CAPA, capa_id)
    if c and c.reklamacija_id == id:
        form = await request.form()
        c.status = str(form.get("status", c.status))
        if c.status == "IZVRSENA" and not c.datum_izvrsenja:
            c.datum_izvrsenja = date.today()
        c.rezultat = str(form.get("rezultat","")).strip() or c.rezultat
        c.provjerio = str(form.get("provjerio","")).strip() or c.provjerio
        def d(k):
            v = str(form.get(k,"")).strip()
            try: return date.fromisoformat(v)
            except: return None
        if d("datum_provjere"): c.datum_provjere = d("datum_provjere")
        db.commit()
    r = _load(db, id)
    return _render_capa(request, r, db)


@router.post("/{id}/capa/{capa_id}/obrisi", response_class=HTMLResponse)
async def capa_obrisi(request: Request, id: int, capa_id: int, db: Session = Depends(get_db)):
    c = db.get(CAPA, capa_id)
    if c and c.reklamacija_id == id:
        db.delete(c); db.commit()
    r = _load(db, id)
    return _render_capa(request, r, db)


# ─── PDF / Excel ──────────────────────────────────────────────────────────────

@router.get("/{id}/pdf")
def pdf(id: int, db: Session = Depends(get_db)):
    r = _load(db, id)
    if not r: return HTMLResponse("Nije pronađeno.", status_code=404)
    buf = generiraj_pdf(r)
    return StreamingResponse(buf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Reklamacija_{r.broj_predmeta}.pdf"'})


@router.get("/excel/izvoz")
def excel(db: Session = Depends(get_db), status: str = "", vrsta: str = ""):
    conds = []
    if status: conds.append(Reklamacija.status == status)
    if vrsta:  conds.append(Reklamacija.vrsta == vrsta)
    rows = db.scalars(
        select(Reklamacija).where(*conds)
        .options(selectinload(Reklamacija.capa))
        .order_by(Reklamacija.datum_prijave.desc())
    ).all()
    buf  = generiraj_excel(rows)
    naziv = f"Reklamacije_{date.today().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{naziv}"'})
