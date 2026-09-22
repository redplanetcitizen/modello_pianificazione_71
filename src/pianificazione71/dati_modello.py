"""Passo D0: parametri del modello a 71 industrie, 2012-2016, prezzi 2012, in MILIARDI di dollari 2012.

Riunisce i risultati del passo C in un unico insieme di parametri coerente in unità:
- sistema prodotti-industrie reale (B_t, D_t), domanda finale osservata per componente;
- Φ_{a,t} reale per unità di investimento FA reale (colonne a somma ≈ fattore di raccordo);
- capitale iniziale, δ, pesi w, κ e deriva θ (opzione di calibrazione a);
- lavoro (FTE), scorte (σ, S_2011, composizione Ψ), estero (μ, importazioni totali).

Righe `Used` e `Other`: fuori dai bilanci materiali, contributi fissati ai valori osservati (H16).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .archivio import Configurazione, percorso_dati
from .blocchi import COMPARTI, coefficienti_lavoro, fte, industrie_comparto, scorte, sigma
from .capacita import (
    CATEGORIE_CAPITALE,
    G17_IO,
    capitale_capacita,
    controllo_g17,
    deriva_capacita,
    kappa,
    leggi_g17,
    leggi_klems,
    pesi_costo_uso,
    utilizzo_per_industria,
)
from .capitale import a_prezzi_2012 as elementari_2012, aggrega_io, pannello, pannello_residenziale
from .margini import leggi_concordanza, leggi_fa_dettaglio
from .passo_c1 import MAKE, PREZZI, USE
from .passo_c2 import CONCORDANZA, FA_INV, FA_RES
from .passo_c4 import PEQ
from .passo_c5 import ANNI_CAPITALE, FILE, REL
from .passo_c6 import G17_CAP, G17_U, KLEMS
from .passo_c7 import DEFL_T, FTE_T, STOCK_T
from .phi import composizione_peq, leggi_peq, stima_phi
from .sistema import ANNI, SPECIALI, a_prezzi_2012 as sistema_reale, indici_prezzo, leggi_make, leggi_use

SCALA = 1000.0  # milioni → miliardi
TIPI = ("E", "S", "N")
COLONNE_PUBBLICHE = ("F06C", "F06S", "F06E", "F06N", "F07C", "F07S", "F07E", "F07N",
                     "F10C", "F10S", "F10E", "F10N")


@dataclass
class Parametri:
    anni: tuple
    industrie: list[str]
    prodotti: list[str]                      # 71 prodotti ordinari
    private: list[str]
    B: dict[int, pd.DataFrame] = field(default_factory=dict)       # prodotti × industrie
    D: dict[int, pd.DataFrame] = field(default_factory=dict)       # industrie × prodotti ordinari
    x_speciali: dict[int, pd.Series] = field(default_factory=dict) # parte di x dovuta a Used/Other (fissa)
    x_oss: dict[int, pd.Series] = field(default_factory=dict)
    q_oss: dict[int, pd.Series] = field(default_factory=dict)
    consumo_oss: dict[int, pd.Series] = field(default_factory=dict)
    pubblica: dict[int, pd.Series] = field(default_factory=dict)
    esportazioni: dict[int, pd.Series] = field(default_factory=dict)
    import_oss: dict[int, pd.Series] = field(default_factory=dict)
    usi_esterni_fissi: dict[int, pd.Series] = field(default_factory=dict)  # voci positive di F050
    scorte_oss: dict[int, pd.Series] = field(default_factory=dict)       # F030 reale (prodotti)
    inv_oss_prodotti: dict[tuple, pd.Series] = field(default_factory=dict)  # (anno, tipo) → F02 reale
    phi: dict[tuple, pd.DataFrame] = field(default_factory=dict)     # (anno, tipo) → prodotti × industrie
    phi_R: dict[int, pd.Series] = field(default_factory=dict)
    I_oss: pd.DataFrame | None = None        # industria, tipo, anno, I (FA reale)
    K0: pd.Series | None = None              # (industria, tipo) → stock inizio 2012
    K_oss: pd.Series | None = None           # (industria, tipo, anno) → stock osservato di inizio anno, 2012-2017 (solo confronto)
    delta: pd.Series | None = None           # (industria, tipo) → δ
    w: pd.Series | None = None               # (industria, tipo) → peso capacità
    kappa: pd.Series | None = None           # industria → κ_2012
    theta: pd.Series | None = None           # industria → deriva annua (0 dove non stimata)
    ell: dict[int, pd.Series] = field(default_factory=dict)
    lavoro_tot: dict[int, float] = field(default_factory=dict)
    sigma: pd.DataFrame | None = None
    S0: pd.Series | None = None              # riga comparto → stock fine 2011
    S_oss: pd.DataFrame | None = None
    psi: pd.Series | None = None             # composizione per prodotto delle scorte (quota ≥ 0)
    mu: dict[int, pd.Series] = field(default_factory=dict)
    import_tot: dict[int, float] = field(default_factory=dict)
    diagnostica: dict = field(default_factory=dict)


def costruisci(cfg: Configurazione) -> Parametri:
    tidy = pd.read_csv(percorso_dati(cfg, *PREZZI))
    usi, makes, reali = {}, {}, {}
    prezzi = None
    for a in ANNI:
        usi[a] = leggi_use(percorso_dati(cfg, *USE), a)
        makes[a] = leggi_make(percorso_dati(cfg, *MAKE), a)
        prezzi = indici_prezzo(tidy, list(usi[a].U.columns)) if prezzi is None else prezzi
        reali[a] = sistema_reale(usi[a], makes[a], prezzi[a])
    industrie = list(usi[2012].U.columns)
    prodotti = industrie[:]  # i 71 prodotti ordinari hanno gli stessi codici delle industrie
    private = [j for j in industrie if not j.startswith("G")]
    P = Parametri(ANNI, industrie, prodotti, private)

    # --- sistema e domanda finale -----------------------------------------------------------
    for a in ANNI:
        s = reali[a]
        P.B[a] = s.B.loc[prodotti] * 1.0                         # coefficienti: adimensionali
        P.D[a] = s.D[prodotti] * 1.0
        P.x_speciali[a] = (s.D[list(SPECIALI)] @ s.q[list(SPECIALI)]) / SCALA
        P.x_oss[a], P.q_oss[a] = s.x / SCALA, s.q.loc[prodotti] / SCALA
        F = s.F.loc[prodotti] / SCALA
        P.consumo_oss[a] = F["F010"]
        P.pubblica[a] = F[list(COLONNE_PUBBLICHE)].sum(axis=1)
        P.esportazioni[a] = F["F040"]
        P.import_oss[a] = (-F["F050"]).clip(lower=0)
        P.usi_esterni_fissi[a] = F["F050"].clip(lower=0)
        P.scorte_oss[a] = F["F030"]
        for t, col in zip(("E", "S", "N", "R"), ("F02E", "F02S", "F02N", "F02R")):
            P.inv_oss_prodotti[(a, t)] = F[col]

    # --- capitale (C5) -----------------------------------------------------------------------
    conc = leggi_concordanza(CONCORDANZA)
    ser = {k: leggi_fa_dettaglio(percorso_dati(cfg, REL, v), anni=ANNI_CAPITALE) for k, v in FILE.items()}
    el = {m: elementari_2012(ser[m + "1"], ser[m + "2"]) for m in "KID"}
    pan = pd.concat([pannello(*(aggrega_io(el[m], conc, m) for m in "KID")),
                     pannello_residenziale(percorso_dati(cfg, *FA_RES), ANNI_CAPITALE)], ignore_index=True)
    p12 = pan[pan["anno"] == 2012].set_index(["industria_io", "tipo"])
    P.K0 = p12["K_inizio_2012"] / SCALA
    # stock osservato di inizio anno t = stock di fine anno t−1 a prezzi 2012 (solo per il confronto ex post)
    P.K_oss = (pan.assign(anno=pan["anno"] + 1).set_index(["industria_io", "tipo", "anno"])["K_2012"] / SCALA).sort_index()
    d = pan.dropna(subset=["delta"]).groupby(["industria_io", "tipo"])
    P.delta = d["D_2012"].sum() / d["K_inizio_2012"].sum()
    P.I_oss = pan[pan["anno"].isin(ANNI)][["industria_io", "tipo", "anno", "I_2012"]].assign(
        I=lambda z: z["I_2012"] / SCALA).drop(columns="I_2012")

    # --- Φ reale per unità di investimento FA reale (C4) ---------------------------------------
    fa_inv = ser["I1"].assign(valore=ser["I1"]["valore"])  # costo corrente, per la stima di Φ
    for a in ANNI:
        u = usi[a]
        cp = composizione_peq(leggi_peq(percorso_dati(cfg, *PEQ), a), u.F["F02E"], prodotti)
        for t in TIPI:
            X = stima_phi(t, a, u.F, fa_inv, conc, industrie, prodotti, cp if t == "E" else None).X
            Xr = X.div(prezzi[a].reindex(prodotti), axis=0) / SCALA        # miliardi 2012
            I = P.I_oss[(P.I_oss["anno"] == a) & (P.I_oss["tipo"] == t)].set_index("industria_io")["I"]
            I = I.reindex(industrie).fillna(0.0)
            P.phi[(a, t)] = Xr.div(I.where(I > 0), axis=1).fillna(0.0)
        fr = P.inv_oss_prodotti[(a, "R")].clip(lower=0)
        IR = float(P.I_oss[(P.I_oss["anno"] == a) & (P.I_oss["tipo"] == "R")]["I"].sum())
        P.phi_R[a] = fr / IR
    P.diagnostica["fattori_raccordo_reali"] = {
        f"{a}_{t}": float((P.phi[(a, t)].sum(axis=0) * P.I_oss[(P.I_oss.anno == a) & (P.I_oss.tipo == t)]
                           .set_index("industria_io")["I"].reindex(industrie).fillna(0)).sum()
                          / P.I_oss[(P.I_oss.anno == a) & (P.I_oss.tipo == t)]["I"].sum())
        for a in ANNI for t in TIPI}

    # --- capacità (C6), opzione (a): κ con deriva ------------------------------------------------
    rem = leggi_klems(percorso_dati(cfg, *KLEMS), CATEGORIE_CAPITALE, [2012])[2012]
    pesi, _ = pesi_costo_uso(pan, rem)
    P.w = pesi.set_index(["industria_io", "tipo"])["w"]
    kcap = capitale_capacita(pan, pesi)
    xr = pd.DataFrame([{"industria_io": j, "anno": a, "x_reale": reali[a].x[j]} for a in ANNI for j in industrie])
    u = utilizzo_per_industria(leggi_g17(percorso_dati(cfg, *G17_U), list(G17_IO), list(ANNI)))
    cap = leggi_g17(percorso_dati(cfg, *G17_CAP), list(G17_IO), list(ANNI))
    kap = kappa(kcap, xr, u)
    der, _ = deriva_capacita(controllo_g17(kcap, xr, kap, u, cap))
    P.kappa = kap.set_index("industria_io")["kappa"]  # K_cap (milioni) / x (milioni): adimensionale
    P.theta = der.set_index("industria_io")["deriva_annua_2012_16"].reindex(P.kappa.index).fillna(0.0)

    # --- lavoro, scorte, estero (C7) -------------------------------------------------------------
    lav = coefficienti_lavoro(fte(pd.read_csv(percorso_dati(cfg, *FTE_T)), ANNI), xr, industrie)
    for a in ANNI:
        la = lav[lav["anno"] == a].set_index("industria_io")
        P.ell[a] = (la["fte_migliaia"] / (la["x_reale"] / SCALA)).reindex(industrie).fillna(0.0)  # migliaia FTE per miliardo
        P.lavoro_tot[a] = float(la["fte_migliaia"].sum())
    sc = scorte(pd.read_csv(percorso_dati(cfg, *STOCK_T)), pd.read_csv(percorso_dati(cfg, *DEFL_T)), [2011] + list(ANNI))
    sc["stock_2012"] /= SCALA
    P.S_oss = sc
    P.sigma = sigma(sc, xr.assign(x_reale=xr["x_reale"] / SCALA), private)
    P.S0 = sc[sc["anno"] == 2011].set_index("riga")["stock_2012"]
    pos = sum(P.scorte_oss[a].clip(lower=0) for a in ANNI)
    P.psi = pos / pos.sum()
    for a in ANNI:
        uso = P.B[a] @ P.x_oss[a] + P.consumo_oss[a] + P.pubblica[a] + sum(
            P.inv_oss_prodotti[(a, t)] for t in ("E", "S", "N", "R"))
        P.mu[a] = (P.import_oss[a] / uso.where(uso > 0)).fillna(0.0).clip(upper=1.0)
        P.import_tot[a] = float(P.import_oss[a].sum())
    return P
