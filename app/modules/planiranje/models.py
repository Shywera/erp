from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PlanStavka(Base):
    """Jedan redak rasporeda tiska (kao redak Excela) — vezan uz presu (stroj_sifra).

    Vrijeme se ulančava po presi: POČETAK = ZAVRŠETAK prethodne stavke (redoslijed).
    otisaka/rad_min/sati_min se RAČUNAJU iz baznih unosa (naklada/kontakata/normativ/...).
    """
    __tablename__ = "plan_stavka"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stroj_sifra: Mapped[str] = mapped_column(String(30), index=True)   # presa: HD CD-1...
    redoslijed: Mapped[int] = mapped_column(Integer, default=0, index=True)

    rn: Mapped[str | None] = mapped_column(String(40))                # radni nalog
    naziv: Mapped[str | None] = mapped_column(String(255))
    papir_naziv: Mapped[str | None] = mapped_column(String(255))
    format_cm: Mapped[str | None] = mapped_column(String(40))         # "63,5x92"

    # Bazni unosi
    naklada: Mapped[int | None] = mapped_column(Integer)
    kontakata: Mapped[int | None] = mapped_column(Integer)
    broj_boja: Mapped[int | None] = mapped_column(Integer)
    normativ: Mapped[int | None] = mapped_column(Integer)             # brzina ar/h
    otpad: Mapped[int] = mapped_column(Integer, default=0)

    # Računato / vrijeme (minute)
    otisaka: Mapped[int | None] = mapped_column(Integer)
    priprema_min: Mapped[int] = mapped_column(Integer, default=0)
    rad_min: Mapped[int | None] = mapped_column(Integer)
    pranje_min: Mapped[int] = mapped_column(Integer, default=0)
    sati_min: Mapped[int | None] = mapped_column(Integer)

    # Raspored
    rok: Mapped[str | None] = mapped_column(String(40))
    pocetak: Mapped[datetime | None] = mapped_column(DateTime)
    zavrsetak: Mapped[datetime | None] = mapped_column(DateTime)

    status: Mapped[str] = mapped_column(String(20), default="plan")   # plan | gotovo
    napomena: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
