"""Esecuzione registrata del passo C7: lavoro (FTE), scorte, estero."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .archivio import Configurazione, percorso_dati
from .blocchi import coefficienti_lavoro, estero, fte, scorte, sigma
from .capacita import KLEMS_AGGREGATI, leggi_klems
from .passo_c1 import MAKE, PREZZI, USE, _csv
from .passo_c6 import KLEMS
from .registro import Esecuzione
from .sistema import ANNI, a_prezzi_2012, indici_prezzo, leggi_make, leggi_use

NIPA = "bea-2026-09-23"
FTE_T = (NIPA, "api/tidy/NIPA/T60500D.csv")
STOCK_T = (NIPA, "api/tidy/NIPA/T50805B.csv")
DEFL_T = (NIPA, "api/tidy/NIPA/T50809B.csv")
CIPI_T = (NIPA, "api/tidy/NIPA/T50705B.csv")
NOME = "M71-C7-lavoro-scorte-estero"


def esegui(cfg: Configurazione) -> Esecuzione:
    parametri = {"fte": "/".join(FTE_T), "scorte": "/".join(STOCK_T), "deflatori_scorte": "/".join(DEFL_T),
                 "klems": "/".join(KLEMS), "ipotesi": ["H13", "H14", "H14a", "H15", "H21", "H22", "D3"]}
    with Esecuzione(NOME, cfg, parametri=parametri) as es:
        tidy_p = pd.read_csv(percorso_dati(cfg, *PREZZI))
        xr, est, prezzi, f030 = [], [], None, {}
        for a in ANNI:
            u, m = leggi_use(percorso_dati(cfg, *USE), a), leggi_make(percorso_dati(cfg, *MAKE), a)
            prezzi = indici_prezzo(tidy_p, list(u.U.columns)) if prezzi is None else prezzi
            s = a_prezzi_2012(u, m, prezzi[a])
            xr += [{"industria_io": j, "anno": a, "x_reale": v} for j, v in s.x.items()]
            est.append(estero(s.F, s.U, a))
            f030[a] = float(u.F["F030"].sum())
            industrie = list(u.U.columns)
        xr = pd.DataFrame(xr)
        private = [j for j in industrie if not j.startswith("G")]

        # lavoro
        lav = coefficienti_lavoro(fte(pd.read_csv(percorso_dati(cfg, *FTE_T)), ANNI), xr, industrie)
        ore = leggi_klems(percorso_dati(cfg, *KLEMS), ["Labor Hours_Quantity"], list(ANNI))
        ctrl_lav = controllo_ore(lav, ore)

        # scorte
        sc = scorte(pd.read_csv(percorso_dati(cfg, *STOCK_T)), pd.read_csv(percorso_dati(cfg, *DEFL_T)),
                    [2011] + list(ANNI))
        sg = sigma(sc, xr, private)
        cipi = pd.read_csv(percorso_dati(cfg, *CIPI_T))
        cipi = cipi[(cipi["LineNumber"] == 1) & cipi["TimePeriod"].astype(str).isin([str(a) for a in ANNI])]
        ctrl_sc = pd.DataFrame({"anno": list(ANNI),
                                "delta_stock_corrente_Q4": [sc[sc.anno == a].stock_corrente.sum() - sc[sc.anno == a - 1].stock_corrente.sum() for a in ANNI],
                                "variazione_scorte_nipa_575": [float(cipi[cipi.TimePeriod.astype(str) == str(a)].value_num.iloc[0]) for a in ANNI],
                                "F030_use": [f030[a] for a in ANNI]})

        e = pd.concat(est, ignore_index=True)
        saldo = e.groupby("anno")[["esportazioni", "importazioni", "voci_positive_F050"]].sum()
        saldo["saldo_merci_servizi"] = saldo["esportazioni"] - saldo["importazioni"] + saldo["voci_positive_F050"]

        for nome, df in (("lavoro.csv", lav), ("controllo_ore_klems.csv", ctrl_lav), ("scorte.csv", sc),
                         ("sigma_scorte.csv", sg), ("controllo_scorte.csv", ctrl_sc), ("estero.csv", e),
                         ("saldo_estero.csv", saldo.reset_index())):
            es.scrivi_testo(nome, _csv(df))
        es.scrivi_testo("sintesi.md", sintesi(lav, ctrl_lav, sg, ctrl_sc, saldo))
    return es


def controllo_ore(lav: pd.DataFrame, ore: pd.DataFrame) -> pd.DataFrame:
    """Crescita FTE 2012→2016 per gruppo KLEMS contro crescita dell'indice delle ore KLEMS."""
    inv = {m: g for g, membri in KLEMS_AGGREGATI.items() for m in membri}
    l = lav.assign(gruppo=lav["industria_io"].map(lambda j: inv.get(j, j)))
    g = l.groupby(["gruppo", "anno"])["fte_migliaia"].sum().unstack()
    g = g[g[2012] > 0]
    out = pd.DataFrame({"crescita_fte": g[2016] / g[2012]})
    out["crescita_ore_klems"] = (ore[2016] / ore[2012]).reindex(out.index)
    return out.dropna().reset_index()


def sintesi(lav, ctrl_lav, sg, ctrl_sc, saldo) -> str:
    tot = lav.groupby("anno")["fte_migliaia"].sum()
    corr = np.corrcoef(ctrl_lav["crescita_fte"], ctrl_lav["crescita_ore_klems"])[0, 1]
    r = ["# M71-C7 — lavoro, scorte, estero", "",
         "## Lavoro (FTE, migliaia)", "",
         f"- totale industrie I/O: {tot[2012]:,.0f} (2012) → {tot[2016]:,.0f} (2016)",
         f"- controllo con l'indice delle ore KLEMS, crescita 2012–2016 per gruppo: correlazione {corr:.2f}; "
         f"scarto medio assoluto {100 * (ctrl_lav['crescita_fte'] - ctrl_lav['crescita_ore_klems']).abs().mean():.1f} punti "
         f"({len(ctrl_lav)} gruppi)", "",
         "## Scorte: σ = stock / produzione del comparto (2012, prezzi IV trim. 2012)", "", "```",
         sg[["comparto", "stock_2012", "sigma"]].to_string(index=False, float_format=lambda v: f"{v:,.3f}"), "```", "",
         "## Controllo scorte (milioni correnti)", "", "```", ctrl_sc.to_string(index=False), "```",
         "La differenza tra variazione degli stock di fine anno e variazione NIPA comprende l'aggiustamento di valutazione.", "",
         "## Estero (milioni di dollari 2012)", "", "```", saldo.to_string(float_format=lambda v: f"{v:,.0f}"), "```"]
    return "\n".join(r) + "\n"
