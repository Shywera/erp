from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Normativ(Base):
    __tablename__ = "normativ"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    naziv: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sifra: Mapped[str | None] = mapped_column(String(60))
    kupac: Mapped[str | None] = mapped_column(String(150))

    # Naklada
    serija: Mapped[int | None] = mapped_column(Integer)          # nominalna, npr. 10000
    koeficijent: Mapped[int | None] = mapped_column(Integer)     # npr. 1000 = tisuća

    # Format arka
    arka_x: Mapped[float | None] = mapped_column(Float)          # mm
    arka_y: Mapped[float | None] = mapped_column(Float)          # mm
    podloga: Mapped[str | None] = mapped_column(String(255))     # naziv podloge/papira
    gramatura: Mapped[int | None] = mapped_column(Integer)       # g/m²

    # Raspored etiketa na arku
    stupaca: Mapped[int | None] = mapped_column(Integer)
    redova: Mapped[int | None] = mapped_column(Integer)
    et_po_arku: Mapped[int | None] = mapped_column(Integer)      # stupaca × redova

    # Dimenzije etikete
    et_xn: Mapped[float | None] = mapped_column(Float)           # netto širina mm
    et_yn: Mapped[float | None] = mapped_column(Float)           # netto visina mm
    et_xb: Mapped[float | None] = mapped_column(Float)           # brutto širina mm
    et_yb: Mapped[float | None] = mapped_column(Float)           # brutto visina mm
    napust: Mapped[int | None] = mapped_column(Integer)          # napust mm

    # Količine
    ukupno_araka: Mapped[int | None] = mapped_column(Integer)
    broj_boja: Mapped[int | None] = mapped_column(Integer)

    napomena: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    boje: Mapped[list["NormativBoja"]] = relationship(
        "NormativBoja", back_populates="normativ",
        order_by="NormativBoja.redoslijed", cascade="all, delete-orphan"
    )
    materijali: Mapped[list["NormativMaterijal"]] = relationship(
        "NormativMaterijal", back_populates="normativ",
        order_by="NormativMaterijal.redoslijed", cascade="all, delete-orphan"
    )
    operacije: Mapped[list["NormativOperacija"]] = relationship(
        "NormativOperacija", back_populates="normativ",
        order_by="NormativOperacija.redoslijed", cascade="all, delete-orphan"
    )


class NormativBoja(Base):
    __tablename__ = "normativ_boja"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    normativ_id: Mapped[int] = mapped_column(Integer, ForeignKey("normativ.id"), index=True)
    redoslijed: Mapped[int] = mapped_column(Integer, default=0)
    naziv_boje: Mapped[str] = mapped_column(String(100))
    pantone_naziv: Mapped[str | None] = mapped_column(String(100))
    kolicina_kg_1000: Mapped[float | None] = mapped_column(Float)  # kg/1000 araka

    normativ: Mapped["Normativ"] = relationship("Normativ", back_populates="boje")


class NormativMaterijal(Base):
    __tablename__ = "normativ_materijal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    normativ_id: Mapped[int] = mapped_column(Integer, ForeignKey("normativ.id"), index=True)
    redoslijed: Mapped[int] = mapped_column(Integer, default=0)

    # soft link to materijal.id — no FK constraint to avoid migration complexity
    materijal_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    naziv: Mapped[str] = mapped_column(String(255))  # filled from materijal or manually
    sifra: Mapped[str | None] = mapped_column(String(60))

    kolicina: Mapped[float | None] = mapped_column(Float)
    jedinica: Mapped[str | None] = mapped_column(String(20))     # kg, m², arak, list...
    cijena_eur: Mapped[float | None] = mapped_column(Float)      # cijena/jedinici
    ukupno_eur: Mapped[float | None] = mapped_column(Float)      # kolicina × cijena

    normativ: Mapped["Normativ"] = relationship("Normativ", back_populates="materijali")


class NormativOperacija(Base):
    __tablename__ = "normativ_operacija"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    normativ_id: Mapped[int] = mapped_column(Integer, ForeignKey("normativ.id"), index=True)
    redoslijed: Mapped[int] = mapped_column(Integer, default=0)

    naziv_operacije: Mapped[str] = mapped_column(String(200))
    stroj_naziv: Mapped[str | None] = mapped_column(String(150))
    stroj_alias: Mapped[str | None] = mapped_column(String(30))

    kolicina: Mapped[int | None] = mapped_column(Integer)
    norma_min: Mapped[int | None] = mapped_column(Integer)       # trajanje u minutama
    eur_h: Mapped[float | None] = mapped_column(Float)           # cijena/satu
    ukupno_eur: Mapped[float | None] = mapped_column(Float)      # eur_h × (norma_min/60)

    normativ: Mapped["Normativ"] = relationship("Normativ", back_populates="operacije")
