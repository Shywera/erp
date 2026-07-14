"""
montaza_calc.py  —  Čiste kalkulacijske i crtačke funkcije za montažu etiketa.
Izvučeno iz Kompleti 1.1 / montaza_mix.py, bez Streamlit ovisnosti.
"""
import io
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')   # non-GUI, thread-safe
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─── Konstante ────────────────────────────────────────────────────────────────

TIPOVI_PAPIRA = ["Bijeli Pregani", "Bijeli Glatki", "Alu"]

# Mapiranje Kompleti tip → Normativi tip
TIP_NORMATIVI = {"Bijeli Pregani": "bijeli", "Bijeli Glatki": "bijeli", "Alu": "metal"}

DEFAULT_PAPIRI = [
    {"naziv": "645x950",  "v": 645, "s": 950,  "tip": "Bijeli Pregani"},
    {"naziv": "645x970",  "v": 645, "s": 970,  "tip": "Bijeli Pregani"},
    {"naziv": "660x990",  "v": 660, "s": 990,  "tip": "Bijeli Pregani"},
    {"naziv": "670x990",  "v": 670, "s": 990,  "tip": "Bijeli Pregani"},
    {"naziv": "680x940",  "v": 680, "s": 940,  "tip": "Bijeli Pregani"},
    {"naziv": "680x990",  "v": 680, "s": 990,  "tip": "Bijeli Pregani"},
    {"naziv": "690x975",  "v": 690, "s": 975,  "tip": "Bijeli Pregani"},
    {"naziv": "700x1000", "v": 700, "s": 1000, "tip": "Bijeli Pregani"},
    {"naziv": "705x930",  "v": 705, "s": 930,  "tip": "Bijeli Pregani"},
    {"naziv": "710x970",  "v": 710, "s": 970,  "tip": "Bijeli Pregani"},
    {"naziv": "720x1020", "v": 720, "s": 1020, "tip": "Bijeli Pregani"},
    {"naziv": "635x920",  "v": 635, "s": 920,  "tip": "Bijeli Glatki"},
    {"naziv": "645x970",  "v": 645, "s": 970,  "tip": "Bijeli Glatki"},
    {"naziv": "670x1000", "v": 670, "s": 1000, "tip": "Bijeli Glatki"},
    {"naziv": "700x1020", "v": 700, "s": 1020, "tip": "Bijeli Glatki"},
    {"naziv": "710x914",  "v": 710, "s": 914,  "tip": "Bijeli Glatki"},
    {"naziv": "710x960",  "v": 710, "s": 960,  "tip": "Bijeli Glatki"},
    {"naziv": "720x1020", "v": 720, "s": 1020, "tip": "Bijeli Glatki"},
    {"naziv": "645x990",  "v": 645, "s": 990,  "tip": "Alu"},
    {"naziv": "650x920",  "v": 650, "s": 920,  "tip": "Alu"},
    {"naziv": "650x960",  "v": 650, "s": 960,  "tip": "Alu"},
    {"naziv": "660x970",  "v": 660, "s": 970,  "tip": "Alu"},
    {"naziv": "670x990",  "v": 670, "s": 990,  "tip": "Alu"},
    {"naziv": "680x940",  "v": 680, "s": 940,  "tip": "Alu"},
    {"naziv": "680x950",  "v": 680, "s": 950,  "tip": "Alu"},
    {"naziv": "680x990",  "v": 680, "s": 990,  "tip": "Alu"},
    {"naziv": "685x970",  "v": 685, "s": 970,  "tip": "Alu"},
    {"naziv": "690x1000", "v": 690, "s": 1000, "tip": "Alu"},
    {"naziv": "700x1010", "v": 700, "s": 1010, "tip": "Alu"},
    {"naziv": "710x920",  "v": 710, "s": 920,  "tip": "Alu"},
    {"naziv": "710x960",  "v": 710, "s": 960,  "tip": "Alu"},
    {"naziv": "720x1000", "v": 720, "s": 1000, "tip": "Alu"},
]

# ─── Baza papira ──────────────────────────────────────────────────────────────

PAPIRI_FILE = Path(__file__).parent / "papiri.json"


def ucitaj_papire():
    if PAPIRI_FILE.exists():
        with open(PAPIRI_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # migracija: dodaj 'tip' ako nedostaje, standardiziraj naziv
        changed = False
        for p in data:
            if 'tip' not in p:
                if "Bijeli Pregani" in p.get('naziv', ''):
                    p['tip'] = "Bijeli Pregani"
                elif "Bijeli Glatki" in p.get('naziv', ''):
                    p['tip'] = "Bijeli Glatki"
                elif "Alu" in p.get('naziv', ''):
                    p['tip'] = "Alu"
                else:
                    p['tip'] = TIPOVI_PAPIRA[0]
                changed = True
            novi_naziv = f"{p['v']}x{p['s']}"
            if p['naziv'] != novi_naziv:
                p['naziv'] = novi_naziv
                changed = True
        if changed:
            spremi_papire(data)
        return data
    return [p.copy() for p in DEFAULT_PAPIRI]


def spremi_papire(papiri):
    with open(PAPIRI_FILE, "w", encoding="utf-8") as f:
        json.dump(papiri, f, ensure_ascii=False, indent=2)


# ─── Optimizacija rasporeda ───────────────────────────────────────────────────

def izracunaj_optimum_1(v_arka, s_arka, v_a, s_a, mg, md, ml, mdes):
    neto_v = v_arka - (mg + md)
    neto_s = s_arka - (ml + mdes)
    if neto_v <= 0 or neto_s <= 0:
        return None
    n_v = int(neto_v // v_a)
    n_s = int(neto_s // s_a)
    if n_v <= 0 or n_s <= 0:
        return {"kompleta": 0}
    ukupno = n_s * n_v
    skart = round(100 - (ukupno * v_a * s_a) / (v_arka * s_arka) * 100, 2)
    return {
        "kompleta": ukupno,
        "stupaca_a": n_s, "u_visinu_a": n_v, "ukupno_a": ukupno,
        "stupaca_b": 0, "u_visinu_b": 0, "ukupno_b": 0,
        "stupaca_c": 0, "u_visinu_c": 0, "ukupno_c": 0,
        "skart_postotak": skart,
    }


def izracunaj_optimum_2(v_arka, s_arka, v_a, s_a, v_b, s_b, mg, md, ml, mdes):
    neto_v = v_arka - (mg + md)
    neto_s = s_arka - (ml + mdes)
    if neto_v <= 0 or neto_s <= 0:
        return None
    n_v_a = neto_v // v_a
    n_v_b = neto_v // v_b
    max_stup_a = neto_s // s_a
    najbolji = {"kompleta": 0}
    for i in range(1, int(max_stup_a) + 1):
        preostala = neto_s - (i * s_a)
        j = preostala // s_b
        if j <= 0:
            continue
        uk_a = i * n_v_a
        uk_b = j * n_v_b
        komp = min(uk_a, uk_b)
        skart = round(100 - ((uk_a * v_a * s_a + uk_b * v_b * s_b) / (v_arka * s_arka) * 100), 2)
        if komp > najbolji.get("kompleta", -1):
            najbolji = {
                "kompleta": komp,
                "stupaca_a": i, "u_visinu_a": int(n_v_a), "ukupno_a": int(uk_a),
                "stupaca_b": int(j), "u_visinu_b": int(n_v_b), "ukupno_b": int(uk_b),
                "stupaca_c": 0, "u_visinu_c": 0, "ukupno_c": 0,
                "skart_postotak": skart,
            }
    return najbolji


def izracunaj_optimum_3(v_arka, s_arka, v_a, s_a, v_b, s_b, v_c, s_c, mg, md, ml, mdes):
    neto_v = v_arka - (mg + md)
    neto_s = s_arka - (ml + mdes)
    if neto_v <= 0 or neto_s <= 0:
        return None
    n_v_a = neto_v // v_a
    n_v_b = neto_v // v_b
    n_v_c = neto_v // v_c
    max_stup_a = neto_s // s_a
    najbolji = {"kompleta": 0}
    for i in range(1, int(max_stup_a) + 1):
        preostala_ab = neto_s - (i * s_a)
        max_stup_b = preostala_ab // s_b
        for j in range(1, int(max_stup_b) + 1):
            preostala_c = preostala_ab - (j * s_b)
            k = preostala_c // s_c
            if k <= 0:
                continue
            uk_a = i * n_v_a
            uk_b = j * n_v_b
            uk_c = k * n_v_c
            komp = min(uk_a, uk_b, uk_c)
            iskor = uk_a * v_a * s_a + uk_b * v_b * s_b + uk_c * v_c * s_c
            skart = round(100 - iskor / (v_arka * s_arka) * 100, 2)
            if komp > najbolji.get("kompleta", -1):
                najbolji = {
                    "kompleta": komp,
                    "stupaca_a": i, "u_visinu_a": int(n_v_a), "ukupno_a": int(uk_a),
                    "stupaca_b": int(j), "u_visinu_b": int(n_v_b), "ukupno_b": int(uk_b),
                    "stupaca_c": int(k), "u_visinu_c": int(n_v_c), "ukupno_c": int(uk_c),
                    "skart_postotak": skart,
                }
    return najbolji


def izracunaj(papir, broj_etiketa, v_a, s_a, v_b, s_b, v_c, s_c, mg, md, ml, mdes):
    """Dispatcher — poziva pravu funkciju ovisno o broju etiketa."""
    v, s = papir['v'], papir['s']
    if broj_etiketa == 1:
        return izracunaj_optimum_1(v, s, v_a, s_a, mg, md, ml, mdes)
    elif broj_etiketa == 2:
        return izracunaj_optimum_2(v, s, v_a, s_a, v_b, s_b, mg, md, ml, mdes)
    else:
        return izracunaj_optimum_3(v, s, v_a, s_a, v_b, s_b, v_c, s_c, mg, md, ml, mdes)


def compute_ocjene(montaza_podaci, k):
    ocjene = {}
    for d in montaza_podaci:
        r = d['rezultat']
        n = d['broj_etiketa']
        komp = r['kompleta']
        if komp <= 0:
            ocjene[d['naziv']] = 0.0
            continue
        skart_udio = r['skart_postotak'] / 100
        if n == 1:
            visak_udio = 0.0
        else:
            visakovi = (r['ukupno_a'] - komp) + (r['ukupno_b'] - komp)
            if n == 3:
                visakovi += (r['ukupno_c'] - komp)
            visak_udio = visakovi / (n * komp)
        ocjene[d['naziv']] = max(0.0, round(float(komp * (1 - k * (skart_udio + visak_udio) / 2)), 1))
    return ocjene


# ─── Grafički prikaz ──────────────────────────────────────────────────────────

D_BG     = '#0e1117'
D_SHEET  = '#1e2030'
D_MARGIN = '#13151f'
D_BORDER = '#555577'
D_TEXT   = '#e0e0e0'
COLOR_A  = '#00d26a'
COLOR_B  = '#29b6f6'
COLOR_C  = '#ffb74d'


def _crtaj_ark(ax, papir, r, v_a, s_a, v_b, s_b, broj_etiketa,
               v_c=0, s_c=0, mg=0, md=0, ml=0, mdes=0, dark=True):
    v_arka, s_arka = papir['v'], papir['s']
    bg     = D_BG    if dark else 'white'
    sheet  = D_SHEET if dark else 'white'
    margin = D_MARGIN if dark else '#d8d8d8'
    border = D_BORDER if dark else 'black'
    text   = D_TEXT  if dark else 'black'

    ax.set_facecolor(bg)
    ax.add_patch(mpatches.Rectangle((0, 0), s_arka, v_arka,
                                    facecolor=sheet, edgecolor=border, linewidth=1.5))
    for xy, w, h in [
        ((0, 0),            ml,             v_arka),
        ((s_arka - mdes, 0), mdes,          v_arka),
        ((ml, 0),            s_arka-ml-mdes, md),
        ((ml, v_arka - mg),  s_arka-ml-mdes, mg),
    ]:
        ax.add_patch(mpatches.Rectangle(xy, w, h, facecolor=margin, edgecolor='none'))

    ca, cb, cc = COLOR_A, COLOR_B, COLOR_C
    if not dark:
        ca, cb, cc = ('#555555', '////'), ('#aaaaaa', r'\\\\'), ('#222222', 'xxxx')

    def _rect(x, y, w, h, col):
        if dark:
            ax.add_patch(mpatches.Rectangle((x, y), w, h,
                                            facecolor=col, edgecolor=bg, linewidth=0.6, alpha=0.9))
        else:
            ax.add_patch(mpatches.Rectangle((x, y), w, h,
                                            facecolor=col[0], hatch=col[1],
                                            edgecolor='white', linewidth=0.5))

    for col in range(r['stupaca_a']):
        for row in range(r['u_visinu_a']):
            _rect(ml + col * s_a, md + row * v_a, s_a, v_a, ca)
    x_b = ml + r['stupaca_a'] * s_a
    for col in range(r['stupaca_b']):
        for row in range(r['u_visinu_b']):
            _rect(x_b + col * s_b, md + row * v_b, s_b, v_b, cb)
    if broj_etiketa == 3:
        x_c = x_b + r['stupaca_b'] * s_b
        for col in range(r['stupaca_c']):
            for row in range(r['u_visinu_c']):
                _rect(x_c + col * s_c, md + row * v_c, s_c, v_c, cc)

    ax.set_xlim(-5, s_arka + 5)
    ax.set_ylim(-5, v_arka + 5)
    ax.set_aspect('equal')
    ax.tick_params(colors=text)
    for spine in ax.spines.values():
        spine.set_edgecolor(border)


def draw_montaza(papir, r, v_a, s_a, v_b, s_b, broj_etiketa,
                 v_c=0, s_c=0, mg=0, md=0, ml=0, mdes=0):
    """Tamni prikaz za ekran."""
    v_arka, s_arka = papir['v'], papir['s']
    max_w, max_h = (9, 6) if broj_etiketa == 3 else (7, 5)
    ratio = v_arka / s_arka
    fw = max_w if ratio <= max_h / max_w else max_h / ratio
    fh = fw * ratio
    fig, ax = plt.subplots(figsize=(fw, fh), facecolor=D_BG)
    _crtaj_ark(ax, papir, r, v_a, s_a, v_b, s_b, broj_etiketa,
               v_c, s_c, mg, md, ml, mdes, dark=True)
    ax.set_ylabel('Visina (mm)', fontsize=10, color=D_TEXT)
    kol_label = "kom" if broj_etiketa == 1 else "kompleta"
    legend = [mpatches.Patch(facecolor=COLOR_A,
                             label=f"A: {s_a}×{v_a} mm  ({r['stupaca_a']}×{r['u_visinu_a']} = {r['ukupno_a']} kom)")]
    if broj_etiketa >= 2:
        legend.append(mpatches.Patch(facecolor=COLOR_B,
                                     label=f"B: {s_b}×{v_b} mm  ({r['stupaca_b']}×{r['u_visinu_b']} = {r['ukupno_b']} kom)"))
    if broj_etiketa == 3:
        legend.append(mpatches.Patch(facecolor=COLOR_C,
                                     label=f"C: {s_c}×{v_c} mm  ({r['stupaca_c']}×{r['u_visinu_c']} = {r['ukupno_c']} kom)"))
    legend.append(mpatches.Patch(facecolor=D_MARGIN, edgecolor=D_BORDER, label="Napust / škart"))
    ax.set_title(f"{papir['naziv']}  —  {int(r['kompleta'])} {kol_label}  |  škart {r['skart_postotak']}%",
                 fontsize=12, fontweight='bold', color=D_TEXT, pad=10)
    ax.legend(handles=legend, loc='upper center', bbox_to_anchor=(0.5, -0.08),
              ncol=len(legend), fontsize=9, facecolor=D_SHEET, edgecolor=D_BORDER,
              labelcolor=D_TEXT)
    plt.tight_layout()
    return fig


def export_montaza_pdf(papir, r, v_a, s_a, v_b, s_b, broj_etiketa,
                       v_c=0, s_c=0, mg=0, md=0, ml=0, mdes=0):
    """A4 landscape B&W PDF za print montaže."""
    v_arka, s_arka = papir['v'], papir['s']
    fig = plt.figure(figsize=(11.69, 8.27), facecolor='white')
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 2.2],
                          left=0.08, right=0.92, top=0.88, bottom=0.18, wspace=0.18)
    ax_t = fig.add_subplot(gs[0])
    ax_t.set_facecolor('#f2f2f2')
    ax_t.axis('off')
    linije = [
        "ANALIZA MONTAŽE", "─" * 28, "",
        f"Format:   {papir['naziv']}",
        f"Dim:      {v_arka} × {s_arka} mm",
        f"Napust:   G:{mg}  D:{md}  L:{ml}  Des:{mdes} mm",
        "", "─" * 28, "",
        f"Etiketa A:  {s_a} × {v_a} mm",
        f"  {r['stupaca_a']} stup. × {r['u_visinu_a']} red. = {r['ukupno_a']} kom",
    ]
    if broj_etiketa >= 2:
        linije += [
            f"  Višak: {int(r['ukupno_a'] - r['kompleta'])} kom", "",
            f"Etiketa B:  {s_b} × {v_b} mm",
            f"  {r['stupaca_b']} stup. × {r['u_visinu_b']} red. = {r['ukupno_b']} kom",
            f"  Višak: {int(r['ukupno_b'] - r['kompleta'])} kom",
        ]
    if broj_etiketa == 3:
        linije += [
            "", f"Etiketa C:  {s_c} × {v_c} mm",
            f"  {r['stupaca_c']} stup. × {r['u_visinu_c']} red. = {r['ukupno_c']} kom",
            f"  Višak: {int(r['ukupno_c'] - r['kompleta'])} kom",
        ]
    ukupno_label = "UKUPNO KOM" if broj_etiketa == 1 else "UKUPNO KOMPLETA"
    linije += ["", "─" * 28, "",
               f"{ukupno_label}:  {int(r['kompleta'])}",
               f"ŠKART:            {r['skart_postotak']}%"]
    ax_t.text(0.06, 0.96, '\n'.join(linije), transform=ax_t.transAxes,
              fontsize=9.5, verticalalignment='top', fontfamily='monospace',
              color='black', linespacing=1.5)

    ax = fig.add_subplot(gs[1])
    _crtaj_ark(ax, papir, r, v_a, s_a, v_b, s_b, broj_etiketa,
               v_c, s_c, mg, md, ml, mdes, dark=False)
    ax.set_ylabel('Visina (mm)', fontsize=9, color='black')
    bw = [('#555555', '////'), ('#aaaaaa', r'\\\\'), ('#222222', 'xxxx')]
    kol_label = "kom" if broj_etiketa == 1 else "kompleta"
    legend = [mpatches.Patch(facecolor=bw[0][0], hatch=bw[0][1], edgecolor='black',
                             label=f"A: {s_a}×{v_a} mm")]
    if broj_etiketa >= 2:
        legend.append(mpatches.Patch(facecolor=bw[1][0], hatch=bw[1][1], edgecolor='black',
                                     label=f"B: {s_b}×{v_b} mm"))
    if broj_etiketa == 3:
        legend.append(mpatches.Patch(facecolor=bw[2][0], hatch=bw[2][1], edgecolor='black',
                                     label=f"C: {s_c}×{v_c} mm"))
    legend.append(mpatches.Patch(facecolor='#d8d8d8', edgecolor='black', label="Napust"))
    ax.legend(handles=legend, loc='upper center', bbox_to_anchor=(0.5, -0.06),
              ncol=len(legend), fontsize=8, facecolor='white', edgecolor='black')
    fig.suptitle(f"{papir['naziv']}  —  {int(r['kompleta'])} {kol_label}  |  škart {r['skart_postotak']}%",
                 fontsize=13, fontweight='bold', color='black', y=0.95)
    buf = io.BytesIO()
    fig.savefig(buf, format='pdf', facecolor='white')
    plt.close(fig)
    buf.seek(0)
    return buf
