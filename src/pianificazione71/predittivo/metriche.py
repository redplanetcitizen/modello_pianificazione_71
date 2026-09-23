"""Metriche di previsione per M71-E6-predittivo.

Le previsioni e i valori osservati sono tabelle lunghe con colonne
  caso, origine, h, anno, gruppo, chiave, valore
I pesi economici (WMAE, WRMSE) sono le quote osservate all'origine τ (peso_tau), mai quote future.
Gruppi: produzione (industria), consumo (prodotto), investimento_tipo, investimento_ind (industria|tipo),
stock_tipo, stock_ind (stock di fine anno), importazioni (prodotto), scorte (comparto), aggregati.
Indicatore sintetico S = Σ_g α_g WMAE_g(modello) / WMAE_g(persistenza), Σ α_g = 1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ALFA = {"produzione": 0.30, "consumo": 0.30, "investimento_tipo": 0.20, "stock_tipo": 0.10,
        "importazioni": 0.05, "scorte": 0.05}


def unisci(prev: pd.DataFrame, oss: pd.DataFrame, pesi: pd.DataFrame, base: pd.DataFrame) -> pd.DataFrame:
    """Previsioni + osservato + peso a τ + livello a τ (per errori sui tassi e sul segno)."""
    m = prev.merge(oss.rename(columns={"valore": "osservato"}), on=["anno", "gruppo", "chiave"], how="inner")
    m = m.merge(pesi.rename(columns={"valore": "peso"}), on=["origine", "gruppo", "chiave"], how="left")
    m = m.merge(base.rename(columns={"valore": "livello_tau"}), on=["origine", "gruppo", "chiave"], how="left")
    m["peso"] = m["peso"].fillna(0.0)
    return m


def metriche_gruppo(m: pd.DataFrame) -> dict:
    e = m["valore"] - m["osservato"]
    ae = e.abs()
    w = m["peso"].clip(lower=0)
    w = w / w.sum() if w.sum() > 0 else pd.Series(1.0 / len(m), index=m.index)
    den = (m["valore"].abs() + m["osservato"].abs())
    smape = (2 * ae / den.where(den > 0)).dropna()
    liv = m["livello_tau"]
    ok = liv.abs() > 1e-9
    g_prev = (m["valore"] - liv)[ok] / liv[ok].abs()
    g_oss = (m["osservato"] - liv)[ok] / liv[ok].abs()
    segno = (np.sign(m["valore"] - liv) == np.sign(m["osservato"] - liv))[ok]
    return {"n": int(len(m)), "MAE": float(ae.mean()), "RMSE": float(np.sqrt((e ** 2).mean())),
            "WMAE": float((w * ae).sum()), "WRMSE": float(np.sqrt((w * e ** 2).sum())),
            "sMAPE": float(smape.mean()) if len(smape) else np.nan,
            "errore_tassi": float((g_prev - g_oss).abs().mean()) if ok.any() else np.nan,
            "segno": float(segno.mean()) if ok.any() else np.nan}


def tabella_metriche(m: pd.DataFrame, per: tuple = ("caso", "h", "gruppo")) -> pd.DataFrame:
    righe = []
    for chiavi, g in m.groupby(list(per)):
        r = dict(zip(per, chiavi))
        r.update(metriche_gruppo(g))
        righe.append(r)
    return pd.DataFrame(righe)


def theil_e_sintesi(tab: pd.DataFrame, riferimento: str = "persistenza", alfa: dict = ALFA) -> pd.DataFrame:
    """Aggiunge Theil U (RMSE / RMSE persistenza) e il rapporto WMAE / WMAE persistenza; poi S per (caso, h)."""
    rif = tab[tab["caso"] == riferimento].set_index(["h", "gruppo"])
    t = tab.copy()
    t["theil_U"] = [r["RMSE"] / rif.at[(r["h"], r["gruppo"]), "RMSE"] if (r["h"], r["gruppo"]) in rif.index
                    and rif.at[(r["h"], r["gruppo"]), "RMSE"] > 0 else np.nan for _, r in t.iterrows()]
    t["rapporto_WMAE"] = [r["WMAE"] / rif.at[(r["h"], r["gruppo"]), "WMAE"] if (r["h"], r["gruppo"]) in rif.index
                          and rif.at[(r["h"], r["gruppo"]), "WMAE"] > 0 else np.nan for _, r in t.iterrows()]
    righe = []
    for (caso, h), g in t.groupby(["caso", "h"]):
        s, tot = 0.0, 0.0
        comp = {}
        for gr, a in alfa.items():
            v = g[g["gruppo"] == gr]["rapporto_WMAE"]
            if len(v) and np.isfinite(v.iloc[0]):
                s += a * float(v.iloc[0]); tot += a; comp[gr] = float(v.iloc[0])
        righe.append({"caso": caso, "h": h, "S": s / tot if tot > 0 else np.nan, "alfa_coperto": tot, **{f"r_{k}": v for k, v in comp.items()}})
    return t, pd.DataFrame(righe)
