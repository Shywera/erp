from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.materijali.models import Materijal

router = APIRouter(prefix="/materijali", tags=["materijali"])
templates = Jinja2Templates(directory="app/templates")


def _to_float(value: str | None) -> float | None:
    if value is None or value.strip() == "":
        return None
    return float(value.replace(",", "."))


def _to_int(value: str | None) -> int | None:
    if value is None or value.strip() == "":
        return None
    return int(value)


def _to_str(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value.strip()


def materijal_form(
    sifra: str = Form(...),
    naziv: str = Form(...),
    jedinica: str = Form(...),
    aktivno: str | None = Form(None),
    sipo_sifra: str = Form(""),
    kategorija: str = Form(""),
    tip: str = Form(""),
    grupa: str = Form(""),
    podgrupa: str = Form(""),
    podgrupa2: str = Form(""),
    podgrupa3: str = Form(""),
    podgrupa4: str = Form(""),
    minimalna_kolicina: str = Form(""),
    minimalno_pakiranje: str = Form(""),
    dobavljac_id: str = Form(""),
    dobavljac_naziv: str = Form(""),
    tarifni_broj: str = Form(""),
    zemlja_porijekla: str = Form(""),
    rok_trajanja: str = Form(""),
    rok_trajanja_godina: str = Form(""),
    rok_dobavljivosti: str = Form(""),
    lokacija_skladiste: str = Form(""),
    pozicija: str = Form(""),
    ulazno_skladiste_1: str = Form(""),
    ulazno_skladiste_2: str = Form(""),
    prijelazno_skladiste_1: str = Form(""),
    prijelazno_skladiste_2: str = Form(""),
    prijelazno_skladiste_3: str = Form(""),
    mjesto_troska_1: str = Form(""),
    mjesto_troska_2: str = Form(""),
    mjesto_troska_3: str = Form(""),
    mjesto_troska_4: str = Form(""),
    mjesto_troska_5: str = Form(""),
    mjesto_troska_6: str = Form(""),
    mjesto_troska_7: str = Form(""),
    mjesto_troska_8: str = Form(""),
    mjesto_troska_9: str = Form(""),
    napomena: str = Form(""),
    datoteke: str = Form(""),
    # Dimenzije i tehnicka svojstva
    promjer_mm: str = Form(""),
    debljina_um: str = Form(""),
    duljina_mm: str = Form(""),
    sirina_mm: str = Form(""),
    visina_mm: str = Form(""),
    povrsina_mm2: str = Form(""),
    volumen_mm3: str = Form(""),
    gramatura_g_m2: str = Form(""),
    kvaliteta: str = Form(""),
    kutija_na_paleti_z: str = Form(""),
    tezina_kg: str = Form(""),
    hilzna: str = Form(""),
    litraza: str = Form(""),
    # Opis i napomene
    tehnicki_naziv: str = Form(""),
    raspored: str = Form(""),
    opis_en: str = Form(""),
    posebna_napomena: str = Form(""),
    napomena_dorada: str = Form(""),
    oznaka: str = Form(""),
    # Proizvodnja / tisak
    tehnika: str = Form(""),
    tip_dorade: str = Form(""),
    komplet: str = Form(""),
    nacrt: str = Form(""),
    sistem: str = Form(""),
    namotaj: str = Form(""),
    podloga: str = Form(""),
    bazni_papir: str = Form(""),
    materijal_tisak: str = Form(""),
    # Boja / tisak
    boja: str = Form(""),
    pantone_id: str = Form(""),
    coated: str | None = Form(None),
    folija: str | None = Form(None),
    lugootporno: str = Form(""),
    prehrana: str = Form(""),
    jednokomp_dvokomp: str = Form(""),
    svjetlostabilnost: str = Form(""),
    certifikati: str = Form(""),
    # Ostalo
    inventarni_broj: str = Form(""),
    ura: str = Form(""),
    proizvodni_broj: str = Form(""),
    kljucni_broj_otpada: str = Form(""),
    qr_nije_potreban: str | None = Form(None),
    zabranjeno_medjuskladiste: str | None = Form(None),
) -> dict:
    return {
        "sifra": sifra.strip(),
        "naziv": naziv.strip(),
        "jedinica": jedinica.strip(),
        "aktivno": aktivno is not None,
        "sipo_sifra": _to_str(sipo_sifra),
        "kategorija": _to_str(kategorija),
        "tip": _to_str(tip),
        "grupa": _to_str(grupa),
        "podgrupa": _to_str(podgrupa),
        "podgrupa2": _to_str(podgrupa2),
        "podgrupa3": _to_str(podgrupa3),
        "podgrupa4": _to_str(podgrupa4),
        "minimalna_kolicina": _to_float(minimalna_kolicina),
        "minimalno_pakiranje": _to_float(minimalno_pakiranje),
        "dobavljac_id": int(dobavljac_id) if dobavljac_id.strip().isdigit() else None,
        "dobavljac_naziv": _to_str(dobavljac_naziv),
        "tarifni_broj": _to_str(tarifni_broj),
        "zemlja_porijekla": _to_str(zemlja_porijekla),
        "rok_trajanja": _to_str(rok_trajanja),
        "rok_trajanja_godina": _to_float(rok_trajanja_godina),
        "rok_dobavljivosti": _to_int(rok_dobavljivosti),
        "lokacija_skladiste": _to_str(lokacija_skladiste),
        "pozicija": _to_str(pozicija),
        "ulazno_skladiste_1": _to_str(ulazno_skladiste_1),
        "ulazno_skladiste_2": _to_str(ulazno_skladiste_2),
        "prijelazno_skladiste_1": _to_str(prijelazno_skladiste_1),
        "prijelazno_skladiste_2": _to_str(prijelazno_skladiste_2),
        "prijelazno_skladiste_3": _to_str(prijelazno_skladiste_3),
        "mjesto_troska_1": _to_str(mjesto_troska_1),
        "mjesto_troska_2": _to_str(mjesto_troska_2),
        "mjesto_troska_3": _to_str(mjesto_troska_3),
        "mjesto_troska_4": _to_str(mjesto_troska_4),
        "mjesto_troska_5": _to_str(mjesto_troska_5),
        "mjesto_troska_6": _to_str(mjesto_troska_6),
        "mjesto_troska_7": _to_str(mjesto_troska_7),
        "mjesto_troska_8": _to_str(mjesto_troska_8),
        "mjesto_troska_9": _to_str(mjesto_troska_9),
        "napomena": _to_str(napomena),
        "datoteke": _to_str(datoteke),
        "promjer_mm": _to_float(promjer_mm),
        "debljina_um": _to_float(debljina_um),
        "duljina_mm": _to_float(duljina_mm),
        "sirina_mm": _to_float(sirina_mm),
        "visina_mm": _to_float(visina_mm),
        "povrsina_mm2": _to_float(povrsina_mm2),
        "volumen_mm3": _to_float(volumen_mm3),
        "gramatura_g_m2": _to_float(gramatura_g_m2),
        "kvaliteta": _to_str(kvaliteta),
        "kutija_na_paleti_z": _to_float(kutija_na_paleti_z),
        "tezina_kg": _to_float(tezina_kg),
        "hilzna": _to_str(hilzna),
        "litraza": _to_float(litraza),
        "tehnicki_naziv": _to_str(tehnicki_naziv),
        "raspored": _to_str(raspored),
        "opis_en": _to_str(opis_en),
        "posebna_napomena": _to_str(posebna_napomena),
        "napomena_dorada": _to_str(napomena_dorada),
        "oznaka": _to_str(oznaka),
        "tehnika": _to_str(tehnika),
        "tip_dorade": _to_str(tip_dorade),
        "komplet": _to_str(komplet),
        "nacrt": _to_str(nacrt),
        "sistem": _to_str(sistem),
        "namotaj": _to_str(namotaj),
        "podloga": _to_str(podloga),
        "bazni_papir": _to_str(bazni_papir),
        "materijal_tisak": _to_str(materijal_tisak),
        "boja": _to_str(boja),
        "pantone_id": _to_int(pantone_id),
        "coated": coated is not None,
        "folija": folija is not None,
        "lugootporno": _to_str(lugootporno),
        "prehrana": _to_str(prehrana),
        "jednokomp_dvokomp": _to_str(jednokomp_dvokomp),
        "svjetlostabilnost": _to_str(svjetlostabilnost),
        "certifikati": _to_str(certifikati),
        "inventarni_broj": _to_str(inventarni_broj),
        "ura": _to_str(ura),
        "proizvodni_broj": _to_str(proizvodni_broj),
        "kljucni_broj_otpada": _to_str(kljucni_broj_otpada),
        "qr_nije_potreban": qr_nije_potreban is not None,
        "zabranjeno_medjuskladiste": zabranjeno_medjuskladiste is not None,
    }


PER_PAGE = 100


@router.get("", response_class=HTMLResponse)
def list_materijali(request: Request):
    return templates.TemplateResponse(request, "materijali/list.html", {})


@router.get("/search", response_class=HTMLResponse)
def search_materijali(request: Request, q: str = "", page: int = 1, db: Session = Depends(get_db)):
    conditions = []
    if q:
        like = f"%{q}%"
        conditions.append(or_(
            Materijal.sifra.ilike(like),
            Materijal.naziv.ilike(like),
            Materijal.dobavljac_naziv.ilike(like),
            Materijal.sipo_sifra.ilike(like),
            Materijal.tehnicki_naziv.ilike(like),
            Materijal.kategorija.ilike(like),
            Materijal.tip.ilike(like),
            Materijal.grupa.ilike(like),
            Materijal.podgrupa.ilike(like),
            Materijal.zemlja_porijekla.ilike(like),
            Materijal.tarifni_broj.ilike(like),
            Materijal.boja.ilike(like),
            Materijal.oznaka.ilike(like),
        ))

    total = db.scalar(select(func.count(Materijal.id)).where(*conditions))
    page = max(1, page)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(page, total_pages)

    materijali = db.scalars(
        select(Materijal).where(*conditions)
        .order_by(Materijal.sifra)
        .offset((page - 1) * PER_PAGE)
        .limit(PER_PAGE)
    ).all()

    return templates.TemplateResponse(
        request, "materijali/_table_body.html", {
            "materijali": materijali,
            "q": q,
            "page": page,
            "total": total,
            "total_pages": total_pages,
            "per_page": PER_PAGE,
        }
    )


@router.get("/novi", response_class=HTMLResponse)
def novi_form(request: Request):
    return templates.TemplateResponse(request, "materijali/detail.html", {"m": None})


@router.post("/novi", response_class=HTMLResponse)
def create_materijal(
    request: Request,
    data: dict = Depends(materijal_form),
    db: Session = Depends(get_db),
):
    m = Materijal(**data)
    db.add(m)
    db.commit()
    db.refresh(m)
    return RedirectResponse(f"/materijali/{m.id}", status_code=303)


@router.get("/{materijal_id}", response_class=HTMLResponse)
def detail(request: Request, materijal_id: int, db: Session = Depends(get_db)):
    m = db.get(Materijal, materijal_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Materijal nije pronaden")
    return templates.TemplateResponse(request, "materijali/detail.html", {"m": m})


@router.post("/{materijal_id}", response_class=HTMLResponse)
def update_materijal(
    request: Request,
    materijal_id: int,
    data: dict = Depends(materijal_form),
    db: Session = Depends(get_db),
):
    m = db.get(Materijal, materijal_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Materijal nije pronaden")
    for key, value in data.items():
        setattr(m, key, value)
    db.commit()
    return RedirectResponse(f"/materijali/{m.id}", status_code=303)


@router.post("/{materijal_id}/obrisi")
def obrisi_materijal(materijal_id: int, db: Session = Depends(get_db)):
    m = db.get(Materijal, materijal_id)
    if m:
        db.delete(m)
        db.commit()
    return RedirectResponse("/materijali", status_code=303)


@router.delete("/{materijal_id}", response_class=HTMLResponse)
def delete_materijal(materijal_id: int, db: Session = Depends(get_db)):
    m = db.get(Materijal, materijal_id)
    if m:
        db.delete(m)
        db.commit()
    return HTMLResponse("")
