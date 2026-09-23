"""Formulazioni e griglia di configurazioni di M71-E6-predittivo.

  P0  previsioni preliminari senza riconciliazione (nessun LP)
  P1  O2 predittivo: obiettivi = consumo previsto ĉ; tratti e pesi come iperparametri
  P2  tracking L1 regolarizzato (LP) del consumo e della produzione previsti
  P3  variante robusta: esogene (lavoro, importazioni totali) a un quantile dei residui di validazione
Chiusure terminali: T1 (H29 non anticipativo), T2 (valore dello stock, v = 1), T3 (T1 + T2).
Gradualità: penalità aggregata per tipo (E6), settoriale per industria e tipo, entrambe, nessuna.
Ogni configurazione è un dict serializzabile: nome → {famiglia, opzioni del modello, chiusura, robustezza}.
"""
from __future__ import annotations

from itertools import product

TRATTI = {
    "E6": ((0.9, 1.0), (0.1, 0.5), (0.2, 0.1)),
    "stretto": ((0.95, 1.0), (0.05, 0.5), (0.10, 0.1)),
    "largo": ((0.9, 1.0), (0.1, 0.5), (0.3, 0.1)),
    "tetto100": ((0.9, 1.0), (0.1, 0.5)),                  # consumo ≤ obiettivo previsto
    "tetto110": ((0.9, 1.0), (0.1, 0.5), (0.1, 0.1)),      # consumo ≤ 1,1 × obiettivo previsto
}
PENALITA = {
    "agg": {"penalita_var_inv": 0.10, "soglia_var_inv": 0.05},
    "agg+ind": {"penalita_var_inv": 0.10, "soglia_var_inv": 0.05, "penalita_var_inv_ind": 0.05},
    "ind": {"penalita_var_inv_ind": 0.05},
    "nessuna": {},
}
TERMINALE = {
    "T1": {"terminale": True, "valore_terminale": 0.0},
    "T2": {"terminale": False, "valore_terminale": 1e-5},
    "T3": {"terminale": True, "valore_terminale": 1e-5},
}
BASE = {"u_non_g17": 1.0, "capacita_non_g17": "uniforme", "sigma_fattore": 0.85, "sigma_max_fattore": 1.20}


def griglia(rapida: bool = False) -> dict:
    """Configurazioni P1, P2 (e P3 costruite a valle sulla P1 di riferimento)."""
    cfg = {}
    tratti = ["E6", "stretto", "largo", "tetto100", "tetto110"] if not rapida else ["E6", "tetto100"]
    pen = ["agg", "agg+ind", "ind", "nessuna"] if not rapida else ["agg", "nessuna"]
    term = ["T1", "T2", "T3"] if not rapida else ["T1", "T3"]
    for tr, pe, te in product(tratti, pen, term):
        cfg[f"P1|{tr}|{pe}|{te}"] = {"famiglia": "P1", "tratti": tr, "penalita": pe, "terminale": te,
                                     "opzioni": {**BASE, "obiettivo": "O2", "tratti_o2": TRATTI[tr], **PENALITA[pe], **TERMINALE[te]}}
    lx = [0.5, 2.0] if not rapida else [1.0]
    li = [0.1, 0.5] if not rapida else [0.5]
    for x, i, te in product(lx, li, ["T1", "T3"]):
        cfg[f"P2|lx{x}|li{i}|{te}"] = {"famiglia": "P2", "lambda_x": x, "lambda_I": i, "terminale": te,
                                       "opzioni": {**BASE, "obiettivo": "P2", "p2_lambda_c": 1.0, "p2_lambda_x": x,
                                                   "penalita_var_inv": i, "soglia_var_inv": 0.0, **TERMINALE[te]}}
    for inv, mm, ss in ((1.0, 0.0, 0.0), (1.0, 1.0, 1.0)):
        for te in ["T1", "T3"]:
            nome = f"P2|inv{inv}|m{mm}|S{ss}|{te}"
            cfg[nome] = {"famiglia": "P2", "lambda_x": 1.0, "lambda_I": 0.5, "terminale": te,
                         "opzioni": {**BASE, "obiettivo": "P2", "p2_lambda_c": 1.0, "p2_lambda_x": 1.0, "penalita_var_inv": 0.5,
                                     "soglia_var_inv": 0.0, "p2_lambda_inv": inv, "p2_lambda_m": mm, "p2_lambda_S": ss, **TERMINALE[te]}}
    cfg["P2|uniformi|li0.5|T1"] = {"famiglia": "P2", "lambda_x": 1.0, "lambda_I": 0.5, "terminale": "T1",
                                   "opzioni": {**BASE, "obiettivo": "P2", "p2_pesi": "uniformi", "p2_lambda_c": 1.0,
                                               "p2_lambda_x": 1.0, "penalita_var_inv": 0.5, "soglia_var_inv": 0.0, **TERMINALE["T1"]}}
    return cfg


RIFERIMENTO_P1 = "P1|E6|agg|T1"     # la traduzione diretta di E6 in forma predittiva
ROBUSTE = {"P3|q25": 0.25, "P3|q75": 0.75}   # quantile dei residui di validazione per lavoro e importazioni totali
