"""Passo D0: identità di controllo del modello al punto osservato (specifica §6).

Si inseriscono nei vincoli del modello i valori osservati (x, q, importazioni, consumo, investimento FA,
variazione delle scorte, stock di capitale FA) e si misura lo scarto di ciascun vincolo.
Uno scarto non indica un errore: va identificato e spiegato (perimetro, base di prezzo, ipotesi).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .blocchi import COMPARTI, industrie_comparto
from .dati_modello import TIPI, Parametri


def controlla(P: Parametri, epsilon: float = 0.10, u_non_g17: float = 1.0, sigma_fattore: float = 1.0) -> dict[str, pd.DataFrame]:
    anni = list(P.anni)
    cap_ind = [j for j in P.kappa.index if j in P.private and j != "HS"]
    bil, cap, lav, est, sc = [], [], [], [], []
    K = {}  # stock di inizio anno osservato (FA): K0 e accumulazione osservata I − D + altre variazioni
    Ioss = P.I_oss.set_index(["industria_io", "tipo", "anno"])["I"]
    for (j, a), k in P.K0.items():
        K[(j, a, anni[0])] = k
    for t in anni:
        for (j, a), _ in P.K0.items():
            K[(j, a, t + 1)] = (1 - P.delta[(j, a)]) * K[(j, a, t)] + Ioss.get((j, a, t), 0.0)
    S = P.S_oss.set_index(["riga", "anno"])["stock_2012"]
    for t in anni:
        B, D = P.B[t], P.D[t]
        inv = pd.Series(0.0, index=P.prodotti)
        for a in TIPI:
            I = pd.Series({j: Ioss.get((j, a, t), 0.0) for j in P.industrie})
            inv += P.phi[(t, a)].fillna(0.0) @ I.reindex(P.phi[(t, a)].columns).fillna(0.0)
        invR = Ioss.get(("HS", "R", t), 0.0) * P.phi_R[t]
        dS = sum(S[(z, t)] - S[(z, t - 1)] for z in COMPARTI)
        uso_scorte = P.psi * dS
        lato_usi = (B @ P.x_oss[t] + P.consumo_oss[t] + inv + invR + uso_scorte + P.pubblica[t]
                    + P.esportazioni[t] + P.usi_esterni_fissi[t])
        residuo = P.q_oss[t] + P.import_oss[t] - lato_usi   # = r osservato (deve essere ≥ 0 nel modello)
        bil.append(pd.DataFrame({"anno": t, "prodotto": P.prodotti, "residuo": residuo.values,
                                 "residuo_rel_q": (residuo / P.q_oss[t].where(P.q_oss[t] > 0)).values,
                                 "scorte_F030": P.scorte_oss[t].values, "scorte_modello": uso_scorte.values,
                                 "inv_F02": sum(P.inv_oss_prodotti[(t, a)] for a in ("E", "S", "N", "R")).values,
                                 "inv_modello": (inv + invR).values}))
        xq = D @ P.q_oss[t] + P.x_speciali[t]
        quote_scarto = float((xq - P.x_oss[t]).abs().max())
        for j in cap_ind + ["HS"]:
            tipi = ["R"] if j == "HS" else [a for a in TIPI if (j, a) in P.K0.index]
            kcap = sum((1.0 if a == "R" else float(P.w[(j, a)])) * K[(j, a, t)] for a in tipi)
            theta = float(P.theta.get(j, 0.0))
            u_j = 1.0 if (theta != 0.0 or j == "HS") else u_non_g17
            u = float(P.x_oss[t][j]) * float(P.kappa[j]) * u_j / (1 + theta) ** (t - anni[0]) / kcap
            cap.append({"anno": t, "industria": j, "utilizzo_implicito": u, "violato": u > 1 + 1e-9,
                        "g17": theta != 0.0})
        lav.append({"anno": t, "lavoro_usato": float((P.ell[t] * P.x_oss[t]).sum()), "lavoro_disponibile": P.lavoro_tot[t],
                    "scarto_quote_max": quote_scarto})
        uso = B @ P.x_oss[t] + P.consumo_oss[t] + inv + P.pubblica[t]
        banda = (1 + epsilon) * P.mu[t] * uso
        est.append({"anno": t, "importazioni": float(P.import_oss[t].sum()), "tetto": P.import_tot[t],
                    "bande_violate": int((P.import_oss[t] > banda + 1e-9).sum()),
                    "eccesso_sulle_bande": float((P.import_oss[t] - banda).clip(lower=0).sum())})
        for z in COMPARTI:
            xs = sum(float(P.x_oss[t][j]) for j in industrie_comparto(z, P.private))
            sg = float(P.sigma.set_index("riga").at[z, "sigma"]) * sigma_fattore
            sc.append({"anno": t, "comparto": z, "stock": S[(z, t)], "minimo": sg * xs,
                       "violato": S[(z, t)] < sg * xs - 1e-9})
    return {"bilanci": pd.concat(bil, ignore_index=True), "capacita": pd.DataFrame(cap),
            "lavoro": pd.DataFrame(lav), "estero": pd.DataFrame(est), "scorte": pd.DataFrame(sc)}
