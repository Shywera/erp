"""
normativ_calc.py  —  Čiste kalkulacijske funkcije (bez Streamlit-a)
Vjeran prijevod Excel formula iz 'normativ rada na rezacim strojevima 2025.xlsx'
"""
import math


# ─── Helper: Excel-style rounding ─────────────────────────────────────────────

def _rounddown(x, dec):
    """ROUNDDOWN(x, dec)  — dec < 0 zaokružuje lijevo od decimalne točke"""
    if dec < 0:
        f = 10 ** (-dec)
        return math.floor(x / f) * f
    f = 10 ** dec
    return math.floor(x * f) / f


def _round(x, dec):
    if dec < 0:
        f = 10 ** (-dec)
        return round(x / f) * f
    f = 10 ** dec
    return round(x * f) / f


# ─── Layout (zajednički za sve strojeve) ──────────────────────────────────────

def calc_layout(arka_x, arka_y, et_xb, et_yb, grajfer, et_xn, et_yn,
                naklada_dorada, brutto_araka):
    """
    Izračunava raspored etiketa na arku i marginalne mjere.
    Ulaz:  sve dimenzije u mm, naklade u komadima.
    Izlaz: rječnik sa svim layout vrijednostima.
    """
    et_po_x    = int(arka_x / et_xb) if et_xb > 0 else 0
    et_po_y    = int(arka_y / et_yb) if et_yb > 0 else 0
    et_na_arku = et_po_x * et_po_y

    bocno_desno  = (arka_x - et_po_x * et_xb) / 2
    bocno_lijevo = bocno_desno
    gornji_napust = arka_y - et_po_y * et_yb - grajfer

    netto_araka = math.ceil(naklada_dorada / et_na_arku) if et_na_arku > 0 else 0

    return dict(
        et_po_x=et_po_x, et_po_y=et_po_y, et_na_arku=et_na_arku,
        bocno_desno=bocno_desno, bocno_lijevo=bocno_lijevo,
        gornji_napust=gornji_napust, netto_araka=netto_araka,
        # proslijeđene dimenzije (za ostale funkcije)
        arka_x=arka_x, arka_y=arka_y,
        et_xb=et_xb, et_yb=et_yb,
        et_xn=et_xn, et_yn=et_yn,
        grajfer=grajfer,
    )


# ─── Parametri strojeva ───────────────────────────────────────────────────────

# Zajednička baza za strojeve strip-rezanja (POLAR 137 i SC20 share-aju gotovo sve)
_BASE_STRIP = dict(
    pregled_naloga=60,
    priprema_robe=420,           # 240+120+60
    presanje_x=45, presanje_y=60,
    kontrola_reza=5, kontrola_svakog=15,  # 3*5
    obrez_1=35, obrez_2=30, obrez_3=30, okret_4=20,
    slaganje_traka=8,
    praznjenje_kante=200, dovoz_odvoz=120,
    araka_paleta_metal=10000, araka_paleta_bijeli=14000,
    vibriranje=240, pregledavanje=60,
)

POLAR_137 = {**_BASE_STRIP,
             'priprema_rm': 120, 'priprema_programa': 60,
             'nulto_uvlacenje': 80, 'strojno_uvlacenje': 60,
             'vrijeme_1_reza': 5,
             'tezina_kante': 17}

SC20_STRIP = {**_BASE_STRIP,
              'priprema_rm': 120, 'priprema_programa': 60,
              'nulto_uvlacenje': 80, 'strojno_uvlacenje': 60,
              'vrijeme_1_reza': 5,
              'tezina_kante': 30}   # jedina razlika od POLAR 137

MCS_115_STRIP = {**_BASE_STRIP,
                 'priprema_rm': 180, 'priprema_programa': 600,
                 'nulto_uvlacenje': 80, 'strojno_uvlacenje': 20,
                 'presanje_x': 35, 'presanje_y': 45,
                 'obrez_1': 20, 'obrez_2': 20, 'obrez_3': 20, 'okret_4': 20,
                 'vrijeme_1_reza': 8,
                 'slaganje_traka': 10,
                 'tezina_kante': 25, 'praznjenje_kante': 180}

# Finish-cut parametri (SC20 i MCS 115 su identični osim gdje je navedeno)
_BASE_FINISH = dict(
    pregled_naloga=60, priprema_robe=420, priprema_rm=120,
    uvlacenje_max_traka=60, kontrola_reza=5, kontrola_svakog=15,
    vrijeme_1_reza=7, postavljanje_max_traka=80,
    praznjenje_kante=200, dovoz_odvoz=120,
    najlon='DA', najlon_sec=10, deklariranje_sec=10,
    pakiranje_1_bunt=3, kontrola_1_bunt=2,
    priprema_rm_pakiranje=480,
)

SC20_FINISH  = {**_BASE_FINISH, 'tezina_kante': 30, 'broj_osoba_pakiranje': 2}
MCS_115_FINISH = {**_BASE_FINISH, 'tezina_kante': 25, 'praznjenje_kante': 180,
                  'kontrola_reza': 10, 'vrijeme_1_reza': 5,
                  'broj_osoba_pakiranje': 1}

# Štancanje strojevi
_BASE_STANC = dict(
    pregled_naloga=60, priprema_robe=420, priprema_rm=120,
    priprema_programa=60, priprema_alata=600,
    nulto_uvlacenje=180, dohvat_trake=10,
    ulaganje_1_trake=6, slaganje_kutije=10,
    vrijeme_1_reza=5,
    QC_pregled=5,
    praznjenje_kante=200, dovoz_odvoz=120,
)

POLAR_DC_11        = {**_BASE_STANC, 'tezina_kante': 15}
BLUMER_1110_DUAL   = {**_BASE_STANC, 'tezina_kante': 20}
BLUMER_110         = {**_BASE_STANC,
                      'ulaganje_1_trake': 8,
                      'vrijeme_1_reza': 6,
                      'tezina_kante': 15, 'praznjenje_kante': 260}

# Tisak strojevi (svi share-aju iste parametre osim radne brzine)
_BASE_PRINT = dict(
    # priprema
    priprema_ploca=900, priprema_boja=480, priprema_laka=1200,
    ovjera_QC=420, provjera_povrat=480,
    # pranje
    pranje_stroj=600, pranje_boja=300, pranje_lak=1800,
    # arci na paleti
    ulaz_metal=13000, ulaz_bijeli=14000,
    izlaganje_metal=9000, izlaganje_bijeli=14000,
    # prolaganje
    prolaganje_svakih=3000, prolaganje_sec=120,
    zamjena_palete=180,
    neispravni_prolaganje=25, neispravni_gore=5, neispravni_dolje=15,
    # dodaci na naklade
    dodatak_dorada=0.01, dodatak_tisak=0.01,
    dodatak_fiksan=200, dodatak_fiksan_boja=40,
)

CX_104 = {**_BASE_PRINT, 'brzina_metal': 9500, 'brzina_bijeli': 11000}
CX_102 = {**_BASE_PRINT, 'brzina_metal': 9200, 'brzina_bijeli': 10500}
CD_102 = {**_BASE_PRINT, 'brzina_metal': 9000, 'brzina_bijeli': 10000}


# ─── Dorada: strip-cut (POLAR 137, SC20, MCS 115) ─────────────────────────────

def _kg_otpad_trake(gramatura, arka_x, arka_y, grajfer, gornji_napust,
                    bocno_desno, bocno_lijevo):
    """Kg otpada pri rezanju na trake na 1.000 araka."""
    # Formula: =(1000*(gram/1000)*(ax/1000)*((grajfer+g_napust)/1000))
    #          +(1000*((ay-grajfer+g_napust)/1000)*(gram/1000)*((bocno_d+bocno_l)/1000))
    return (
        1000 * (gramatura/1000) * (arka_x/1000) * ((grajfer + gornji_napust)/1000) +
        1000 * ((arka_y - grajfer + gornji_napust)/1000) *
               (gramatura/1000) * ((bocno_desno + bocno_lijevo)/1000)
    )


def calc_strip_cut(P, layout, gramatura, tip_papira, odabir_rez, brutto_araka):
    """
    Normativ rezanja na trake.
    P          : POLAR_137, SC20_STRIP ili MCS_115_STRIP
    Vraća dict s normativom i međuvrijednostima.
    """
    et_po_x = layout['et_po_x']
    et_po_y = layout['et_po_y']

    # Broj rezova ovisi o smjeru
    broj_rezova = et_po_x if odabir_rez == 'X' else et_po_y

    # Otpad
    kg_otpad = _kg_otpad_trake(
        gramatura, layout['arka_x'], layout['arka_y'],
        layout['grajfer'], layout['gornji_napust'],
        layout['bocno_desno'], layout['bocno_lijevo'],
    )
    ukupno_otpada = brutto_araka / 1000 * kg_otpad
    broj_kanti    = int(ukupno_otpada / P['tezina_kante']) if P['tezina_kante'] > 0 else 0

    if tip_papira == 'metal':
        broj_paleta = math.ceil(brutto_araka / P['araka_paleta_metal'])
    else:
        broj_paleta = math.ceil(brutto_araka / P['araka_paleta_bijeli'])

    # Priprema: =SUM(D27:D35)+SUM(D37:D40)+(D36*D48)+(D48*D42)
    priprema = (
        P['pregled_naloga'] + P['priprema_robe'] + P['priprema_rm'] + P['priprema_programa'] +
        P['nulto_uvlacenje'] + P['strojno_uvlacenje'] +
        P['presanje_x'] + P['presanje_y'] + P['kontrola_reza'] +
        P['obrez_1'] + P['obrez_2'] + P['obrez_3'] + P['okret_4'] +
        P['kontrola_svakog'] * broj_rezova +
        broj_rezova * P['slaganje_traka']
    )

    # Ukupno 1.000 araka: =D33+D34+(D36*D48)+D42+D32+(D48*D41)
    ukupno_1000 = (
        P['presanje_x'] + P['presanje_y'] +
        P['kontrola_svakog'] * broj_rezova +
        P['slaganje_traka'] +
        P['strojno_uvlacenje'] +
        broj_rezova * P['vrijeme_1_reza']
    )

    ponavljanja    = int(math.ceil(brutto_araka / 1000))
    uk_rezanje     = ponavljanja * ukupno_1000
    t_praznjenje   = broj_kanti  * P['praznjenje_kante']
    t_transport    = 2 * broj_paleta * P['dovoz_odvoz']   # dovoz + odvoz
    total          = uk_rezanje + t_praznjenje + t_transport

    # Vibriranje
    vib_total  = ponavljanja * (P['vibriranje'] + P['pregledavanje'])
    korekcija  = max(total, vib_total)

    # Normativ (ar/h, korigirano za pauzu 0,5h)
    if korekcija > 0:
        normativ_arh = _rounddown(brutto_araka / (korekcija / 3600), -2)
    else:
        normativ_arh = 0
    normativ_7h   = normativ_arh * 7
    normativ_final = normativ_7h / 7.5          # ← normativ za kalkulaciju

    return dict(
        broj_rezova=broj_rezova,
        kg_otpad=round(kg_otpad, 2),
        ukupno_otpada=round(ukupno_otpada, 1),
        broj_kanti=broj_kanti,
        broj_paleta=broj_paleta,
        priprema_sec=int(priprema),
        ukupno_1000_sec=int(ukupno_1000),
        ponavljanja=ponavljanja,
        total_sec=int(total),
        vibriranje_total_sec=int(vib_total),
        korekcija_sec=int(korekcija),
        normativ_arh=int(normativ_arh),
        normativ_final=round(normativ_final, 0),   # ar/h — normativ za kalkulaciju
    )


# ─── Dorada: finish-cut + pakiranje (SC20, MCS 115) ──────────────────────────

def calc_finish_cut(PF, layout, gramatura, odabir_rez, brutto_araka,
                    naklada_dorada, et_u_kutiji, kutija_na_paleti,
                    strip_paleta):
    """
    Normativ rezanja na gotovo i pakiranja.
    strip_paleta: broj paleta iz prethodnog strip-cut-a (za transport).
    """
    et_po_x = layout['et_po_x']
    et_po_y = layout['et_po_y']
    et_xb   = layout['et_xb']
    et_yb   = layout['et_yb']
    et_xn   = layout['et_xn']
    et_yn   = layout['et_yn']

    # Kontra os — finish-cut je okomit na strip-cut
    kontra_os = 'Y' if odabir_rez == 'X' else 'X'

    # Max traka u stroju (max 8, ograničenje 1300 mm)
    # =IF((8*et_xb)<1300, 8, INT(1300/et_xb))
    max_traka = 8 if (8 * et_xb) < 1300 else int(1300 / et_xb)

    # Broj rezova u finish smjeru
    # =IF(kontra=="X", et_po_x, et_po_y)
    br_rez_f = et_po_x if kontra_os == 'X' else et_po_y

    # Međurez?
    medurez = (
        (kontra_os == 'Y' and (et_yb - et_yn) > 0) or
        (kontra_os == 'X' and (et_xb - et_xn) > 0)
    )

    # Ukupno traka za nakladu
    # =IF(kontra=="Y", et_po_x*(brutto/1000), et_po_y*(brutto/1000))
    trake = (et_po_x if kontra_os == 'Y' else et_po_y) * (brutto_araka / 1000)

    # Broj ponavljanja
    ponavljanja_f = math.ceil(trake / max_traka)

    # Otpad finish-cut
    sirina = max_traka * et_xb if kontra_os == 'Y' else et_yb * max_traka
    if kontra_os == 'Y':
        otpad_f = (ponavljanja_f*1000)*(gramatura/1000)*(sirina/1000)*((et_yb-et_yn)/1000)*br_rez_f
    else:
        otpad_f = (ponavljanja_f*1000)*(gramatura/1000)*(sirina/1000)*((et_xb-et_xn)/1000)*br_rez_f
    kanti_f = math.ceil(otpad_f / PF['tezina_kante']) if PF['tezina_kante'] > 0 else 0

    # Pakiranje — količine
    max_et_paleta = kutija_na_paleti * et_u_kutiji
    paleta_gotova = math.ceil(naklada_dorada / max_et_paleta) if max_et_paleta > 0 else 0
    broj_kutija   = math.ceil(naklada_dorada / et_u_kutiji)   if et_u_kutiji > 0    else 0
    uk_buntevi    = int(max_traka * br_rez_f * ponavljanja_f)

    # ── Finish-cut vrijeme ────────────────────────────────────────────────────
    # Priprema: =SUM(D61:D64)+(D65*D73)+D72
    priprema_f = (
        PF['pregled_naloga'] + PF['priprema_robe'] +
        PF['priprema_rm'] + PF['uvlacenje_max_traka'] +
        PF['kontrola_reza'] * br_rez_f +
        PF['postavljanje_max_traka']
    )

    # Po ponavljanju: =(D73*D66)+(D73*D67)
    per_rep = br_rez_f * (PF['kontrola_svakog'] + PF['vrijeme_1_reza'])
    # Ukupno rezanje: =(per_rep*ponavljanja)+postavljanje
    t_rezanje_f = per_rep * ponavljanja_f + PF['postavljanje_max_traka']

    # Gubici transport: =(kanti_f*praznjenje)+(paleta_gotova*dovoz)+(strip_paleta*dovoz)
    t_gubitak_f = (
        kanti_f       * PF['praznjenje_kante'] +
        paleta_gotova * PF['dovoz_odvoz'] +
        strip_paleta  * PF['dovoz_odvoz']
    )
    total_f = t_rezanje_f + t_gubitak_f

    brzina_f = _round(naklada_dorada / (total_f / 3600), -3) if total_f > 0 else 0
    norm_f   = _round(brzina_f * 7 / 7.5, -3)                  # et/h — normativ finish

    # ── Pakiranje ─────────────────────────────────────────────────────────────
    najlon_t    = PF['najlon_sec']       * broj_kutija if PF['najlon'] == 'DA' else 0
    deklara_t   = PF['deklariranje_sec'] * broj_kutija
    pak_et_t    = uk_buntevi * PF['pakiranje_1_bunt']
    kontrol_t   = uk_buntevi * PF['kontrola_1_bunt']
    total_pak   = najlon_t + deklara_t + pak_et_t + kontrol_t + PF['priprema_rm_pakiranje']

    brzina_pak  = _round(naklada_dorada / (total_pak / 3600), -3) if total_pak > 0 else 0
    norm_pak_1  = _round(brzina_pak * 7 / 7.5, -3)              # et/h — 1 operater
    norm_pak_2  = norm_pak_1 * 2                                 # et/h — 2 operatera

    return dict(
        kontra_os=kontra_os, max_traka=max_traka,
        br_rez_finish=br_rez_f, medurez=medurez,
        trake=round(trake, 1), ponavljanja_finish=int(ponavljanja_f),
        otpad_finish=round(otpad_f, 1), kanti_finish=kanti_f,
        paleta_gotova=paleta_gotova, broj_kutija=broj_kutija,
        uk_buntevi=uk_buntevi,
        total_finish_sec=int(total_f),
        normativ_finish=int(norm_f),              # et/h
        total_pakiranje_sec=int(total_pak),
        normativ_pak_1op=int(norm_pak_1),         # et/h — normativ za kalkulaciju
        normativ_pak_2op=int(norm_pak_2),
    )


def calc_sc20(layout, gramatura, tip_papira, odabir_rez, brutto_araka,
              naklada_dorada, et_u_kutiji, kutija_na_paleti,
              p_strip=None, p_finish=None):
    """SC20: strip + finish + pakiranje."""
    strip = calc_strip_cut(p_strip or SC20_STRIP, layout, gramatura, tip_papira,
                           odabir_rez, brutto_araka)
    finish = calc_finish_cut(p_finish or SC20_FINISH, layout, gramatura, odabir_rez,
                             brutto_araka, naklada_dorada,
                             et_u_kutiji, kutija_na_paleti,
                             strip['broj_paleta'])
    # Kombinirani normativ (=ROUND(naklada/F140,-2), F140=F122+F112)
    # F122 = naklada/normativ_finish (h), F112 = brutto/normativ_strips (h)
    h_strips = brutto_araka / strip['normativ_final']   if strip['normativ_final'] > 0 else 0
    h_finish = naklada_dorada / finish['normativ_finish'] if finish['normativ_finish'] > 0 else 0
    if (h_strips + h_finish) > 0:
        norm_ukupno = _round(naklada_dorada / (h_strips + h_finish), -2)
    else:
        norm_ukupno = 0
    return dict(strip=strip, finish=finish, norm_ukupno=int(norm_ukupno))


def calc_mcs115(layout, gramatura, tip_papira, odabir_rez, brutto_araka,
                naklada_dorada, et_u_kutiji, kutija_na_paleti,
                p_strip=None, p_finish=None):
    """MCS 115: strip + finish + pakiranje."""
    strip = calc_strip_cut(p_strip or MCS_115_STRIP, layout, gramatura, tip_papira,
                           odabir_rez, brutto_araka)
    finish = calc_finish_cut(p_finish or MCS_115_FINISH, layout, gramatura, odabir_rez,
                             brutto_araka, naklada_dorada,
                             et_u_kutiji, kutija_na_paleti,
                             strip['broj_paleta'])
    h_strips = brutto_araka / strip['normativ_final']   if strip['normativ_final'] > 0 else 0
    h_finish = naklada_dorada / finish['normativ_finish'] if finish['normativ_finish'] > 0 else 0
    if (h_strips + h_finish) > 0:
        norm_ukupno = _round(naklada_dorada / (h_strips + h_finish), -2)
    else:
        norm_ukupno = 0
    return dict(strip=strip, finish=finish, norm_ukupno=int(norm_ukupno))


# ─── Dorada: štancanje (POLAR DC 11, BLUMER) ─────────────────────────────────

def calc_stancanje(P, layout, gramatura, odabir_rez, brutto_araka,
                   naklada_dorada, et_u_kutiji, kutija_na_paleti):
    """
    Normativ štancanja.
    P: POLAR_DC_11, BLUMER_1110_DUAL ili BLUMER_110
    """
    et_po_x    = layout['et_po_x']
    et_po_y    = layout['et_po_y']
    et_na_arku = layout['et_na_arku']
    et_xb = layout['et_xb']; et_yb = layout['et_yb']
    et_xn = layout['et_xn']; et_yn = layout['et_yn']

    # Broj rezova po traci: =IF(X, et_po_y, et_po_x)
    broj_rezova = et_po_y if odabir_rez == 'X' else et_po_x

    # Otpad po 1000 etiketa
    kg_ot_1000 = (
        ((et_xb - et_xn)/1000) * (et_yn/1000) +
        ((et_yb - et_yn)/1000) * (et_xb/1000)
    ) * 1000 * (gramatura/1000)
    ukupno_ot  = naklada_dorada / 1000 * kg_ot_1000
    broj_kanti = int(ukupno_ot / P['tezina_kante']) if P['tezina_kante'] > 0 else 0

    # Broj traka: =D24*(D17/D45)/1000 = brutto*(et_na_arku/broj_rezova)/1000
    broj_traka = brutto_araka * (et_na_arku / broj_rezova) / 1000 if broj_rezova > 0 else 0

    # Pakiranje — količine
    max_et_paleta = kutija_na_paleti * et_u_kutiji
    broj_paleta   = math.ceil(naklada_dorada / max_et_paleta) if max_et_paleta > 0 else 0
    broj_kutija   = math.ceil(naklada_dorada / et_u_kutiji)   if et_u_kutiji    > 0 else 0

    # Priprema štancanja: =D27+D28+D29+D30+D31+D32+D33+(D45*D39)
    priprema = (
        P['pregled_naloga'] + P['priprema_robe'] + P['priprema_rm'] +
        P['priprema_programa'] + P['priprema_alata'] +
        P['nulto_uvlacenje'] + P['dohvat_trake'] +
        broj_rezova * P['vrijeme_1_reza']
    )

    # Ukupno 1 trake: =(broj_rezova-1)*D39
    uk_1_trake = (broj_rezova - 1) * P['vrijeme_1_reza']

    # Ukupno štancanje: =(ponavljanja*uk_1_trake)+(ponavljanja*dohvat)
    uk_stanc = broj_traka * (uk_1_trake + P['dohvat_trake'])

    # Pražnjenje: =broj_kanti * praznjenje
    t_praznjenje = broj_kanti * P['praznjenje_kante']

    total_stanc = uk_stanc + t_praznjenje

    # Brzina štancanja: =ROUNDDOWN(brutto*et_na_arku/(total/3600), -2)
    if total_stanc > 0:
        brzina_s  = _rounddown(brutto_araka * et_na_arku / (total_stanc / 3600), -2)
    else:
        brzina_s  = 0
    norm_stanc = _round(brzina_s * 7 / 7.5, -2)   # et/h — normativ štancanje

    # ── Pakiranje ─────────────────────────────────────────────────────────────
    # ukupno_ulaganje  = D50 * D36 = broj_traka * ulaganje_1_trake
    t_ulaganje  = broj_traka * P['ulaganje_1_trake']
    # dovoz/odvoz paleta
    t_dovoz     = broj_paleta * P['dovoz_odvoz']
    t_odvoz     = broj_paleta * P['dovoz_odvoz']
    # QC pregled: =broj_traka * broj_rezova * QC_pregled
    t_QC        = broj_traka * broj_rezova * P['QC_pregled']
    # slaganje + deklariranje: =broj_kutija * slaganje_kutije
    t_slaganje  = broj_kutija * P['slaganje_kutije']

    total_pak  = t_ulaganje + t_dovoz + t_odvoz + t_QC + t_slaganje

    # Brzina pakiranja: =ROUNDDOWN(brutto*et_na_arku/(total_pak/3600), -2)
    if total_pak > 0:
        brzina_pak = _rounddown(brutto_araka * et_na_arku / (total_pak / 3600), -2)
    else:
        brzina_pak = 0
    norm_pak = _round(brzina_pak * 7 / 7.5, -2)    # et/h — normativ pakiranje

    return dict(
        broj_rezova=broj_rezova,
        kg_ot_1000=round(kg_ot_1000, 4),
        ukupno_ot=round(ukupno_ot, 1),
        broj_kanti=broj_kanti,
        broj_traka=round(broj_traka, 1),
        broj_paleta=broj_paleta, broj_kutija=broj_kutija,
        priprema_sec=int(priprema),
        total_stanc_sec=int(total_stanc),
        normativ_stanc=int(norm_stanc),     # et/h — normativ za kalkulaciju (štancanje)
        total_pak_sec=int(total_pak),
        normativ_pak=int(norm_pak),         # et/h — normativ za kalkulaciju (pakiranje)
    )


# ─── Tisak (CX 104, CX 102, CD 102) ──────────────────────────────────────────

def calc_tisak(P, layout, gramatura, tip_papira, naklada_tisak,
               broj_boja, lakirano, prolazi):
    """
    Normativ tiska na offset stroju.
    P     : CX_104, CX_102 ili CD_102
    Vraća dict sa svim normativima i međuvrijednostima.
    """
    et_na_arku = layout['et_na_arku']
    metal      = (tip_papira == 'metal')

    # ── Brutto arci ──────────────────────────────────────────────────────────
    # netto = ROUNDUP(naklada / et_na_arku, 0)
    netto = math.ceil(naklada_tisak / et_na_arku) if et_na_arku > 0 else 0

    # za_doradu = ROUND(netto*(1+0.01), 0)
    za_doradu = round(netto * (1 + P['dodatak_dorada']))

    # za_tisak = ROUND(za_doradu*(1+0.01), 0)
    za_tisak  = round(za_doradu * (1 + P['dodatak_tisak']))

    # fiksan = 200 + boje*40
    fiksan    = P['dodatak_fiksan'] + broj_boja * P['dodatak_fiksan_boja']

    # brutto_tis = ROUNDUP(za_doradu, -2)
    brutto_tis = math.ceil(za_doradu / 100) * 100

    # makulatura = ROUNDUP(za_tisak - za_doradu + fiksan*prolazi, -2)
    makulatura = math.ceil((za_tisak - za_doradu + fiksan * prolazi) / 100) * 100

    # brutto_izdati = brutto_tis + makulatura
    brutto_izdati = brutto_tis + makulatura

    # palete ulaz / izlaganje
    if metal:
        paleta_ulaz   = math.ceil(brutto_izdati / P['ulaz_metal'])
        paleta_izlag  = math.ceil(brutto_izdati / P['izlaganje_metal'])
        prolaganja    = math.ceil(brutto_izdati / P['prolaganje_svakih'])
    else:
        paleta_ulaz   = math.ceil(brutto_izdati / P['ulaz_bijeli'])
        paleta_izlag  = math.ceil(brutto_izdati / P['izlaganje_bijeli'])
        prolaganja    = 0

    # gubici arci na paletama (gornji + donji sloj)
    gub_ulaganje  = paleta_ulaz  * (P['neispravni_gore'] + P['neispravni_dolje'])
    gub_izlaganje = prolaganja   *  P['neispravni_prolaganje']
    skart         = gub_ulaganje + gub_izlaganje

    ocekivani_brutto = skart + brutto_izdati

    # ── Tisak ─────────────────────────────────────────────────────────────────
    # tisak_sec = ROUNDUP(ocekivani_brutto / brzina * 3600, -2)
    brzina_stroja = P['brzina_metal'] if metal else P['brzina_bijeli']
    if brzina_stroja > 0:
        tisak_sec = math.ceil(ocekivani_brutto / brzina_stroja * 3600 / 100) * 100
    else:
        tisak_sec = 0

    # gubitak_tisak = (paleta_ulaz+paleta_izlag)*zamjena + prolaganja*prolaganje_sec
    gub_tisak  = (
        (paleta_ulaz + paleta_izlag) * P['zamjena_palete'] +
        prolaganja * P['prolaganje_sec']
    )
    uk_tisak   = tisak_sec + gub_tisak

    # Normativ
    if uk_tisak > 0:
        brzina_arh = _rounddown(ocekivani_brutto / (uk_tisak / 3600), -2)
    else:
        brzina_arh = 0
    norm_tisk     = _round(brzina_arh / 8 * 7.5, -2)       # ar/h — normativ tiska

    # ── Priprema ──────────────────────────────────────────────────────────────
    # =D58+(D59*boje)+D61+D62+IF(lak=="DA",D60,0)
    priprema = (
        P['priprema_ploca'] + P['priprema_boja'] * broj_boja +
        P['ovjera_QC'] + P['provjera_povrat'] +
        (P['priprema_laka'] if lakirano == 'DA' else 0)
    )

    # ── Pranje ────────────────────────────────────────────────────────────────
    # =D64+(D65*boje)+D62+IF(lak=="DA",D66,0)
    pranje = (
        P['pranje_stroj'] + P['pranje_boja'] * broj_boja +
        P['provjera_povrat'] +
        (P['pranje_lak'] if lakirano == 'DA' else 0)
    )

    return dict(
        netto_araka=netto,
        za_doradu=za_doradu,
        brutto_izdati=brutto_izdati,
        ocekivani_brutto=ocekivani_brutto,
        skart=skart,
        paleta_ulaz=paleta_ulaz, paleta_izlag=paleta_izlag,
        prolaganja=prolaganja,
        tisak_sec=int(tisak_sec),
        uk_tisak_sec=int(uk_tisak),
        normativ_tisk=int(norm_tisk),       # ar/h — normativ radne brzine
        priprema_sec=int(priprema),         # sec — normativ pripreme
        pranje_sec=int(pranje),             # sec — normativ pranja
        priprema_h=round(priprema/3600, 2),
        pranje_h=round(pranje/3600, 2),
    )


# ─── Parametri strojeva — upravljanje ────────────────────────────────────────

import json as _json
import pathlib as _pathlib

DEFAULT_PARAMS = {
    'POLAR_137':      dict(POLAR_137),
    'SC20_STRIP':     dict(SC20_STRIP),
    'SC20_FINISH':    dict(SC20_FINISH),
    'MCS_115_STRIP':  dict(MCS_115_STRIP),
    'MCS_115_FINISH': dict(MCS_115_FINISH),
    'POLAR_DC_11':    dict(POLAR_DC_11),
    'BLUMER_1110_DUAL': dict(BLUMER_1110_DUAL),
    'BLUMER_110':     dict(BLUMER_110),
    'CX_104':         dict(CX_104),
    'CX_102':         dict(CX_102),
    'CD_102':         dict(CD_102),
}

_PARAMS_FILE = _pathlib.Path(__file__).parent / 'params.json'


def ucitaj_params() -> dict:
    result = {k: dict(v) for k, v in DEFAULT_PARAMS.items()}
    if _PARAMS_FILE.exists():
        with open(_PARAMS_FILE, encoding='utf-8') as fh:
            data = _json.load(fh)
        for key, vals in data.items():
            if key in result:
                result[key].update(vals)
    return result


def spremi_params(params: dict) -> None:
    with open(_PARAMS_FILE, 'w', encoding='utf-8') as fh:
        _json.dump(params, fh, ensure_ascii=False, indent=2)
