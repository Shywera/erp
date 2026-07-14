from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Materijal(Base):
    __tablename__ = "materijal"

    id: Mapped[int] = mapped_column(primary_key=True)
    sifra: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    sipo_sifra: Mapped[str | None] = mapped_column(String(50))
    naziv: Mapped[str] = mapped_column(String(255), index=True)
    jedinica: Mapped[str] = mapped_column(String(20))

    kategorija: Mapped[str | None] = mapped_column(String(100))
    tip: Mapped[str | None] = mapped_column(String(100))
    grupa: Mapped[str | None] = mapped_column(String(100))
    podgrupa: Mapped[str | None] = mapped_column(String(100))
    podgrupa2: Mapped[str | None] = mapped_column(String(100))
    podgrupa3: Mapped[str | None] = mapped_column(String(100))
    podgrupa4: Mapped[str | None] = mapped_column(String(100))

    aktivno: Mapped[bool] = mapped_column(Boolean, default=True)
    minimalna_kolicina: Mapped[float | None] = mapped_column(Numeric(12, 3))
    minimalno_pakiranje: Mapped[float | None] = mapped_column(Numeric(12, 3))

    # No FK constraint yet - kontakt (Kupci/Dobavljaci) module doesn't exist yet.
    dobavljac_id: Mapped[int | None] = mapped_column(Integer)
    # Supplier name as text, from legacy ERP import - until kontakt module + matching exists.
    dobavljac_naziv: Mapped[str | None] = mapped_column(String(255))

    tarifni_broj: Mapped[str | None] = mapped_column(String(50))
    zemlja_porijekla: Mapped[str | None] = mapped_column(String(100))
    rok_trajanja: Mapped[str | None] = mapped_column(String(50))
    rok_trajanja_godina: Mapped[float | None] = mapped_column(Numeric(5, 2))
    rok_dobavljivosti: Mapped[int | None] = mapped_column(Integer)

    # Skladiste/WMS - placeholders carried over from legacy ERP import, populated later by WMS modul.
    lokacija_skladiste: Mapped[str | None] = mapped_column(String(100))
    pozicija: Mapped[str | None] = mapped_column(String(100))
    ulazno_skladiste_1: Mapped[str | None] = mapped_column(String(100))
    ulazno_skladiste_2: Mapped[str | None] = mapped_column(String(100))
    prijelazno_skladiste_1: Mapped[str | None] = mapped_column(String(100))
    prijelazno_skladiste_2: Mapped[str | None] = mapped_column(String(100))
    prijelazno_skladiste_3: Mapped[str | None] = mapped_column(String(100))

    # Mjesta troska (strojevi) - placeholders carried over from legacy ERP import, populated later by Strojevi modul.
    mjesto_troska_1: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_2: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_3: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_4: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_5: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_6: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_7: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_8: Mapped[str | None] = mapped_column(String(50))
    mjesto_troska_9: Mapped[str | None] = mapped_column(String(50))

    datoteke: Mapped[str | None] = mapped_column(Text)
    napomena: Mapped[str | None] = mapped_column(Text)

    # Dimenzije i tehnicka svojstva (legacy ERP: Radius, Thickness, Length, Width, Height,
    # Surface, Volumen, ConvU1U2, Quality, BoxesOnPaletteZ, Weight, Variant, Liter)
    promjer_mm: Mapped[float | None] = mapped_column(Numeric(10, 3))
    debljina_um: Mapped[float | None] = mapped_column(Numeric(10, 3))
    duljina_mm: Mapped[float | None] = mapped_column(Numeric(10, 2))
    sirina_mm: Mapped[float | None] = mapped_column(Numeric(10, 2))
    visina_mm: Mapped[float | None] = mapped_column(Numeric(10, 2))
    povrsina_mm2: Mapped[float | None] = mapped_column(Numeric(14, 2))
    volumen_mm3: Mapped[float | None] = mapped_column(Numeric(16, 2))
    gramatura_g_m2: Mapped[float | None] = mapped_column(Numeric(8, 2))
    kvaliteta: Mapped[str | None] = mapped_column(String(100))
    kutija_na_paleti_z: Mapped[float | None] = mapped_column(Numeric(10, 2))
    tezina_kg: Mapped[float | None] = mapped_column(Numeric(10, 3))
    hilzna: Mapped[str | None] = mapped_column(String(50))
    litraza: Mapped[float | None] = mapped_column(Numeric(10, 3))

    # Opis / napomene (legacy ERP: Other, Description, DescriptionEng, Remark, DoradaRemark, Signature)
    tehnicki_naziv: Mapped[str | None] = mapped_column(String(255))
    raspored: Mapped[str | None] = mapped_column(String(255))
    opis_en: Mapped[str | None] = mapped_column(Text)
    posebna_napomena: Mapped[str | None] = mapped_column(Text)
    napomena_dorada: Mapped[str | None] = mapped_column(Text)
    oznaka: Mapped[str | None] = mapped_column(String(100))

    # Proizvodnja / tisak (legacy ERP: Technique, DoradaType, Complet, Drawing, System,
    # Namotaj, SubSurface, BasePaper, Material)
    tehnika: Mapped[str | None] = mapped_column(String(100))
    tip_dorade: Mapped[str | None] = mapped_column(String(100))
    komplet: Mapped[str | None] = mapped_column(String(100))
    nacrt: Mapped[str | None] = mapped_column(String(100))
    sistem: Mapped[str | None] = mapped_column(String(100))
    namotaj: Mapped[str | None] = mapped_column(String(100))
    podloga: Mapped[str | None] = mapped_column(String(100))
    bazni_papir: Mapped[str | None] = mapped_column(String(100))
    materijal_tisak: Mapped[str | None] = mapped_column(String(100))

    # Boja / tisak (legacy ERP: Color, ColorId/PantoneId, Coated, Foil, Lugootporno, Food,
    # OneComponentTwoComponent, LightStability, Certificates)
    boja: Mapped[str | None] = mapped_column(String(100))
    pantone_id: Mapped[int | None] = mapped_column(ForeignKey("pantone.id"))
    coated: Mapped[bool | None] = mapped_column(Boolean)
    folija: Mapped[bool | None] = mapped_column(Boolean)
    lugootporno: Mapped[str | None] = mapped_column(String(50))
    prehrana: Mapped[str | None] = mapped_column(String(50))
    jednokomp_dvokomp: Mapped[str | None] = mapped_column(String(50))
    svjetlostabilnost: Mapped[str | None] = mapped_column(String(50))
    certifikati: Mapped[str | None] = mapped_column(String(255))

    # Ostalo (legacy ERP: InventoryNumber, Ura, ProductionNumber, JunkKeyNumber)
    inventarni_broj: Mapped[str | None] = mapped_column(String(100))
    ura: Mapped[str | None] = mapped_column(String(50))
    proizvodni_broj: Mapped[str | None] = mapped_column(String(100))
    kljucni_broj_otpada: Mapped[str | None] = mapped_column(String(50))

    # legacy ERP checkboxes: QrNotNeeded, IsMsExcluded
    qr_nije_potreban: Mapped[bool] = mapped_column(Boolean, default=False)
    zabranjeno_medjuskladiste: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    updated_by: Mapped[str | None] = mapped_column(String(100))

    papir: Mapped["MaterijalPapir | None"] = relationship(
        back_populates="materijal", uselist=False, cascade="all, delete-orphan"
    )
    etiketa: Mapped["MaterijalEtiketa | None"] = relationship(
        back_populates="materijal",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="MaterijalEtiketa.materijal_id",
    )
    cijene: Mapped[list["CijenaPovijest"]] = relationship(
        back_populates="materijal", cascade="all, delete-orphan"
    )
    pantone: Mapped["Pantone | None"] = relationship()


class Pantone(Base):
    __tablename__ = "pantone"

    id: Mapped[int] = mapped_column(primary_key=True)
    kod: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    naziv: Mapped[str | None] = mapped_column(String(100))
    hex_boja: Mapped[str | None] = mapped_column(String(7))


class MaterijalPapir(Base):
    __tablename__ = "materijal_papir"

    materijal_id: Mapped[int] = mapped_column(
        ForeignKey("materijal.id"), primary_key=True
    )
    tip_papira: Mapped[str | None] = mapped_column(String(50))
    gramatura_g_m2: Mapped[float | None] = mapped_column(Numeric(8, 2))
    sirina_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    duljina_role_m: Mapped[float | None] = mapped_column(Numeric(8, 2))
    format_arka_x_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    format_arka_y_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))

    materijal: Mapped["Materijal"] = relationship(back_populates="papir")


class MaterijalEtiketa(Base):
    __tablename__ = "materijal_etiketa"

    materijal_id: Mapped[int] = mapped_column(
        ForeignKey("materijal.id"), primary_key=True
    )
    # No FK constraint yet - kontakt module doesn't exist yet.
    kupac_id: Mapped[int | None] = mapped_column(Integer)
    papir_materijal_id: Mapped[int | None] = mapped_column(ForeignKey("materijal.id"))

    format_netto_x_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    format_netto_y_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    format_brutto_x_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))
    format_brutto_y_mm: Mapped[float | None] = mapped_column(Numeric(8, 2))

    etiketa_u_kutiji: Mapped[int | None] = mapped_column(Integer)
    kutija_tip: Mapped[str | None] = mapped_column(String(100))
    paleta_tip: Mapped[str | None] = mapped_column(String(100))
    kutija_na_paleti: Mapped[int | None] = mapped_column(Integer)

    materijal: Mapped["Materijal"] = relationship(
        back_populates="etiketa", foreign_keys=[materijal_id]
    )
    papir_materijal: Mapped["Materijal | None"] = relationship(
        foreign_keys=[papir_materijal_id]
    )


class CijenaPovijest(Base):
    __tablename__ = "cijena_povijest"

    id: Mapped[int] = mapped_column(primary_key=True)
    materijal_id: Mapped[int] = mapped_column(ForeignKey("materijal.id"), index=True)
    # No FK constraint yet - kontakt module doesn't exist yet.
    dobavljac_id: Mapped[int | None] = mapped_column(Integer)

    cijena: Mapped[float] = mapped_column(Numeric(10, 4))
    valuta: Mapped[str] = mapped_column(String(3), default="EUR")
    datum_vazenja: Mapped[date] = mapped_column(Date)
    napomena: Mapped[str | None] = mapped_column(Text)

    materijal: Mapped["Materijal"] = relationship(back_populates="cijene")
