from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Kontakt(Base):
    __tablename__ = "kontakt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sifra: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    naziv: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    interni_naziv: Mapped[str | None] = mapped_column(String(255))
    naziv_dodatni: Mapped[str | None] = mapped_column(String(255))

    # dobavljac | kupac | oba | ostalo
    tip: Mapped[str] = mapped_column(String(20), default="dobavljac", index=True)
    grupa: Mapped[str | None] = mapped_column(String(100))

    # Identifikacija
    oib: Mapped[str | None] = mapped_column(String(20))
    maticni_broj: Mapped[str | None] = mapped_column(String(20))

    # Lokacija
    adresa: Mapped[str | None] = mapped_column(String(255))
    postanski_broj: Mapped[str | None] = mapped_column(String(10))
    mjesto: Mapped[str | None] = mapped_column(String(100))
    drzava: Mapped[str | None] = mapped_column(String(60), default="Hrvatska")

    # Kontakt podaci
    telefon: Mapped[str | None] = mapped_column(String(50))
    mobitel: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(150))
    web: Mapped[str | None] = mapped_column(String(150))
    referent: Mapped[str | None] = mapped_column(String(150))

    # Nabavni uvjeti
    valuta_placanja_dan: Mapped[int | None] = mapped_column(Integer)
    radno_vrijeme: Mapped[str | None] = mapped_column(String(100))
    hbor_osiguranje: Mapped[bool] = mapped_column(Boolean, default=False)
    hbor_rok_placanja_dan: Mapped[int | None] = mapped_column(Integer)

    napomena: Mapped[str | None] = mapped_column(Text)
    aktivan: Mapped[bool] = mapped_column(Boolean, default=True)

    adrese: Mapped[list["Adresar"]] = relationship(
        back_populates="kontakt", cascade="all, delete-orphan",
        order_by="Adresar.naziv_pj",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    TIP_LABEL = {
        "dobavljac": "Dobavljač",
        "kupac": "Kupac",
        "oba": "Kupac i dobavljač",
        "ostalo": "Ostalo",
    }

    @property
    def tip_display(self):
        return self.TIP_LABEL.get(self.tip, self.tip)


class Adresar(Base):
    """Poslovne jedinice / adrese partnera (legacy ERP: Adresar). Više po kontaktu."""
    __tablename__ = "adresar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kontakt_id: Mapped[int | None] = mapped_column(ForeignKey("kontakt.id"), index=True)
    kontakt: Mapped["Kontakt | None"] = relationship(back_populates="adrese")

    # Sirovi naziv partnera iz legacy ERP (za matching pri uvozu kad veza nije nadena)
    partner_naziv: Mapped[str | None] = mapped_column(String(255), index=True)

    naziv_pj: Mapped[str | None] = mapped_column(String(255))  # naziv poslovne jedinice
    drzava: Mapped[str | None] = mapped_column(String(80))
    zupanija: Mapped[str | None] = mapped_column(String(120))
    opcina: Mapped[str | None] = mapped_column(String(120))
    grad: Mapped[str | None] = mapped_column(String(120))
    adresa: Mapped[str | None] = mapped_column(Text)
    kilometri: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
