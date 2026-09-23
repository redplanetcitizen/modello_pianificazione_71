"""Passo E3: funzione d'investimento stimata fuori campione e inserita in O2 (orizzonte 2010-2019).

1. Dati di stima, per tipo a ∈ {E, S, N, R}, sullo stesso perimetro del modello (industrie private con capitale;
   HS per R): investimento I_{a,t} e stock di inizio anno K_{a,t} a prezzi 2012 (Fixed Assets), produzione X_t
   a prezzi 2012 delle industrie private (per R: HS), 1997-2019.
2. Stima sul 1998-2009 (solo anni precedenti l'orizzonte del modello: nessuna circolarità) di due regole:
   - acceleratore flessibile in forma di tassi: I/K = c0 + c1·X/K  →  I = c0·K + c1·X;
   - tasso d'investimento costante: I/K = media 2005-2009  →  I = i·K.
   Verifica fuori campione sul 2010-2019 (e 2012-2016): scarto percentuale medio assoluto.
3. Inserimento in O2 come regola endogena (K e X sono variabili del modello), in banda ±10% o con penalità a
   gradini sullo scarto (libera fino al 5% di I_2009, poi 0,1 fino al 15%, poi 0,5 per unità relativa).
   Caso diagnostico: investimento per tipo fissato ai valori osservati (scomposizione del vantaggio di consumo).
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd

from .archivio import Configurazione, percorso_dati
from .capitale import a_prezzi_2012 as elementari_2012, aggrega_io, pannello, pannello_residenziale
from .dati_modello import SCALA, costruisci
from .grafici import TIPI_TUTTI, serie
from .margini import leggi_concordanza, leggi_fa_dettaglio
from .modello import Opzioni, costruisci_e_risolvi
from .passo_c1 import MAKE, PREZZI, USE, _csv
from .passo_c2 import CONCORDANZA, FA_RES
from .passo_c5 import FILE, REL
from .passo_d import VARIANTE, _scrivi_risultato
from .passo_e1 import scarti
from .passo_e2 import COLORI, NOMI, _figura, utilizzo_totale
from .registro import Esecuzione
from .sistema import a_prezzi_2012 as sistema_reale, indici_prezzo, leggi_make, leggi_use

ANNI_DATI = range(1997, 2020)
STIMA = (1998, 2009)
TASSO = (2005, 2009)
ORIZZONTE = range(2010, 2020)
RIPORTATI = range(2012, 2017)


def dati_stima(cfg: Configurazione, P) -> pd.DataFrame:
    anni_k = range(ANNI_DATI[0] - 1, ANNI_DATI[-1] + 1)
    conc = leggi_concordanza(CONCORDANZA)
    ser = {k: leggi_fa_dettaglio(percorso_dati(cfg, REL, v), anni=anni_k) for k, v in FILE.items()}
    el = {m: elementari_2012(ser[m + "1"], ser[m + "2"]) for m in "KID"}
    pan = pd.concat([pannello(*(aggrega_io(el[m], conc, m) for m in "KID")),
                     pannello_residenziale(percorso_dati(cfg, *FA_RES), anni_k)], ignore_index=True)
    tidy = pd.read_csv(percorso_dati(cfg, *PREZZI))
    x, prezzi = {}, None
    for a in ANNI_DATI:
        u, m = leggi_use(percorso_dati(cfg, *USE), a), leggi_make(percorso_dati(cfg, *MAKE), a)
        prezzi = indici_prezzo(tidy, list(u.U.columns), ANNI_DATI) if prezzi is None else prezzi
        x[a] = sistema_reale(u, m, prezzi[a]).x
    cap_ind = [j for j in P.kappa.index if j in P.private and j != "HS"]
    coppie = {(j, t) for j in cap_ind for t in "ESN" if (j, t) in P.K0.index and P.K0[(j, t)] > 0} | {("HS", "R")}
    chiave = list(zip(pan["industria_io"], pan["tipo"]))
    pan = pan[[c in coppie for c in chiave]]
    g = pan.groupby(["tipo", "anno"])[["K_inizio_2012", "I_2012"]].sum() / SCALA
    righe = []
    for a in TIPI_TUTTI:
        for t in ANNI_DATI:
            X = float(x[t]["HS"] if a == "R" else x[t].reindex(P.private).sum()) / SCALA
            righe.append({"tipo": a, "anno": t, "K": float(g.loc[(a, t), "K_inizio_2012"]),
                          "I": float(g.loc[(a, t), "I_2012"]), "X": X})
    d = pd.DataFrame(righe)
    d["i"], d["x_su_k"] = d["I"] / d["K"], d["X"] / d["K"]
    return d


def stima(d: pd.DataFrame) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    regole, righe, prev = {"acceleratore": {}, "tasso_costante": {}}, [], []
    for a in TIPI_TUTTI:
        z = d[d.tipo == a].set_index("anno")
        st = z.loc[STIMA[0]:STIMA[1]]
        X = np.c_[np.ones(len(st)), st["x_su_k"].values]
        b, *_ = np.linalg.lstsq(X, st["i"].values, rcond=None)
        res = st["i"].values - X @ b
        r2 = 1 - res @ res / ((st["i"] - st["i"].mean()) @ (st["i"] - st["i"].mean()))
        tasso = float(z.loc[TASSO[0]:TASSO[1], "i"].mean())
        regole["acceleratore"][a] = {"k": float(b[0]), "x": float(b[1])}
        regole["tasso_costante"][a] = {"k": tasso, "x": 0.0}
        for t in z.index:
            prev.append({"tipo": a, "anno": t, "I_osservato": z.loc[t, "I"],
                         "I_acceleratore": b[0] * z.loc[t, "K"] + b[1] * z.loc[t, "X"],
                         "I_tasso_costante": tasso * z.loc[t, "K"]})
        pv = pd.DataFrame([p for p in prev if p["tipo"] == a]).set_index("anno")
        mape = lambda col, a0, a1: float((pv.loc[a0:a1, col] / pv.loc[a0:a1, "I_osservato"] - 1).abs().mean() * 100)
        righe.append({"tipo": a, "c0": b[0], "c1": b[1], "R2_stima": r2, "tasso_2005_09": tasso,
                      "MAPE_acc_2010_19": mape("I_acceleratore", 2010, 2019), "MAPE_acc_2012_16": mape("I_acceleratore", 2012, 2016),
                      "MAPE_tasso_2010_19": mape("I_tasso_costante", 2010, 2019), "MAPE_tasso_2012_16": mape("I_tasso_costante", 2012, 2016)})
    return regole, pd.DataFrame(righe), pd.DataFrame(prev)


def esegui(cfg: Configurazione) -> Esecuzione:
    u2010 = utilizzo_totale(cfg, ORIZZONTE[0])
    calib = {"u_non_g17": u2010, "sigma_fattore": VARIANTE["sigma_fattore"]}
    P = costruisci(cfg, ORIZZONTE)
    with Esecuzione("M71-E3-funzione-investimento", cfg, parametri={"stima": STIMA, "tasso": TASSO, "orizzonte": list(ORIZZONTE),
                                                                   "calibrazione": calib}) as es:
        d = dati_stima(cfg, P)
        regole, tab_stima, prev = stima(d)
        es.scrivi_testo("dati_stima.csv", _csv(d))
        es.scrivi_testo("stima_regole.csv", _csv(tab_stima))
        es.scrivi_testo("previsioni_fuori_campione.csv", _csv(prev))
        oss = P.I_oss.groupby(["tipo", "anno"])["I"].sum()
        osservato = {a: {"costante": {t: float(oss.get((a, t), 0.0)) for t in ORIZZONTE}} for a in TIPI_TUTTI}
        casi = {
            "O2": {},
            "acceleratore_banda_10%": {"regola_inv": regole["acceleratore"]},
            "tasso_costante_banda_10%": {"regola_inv": regole["tasso_costante"]},
            "tasso_costante_penalita": {"regola_inv": regole["tasso_costante"], "regola_modo": "penalita"},
            "investimento_osservato": {"regola_inv": osservato, "regola_eps": 0.0},
        }
        opz = {k: Opzioni(obiettivo="O2", **calib, **m) for k, m in casi.items()}
        es.scrivi_testo("opzioni.json", pd.Series({k: str(dataclasses.asdict(v)) for k, v in opz.items()}).to_json(indent=1))
        tab, ris = [], {}
        for nome, o in opz.items():
            R = costruisci_e_risolvi(P, o)
            riga = _scrivi_risultato(es, nome, R)
            if R.stato == "Optimal":
                ris[nome] = R
                a = R.tabelle["aggregati"].set_index("anno")
                riga.update({"consumo_cumulato_2012_16": float(a.loc[list(RIPORTATI), "consumo_privato"].sum()),
                             "consumo_cumulato_2010_19": float(a["consumo_privato"].sum()),
                             "anni_disinv_netto_2010_19": int((a["investimento_netto"] < 0).sum())})
            tab.append(riga)
        t = pd.DataFrame(tab).set_index("caso")
        es.scrivi_testo("casi.csv", _csv(t.reset_index()))
        s = serie(P, ris)
        es.scrivi_testo("serie_2010_2019.csv", _csv(s))
        sc_tutto = scarti(s)
        sc_rip = scarti(s[s["anno"].isin(list(RIPORTATI) + [RIPORTATI[-1] + 1])
                          & ~(s["variabile"].str.startswith(("produzione", "consumo", "investimento")) & (s["anno"] > RIPORTATI[-1]))])
        es.scrivi_testo("scarti_2010_2019.csv", _csv(sc_tutto.rename_axis("caso").reset_index()))
        es.scrivi_testo("scarti_2012_2016.csv", _csv(sc_rip.rename_axis("caso").reset_index()))
        col = ["produzione_lorda", "consumo_privato", "media_investimento", "media_stock"]
        sint = t[["stato", "consumo_cumulato_2010_19", "consumo_cumulato_2012_16", "anni_disinv_netto_2010_19"]].join(
            sc_tutto[col].add_suffix("_10_19")).join(sc_rip[col].add_suffix("_12_16"))
        nota = "Orizzonte 2010-2019 (stock: inizio 2010-2020); calibrazione sul 2010."
        for n0, caso, titolo in ((1, "tasso_costante_banda_10%", "O2 + regola a tasso costante (banda ±10%)"),
                                 (4, "acceleratore_banda_10%", "O2 + regola acceleratore (banda ±10%)")):
            if caso not in ris:
                continue
            NOMI[caso], COLORI[caso] = titolo, "#1f77b4" if n0 == 1 else "#d62728"
            se = s[s.caso.isin(["osservato", caso])]
            es.scrivi_byte(f"{n0}_{caso}_produzione_consumo.png", _figura(
                se, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
                f"{titolo} ed economia osservata: produzione e consumo", 1, 2, (16, 5.8), [caso], nota))
            es.scrivi_byte(f"{n0 + 1}_{caso}_investimento_per_tipo.png", _figura(
                se, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
                f"{titolo} ed economia osservata: investimento per tipo", 2, 2, (16, 10), [caso], nota))
            es.scrivi_byte(f"{n0 + 2}_{caso}_stock_per_tipo.png", _figura(
                se, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
                f"{titolo} ed economia osservata: stock per tipo (2020 = fine orizzonte)", 2, 2, (16, 10), [caso], nota))
        es.scrivi_testo("sintesi.md", "# M71-E3 — funzione d'investimento stimata, O2 2010-2019\n\n## Stima (1998-2009) e verifica fuori campione\n\n```\n"
                        + tab_stima.to_string(index=False, float_format=lambda v: f"{v:,.4f}") + "\n```\n\n## Casi\n\n```\n"
                        + sint.to_string(float_format=lambda v: f"{v:,.2f}") + "\n```\n\n## Scarti 2010-2019 per variabile\n\n```\n"
                        + sc_tutto.round(1).to_string() + "\n```\n")
    return es
