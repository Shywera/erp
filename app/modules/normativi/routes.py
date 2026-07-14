import base64
import io

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from app.modules.normativi.montaza_calc import (
    TIPOVI_PAPIRA, ucitaj_papire, spremi_papire,
    DEFAULT_PAPIRI, izracunaj, compute_ocjene,
    draw_montaza, export_montaza_pdf,
)
from app.modules.normativi.calc import (
    calc_layout, calc_strip_cut, calc_sc20, calc_mcs115,
    calc_stancanje, calc_tisak,
    DEFAULT_PARAMS, ucitaj_params, spremi_params,
)

router = APIRouter(prefix="/normativi", tags=["normativi"])
templates = Jinja2Templates(directory="app/templates")


def _sfmt(sec):
    sec = int(sec)
    if sec < 3600:
        return f"{sec // 60} min"
    return f"{sec // 3600}h {(sec % 3600) // 60:02d}min"


templates.env.filters["sfmt"] = _sfmt
templates.env.filters["fmtn"] = lambda n: f"{int(n):,}" if n is not None else "—"

# loaded machine params — updated in-place on save
_PARAMS: dict = ucitaj_params()

DEFAULTS = dict(
    naziv="33 export 33 cl - leđna",
    gramatura=68,
    tip_papira="metal",
    arka_x=970, arka_y=685,
    et_xn=60.0, et_yn=73.0,
    et_xb=60.0, et_yb=73.0,
    grajfer=20,
    naklada_dorada=10_000_000,
    odabir_rez="X",
    brutto_araka=72_000,
    et_u_kutiji=58_000,
    kutija_na_paleti=48,
    kutija_tip="k-26+k-27",
    paleta_tip="IND. 1200x1000",
    naklada_tisak=30_000_000,
    broj_boja=5,
    lakirano="NE",
    prolazi=1,
)

_LABELS = {
    'pregled_naloga':         'Pregled naloga (sec)',
    'priprema_robe':          'Priprema robe (sec)',
    'priprema_rm':            'Priprema radnog mjesta (sec)',
    'priprema_programa':      'Priprema programa (sec)',
    'priprema_alata':         'Priprema alata (sec)',
    'nulto_uvlacenje':        'Nulto uvlačenje (sec)',
    'strojno_uvlacenje':      'Strojno uvlačenje (sec)',
    'presanje_x':             'Prešanje po X osi (sec)',
    'presanje_y':             'Prešanje po Y osi (sec)',
    'kontrola_reza':          'Kontrola reza (sec)',
    'kontrola_svakog':        'Kontrola svakog reza (sec)',
    'obrez_1':                'Obrez 1 (sec)',
    'obrez_2':                'Obrez 2 (sec)',
    'obrez_3':                'Obrez 3 (sec)',
    'okret_4':                'Okret 4 (sec)',
    'slaganje_traka':         'Slaganje traka (sec)',
    'vibriranje':             'Vibriranje (sec)',
    'pregledavanje':          'Pregledavanje (sec)',
    'praznjenje_kante':       'Pražnjenje kante (sec)',
    'dovoz_odvoz':            'Dovoz/odvoz palete (sec)',
    'araka_paleta_metal':     'Araka/paleti — metal',
    'araka_paleta_bijeli':    'Araka/paleti — bijeli',
    'tezina_kante':           'Težina kante (kg)',
    'vrijeme_1_reza':         'Vrijeme 1 reza (sec)',
    'uvlacenje_max_traka':    'Uvlačenje max traka (sec)',
    'postavljanje_max_traka': 'Postavljanje max traka (sec)',
    'najlon':                 'Najlon (DA/NE)',
    'najlon_sec':             'Stavljanje najlona/kutiji (sec)',
    'deklariranje_sec':       'Deklariranje/kutiji (sec)',
    'pakiranje_1_bunt':       'Pakiranje 1 bunt (sec)',
    'kontrola_1_bunt':        'Kontrola 1 bunt (sec)',
    'priprema_rm_pakiranje':  'Priprema RM pakiranje (sec)',
    'broj_osoba_pakiranje':   'Broj osoba pakiranje',
    'dohvat_trake':           'Dohvat trake (sec)',
    'ulaganje_1_trake':       'Ulaganje 1 trake (sec)',
    'slaganje_kutije':        'Slaganje kutije (sec)',
    'QC_pregled':             'QC pregled (sec)',
    'priprema_ploca':         'Priprema ploča (sec)',
    'priprema_boja':          'Priprema boje (sec)',
    'priprema_laka':          'Priprema laka (sec)',
    'ovjera_QC':              'Ovjera QC (sec)',
    'provjera_povrat':        'Provjera povrata (sec)',
    'pranje_stroj':           'Pranje stroja (sec)',
    'pranje_boja':            'Pranje boje (sec)',
    'pranje_lak':             'Pranje laka (sec)',
    'ulaz_metal':             'Araka/paleti ulaz — metal',
    'ulaz_bijeli':            'Araka/paleti ulaz — bijeli',
    'izlaganje_metal':        'Araka/paleti izlaganje — metal',
    'izlaganje_bijeli':       'Araka/paleti izlaganje — bijeli',
    'prolaganje_svakih':      'Prolaganje svakih (araka)',
    'prolaganje_sec':         'Prolaganje (sec)',
    'zamjena_palete':         'Zamjena palete (sec)',
    'neispravni_prolaganje':  'Neispravni — prolaganje',
    'neispravni_gore':        'Neispravni — gore',
    'neispravni_dolje':       'Neispravni — dolje',
    'dodatak_dorada':         'Dodatak dorada',
    'dodatak_tisak':          'Dodatak tisak',
    'dodatak_fiksan':         'Dodatak fiksan (arci)',
    'dodatak_fiksan_boja':    'Dodatak fiksan/boji (arci)',
    'brzina_metal':           'Radna brzina — metal (ar/h)',
    'brzina_bijeli':          'Radna brzina — bijeli (ar/h)',
}

# Machines grouped for the parametri page
_PARAM_GROUPS = [
    ("✂ Rezanje", [
        ("POLAR_137",      "POLAR 137"),
        ("SC20_STRIP",     "SC20 — Rezanje na trake"),
        ("SC20_FINISH",    "SC20 — Na gotovo + pakiranje"),
        ("MCS_115_STRIP",  "MCS 115 — Rezanje na trake"),
        ("MCS_115_FINISH", "MCS 115 — Na gotovo + pakiranje"),
    ]),
    ("▣ Štancanje", [
        ("POLAR_DC_11",    "POLAR DC 11"),
        ("BLUMER_1110_DUAL", "BLUMER ATLAS 1110 DUAL"),
        ("BLUMER_110",     "BLUMER ATLAS 110"),
    ]),
    ("◎ Tisak", [
        ("CX_104", "CX 104 6+LX"),
        ("CX_102", "CX 102 5+LX"),
        ("CD_102", "CD 102 6+LX"),
    ]),
]


def _f(v, default=0.0):
    try:
        return float(str(v).replace(",", "."))
    except Exception:
        return default


def _i(v, default=0):
    try:
        return int(float(str(v).replace(",", ".")))
    except Exception:
        return default


def _parse(form) -> dict:
    return dict(
        naziv=str(form.get("naziv", DEFAULTS["naziv"])),
        gramatura=_i(form.get("gramatura"), DEFAULTS["gramatura"]),
        tip_papira=str(form.get("tip_papira", "metal")),
        arka_x=_f(form.get("arka_x"), DEFAULTS["arka_x"]),
        arka_y=_f(form.get("arka_y"), DEFAULTS["arka_y"]),
        et_xn=_f(form.get("et_xn"), DEFAULTS["et_xn"]),
        et_yn=_f(form.get("et_yn"), DEFAULTS["et_yn"]),
        et_xb=_f(form.get("et_xb"), DEFAULTS["et_xb"]),
        et_yb=_f(form.get("et_yb"), DEFAULTS["et_yb"]),
        grajfer=_f(form.get("grajfer"), DEFAULTS["grajfer"]),
        naklada_dorada=_i(form.get("naklada_dorada"), DEFAULTS["naklada_dorada"]),
        odabir_rez=str(form.get("odabir_rez", "X")),
        brutto_araka=_i(form.get("brutto_araka"), DEFAULTS["brutto_araka"]),
        et_u_kutiji=_i(form.get("et_u_kutiji"), DEFAULTS["et_u_kutiji"]),
        kutija_na_paleti=_i(form.get("kutija_na_paleti"), DEFAULTS["kutija_na_paleti"]),
        kutija_tip=str(form.get("kutija_tip", DEFAULTS["kutija_tip"])),
        paleta_tip=str(form.get("paleta_tip", DEFAULTS["paleta_tip"])),
        naklada_tisak=_i(form.get("naklada_tisak"), DEFAULTS["naklada_tisak"]),
        broj_boja=_i(form.get("broj_boja"), DEFAULTS["broj_boja"]),
        lakirano=str(form.get("lakirano", "NE")),
        prolazi=_i(form.get("prolazi"), DEFAULTS["prolazi"]),
    )


def _calc(p: dict) -> dict:
    P = _PARAMS
    layout = calc_layout(
        p["arka_x"], p["arka_y"], p["et_xb"], p["et_yb"], p["grajfer"],
        p["et_xn"], p["et_yn"], p["naklada_dorada"], p["brutto_araka"],
    )
    if layout["et_na_arku"] == 0:
        return {"layout": layout, "error": "Etiketa ne stane na arku — provjeri dimenzije."}

    r137 = calc_strip_cut(
        P['POLAR_137'], layout, p["gramatura"], p["tip_papira"], p["odabir_rez"], p["brutto_araka"]
    )
    sc = calc_sc20(
        layout, p["gramatura"], p["tip_papira"], p["odabir_rez"],
        p["brutto_araka"], p["naklada_dorada"], p["et_u_kutiji"], p["kutija_na_paleti"],
        p_strip=P['SC20_STRIP'], p_finish=P['SC20_FINISH'],
    )
    mcs = calc_mcs115(
        layout, p["gramatura"], p["tip_papira"], p["odabir_rez"],
        p["brutto_araka"], p["naklada_dorada"], p["et_u_kutiji"], p["kutija_na_paleti"],
        p_strip=P['MCS_115_STRIP'], p_finish=P['MCS_115_FINISH'],
    )
    stanc = [
        ("POLAR DC 11",            calc_stancanje(P['POLAR_DC_11'],       layout, p["gramatura"], p["odabir_rez"], p["brutto_araka"], p["naklada_dorada"], p["et_u_kutiji"], p["kutija_na_paleti"])),
        ("BLUMER ATLAS 1110 DUAL", calc_stancanje(P['BLUMER_1110_DUAL'],  layout, p["gramatura"], p["odabir_rez"], p["brutto_araka"], p["naklada_dorada"], p["et_u_kutiji"], p["kutija_na_paleti"])),
        ("BLUMER ATLAS 110",       calc_stancanje(P['BLUMER_110'],        layout, p["gramatura"], p["odabir_rez"], p["brutto_araka"], p["naklada_dorada"], p["et_u_kutiji"], p["kutija_na_paleti"])),
    ]
    tisak = [
        ("CX 104 6+LX", calc_tisak(P['CX_104'], layout, p["gramatura"], p["tip_papira"], p["naklada_tisak"], p["broj_boja"], p["lakirano"], p["prolazi"])),
        ("CX 102 5+LX", calc_tisak(P['CX_102'], layout, p["gramatura"], p["tip_papira"], p["naklada_tisak"], p["broj_boja"], p["lakirano"], p["prolazi"])),
        ("CD 102 6+LX", calc_tisak(P['CD_102'], layout, p["gramatura"], p["tip_papira"], p["naklada_tisak"], p["broj_boja"], p["lakirano"], p["prolazi"])),
    ]
    return {"layout": layout, "r137": r137, "sc": sc, "mcs": mcs, "stanc": stanc, "tisak": tisak, "error": None}


# ─── Kalkulator ───────────────────────────────────────────────────────────────

@router.get("/kalkulator", response_class=HTMLResponse)
def kalkulator(request: Request):
    p = DEFAULTS.copy()
    ctx = _calc(p)
    return templates.TemplateResponse(request, "normativi/kalkulator.html", {"p": p, **ctx})


@router.post("/kalkulator/izracunaj", response_class=HTMLResponse)
async def kalkulator_izracunaj(request: Request):
    form = await request.form()
    p = _parse(form)
    ctx = _calc(p)
    return templates.TemplateResponse(request, "normativi/_rezultati.html", {"p": p, **ctx})


# ─── Parametri strojeva ───────────────────────────────────────────────────────

@router.get("/parametri", response_class=HTMLResponse)
def parametri(request: Request):
    return templates.TemplateResponse(request, "normativi/parametri.html", {
        "params": _PARAMS,
        "default_params": DEFAULT_PARAMS,
        "groups": _PARAM_GROUPS,
        "labels": _LABELS,
    })


@router.post("/parametri/{key}/spremi", response_class=RedirectResponse)
async def parametri_spremi(request: Request, key: str):
    if key not in DEFAULT_PARAMS:
        return RedirectResponse("/normativi/parametri", status_code=303)
    form = await request.form()
    updated = {}
    for k, v in DEFAULT_PARAMS[key].items():
        raw = form.get(k)
        if raw is None:
            updated[k] = v
        elif isinstance(v, bool):
            updated[k] = raw in ("DA", "true", "1")
        elif isinstance(v, float):
            try:
                updated[k] = float(raw)
            except ValueError:
                updated[k] = v
        elif isinstance(v, int):
            try:
                updated[k] = int(float(raw))
            except ValueError:
                updated[k] = v
        else:
            updated[k] = str(raw)
    _PARAMS[key] = updated
    spremi_params(_PARAMS)
    return RedirectResponse("/normativi/parametri", status_code=303)


@router.post("/parametri/{key}/reset", response_class=RedirectResponse)
async def parametri_reset(request: Request, key: str):
    if key in DEFAULT_PARAMS:
        _PARAMS[key] = dict(DEFAULT_PARAMS[key])
        spremi_params(_PARAMS)
    return RedirectResponse("/normativi/parametri", status_code=303)


@router.post("/parametri/reset-sve", response_class=RedirectResponse)
async def parametri_reset_sve(request: Request):
    _PARAMS.clear()
    _PARAMS.update({k: dict(v) for k, v in DEFAULT_PARAMS.items()})
    spremi_params(_PARAMS)
    return RedirectResponse("/normativi/parametri", status_code=303)


# ─── Montaža ──────────────────────────────────────────────────────────────────

def _parse_montaza(form) -> dict:
    def fi(key, default=0):
        try:
            return int(float(str(form.get(key, default))))
        except Exception:
            return default

    try:
        k_ocjena = float(str(form.get("k_ocjena", 0.5)).replace(",", "."))
    except Exception:
        k_ocjena = 0.5

    return dict(
        tip_papira=str(form.get("tip_papira", TIPOVI_PAPIRA[0])),
        broj_etiketa=fi("broj_etiketa", 2),
        v_a=fi("v_a"), s_a=fi("s_a"),
        v_b=fi("v_b"), s_b=fi("s_b"),
        v_c=fi("v_c"), s_c=fi("s_c"),
        mg=fi("mg", 8), md=fi("md", 12),
        ml=fi("ml", 5), mdes=fi("mdes", 5),
        odmak=fi("odmak", 0),
        k_ocjena=k_ocjena,
    )


def _calc_montaza(p: dict):
    papiri = ucitaj_papire()
    filtrirani = [pp for pp in papiri if pp.get('tip') == p['tip_papira']]
    odmak = p['odmak']
    mg, md, ml, mdes = p['mg'] + odmak, p['md'] + odmak, p['ml'] + odmak, p['mdes'] + odmak
    n = p['broj_etiketa']

    rezultati, montaza_podaci = [], []
    for pp in filtrirani:
        r = izracunaj(pp, n, p['v_a'], p['s_a'], p['v_b'], p['s_b'],
                      p['v_c'], p['s_c'], mg, md, ml, mdes)
        if r and r['kompleta'] > 0:
            rezultati.append({"naziv": pp['naziv'], "papir": pp, "rezultat": r})
            montaza_podaci.append({
                "naziv": pp['naziv'], "papir": pp, "rezultat": r,
                "v_a": p['v_a'], "s_a": p['s_a'],
                "v_b": p['v_b'], "s_b": p['s_b'],
                "v_c": p['v_c'], "s_c": p['s_c'],
                "broj_etiketa": n, "mg": mg, "md": md, "ml": ml, "mdes": mdes,
            })

    if montaza_podaci:
        ocjene = compute_ocjene(montaza_podaci, p['k_ocjena'])
        for item in rezultati:
            item['ocjena'] = ocjene.get(item['naziv'], 0.0)
        rezultati.sort(key=lambda x: x['ocjena'], reverse=True)
        montaza_podaci.sort(key=lambda x: ocjene.get(x['naziv'], 0), reverse=True)

    return rezultati, montaza_podaci


def _chart_b64(d: dict) -> str:
    import matplotlib.pyplot as plt
    fig = draw_montaza(
        d['papir'], d['rezultat'],
        d['v_a'], d['s_a'], d['v_b'], d['s_b'], d['broj_etiketa'],
        d['v_c'], d['s_c'], d['mg'], d['md'], d['ml'], d['mdes'],
    )
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


@router.get("/montaza", response_class=HTMLResponse)
def montaza(request: Request):
    papiri = ucitaj_papire()
    return templates.TemplateResponse(request, "normativi/montaza.html", {
        "tipovi": TIPOVI_PAPIRA,
        "papiri": papiri,
        "rezultati": [], "montaza_podaci": [],
        "p": dict(tip_papira=TIPOVI_PAPIRA[0], broj_etiketa=2,
                  v_a=0, s_a=0, v_b=0, s_b=0, v_c=0, s_c=0,
                  mg=8, md=12, ml=5, mdes=5, odmak=0, k_ocjena=0.5),
    })


@router.post("/montaza/izracunaj", response_class=HTMLResponse)
async def montaza_izracunaj(request: Request):
    form = await request.form()
    p = _parse_montaza(form)

    greska = None
    if p['v_a'] <= 0 or p['s_a'] <= 0:
        greska = "Unesite dimenzije etikete A."
    elif p['broj_etiketa'] >= 2 and (p['v_b'] <= 0 or p['s_b'] <= 0):
        greska = "Unesite dimenzije etikete B."
    elif p['broj_etiketa'] == 3 and (p['v_c'] <= 0 or p['s_c'] <= 0):
        greska = "Unesite dimenzije etikete C."

    if greska:
        return templates.TemplateResponse(request, "normativi/_montaza_rezultati.html",
                                          {"greska": greska, "rezultati": [], "montaza_podaci": [], "p": p})

    rezultati, montaza_podaci = _calc_montaza(p)
    if not rezultati:
        greska = "Nijedna etiketa ne stane s obzirom na zadane napuste."

    return templates.TemplateResponse(request, "normativi/_montaza_rezultati.html", {
        "greska": greska, "rezultati": rezultati, "montaza_podaci": montaza_podaci, "p": p,
    })


@router.post("/montaza/chart", response_class=HTMLResponse)
async def montaza_chart(request: Request):
    form = await request.form()
    p = _parse_montaza(form)
    naziv = str(form.get("odabrani_format", ""))

    _, montaza_podaci = _calc_montaza(p)
    d = next((x for x in montaza_podaci if x['naziv'] == naziv), None)
    if not d:
        return HTMLResponse("<p class='text-gray-400 text-sm'>Format nije pronađen.</p>")

    b64 = _chart_b64(d)
    return HTMLResponse(f'<img src="data:image/png;base64,{b64}" class="max-w-full rounded-lg shadow">')


@router.post("/montaza/pdf")
async def montaza_pdf(request: Request):
    form = await request.form()
    p = _parse_montaza(form)
    naziv = str(form.get("odabrani_format", ""))

    _, montaza_podaci = _calc_montaza(p)
    d = next((x for x in montaza_podaci if x['naziv'] == naziv), None)
    if not d:
        return HTMLResponse("Format nije pronađen.", status_code=404)

    buf = export_montaza_pdf(
        d['papir'], d['rezultat'],
        d['v_a'], d['s_a'], d['v_b'], d['s_b'], d['broj_etiketa'],
        d['v_c'], d['s_c'], d['mg'], d['md'], d['ml'], d['mdes'],
    )
    safe = naziv.replace(" ", "_")
    return Response(
        content=buf.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="montaza_{safe}.pdf"'},
    )


# ─── Baza papira ──────────────────────────────────────────────────────────────

def _papiri_ctx():
    papiri = ucitaj_papire()
    grupe = {tip: [] for tip in TIPOVI_PAPIRA}
    for i, pp in enumerate(papiri):
        grupe[pp.get('tip', TIPOVI_PAPIRA[0])].append((i, pp))
    return papiri, grupe


@router.get("/montaza/papiri", response_class=HTMLResponse)
def papiri_lista(request: Request):
    papiri, grupe = _papiri_ctx()
    return templates.TemplateResponse(request, "normativi/_papiri.html",
                                      {"tipovi": TIPOVI_PAPIRA, "grupe": grupe, "papiri": papiri})


@router.post("/montaza/papiri/dodaj", response_class=HTMLResponse)
async def papiri_dodaj(request: Request):
    form = await request.form()
    tip = str(form.get("novi_tip", TIPOVI_PAPIRA[0]))
    try:
        v = int(float(str(form.get("novi_v", 0))))
        s = int(float(str(form.get("novi_s", 0))))
    except Exception:
        v = s = 0
    papiri = ucitaj_papire()
    if v > 0 and s > 0:
        papiri.append({"naziv": f"{v}x{s}", "v": v, "s": s, "tip": tip})
        spremi_papire(papiri)
    papiri, grupe = _papiri_ctx()
    return templates.TemplateResponse(request, "normativi/_papiri.html",
                                      {"tipovi": TIPOVI_PAPIRA, "grupe": grupe, "papiri": papiri})


@router.post("/montaza/papiri/{idx}/obrisi", response_class=HTMLResponse)
async def papiri_obrisi(request: Request, idx: int):
    papiri = ucitaj_papire()
    if 0 <= idx < len(papiri):
        papiri.pop(idx)
        spremi_papire(papiri)
    papiri, grupe = _papiri_ctx()
    return templates.TemplateResponse(request, "normativi/_papiri.html",
                                      {"tipovi": TIPOVI_PAPIRA, "grupe": grupe, "papiri": papiri})


@router.post("/montaza/papiri/{idx}/uredi", response_class=HTMLResponse)
async def papiri_uredi(request: Request, idx: int):
    form = await request.form()
    tip = str(form.get("tip", TIPOVI_PAPIRA[0]))
    try:
        v = int(float(str(form.get("v", 0))))
        s = int(float(str(form.get("s", 0))))
    except Exception:
        v = s = 0
    papiri = ucitaj_papire()
    if 0 <= idx < len(papiri) and v > 0 and s > 0:
        papiri[idx] = {"naziv": f"{v}x{s}", "v": v, "s": s, "tip": tip}
        spremi_papire(papiri)
    papiri, grupe = _papiri_ctx()
    return templates.TemplateResponse(request, "normativi/_papiri.html",
                                      {"tipovi": TIPOVI_PAPIRA, "grupe": grupe, "papiri": papiri})


@router.post("/montaza/papiri/reset", response_class=HTMLResponse)
async def papiri_reset(request: Request):
    papiri = [p.copy() for p in DEFAULT_PAPIRI]
    spremi_papire(papiri)
    papiri, grupe = _papiri_ctx()
    return templates.TemplateResponse(request, "normativi/_papiri.html",
                                      {"tipovi": TIPOVI_PAPIRA, "grupe": grupe, "papiri": papiri})
