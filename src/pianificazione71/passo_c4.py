"""Esecuzione registrata del passo C4: stima di Φ per anno e tipo di bene, con sensibilità alla struttura iniziale."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .archivio import Configurazione, percorso_dati
from .margini import leggi_concordanza, leggi_fa_dettaglio
from .passo_c1 import USE, _csv
from .passo_c2 import CONCORDANZA, FA_INV
from .phi import LAMBDA, composizione, composizione_peq, diagnostica, leggi_peq, stima_phi
from .registro import Esecuzione
from .sistema import ANNI, leggi_use

PEQ = ("bea-2026-09-22", "manual/M4/PEQBridge_Summary.xlsx")
NOME = "M71-C4-phi"
LAMBDA_SENSIBILITA = (0.2, 1.0)  # 1.0 = composizione comune per tutte le industrie (nessuna informazione FA)


def esegui(cfg: Configurazione) -> Esecuzione:
    parametri = {"lambda": LAMBDA, "lambda_sensibilita": list(LAMBDA_SENSIBILITA), "fa": "/".join(FA_INV),
                 "peq": "/".join(PEQ), "use": "/".join(USE), "ipotesi": ["H13", "H18", "H18a", "H19", "D1"]}
    with Esecuzione(NOME, cfg, parametri=parametri) as es:
        fa = leggi_fa_dettaglio(percorso_dati(cfg, *FA_INV))
        conc = leggi_concordanza(CONCORDANZA)
        diag, sens = [], []
        for anno in ANNI:
            u = leggi_use(percorso_dati(cfg, *USE), anno)
            ind = list(u.U.columns)
            prod = ind[:]  # 71 prodotti ordinari; Used e Other sono esogeni (H16)
            cp = composizione_peq(leggi_peq(percorso_dati(cfg, *PEQ), anno), u.F["F02E"], prod)
            es.scrivi_testo(f"phi/{anno}/composizione_peq.csv", _csv(cp, index=True))
            for tipo in "ESN":
                base = stima_phi(tipo, anno, u.F, fa, conc, ind, prod, cp if tipo == "E" else None)
                diag.append(diagnostica(base))
                es.scrivi_testo(f"phi/{anno}/X_{tipo}.csv", _csv(base.X, index=True))
                es.scrivi_testo(f"phi/{anno}/Phi_{tipo}.csv", _csv(composizione(base.X), index=True))
                for lam in LAMBDA_SENSIBILITA:
                    alt = stima_phi(tipo, anno, u.F, fa, conc, ind, prod, cp if tipo == "E" else None, lam=lam)
                    d = np.abs(alt.X.values - base.X.values).sum() / np.abs(base.X.values).sum()
                    sens.append({"anno": anno, "tipo": tipo, "lambda": lam, "differenza_relativa_da_base": float(d)})
            r = u.F["F02R"].reindex(prod).fillna(0.0)
            es.scrivi_testo(f"phi/{anno}/phi_R.csv", _csv((r / r.sum()).to_frame("phi_R"), index=True))
        d, s = pd.DataFrame(diag), pd.DataFrame(sens)
        es.scrivi_testo("diagnostica.csv", _csv(d))
        es.scrivi_testo("sensibilita_struttura_iniziale.csv", _csv(s))
        es.scrivi_testo("sintesi.md", sintesi(d, s))
    return es


def sintesi(d: pd.DataFrame, s: pd.DataFrame) -> str:
    r = ["# M71-C4 — stima di Φ (composizione dell'investimento per industria)", "",
         f"Struttura iniziale dal dettaglio dei Fixed Assets, quota comune λ = {LAMBDA}; bilanciamento GRAS.", "",
         "| Anno | Tipo | Iter. | Converge | Scala Use/FA | Spostamento dalla struttura iniziale | Celle negative |",
         "|---:|---|---:|---|---:|---:|---:|"]
    for _, x in d.iterrows():
        r.append(f"| {x.anno} | {x.tipo} | {x.iterazioni} | {x.convergenza} | {x.scala_colonne_use_su_fa:.4f} | "
                 f"{100 * x.spostamento_relativo_da_struttura_iniziale:.1f}% | {x.celle_negative} |")
    r += ["", "## Sensibilità alla struttura iniziale", "",
          "Differenza relativa Σ|X_λ − X_base| / ΣX_base (media sui 5 anni):", ""]
    m = s.groupby(["tipo", "lambda"])["differenza_relativa_da_base"].mean().unstack()
    r += ["```", m.to_string(float_format=lambda v: f"{100 * v:.1f}%"), "```",
          "", "λ = 1 corrisponde a una composizione comune a tutte le industrie: misura quanta informazione "
          "apporta il dettaglio dei Fixed Assets."]
    return "\n".join(r) + "\n"
