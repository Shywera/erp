from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.strojevi.models import Stroj

router = APIRouter(prefix="/strojevi", tags=["strojevi"])
templates = Jinja2Templates(directory="app/templates")


def _to_int(v: str | None) -> int | None:
    return int(v) if v and v.strip() else None


def _to_float(v: str | None) -> float | None:
    return float(v.replace(",", ".")) if v and v.strip() else None


def _to_str(v: str | None) -> str | None:
    return v.strip() if v and v.strip() else None


def stroj_form(
    sifra: str = Form(...),
    naziv: str = Form(...),
    tip: str = Form(""),
    aktivno: str | None = Form(None),
    max_format_x_mm: str = Form(""),
    max_format_y_mm: str = Form(""),
    min_format_x_mm: str = Form(""),
    min_format_y_mm: str = Form(""),
    broj_boja: str = Form(""),
    ima_lak: str | None = Form(None),
    ima_uv: str | None = Form(None),
    brzina_metal_arh: str = Form(""),
    brzina_bijeli_arh: str = Form(""),
    brzina_arh: str = Form(""),
    broj_osoba: str = Form(""),
    napomena: str = Form(""),
) -> dict:
    return {
        "sifra": sifra.strip(),
        "naziv": naziv.strip(),
        "tip": _to_str(tip),
        "aktivno": aktivno is not None,
        "max_format_x_mm": _to_float(max_format_x_mm),
        "max_format_y_mm": _to_float(max_format_y_mm),
        "min_format_x_mm": _to_float(min_format_x_mm),
        "min_format_y_mm": _to_float(min_format_y_mm),
        "broj_boja": _to_int(broj_boja),
        "ima_lak": ima_lak is not None,
        "ima_uv": ima_uv is not None,
        "brzina_metal_arh": _to_int(brzina_metal_arh),
        "brzina_bijeli_arh": _to_int(brzina_bijeli_arh),
        "brzina_arh": _to_int(brzina_arh),
        "broj_osoba": _to_int(broj_osoba),
        "napomena": _to_str(napomena),
    }


@router.get("", response_class=HTMLResponse)
def list_strojevi(request: Request, db: Session = Depends(get_db)):
    strojevi = db.scalars(select(Stroj).order_by(Stroj.tip, Stroj.sifra)).all()
    return templates.TemplateResponse(
        request, "strojevi/list.html", {"strojevi": strojevi}
    )


@router.get("/search", response_class=HTMLResponse)
def search_strojevi(request: Request, q: str = "", db: Session = Depends(get_db)):
    stmt = select(Stroj).order_by(Stroj.tip, Stroj.sifra)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            Stroj.sifra.ilike(like),
            Stroj.naziv.ilike(like),
            Stroj.tip.ilike(like),
            Stroj.napomena.ilike(like),
        ))
    strojevi = db.scalars(stmt).all()
    return templates.TemplateResponse(
        request, "strojevi/_table_body.html", {"strojevi": strojevi}
    )


@router.get("/novi", response_class=HTMLResponse)
def novi_form(request: Request):
    return templates.TemplateResponse(request, "strojevi/detail.html", {"s": None})


@router.post("/novi", response_class=HTMLResponse)
def create_stroj(
    request: Request,
    data: dict = Depends(stroj_form),
    db: Session = Depends(get_db),
):
    s = Stroj(**data)
    db.add(s)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "strojevi/detail.html",
            {"s": Stroj(**data), "error": f"Šifra '{data['sifra']}' već postoji."},
            status_code=409,
        )
    db.refresh(s)
    return RedirectResponse(f"/strojevi/{s.id}", status_code=303)


@router.get("/{stroj_id}", response_class=HTMLResponse)
def detail(request: Request, stroj_id: int, db: Session = Depends(get_db)):
    s = db.get(Stroj, stroj_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Stroj nije pronaden")
    return templates.TemplateResponse(request, "strojevi/detail.html", {"s": s})


@router.post("/{stroj_id}", response_class=HTMLResponse)
def update_stroj(
    request: Request,
    stroj_id: int,
    data: dict = Depends(stroj_form),
    db: Session = Depends(get_db),
):
    s = db.get(Stroj, stroj_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Stroj nije pronaden")
    for key, value in data.items():
        setattr(s, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        s = db.get(Stroj, stroj_id)
        return templates.TemplateResponse(
            request,
            "strojevi/detail.html",
            {"s": s, "error": f"Šifra '{data['sifra']}' već postoji."},
            status_code=409,
        )
    return RedirectResponse(f"/strojevi/{s.id}", status_code=303)


@router.post("/{stroj_id}/obrisi")
def obrisi_stroj(stroj_id: int, db: Session = Depends(get_db)):
    s = db.get(Stroj, stroj_id)
    if s:
        db.delete(s)
        db.commit()
    return RedirectResponse("/strojevi", status_code=303)


@router.delete("/{stroj_id}", response_class=HTMLResponse)
def delete_stroj(stroj_id: int, db: Session = Depends(get_db)):
    s = db.get(Stroj, stroj_id)
    if s:
        db.delete(s)
        db.commit()
    return HTMLResponse("")
