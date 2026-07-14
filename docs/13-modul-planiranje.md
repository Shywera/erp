# Module: Planiranje tiska (eligibility + izračun vremena)

> **Status: Kalkulator + Raspored izgrađeni ✅** — (1) eligibility resolver + izračun vremena
> (stateless), (2) **raspored po presi** s importom Excela, ulančavanjem POČETAK→ZAVRŠETAK i
> **drag-and-drop** redoslijedom. Registriran u `main.py`, maknut iz `WIP_MODULES`, u sidebaru
> **Planiranje → Planiranje tiska**. Sljedeće: auto-planiranje (+ moguć Claude), izvoz u Excel.

## Svrha
Most između materijala/strojeva i planiranja tiska. Za **nalog** (materijal + format +
boje + naklada) vrati **dopuštene prese** i **trajanje po presi** (PRIP + RAD + PRA).
Trenutno planer to radi ručno u Excelu (`C:\Users\Tehnolog\Desktop\Planiranje\Raspored
strojevi TISAK.xls` — 3 lista = 3 prese, vrijeme se ulančava POČETAK = prethodni ZAVRŠETAK).

**Namjerno NE ovisi** o `normativi` / proizvodima / radnim nalozima (ne rade / ne postoje).
Unos naloga je ručan (kao redak Excela). Čita samo `strojevi` + `materijali`.

## Pravilo dopuštenosti (po presi)
Kandidati = aktivne prese (`Stroj.tip='tisak'`, `broj_boja` zadan → HD CD-1/CD-2/CX-104/CX-1).
Presa je dopuštena ako:
- **mjesto troška:** `stroj.sifra ∈ {materijal.mjesto_troska_1..9}` (ako materijal ima zadano; inače sve prese dolaze u obzir);
- **format:** `format ≤ max_format` stroja (uz rotaciju);
- **boje:** `broj_boja_naloga ≤ stroj.broj_boja`;
- **UV:** ako nalog treba UV → samo prese s `ima_uv` (CD);
- **lak:** ako nalog treba lak → samo prese s `ima_lak` (CX).

## Formula vremena (validirano na ~1000 stvarnih naloga iz Excela)
```
neto araka = ceil(naklada / kontakata)          # kontakata = etiketa po arku
otisaka    = neto + otpad                        # otpad = makeready araka (median ~600)
RAD (min)  = ceil((otisaka / NORMATIV) * 60 / 15) * 15   # zaokruženo gore na 15 min, min 15
SATI (min) = PRIP + RAD + PRA
```
- **NORMATIV** = brzina ar/h, ovisi o **PAPIRU** (npr. PROMET 68g=7250, MOSAICO=10000,
  PARADE PRO=9000). Ako nije zadan → fallback na `stroj.brzina_metal_arh/bijeli_arh`.
- Provjereno na RN3818/3756/3821 (CD1): otisaka i SATI se poklapaju s ručnim rasporedom.

> Napomena: u UI-u se zovu **strojevi (za tisak)**, ne „prese" (interni nazivi funkcija
> `prese()`/`presa` su samo kod). „Stroj" = HD CD-1/CD-2/CX-104/CX-1.

## Datoteke
```
app/modules/planiranje/
  service.py     # Nalog, prese(), mjesta_troska(), razlozi_nedopustenosti(), brzina_arh(),
                 # vrijeme(), planiraj(), fmt_min()  +  izracun_stavku(), preracunaj_raspored(),
                 # opterecenje(), uvezi_excel()  (raspored)
  models.py      # PlanStavka (redak rasporeda po stroju)  → migracija 16cc9cb27461
  routes.py      # kalkulator + raspored rute
app/templates/planiranje/
  planiranje.html, _rezultat.html         # kalkulator
  raspored.html, _tablica.html            # raspored po stroju (drag-and-drop)
```

## Rute
**Kalkulator:** `GET /planiranje` (forma), `POST /planiranje/izracun` (HTMX → dopušteni
strojevi s vremenom + nedopušteni s razlozima).
**Raspored:** `GET /planiranje/raspored` → prvi stroj; `GET /planiranje/raspored/{slug}`
(tabovi cd1/cd2/cx104/cx1); `POST /planiranje/uvoz` (import Excela, zamjena); `POST
/planiranje/raspored/{slug}/dodaj`; `POST /planiranje/stavka/{id}/obrisi`; `POST
/planiranje/raspored/{slug}/redoslijed` (drag-and-drop reorder → re-chain).

## Raspored po stroju (`PlanStavka`)
- **Import** postojećeg `Raspored strojevi TISAK.xls` (pandas `engine='calamine'`, 3 lista =
  3 stroja; samo redovi s numeričkim RN). Gumb „⤓ Uvezi Excel" (zamjenjuje postojeće).
- **Ulančavanje:** po stroju, redom `redoslijed`, `POČETAK = ZAVRŠETAK prethodne`
  (kontinuirano, kao Excel); `ZAVRŠETAK = POČETAK + SATI`. `preracunaj_raspored()`.
- **Drag-and-drop** (SortableJS + HTMX): povučeš red → nova lista id-eva → `redoslijed`
  ruta normalizira redoslijed i **preračuna ulančavanje**, vrati osvježenu tablicu.
- **Gotovo (žuto):** `POST /planiranje/stavka/{id}/status` toggle (✓ po retku) — završen nalog
  ostaje u planu, redak je **žut** (kao u Excelu). `PlanStavka.status` = plan|gotovo.
- **Excel-look:** gridlinije na svakoj ćeliji, svijetli header velikim slovima, sticky thead,
  gusto; stupci RN/ROK/NAZIV/PAPIR/FORMAT/NAKLADA/KONT/OTISAKA/NORM/PRIP/RAD/PRA/SATI/POČETAK/ZAVRŠETAK.
- **Inline uređivanje ćelija** (`POST /planiranje/stavka/{id}/uredi`, polje+vrijednost): ćelije
  su `<input>` (klik→upis, kao Excel). Tekst (RN/ROK/NAZIV/PAPIR/FORMAT) sprema tiho (hx-swap=none,
  fokus ostaje); broj (NAKLADA/KONT/NORM/PRIP/PRA) → **preračun + re-chain** i osvježi tablicu.
  OTISAKA/RAD/SATI/POČETAK/ZAVRŠETAK su računati (read-only, sivi).
- Dodaj/obriši nalog → auto-preračun. Sažetak: broj naloga, ukupno sati, završetak po stroju.
- NB: import postavlja `otpad=0` (otisaka = neto bez makeready-a) — SATI se uglavnom poklapaju
  (RAD često na min 15). Za točan otisaka kao u Excelu postaviti default otpad.

## Sljedeće (roadmap)
- **Auto-planiranje** — software sam raspoređuje naloge po strojevima (rokovi/opterećenje),
  moguća integracija Claudea.
- Excel-style inline upis u tablici; izvoz rasporeda natrag u Excel; po želji zaseban app (kao WMS).
