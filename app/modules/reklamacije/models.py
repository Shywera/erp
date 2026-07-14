from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Reklamacija(Base):
    __tablename__ = "reklamacija"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    broj_predmeta: Mapped[str] = mapped_column(String(20), unique=True, index=True)

    vrsta: Mapped[str] = mapped_column(String(20), default="INTERNA", index=True)
    status: Mapped[str] = mapped_column(String(20), default="NOVO", index=True)
    prioritet: Mapped[str] = mapped_column(String(10), default="SREDNJI", index=True)
    kategorija: Mapped[str | None] = mapped_column(String(10))

    naslov: Mapped[str] = mapped_column(String(200))
    opis: Mapped[str] = mapped_column(Text)
    prijavitelj: Mapped[str] = mapped_column(String(100))

    kupac_dobavljac: Mapped[str | None] = mapped_column(String(150))
    referentni_broj: Mapped[str | None] = mapped_column(String(100))
    naziv_proizvoda: Mapped[str | None] = mapped_column(String(200))
    broj_radnog_naloga: Mapped[str | None] = mapped_column(String(100))
    stroj: Mapped[str | None] = mapped_column(String(100))
    osoblje: Mapped[str | None] = mapped_column(String(200))

    datum_prijave: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    datum_azuriranja: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    datum_zatvaranja: Mapped[datetime | None] = mapped_column(DateTime)
    rok_rjesavanja: Mapped[date | None] = mapped_column(Date)

    korekcija: Mapped[str | None] = mapped_column(Text)
    analiza_uzroka: Mapped[str | None] = mapped_column(Text)
    uzrok_kategorija: Mapped[str | None] = mapped_column(String(100))
    napomena: Mapped[str | None] = mapped_column(Text)

    vezana_nesukladnost: Mapped[str | None] = mapped_column(String(50))
    promjene_sustava: Mapped[str | None] = mapped_column(String(2))
    broj_promjene: Mapped[str | None] = mapped_column(String(50))

    capa: Mapped[list["CAPA"]] = relationship(back_populates="reklamacija",
                                               cascade="all, delete-orphan",
                                               order_by="CAPA.rok_izvrsenja")

    VRSTA = {
        "INTERNA":   "Interna nesukladnost",
        "KUPAC":     "Reklamacija kupca",
        "DOBAVLJAC": "Nesukladnost dobavljača",
    }
    STATUS = {
        "NOVO":      "Novo",
        "U_OBRADI":  "U obradi",
        "CEKA":      "Čeka dijelove/odgovor",
        "RIJESENO":  "Riješeno",
        "ZATVORENO": "Zatvoreno",
    }
    PRIORITET = {
        "NIZAK":   "Nizak",
        "SREDNJI": "Srednji",
        "VISOK":   "Visok",
        "KRITICAN": "Kritičan",
    }
    KATEGORIJA = {
        "MANJA": "Manja",
        "VECA":  "Veća",
    }

    @property
    def vrsta_display(self): return self.VRSTA.get(self.vrsta, self.vrsta)
    @property
    def status_display(self): return self.STATUS.get(self.status, self.status)
    @property
    def prioritet_display(self): return self.PRIORITET.get(self.prioritet, self.prioritet)
    @property
    def kategorija_display(self): return self.KATEGORIJA.get(self.kategorija or "", "")

    @property
    def je_zatvorena(self): return self.status in ("RIJESENO", "ZATVORENO")

    @property
    def rok_prekoracen(self):
        return bool(self.rok_rjesavanja and self.rok_rjesavanja < date.today() and not self.je_zatvorena)

    @property
    def broj_capa(self): return len(self.capa)

    @property
    def broj_otvorenih_capa(self): return sum(1 for c in self.capa if c.status != "IZVRSENA")


class CAPA(Base):
    __tablename__ = "capa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reklamacija_id: Mapped[int] = mapped_column(Integer, ForeignKey("reklamacija.id"), index=True)
    reklamacija: Mapped["Reklamacija"] = relationship(back_populates="capa")

    vrsta: Mapped[str] = mapped_column(String(20), default="KOREKTIVNA")
    opis_mjere: Mapped[str] = mapped_column(Text)
    odgovorna_osoba: Mapped[str] = mapped_column(String(100))
    rok_izvrsenja: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="PLANIRANA")
    datum_izvrsenja: Mapped[date | None] = mapped_column(Date)
    rezultat: Mapped[str | None] = mapped_column(Text)
    provjerio: Mapped[str | None] = mapped_column(String(100))
    datum_provjere: Mapped[date | None] = mapped_column(Date)

    VRSTA = {"KOREKTIVNA": "Korektivna mjera", "PREVENTIVNA": "Preventivna mjera"}
    STATUS = {
        "PLANIRANA": "Planirana",
        "U_TIJEKU":  "U tijeku",
        "IZVRSENA":  "Izvršena",
        "ODGODENA":  "Odgođena",
    }

    @property
    def vrsta_display(self): return self.VRSTA.get(self.vrsta, self.vrsta)
    @property
    def status_display(self): return self.STATUS.get(self.status, self.status)

    @property
    def je_prekoracen(self):
        return bool(self.rok_izvrsenja and self.rok_izvrsenja < date.today() and self.status != "IZVRSENA")
