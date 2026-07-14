# ERP / MES / WMS — modularni sustav za tiskarsku proizvodnju

Modularni poslovno-proizvodni sustav građen za tiskaru samoljepljivih etiketa.
Svaki modul je samostalna cjelina (modeli + rute + predlošci) registrirana u
zajedničku FastAPI aplikaciju, s Alembic migracijama i dokumentacijom po modulu.

## Moduli

| Modul | Opis | Status |
|---|---|---|
| **materijali** | šifrarnik artikala, povijest cijena, dobavljači | ✅ |
| **strojevi** | strojevi / troškovni centri | ✅ |
| **normativi** | kalkulator vremena i brzina proizvodnje + montaža | ✅ |
| **kontakt** | kupci/dobavljači + adresar (~1300 partnera) | ✅ |
| **pantoni** | Pantone šifrarnik | ✅ |
| **reklamacije** | QMS: reklamacije + CAPA + PDF/Excel | ✅ |
| **skladiste (WMS)** | paletno skladište: zaprimanje, izdavanje, karta, PDF | ✅ |
| **tehnoloski postupci** | normativ kartica proizvoda | 🔨 u izradi |
| **planiranje** | planiranje tiska po strojevima | 🔨 nacrt |
| prodaja · nabava · financije · MES | placeholderi | 📋 plan |

Dokumentacija svakog modula: [`docs/`](docs/) — pregled domene, katalog naslijeđenih
alata koje sustav zamjenjuje, otvorene odluke i po-modulska dokumentacija.

## Tehnologije

FastAPI · SQLAlchemy 2.0 · Alembic · SQLite/PostgreSQL · Jinja2 · HTMX · Alpine.js · Tailwind CSS · reportlab

## Brzi start (Windows)

```bat
instalacija.bat     REM jednom: okruženje + ovisnosti + migracije
pokreni.bat         REM start na http://localhost:8000
```

Integracija s naslijeđenim ERP-om ide preko **read-only adaptera** (`ERP_ADAPTER=mock|erp`);
kredencijali se drže isključivo u `.env`. Repozitorij sadrži demo podatke.

## Povezani projekti

Samostalne izvedbe pojedinih modula:
[WMS](https://github.com/Shywera/wms) · [Reklamacije/QMS](https://github.com/Shywera/reklamacije) ·
[Ponude](https://github.com/Shywera/Ponude) · [Normativi i montaža](https://github.com/Shywera/normativ-montaza) ·
[Alati](https://github.com/Shywera/tools)
