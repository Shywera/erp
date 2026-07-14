from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MaterijalPapirData(BaseModel):
    tip_papira: str | None = None
    gramatura_g_m2: float | None = None
    sirina_mm: float | None = None
    duljina_role_m: float | None = None
    format_arka_x_mm: float | None = None
    format_arka_y_mm: float | None = None


class MaterijalEtiketaData(BaseModel):
    kupac_id: int | None = None
    papir_materijal_id: int | None = None
    format_netto_x_mm: float | None = None
    format_netto_y_mm: float | None = None
    format_brutto_x_mm: float | None = None
    format_brutto_y_mm: float | None = None
    etiketa_u_kutiji: int | None = None
    kutija_tip: str | None = None
    paleta_tip: str | None = None
    kutija_na_paleti: int | None = None


class MaterijalBase(BaseModel):
    sifra: str
    sipo_sifra: str | None = None
    naziv: str
    jedinica: str
    kategorija: str | None = None
    tip: str | None = None
    grupa: str | None = None
    podgrupa: str | None = None
    aktivno: bool = True
    minimalna_kolicina: float | None = None
    dobavljac_id: int | None = None
    napomena: str | None = None


class MaterijalCreate(MaterijalBase):
    papir: MaterijalPapirData | None = None
    etiketa: MaterijalEtiketaData | None = None


class MaterijalRead(MaterijalBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    updated_by: str | None = None
    papir: MaterijalPapirData | None = None
    etiketa: MaterijalEtiketaData | None = None


class CijenaPovijestCreate(BaseModel):
    dobavljac_id: int | None = None
    cijena: float
    valuta: str = "EUR"
    datum_vazenja: date
    napomena: str | None = None


class CijenaPovijestRead(CijenaPovijestCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    materijal_id: int
