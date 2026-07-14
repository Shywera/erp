from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Stroj(Base):
    __tablename__ = "stroj"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sifra: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    naziv: Mapped[str] = mapped_column(String(255), nullable=False)
    tip: Mapped[str | None] = mapped_column(String(50))
    # tisak | rezanje | stancanje | priprema | ljepljenje | ostalo
    aktivno: Mapped[bool] = mapped_column(Boolean, default=True)

    # Format
    max_format_x_mm: Mapped[float | None] = mapped_column(Float)
    max_format_y_mm: Mapped[float | None] = mapped_column(Float)
    min_format_x_mm: Mapped[float | None] = mapped_column(Float)
    min_format_y_mm: Mapped[float | None] = mapped_column(Float)

    # Tisak
    broj_boja: Mapped[int | None] = mapped_column(Integer)
    ima_lak: Mapped[bool] = mapped_column(Boolean, default=False)
    ima_uv: Mapped[bool] = mapped_column(Boolean, default=False)

    # Brzine (ar/h ili et/h ovisno o stroju)
    brzina_metal_arh: Mapped[int | None] = mapped_column(Integer)
    brzina_bijeli_arh: Mapped[int | None] = mapped_column(Integer)
    brzina_arh: Mapped[int | None] = mapped_column(Integer)

    # Operativno
    broj_osoba: Mapped[int | None] = mapped_column(Integer)
    napomena: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
