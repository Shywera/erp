from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.modules.materijali.routes import router as materijali_router
from app.modules.strojevi.routes import router as strojevi_router
from app.modules.normativi.routes import router as normativi_router
from app.modules.tehnoloski_postupci.routes import router as tp_router
from app.modules.kontakt.routes import router as kontakt_router
from app.modules.reklamacije.routes import router as reklamacije_router
from app.modules.pantoni.routes import router as pantoni_router
from app.modules.skladiste.routes import router as skladiste_router
from app.modules.planiranje.routes import router as planiranje_router

app = FastAPI(title="ERP/MES/WMS")
app.include_router(materijali_router)
app.include_router(strojevi_router)
app.include_router(normativi_router)
app.include_router(tp_router)
app.include_router(kontakt_router)
app.include_router(reklamacije_router)
app.include_router(pantoni_router)
app.include_router(skladiste_router)
app.include_router(planiranje_router)

_templates = Jinja2Templates(directory="app/templates")

# WMS (skladiste) je prebačen u zaseban vanjski app — ostaje VIDLJIV u izborniku, ali su sve
# njegove rute ZAKLJUČANE (klik vrati lock stranicu). Kod skladiste modula ostaje netaknut.
@app.middleware("http")
async def _zakljucaj_skladiste(request: Request, call_next):
    p = request.url.path
    if p == "/skladiste" or p.startswith("/skladiste/"):
        return _templates.TemplateResponse(request, "zakljucano.html", {}, status_code=423)
    return await call_next(request)


WIP_MODULES = {
    # Matični podaci
    # "kupci" — implemented
    # "tehnoloski-postupci" — implemented, removed from WIP
    # Planiranje
    "planiranje-nabave":    "Planiranje nabave iz proizvodnje",
    # "planiranje" — implemented (eligibility + izračun vremena)
    # Prodaja
    "kalkulacije":          "Upit / Kalkulacije / Sifrarnik",
    "ponude":               "Ponude",
    "narudzbe":             "Narudzbe",
    "analiza-prodaje":      "Analiza prodaje",
    "knjiga-izvoza":        "Knjiga izvoza",
    # Nabava
    "primke":               "Primke i meduskladisnice",
    "ulazni-racuni":        "Ulazni racuni",
    "analiza-nabave":       "Analiza nabave",
    "knjiga-uvoza":         "Knjiga uvoza",
    # Financije
    "otpremnice":           "Otpremnice",
    "izlazni-racuni":       "Izlazni racuni",
    "racuni":               "Racuni",
    "proforma":             "Proforma",
    # Skladiste
    # "skladiste" — implemented (WMS modul, Faza 1)
    "inventura":            "Inventura",
    "tjedne-usklade":       "Tjedne usklade",
    # Proizvodnja / MES
    "radni-nalozi":         "Radni nalozi",
    "dnevnici-rada":        "Dnevnici rada",
    "efikasnost":           "Efikasnost radnika",
    "odrzavanje":           "Odrzavanje",
}


def _wip_handler(naziv: str):
    def handler(request: Request):
        return _templates.TemplateResponse(request, "placeholder.html", {"naziv": naziv})
    return handler


for _slug, _naziv in WIP_MODULES.items():
    app.add_api_route(f"/{_slug}", _wip_handler(_naziv), response_class=HTMLResponse)


@app.get("/")
def root():
    return RedirectResponse("/materijali")
