from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.materijali.models import Pantone

router = APIRouter(prefix="/pantoni", tags=["pantoni"])
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def list_pantoni(request: Request, db: Session = Depends(get_db)):
    pantoni = db.scalars(select(Pantone).order_by(Pantone.kod)).all()
    return templates.TemplateResponse(request, "pantoni/list.html", {"pantoni": pantoni})


@router.post("")
def create_pantone(
    kod: str = Form(...),
    naziv: str = Form(""),
    hex_boja: str = Form(""),
    db: Session = Depends(get_db),
):
    p = Pantone(
        kod=kod.strip(),
        naziv=naziv.strip() or None,
        hex_boja=hex_boja.strip() or None,
    )
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        # kod ima unique constraint — duplikat se tiho ignorira
        db.rollback()
    return RedirectResponse("/pantoni", status_code=303)


@router.post("/{pantone_id}/obrisi")
def delete_pantone(pantone_id: int, db: Session = Depends(get_db)):
    p = db.get(Pantone, pantone_id)
    if p:
        db.delete(p)
        db.commit()
    return RedirectResponse("/pantoni", status_code=303)
