# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```powershell
# Dev server (auto-reload)
.venv\Scripts\uvicorn app.main:app --reload

# Alembic migrations
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m alembic revision --autogenerate -m "opis promjene"

# Seed strojevi (run once after first migration)
.venv\Scripts\python -m app.modules.strojevi.seed

# Import materijali from legacy ERP Excel export
.venv\Scripts\python -m app.modules.materijali.import_pauk <putanja.xlsx>

# Import partnera (Kontakti) i adresa (Adresar) iz legacy ERP Excel exporta
.venv\Scripts\python -m app.modules.kontakt.import_pauk "Resources/Kontakti(1).xlsx" "Resources/Adresar.xlsx"
```

## Legacy ERP pristup

- URL i kredencijali idu **isključivo u `.env`** (`ERP_API_URL/USER/PASS`) — nikad u kod/repo.
- **Samo čitanje** — ne mijenjati ništa u legacy sustavu.
- Legacy ERP je ASP.NET MVC app; stranice vraćaju standardni HTML, login je forma na `/Account/Login`

## Arhitektura

**Stack:** FastAPI 0.137 + SQLAlchemy 2.0 + Jinja2 + HTMX 1.9 + Alpine.js 3 + Tailwind CSS (CDN)  
**Baza:** SQLite (`dev.db`) lokalno; Postgres (`psycopg2-binary`) na produkciji via `DATABASE_URL` u `.env`  
**Nema build stepa** — Tailwind dolazi s CDN-a, nema kompajliranja asseta.

### Status modula (lipanj 2026.)

Implementirano (registrirano u `main.py`, ima rute + dokumentaciju u `docs/`):
- **materijali** — šifrarnik artikala (paginacija, povijest cijena, dobavljač autocomplete) — [docs](docs/05-modul-materijali.md)
- **strojevi** — strojevi/troškovni centri (seed) — [docs](docs/06-modul-strojevi.md)
- **normativi** — kalkulator + montaža + parametri (bez DB tablica, JSON) — [docs](docs/07-modul-normativi.md)
- **tehnoloski_postupci** — normativ kartica proizvoda — **U IZRADI** (sticky banner) — [docs](docs/08-modul-tehnoloski-postupci.md)
- **kontakt** — kupci/dobavljači + adresar (~1287 partnera iz legacy ERP) — [docs](docs/09-modul-kontakt.md)
- **pantoni** — Pantone šifrarnik — [docs](docs/10-modul-pantoni.md)
- **reklamacije** — QMS: reklamacije + CAPA + PDF/Excel — [docs](docs/11-modul-reklamacije.md)
- **planiranje** — planiranje tiska — **U IZRADI / WIP (nacrt, sticky banner)**: kalkulator
  (eligibility + izračun vremena, validiran na Excelu) + raspored po stroju (`PlanStavka`,
  import/ulančavanje/drag-drop/inline-edit). Korisnik odlučio da prava automatizacija ide kao
  **zaseban alat nad Excelom** (`Raspored strojevi TISAK.xls`), ne ovaj ERP raspored. ERP dio
  ostaje kao referenca. — [docs](docs/13-modul-planiranje.md)
- **skladiste (WMS)** — **gotovo osim go-live**: temelj + ERP adapter (mock 165 pravih
  papira, `ERP_ADAPTER=mock|pauk`), **multi-paletno zaprimanje** (plan: šifra→broj paleta→zona→
  lista pozicija→skeniraj/vrati/otkaži), **izdavanje po količini araka** (FIFO/FEFO alokacija
  cijelih paleta + ostatak), single zaprimanje/izdavanje (pod-opcije), inventura, **Prioriteti
  GUI** + prostorni modovi, **karta = tlocrt** (ulaz dolje-desno, A1 do ulaza), sve-palete lista,
  **PDF ispisi** (`pdf.py`: stanje-tlocrt = `/skladiste/stanje/pdf`, lista zaprimanja =
  `/skladiste/zaprimanje/plan/{id}/pdf`; reportlab + Arial TTF za hrvatske znakove).
  Kapacitet 1473. Sljedeće: go-live (pravi legacy ERP). — [docs](docs/12-modul-skladiste.md)

Ostalo (Prodaja, Nabava, Financije, Proizvodnja/MES) je još u `WIP_MODULES`
placeholder fazi. Procjene trajanja: `arhitektura-report.html`.

> **Dokumentaciju držati ažurnom uz kod.** Kad se modul doda/promijeni: ažuriraj njegov
> `docs/NN-modul-*.md` i ovaj status. Po-modulu doc prati format `docs/05-modul-materijali.md`.

### Struktura modula

Svaki modul prati isti pattern kao `app/modules/materijali/`:
```
app/modules/<naziv>/
    __init__.py
    models.py      # SQLAlchemy mapped_column stil (SA 2.0)
    routes.py      # APIRouter s prefix="/<naziv>"
    seed.py        # opcionalno — inicijalni podaci
```

Svaki novi modul mora biti:
1. Registriran u `app/main.py` (`app.include_router(...)`)
2. Importiran u `alembic/env.py` (`from app.modules.<naziv> import models  # noqa`)
3. Dodan u sidebar u `app/templates/base.html`
4. Maknut iz `WIP_MODULES` dict u `main.py` (dok je WIP, tamo ostaje)

### WIP moduli

`main.py` drži `WIP_MODULES` dict koji automatski registrira placeholder rute za sve module koji još nisu implementirani. Kad se modul implementira: makni ga iz dict-a, dodaj router.

### Request flow

```
Browser → FastAPI route → SQLAlchemy query → Jinja2 template → HTML response
```

HTMX search radi na svim list stranicama: `GET /<modul>/search?q=...` vraća samo `<tbody>` partial (`_table_body.html`).

## UI konvencije

- **Pozadina stranice:** `bg-gray-100`
- **Kartice:** `bg-white rounded-lg border border-gray-300 shadow-md overflow-hidden`
- **Card header:** `bg-slate-700 px-4 py-2.5` s `text-white text-xs font-bold uppercase tracking-widest`
- **Sidebar:** `bg-slate-900`, aktivna stavka `bg-blue-600 text-white`
- **Input polja:** `border border-gray-400 bg-white`, focus `ring-blue-500`
- **Table header:** `bg-slate-800 text-white text-xs uppercase tracking-wide`
- **Alternating rows:** `even:bg-gray-50 hover:bg-blue-50`

### Jinja2 macro pattern za `{% call card() %}`

`detail.html` koristi `{% call card('Naslov') %} ... {% endcall %}` — `caller()` je Jinja2 mehanizam, ne poziv funkcije. Makroi su definirani unutar samog template-a (ne u zasebnim datotekama) jer trebaju pristup `request` objektu iz globalnog konteksta.

## Domenska znanja

- Firma je tiskara samoljepljivih etiketa (metalizirani i bijeli papir)
- **Normativi** = kalkulacije vremena/brzine po stroju (ar/h, et/h). Logika je u `Arhiva skripta/Normativi/0.2/normativ_calc.py`
- Brzine tiskarskih strojeva (iz normativ_calc.py): CD 102 metal/bijeli = 9000/10000, CX 102 = 9200/10500, CX 104 = 9500/11000 ar/h
- **legacy ERP** = stari ERP sustav koji se zamjenjuje ovim projektom
- `mjesto_troska_1..9` na materijalu = strojevi/troškovni centri na kojima se taj materijal obrađuje (referenciraju `stroj.sifra`)
