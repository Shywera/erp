import json

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import escape
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.modules.kontakt.models import Adresar, Kontakt


def _js_attr(value) -> str:
    """Safely embed a string as a JS string literal inside an HTML attribute.

    json.dumps produces a valid double-quoted JS literal (escapes quotes,
    backslashes, control chars); markupsafe.escape then makes it safe for the
    surrounding onclick="..." attribute context.
    """
    return str(escape(json.dumps("" if value is None else str(value))))

router = APIRouter(prefix="/kupci", tags=["kontakt"])
templates = Jinja2Templates(directory="app/templates")

TIPOVI = ["dobavljac", "kupac", "oba", "ostalo"]
TIP_LABEL = {
    "dobavljac": "Dobavljač",
    "kupac": "Kupac",
    "oba": "Kupac i dobavljač",
    "ostalo": "Ostalo",
}


def _db() -> Session:
    return next(get_db())


def _parse(form) -> dict:
    def s(k, default=""):
        v = str(form.get(k, default)).strip()
        return v or None

    def i(k):
        try:
            return int(str(form.get(k, "")).strip())
        except Exception:
            return None

    return dict(
        sifra=s("sifra") or "",
        naziv=s("naziv") or "Bez naziva",
        interni_naziv=s("interni_naziv"),
        naziv_dodatni=s("naziv_dodatni"),
        tip=str(form.get("tip", "dobavljac")),
        grupa=s("grupa"),
        oib=s("oib"),
        maticni_broj=s("maticni_broj"),
        adresa=s("adresa"),
        postanski_broj=s("postanski_broj"),
        mjesto=s("mjesto"),
        drzava=s("drzava") or "Hrvatska",
        telefon=s("telefon"),
        mobitel=s("mobitel"),
        email=s("email"),
        web=s("web"),
        referent=s("referent"),
        valuta_placanja_dan=i("valuta_placanja_dan"),
        radno_vrijeme=s("radno_vrijeme"),
        hbor_osiguranje="hbor_osiguranje" in form,
        hbor_rok_placanja_dan=i("hbor_rok_placanja_dan"),
        napomena=s("napomena"),
        aktivan="aktivan" in form,
    )


# ─── Autocomplete (za Materijal i druge module) ───────────────────────────────

@router.get("/autocomplete", response_class=HTMLResponse)
def autocomplete(request: Request, q: str = "", tip: str = ""):
    if len(q) < 2:
        return HTMLResponse("")
    db = _db()
    stmt = select(Kontakt).where(Kontakt.aktivan == True)
    if tip:
        stmt = stmt.where(or_(Kontakt.tip == tip, Kontakt.tip == "oba"))
    like = f"%{q}%"
    stmt = stmt.where(or_(
        Kontakt.naziv.ilike(like),
        Kontakt.sifra.ilike(like),
        Kontakt.mjesto.ilike(like),
    )).order_by(Kontakt.naziv).limit(12)
    rows = db.scalars(stmt).all()

    if not rows:
        return HTMLResponse(
            '<div class="absolute z-50 bg-white border border-gray-300 rounded shadow-lg w-full">'
            '<div class="px-3 py-2 text-sm text-gray-400">Nema rezultata</div></div>'
        )

    items = ""
    for r in rows:
        badge = f'<span class="text-[10px] px-1 py-0.5 rounded bg-slate-100 text-slate-500 ml-1">{escape(TIP_LABEL.get(r.tip, r.tip))}</span>'
        city = f' <span class="text-gray-400">· {escape(r.mjesto)}</span>' if r.mjesto else ""
        onclick = f"kontaktSelect({r.id},{_js_attr(r.naziv)},{_js_attr(r.sifra)})"
        items += (
            f'<div class="px-3 py-1.5 hover:bg-blue-50 cursor-pointer text-sm border-b border-gray-100 last:border-0"'
            f' onclick="{onclick}">'
            f'<span class="font-mono text-xs text-gray-400 mr-1">{escape(r.sifra)}</span>'
            f'{escape(r.naziv)}{city}{badge}</div>'
        )
    return HTMLResponse(
        f'<div class="absolute z-50 bg-white border border-gray-300 rounded shadow-lg max-h-64 overflow-y-auto w-full">{items}</div>'
    )


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
def kupci_list(request: Request, tip: str = ""):
    return templates.TemplateResponse(request, "kontakt/list.html",
                                      {"tipovi": TIPOVI, "tip_label": TIP_LABEL, "filter_tip": tip})


@router.get("/search", response_class=HTMLResponse)
def kupci_search(request: Request, q: str = "", tip: str = ""):
    db = _db()
    stmt = select(Kontakt).order_by(Kontakt.naziv)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            Kontakt.naziv.ilike(like),
            Kontakt.sifra.ilike(like),
            Kontakt.mjesto.ilike(like),
            Kontakt.oib.ilike(like),
        ))
    if tip:
        stmt = stmt.where(or_(Kontakt.tip == tip, Kontakt.tip == "oba"))
    kontakti = db.scalars(stmt).all()
    return templates.TemplateResponse(request, "kontakt/_table_body.html",
                                      {"kontakti": kontakti, "q": q, "tip_label": TIP_LABEL})


# ─── New ──────────────────────────────────────────────────────────────────────

@router.get("/novi", response_class=HTMLResponse)
def kupci_novi(request: Request):
    return templates.TemplateResponse(request, "kontakt/detail.html",
                                      {"k": None, "tipovi": TIPOVI, "tip_label": TIP_LABEL})


@router.post("/novi", response_class=RedirectResponse)
async def kupci_spremi_novi(request: Request):
    form = await request.form()
    data = _parse(form)
    db = _db()
    # auto-sifra ako nije upisana
    if not data["sifra"]:
        last = db.scalar(select(Kontakt.id).order_by(Kontakt.id.desc())) or 0
        data["sifra"] = f"K{last + 1:04d}"
    k = Kontakt(**data)
    db.add(k)
    db.commit()
    db.refresh(k)
    return RedirectResponse(f"/kupci/{k.id}", status_code=303)


# ─── Detail / Edit ────────────────────────────────────────────────────────────

@router.get("/{id}", response_class=HTMLResponse)
def kupci_detail(request: Request, id: int):
    db = _db()
    k = db.scalar(
        select(Kontakt).where(Kontakt.id == id).options(selectinload(Kontakt.adrese))
    )
    if k is None:
        return HTMLResponse("Kontakt nije pronađen.", status_code=404)
    return templates.TemplateResponse(request, "kontakt/detail.html",
                                      {"k": k, "tipovi": TIPOVI, "tip_label": TIP_LABEL})


@router.post("/{id}", response_class=RedirectResponse)
async def kupci_azuriraj(request: Request, id: int):
    db = _db()
    k = db.get(Kontakt, id)
    if k is None:
        return RedirectResponse("/kupci", status_code=303)
    form = await request.form()
    data = _parse(form)
    if not data["sifra"]:
        data["sifra"] = k.sifra
    for key, val in data.items():
        setattr(k, key, val)
    db.commit()
    return RedirectResponse(f"/kupci/{id}", status_code=303)


@router.post("/{id}/obrisi", response_class=RedirectResponse)
async def kupci_obrisi(request: Request, id: int):
    db = _db()
    k = db.get(Kontakt, id)
    if k:
        db.delete(k)
        db.commit()
    return RedirectResponse("/kupci", status_code=303)


# ─── Adresar (poslovne jedinice partnera) ─────────────────────────────────────

def _render_adresar(request, db, kontakt_id):
    k = db.scalar(
        select(Kontakt).where(Kontakt.id == kontakt_id).options(selectinload(Kontakt.adrese))
    )
    return templates.TemplateResponse(request, "kontakt/_adresar.html", {"k": k})


def _parse_adresa(form) -> dict:
    def s(k):
        v = str(form.get(k, "")).strip()
        return v or None

    def f(k):
        v = str(form.get(k, "")).strip().replace(",", ".")
        try:
            return float(v)
        except Exception:
            return None

    return dict(
        naziv_pj=s("naziv_pj"),
        drzava=s("drzava"),
        zupanija=s("zupanija"),
        opcina=s("opcina"),
        grad=s("grad"),
        adresa=s("adresa"),
        kilometri=f("kilometri"),
    )


@router.post("/{id}/adresar/dodaj", response_class=HTMLResponse)
async def adresar_dodaj(request: Request, id: int):
    db = _db()
    k = db.get(Kontakt, id)
    if k is None:
        return HTMLResponse("", status_code=404)
    form = await request.form()
    data = _parse_adresa(form)
    a = Adresar(kontakt_id=id, partner_naziv=k.naziv, **data)
    db.add(a)
    db.commit()
    return _render_adresar(request, db, id)


@router.post("/{id}/adresar/{adresa_id}/obrisi", response_class=HTMLResponse)
async def adresar_obrisi(request: Request, id: int, adresa_id: int):
    db = _db()
    a = db.get(Adresar, adresa_id)
    if a and a.kontakt_id == id:
        db.delete(a)
        db.commit()
    return _render_adresar(request, db, id)
