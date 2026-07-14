from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.tehnoloski_postupci.models import (
    Normativ, NormativBoja, NormativMaterijal, NormativOperacija,
)
from app.modules.materijali.models import Materijal

router = APIRouter(prefix="/tehnoloski-postupci", tags=["tehnoloski-postupci"])
templates = Jinja2Templates(directory="app/templates")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _f(v, default=None):
    if v is None or str(v).strip() == "":
        return default
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return default


def _i(v, default=None):
    if v is None or str(v).strip() == "":
        return default
    try:
        return int(float(str(v).replace(",", ".")))
    except Exception:
        return default


def _hhmm_to_min(s: str) -> int | None:
    """Parse 'hh:mm' or plain minutes string into total minutes."""
    s = str(s).strip()
    if not s:
        return None
    if ":" in s:
        parts = s.split(":")
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except Exception:
            return None
    return _i(s)


def _min_to_hhmm(minutes: int | None) -> str:
    if minutes is None:
        return ""
    h, m = divmod(int(minutes), 60)
    return f"{h:02d}:{m:02d}"


templates.env.filters["hhmm"] = _min_to_hhmm
templates.env.filters["fmtn"] = lambda n: (
    f"{int(n):,}".replace(",", ".") if n is not None else "—"
)
templates.env.filters["fmteur"] = lambda n: (
    f"{float(n):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if n is not None else "—"
)


def _get_db() -> Session:
    return next(get_db())


def _et_po_arku(form_val, stupaca, redova):
    """et_po_arku = stupaca × redova. Use explicit form value if given,
    otherwise auto-compute from stupaca and redova."""
    explicit = _i(form_val)
    if explicit is not None:
        return explicit
    if stupaca is not None and redova is not None:
        return stupaca * redova
    return None


def _zbroj(n: Normativ) -> dict:
    mat_total = sum((m.ukupno_eur or 0) for m in n.materijali)
    op_total = sum(
        (o.eur_h or 0) * ((o.norma_min or 0) / 60)
        for o in n.operacije
    )
    grand = mat_total + op_total
    per_1000 = None
    if n.serija and n.koeficijent and grand > 0:
        ukupno_kom = n.serija * n.koeficijent
        per_1000 = grand / (ukupno_kom / 1000) if ukupno_kom else None
    return {
        "mat_total": mat_total,
        "op_total": op_total,
        "grand": grand,
        "per_1000": per_1000,
    }


# ─── Autocomplete za materijale ───────────────────────────────────────────────

@router.get("/materijal-search", response_class=HTMLResponse)
def materijal_search(request: Request, q: str = ""):
    if len(q) < 2:
        return HTMLResponse("")
    db = _get_db()
    like = f"%{q}%"
    rows = db.scalars(
        select(Materijal)
        .where(or_(Materijal.naziv.ilike(like), Materijal.sifra.ilike(like)))
        .order_by(Materijal.naziv)
        .limit(12)
    ).all()
    items = "".join(
        f'<div class="px-3 py-1.5 hover:bg-blue-50 cursor-pointer text-sm border-b border-gray-100 last:border-0"'
        f' onclick="selectMat({r.id},\'{r.naziv.replace(chr(39), "")}\',\'{r.sifra or ""}\',\'{r.jedinica or ""}\',\'\')"><span class="font-mono text-xs text-gray-400">{r.sifra}</span> {r.naziv}</div>'
        for r in rows
    )
    if not items:
        items = '<div class="px-3 py-2 text-sm text-gray-400">Nema rezultata</div>'
    return HTMLResponse(
        f'<div class="absolute z-50 bg-white border border-gray-300 rounded shadow-lg max-h-60 overflow-y-auto w-full">{items}</div>'
    )


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
def tp_list(request: Request):
    return templates.TemplateResponse(request, "tehnoloski_postupci/list.html", {})


@router.get("/search", response_class=HTMLResponse)
def tp_search(request: Request, q: str = ""):
    db = _get_db()
    stmt = select(Normativ).order_by(Normativ.updated_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            Normativ.naziv.ilike(like),
            Normativ.kupac.ilike(like),
            Normativ.sifra.ilike(like),
        ))
    normatives = db.scalars(stmt).all()
    return templates.TemplateResponse(request, "tehnoloski_postupci/_table_body.html",
                                      {"normatives": normatives, "q": q})


# ─── New ──────────────────────────────────────────────────────────────────────

@router.get("/novi", response_class=HTMLResponse)
def tp_novi(request: Request):
    return templates.TemplateResponse(request, "tehnoloski_postupci/detail.html",
                                      {"n": None})


@router.post("/novi", response_class=RedirectResponse)
async def tp_spremi_novi(request: Request):
    form = await request.form()
    db = _get_db()
    stupaca = _i(form.get("stupaca"))
    redova = _i(form.get("redova"))
    n = Normativ(
        naziv=str(form.get("naziv", "")).strip() or "Bez naziva",
        sifra=str(form.get("sifra", "")).strip() or None,
        kupac=str(form.get("kupac", "")).strip() or None,
        serija=_i(form.get("serija")),
        koeficijent=_i(form.get("koeficijent")),
        arka_x=_f(form.get("arka_x")),
        arka_y=_f(form.get("arka_y")),
        podloga=str(form.get("podloga", "")).strip() or None,
        gramatura=_i(form.get("gramatura")),
        stupaca=stupaca,
        redova=redova,
        et_po_arku=_et_po_arku(form.get("et_po_arku"), stupaca, redova),
        et_xn=_f(form.get("et_xn")),
        et_yn=_f(form.get("et_yn")),
        et_xb=_f(form.get("et_xb")),
        et_yb=_f(form.get("et_yb")),
        napust=_i(form.get("napust")),
        ukupno_araka=_i(form.get("ukupno_araka")),
        broj_boja=_i(form.get("broj_boja")),
        napomena=str(form.get("napomena", "")).strip() or None,
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return RedirectResponse(f"/tehnoloski-postupci/{n.id}", status_code=303)


# ─── Detail / Edit header ─────────────────────────────────────────────────────

@router.get("/{id}", response_class=HTMLResponse)
def tp_detail(request: Request, id: int):
    db = _get_db()
    n = db.get(Normativ, id)
    if n is None:
        return HTMLResponse("Normativ nije pronađen.", status_code=404)
    return templates.TemplateResponse(request, "tehnoloski_postupci/detail.html",
                                      {"n": n, "zbroj": _zbroj(n),
                                       "boje": n.boje,
                                       "materijali": n.materijali,
                                       "operacije": n.operacije})


@router.post("/{id}/header", response_class=RedirectResponse)
async def tp_azuriraj_header(request: Request, id: int):
    db = _get_db()
    n = db.get(Normativ, id)
    if n is None:
        return RedirectResponse("/tehnoloski-postupci", status_code=303)
    form = await request.form()
    n.naziv = str(form.get("naziv", n.naziv)).strip() or n.naziv
    n.sifra = str(form.get("sifra", "")).strip() or None
    n.kupac = str(form.get("kupac", "")).strip() or None
    n.serija = _i(form.get("serija"))
    n.koeficijent = _i(form.get("koeficijent"))
    n.arka_x = _f(form.get("arka_x"))
    n.arka_y = _f(form.get("arka_y"))
    n.podloga = str(form.get("podloga", "")).strip() or None
    n.gramatura = _i(form.get("gramatura"))
    n.stupaca = _i(form.get("stupaca"))
    n.redova = _i(form.get("redova"))
    n.et_po_arku = _et_po_arku(form.get("et_po_arku"), n.stupaca, n.redova)
    n.et_xn = _f(form.get("et_xn"))
    n.et_yn = _f(form.get("et_yn"))
    n.et_xb = _f(form.get("et_xb"))
    n.et_yb = _f(form.get("et_yb"))
    n.napust = _i(form.get("napust"))
    n.ukupno_araka = _i(form.get("ukupno_araka"))
    n.broj_boja = _i(form.get("broj_boja"))
    n.napomena = str(form.get("napomena", "")).strip() or None
    db.commit()
    return RedirectResponse(f"/tehnoloski-postupci/{id}", status_code=303)


@router.post("/{id}/obrisi", response_class=HTMLResponse)
async def tp_obrisi(request: Request, id: int):
    db = _get_db()
    n = db.get(Normativ, id)
    if n:
        db.delete(n)
        db.commit()
    # HTMX (list row delete button) expects to be told where to go via a header,
    # otherwise it would swap the whole list page into a single <tr>.
    if request.headers.get("HX-Request") == "true":
        return HTMLResponse("", headers={"HX-Redirect": "/tehnoloski-postupci"})
    return RedirectResponse("/tehnoloski-postupci", status_code=303)


# ─── Boje ─────────────────────────────────────────────────────────────────────

def _render_boje(request, n):
    return templates.TemplateResponse(request, "tehnoloski_postupci/_boje.html",
                                      {"n": n, "boje": n.boje})


@router.post("/{id}/boje/dodaj", response_class=HTMLResponse)
async def boja_dodaj(request: Request, id: int):
    db = _get_db()
    n = db.get(Normativ, id)
    if not n:
        return HTMLResponse("", status_code=404)
    form = await request.form()
    red = max((b.redoslijed for b in n.boje), default=0) + 1
    db.add(NormativBoja(
        normativ_id=id,
        redoslijed=red,
        naziv_boje=str(form.get("naziv_boje", "")).strip() or "—",
        pantone_naziv=str(form.get("pantone_naziv", "")).strip() or None,
        kolicina_kg_1000=_f(form.get("kolicina_kg_1000")),
    ))
    db.commit()
    db.refresh(n)
    return _render_boje(request, n)


@router.post("/{id}/boje/{boja_id}/obrisi", response_class=HTMLResponse)
async def boja_obrisi(request: Request, id: int, boja_id: int):
    db = _get_db()
    b = db.get(NormativBoja, boja_id)
    if b and b.normativ_id == id:
        db.delete(b)
        db.commit()
    n = db.get(Normativ, id)
    return _render_boje(request, n)


# ─── Materijal ────────────────────────────────────────────────────────────────

def _render_mat(request, n):
    return templates.TemplateResponse(request, "tehnoloski_postupci/_materijali.html",
                                      {"n": n, "materijali": n.materijali})


@router.post("/{id}/materijal/dodaj", response_class=HTMLResponse)
async def mat_dodaj(request: Request, id: int):
    db = _get_db()
    n = db.get(Normativ, id)
    if not n:
        return HTMLResponse("", status_code=404)
    form = await request.form()
    kol = _f(form.get("kolicina"))
    cij = _f(form.get("cijena_eur"))
    ukupno = (kol * cij) if (kol is not None and cij is not None) else None
    red = max((m.redoslijed for m in n.materijali), default=0) + 1
    db.add(NormativMaterijal(
        normativ_id=id,
        redoslijed=red,
        materijal_id=_i(form.get("materijal_id")),
        naziv=str(form.get("naziv", "")).strip() or "—",
        sifra=str(form.get("sifra", "")).strip() or None,
        kolicina=kol,
        jedinica=str(form.get("jedinica", "")).strip() or None,
        cijena_eur=cij,
        ukupno_eur=ukupno,
    ))
    db.commit()
    db.refresh(n)
    return _render_mat(request, n)


@router.post("/{id}/materijal/{mat_id}/obrisi", response_class=HTMLResponse)
async def mat_obrisi(request: Request, id: int, mat_id: int):
    db = _get_db()
    m = db.get(NormativMaterijal, mat_id)
    if m and m.normativ_id == id:
        db.delete(m)
        db.commit()
    n = db.get(Normativ, id)
    return _render_mat(request, n)


# ─── Operacije ────────────────────────────────────────────────────────────────

def _render_op(request, n):
    zb = _zbroj(n)
    return templates.TemplateResponse(request, "tehnoloski_postupci/_operacije.html",
                                      {"n": n, "operacije": n.operacije, "zbroj": zb})


@router.post("/{id}/operacije/dodaj", response_class=HTMLResponse)
async def op_dodaj(request: Request, id: int):
    db = _get_db()
    n = db.get(Normativ, id)
    if not n:
        return HTMLResponse("", status_code=404)
    form = await request.form()
    norma = _hhmm_to_min(form.get("norma_min", ""))
    eur_h = _f(form.get("eur_h"))
    ukupno = ((eur_h * norma / 60) if (eur_h and norma) else None)
    red = max((o.redoslijed for o in n.operacije), default=0) + 1
    db.add(NormativOperacija(
        normativ_id=id,
        redoslijed=red,
        naziv_operacije=str(form.get("naziv_operacije", "")).strip() or "—",
        stroj_naziv=str(form.get("stroj_naziv", "")).strip() or None,
        stroj_alias=str(form.get("stroj_alias", "")).strip() or None,
        kolicina=_i(form.get("kolicina")),
        norma_min=norma,
        eur_h=eur_h,
        ukupno_eur=ukupno,
    ))
    db.commit()
    db.refresh(n)
    return _render_op(request, n)


@router.post("/{id}/operacije/{op_id}/obrisi", response_class=HTMLResponse)
async def op_obrisi(request: Request, id: int, op_id: int):
    db = _get_db()
    o = db.get(NormativOperacija, op_id)
    if o and o.normativ_id == id:
        db.delete(o)
        db.commit()
    n = db.get(Normativ, id)
    return _render_op(request, n)
