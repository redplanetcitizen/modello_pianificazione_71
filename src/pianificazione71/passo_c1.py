"""Esecuzione registrata del passo C1 (sistema prodotti-industrie 2012-2016)."""
from __future__ import annotations

import io

import pandas as pd

from .archivio import Configurazione, percorso_dati
from .registro import Esecuzione
from .sistema import (
    ANNI,
    a_prezzi_2012,
    controlli_reali,
    identita,
    importazioni_positive,
    indici_prezzo,
    leggi_make,
    leggi_use,
    negativi,
    prevalenza_prodotto,
)

USE = ("bea-2025-09", "manual/M1/IOUse_Before_Redefinitions_PRO_Summary.xlsx")
MAKE = ("bea-2025-09", "manual/M1/IOMake_Before_Redefinitions_PRO_Summary.xlsx")
PREZZI = ("bea-2026-09-23", "api/tidy/GDPbyIndustry/18.csv")
NOME = "M71-C1-sistema"


def _csv(df: pd.DataFrame, index: bool = False) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=index, float_format="%.10g", lineterminator="\n")
    return buf.getvalue()


def esegui(cfg: Configurazione) -> Esecuzione:
    parametri = {"anni": list(ANNI), "use": "/".join(USE), "make": "/".join(MAKE), "prezzi": "/".join(PREZZI),
                 "ipotesi": ["H1", "H2", "H3", "H4", "H5", "H6", "H24"]}
    with Esecuzione(NOME, cfg, parametri=parametri) as es:
        p_use, p_make = percorso_dati(cfg, *USE), percorso_dati(cfg, *MAKE)
        tidy = pd.read_csv(percorso_dati(cfg, *PREZZI))
        ident, neg, imp_pos, punt, prev, ctrl = [], [], [], [], [], []
        prezzi = None
        riepilogo = []
        for anno in ANNI:
            u, m = leggi_use(p_use, anno), leggi_make(p_make, anno)
            if prezzi is None:
                prezzi = indici_prezzo(tidy, list(u.U.columns))
            ident.append(identita(u, m))
            neg.append(negativi(u, m))
            imp_pos.append(importazioni_positive(u))
            punt += [u.puntini, m.puntini]
            prev.append(prevalenza_prodotto(m))
            s = a_prezzi_2012(u, m, prezzi[anno])
            ctrl.append(controlli_reali(s))
            cart = f"sistema/{anno}/"
            for nome, df in (("B", s.B), ("D", s.D), ("U_reale", s.U), ("F_reale", s.F), ("V_reale", s.V)):
                es.scrivi_testo(cart + f"{nome}.csv", _csv(df, index=True))
            es.scrivi_testo(cart + "x_q_reale.csv", _csv(pd.DataFrame(
                {"x_reale": s.x}).join(pd.DataFrame({"q_reale": s.q}), how="outer"), index=True))
            riepilogo.append({"anno": anno, "x_nominale": float(u.x.sum()), "x_reale_2012": float(s.x.sum()),
                              "q_nominale": float(u.q.sum()), "q_reale_2012": float(s.q.sum()),
                              "importazioni_nominali": float(-u.F["F050"].sum())})

        tabelle = {
            "identita.csv": pd.concat(ident, ignore_index=True),
            "negativi.csv": pd.concat(neg, ignore_index=True),
            "importazioni_positive.csv": pd.concat(imp_pos, ignore_index=True),
            "puntini.csv": pd.concat(punt, ignore_index=True),
            "prevalenza_prodotto.csv": pd.concat(prev, ignore_index=True),
            "controlli_reali.csv": pd.DataFrame(ctrl),
            "riepilogo.csv": pd.DataFrame(riepilogo),
        }
        for nome, df in tabelle.items():
            es.scrivi_testo(nome, _csv(df))
        es.scrivi_testo("prezzi.csv", _csv(prezzi, index=True))
        es.scrivi_testo("sintesi.md", sintesi(tabelle, prezzi))
    return es


def sintesi(t: dict[str, pd.DataFrame], prezzi: pd.DataFrame) -> str:
    ident, neg, punt, prev, ctrl = (t["identita.csv"], t["negativi.csv"], t["puntini.csv"],
                                    t["prevalenza_prodotto.csv"], t["controlli_reali.csv"])
    righe = ["# M71-C1 — sistema prodotti-industrie 2012-2016", ""]
    righe += ["## Identità contabili (milioni di dollari correnti)", "",
              "| Identità | Scarto massimo sui 5 anni | Voce |", "|---|---:|---|"]
    for nome, g in ident.groupby("identita", sort=False):
        r = g.loc[g["max_abs"].idxmax()]
        righe.append(f"| {nome} | {r.max_abs:,.0f} | {r.voce_max} ({r.anno}) |")
    righe += ["", "## Celle \"...\"", ""]
    for (tav, anno), g in punt.groupby(["tavola", "anno"]):
        righe.append(f"- {tav} {anno}: {len(g)} celle")
    righe += ["", "## Valori negativi per categoria (5 anni)", ""]
    for cat, g in neg.groupby("categoria"):
        righe.append(f"- {cat}: {len(g)}")
    righe += ["", "## Prevalenza del prodotto nell'industria con lo stesso codice", "",
              f"- quota minima: {prev['quota_stesso_codice'].min():.3f} "
              f"({prev.loc[prev['quota_stesso_codice'].idxmin(), 'prodotto']}, "
              f"{prev.loc[prev['quota_stesso_codice'].idxmin(), 'anno']})",
              f"- prodotti per cui l'industria principale non ha lo stesso codice: "
              f"{int((~prev['principale_coincide']).sum())} casi prodotto-anno"]
    righe += ["", "## Sistema a prezzi 2012", "", "```", ctrl.to_string(index=False), "```"]
    righe += ["", "## Indici di prezzo (2012 = 1): intervallo nel 2016", "",
              f"- minimo {prezzi[2016].min():.3f} ({prezzi[2016].idxmin()}), massimo {prezzi[2016].max():.3f} ({prezzi[2016].idxmax()})"]
    return "\n".join(righe) + "\n"
