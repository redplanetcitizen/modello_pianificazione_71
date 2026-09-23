"""Verifiche di stabilità numerica per M71-E6-predittivo (una origine, configurazioni scelte).

  1. molteplicità: perturbazione casuale dei costi dell'obiettivo (±0,1%) e confronto della soluzione;
  2. sensibilità ai dati: coefficienti tecnici B e obiettivi di consumo perturbati dell'1% (rumore con seme fisso);
  3. sensibilità ai pesi dell'obiettivo: ±20% sulle penalità e sui pesi di tracking;
  4. tolleranze del solver: primal/dual feasibility 1e-6 contro 1e-9;
  5. algoritmo: simplex contro punto interno (ipm);
  6. scala: variabili in milioni invece che in miliardi (costi riscalati).
Misura: variazione relativa media delle previsioni aggregate (produzione, consumo, investimento per tipo) e
della soluzione completa (norma L1 relativa), più il numero di variabili al limite zero.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd

from ..modello import Opzioni, costruisci_e_risolvi
from .backtest import previsioni_modello


def _agg(P, R, tau):
    p = previsioni_modello(P, R, tau, "x")
    return p[p["gruppo"].isin(["aggregati", "investimento_tipo"])].set_index(["gruppo", "chiave", "anno"])["valore"]


def _scarto(a: pd.Series, b: pd.Series) -> float:
    return float(((a - b).abs() / a.abs().where(a.abs() > 1e-9)).dropna().mean())


def verifica(P, tau: int, opzioni: dict, fattori) -> pd.DataFrame:
    base_o = Opzioni(**opzioni, terminale_fattori=fattori)
    R0 = costruisci_e_risolvi(P, base_o)
    a0, x0 = _agg(P, R0, tau), R0.grezzi["valori"]
    righe = [{"verifica": "riferimento", "stato": R0.stato, "obiettivo": R0.obiettivo, "scarto_aggregati": 0.0, "scarto_soluzione": 0.0,
              "quota_variabili_a_zero": float(np.mean(np.abs(x0) < 1e-9))}]

    def riga(nome, P_, o_):
        R = costruisci_e_risolvi(P_, o_)
        if R.stato != "Optimal":
            righe.append({"verifica": nome, "stato": R.stato}); return
        x = R.grezzi["valori"]
        sc_sol = float(np.abs(x - x0).sum() / max(np.abs(x0).sum(), 1e-9)) if len(x) == len(x0) else np.nan
        righe.append({"verifica": nome, "stato": R.stato, "obiettivo": R.obiettivo, "scarto_aggregati": _scarto(a0, _agg(P_, R, tau)),
                      "scarto_soluzione": sc_sol, "quota_variabili_a_zero": float(np.mean(np.abs(x) < 1e-9))})

    for seme in (1, 2):
        riga(f"molteplicita_costi_perturbati_{seme}", P, Opzioni(**opzioni, terminale_fattori=fattori, perturba_costi=1e-3, seme_perturbazione=seme))
    rng = np.random.default_rng(7)
    Pp = copy.deepcopy(P)
    for t in Pp.anni:
        Pp.B[t] = Pp.B[t] * (1 + 0.01 * rng.uniform(-1, 1, Pp.B[t].shape))
        Pp.consumo_oss[t] = Pp.consumo_oss[t] * (1 + 0.01 * rng.uniform(-1, 1, len(Pp.consumo_oss[t])))
    riga("dati_perturbati_1%", Pp, base_o)
    for fatt in (0.8, 1.2):
        o = dict(opzioni)
        for k in ("penalita_var_inv", "penalita_var_inv_ind", "p2_lambda_x", "p2_lambda_inv", "p2_lambda_m", "p2_lambda_S", "valore_terminale"):
            if o.get(k):
                o[k] = o[k] * fatt
        riga(f"pesi_obiettivo_x{fatt}", P, Opzioni(**o, terminale_fattori=fattori))
    for tol in (1e-6, 1e-9):
        riga(f"tolleranze_{tol:g}", P, Opzioni(**opzioni, terminale_fattori=fattori,
                                              opzioni_highs={"primal_feasibility_tolerance": tol, "dual_feasibility_tolerance": tol}))
    riga("algoritmo_ipm", P, Opzioni(**opzioni, terminale_fattori=fattori, opzioni_highs={"solver": "ipm"}))
    # scala: milioni invece di miliardi su tutte le grandezze monetarie del modello
    Ps = copy.deepcopy(P)
    for nome in ("x_speciali", "consumo_oss", "pubblica", "esportazioni", "import_oss", "usi_esterni_fissi", "scorte_oss", "x_oss", "q_oss"):
        d = getattr(Ps, nome)
        for t in d:
            d[t] = d[t] * 1000.0
    for k in Ps.inv_oss_prodotti:
        Ps.inv_oss_prodotti[k] = Ps.inv_oss_prodotti[k] * 1000.0
    Ps.K0, Ps.I_prec, Ps.S0 = Ps.K0 * 1000.0, Ps.I_prec * 1000.0, Ps.S0 * 1000.0
    Ps.import_tot = {t: v * 1000.0 for t, v in Ps.import_tot.items()}
    Ps.ell = {t: v / 1000.0 for t, v in Ps.ell.items()}
    if getattr(Ps, "previsioni", None):
        Ps.previsioni = {k: v * 1000.0 for k, v in Ps.previsioni.items()}
    os_ = dict(opzioni)
    if os_.get("valore_terminale"):
        os_["valore_terminale"] = os_["valore_terminale"] / 1000.0      # λ_K per unità di stock: riscalato con le unità
    Rs = costruisci_e_risolvi(Ps, Opzioni(**os_, terminale_fattori=fattori))
    if Rs.stato == "Optimal":
        as_ = _agg(Ps, Rs, tau) / 1000.0
        righe.append({"verifica": "scala_milioni", "stato": Rs.stato, "obiettivo": Rs.obiettivo, "scarto_aggregati": _scarto(a0, as_),
                      "scarto_soluzione": np.nan, "quota_variabili_a_zero": float(np.mean(np.abs(Rs.grezzi["valori"]) < 1e-9))})
    else:
        righe.append({"verifica": "scala_milioni", "stato": Rs.stato})
    return pd.DataFrame(righe)
