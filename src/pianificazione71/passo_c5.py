"""Esecuzione registrata del passo C5: capitale, investimento, ammortamento a prezzi 2012; identità di accumulazione."""
from __future__ import annotations

import pandas as pd

from .archivio import Configurazione, percorso_dati
from .capitale import a_prezzi_2012, aggrega_io, pannello, pannello_residenziale, sintesi_identita
from .margini import leggi_concordanza, leggi_fa_dettaglio
from .passo_c1 import _csv
from .passo_c2 import CONCORDANZA, FA_RES
from .registro import Esecuzione

REL = "bea-2026-09-22"
FILE = {"K1": "manual/M3/detailnonres_stk1.xlsx", "K2": "manual/M3/detailnonres_stk2.xlsx",
        "I1": "manual/M3/detailnonres_inv1.xlsx", "I2": "manual/M3/detailnonres_inv2.xlsx",
        "D1": "manual/M3/detailnonres_dep1.xlsx", "D2": "manual/M3/detailnonres_dep2.xlsx"}
ANNI_CAPITALE = range(2011, 2017)  # 2011: stock di fine anno = stock iniziale del 2012
NOME = "M71-C5-capitale"


def esegui(cfg: Configurazione) -> Esecuzione:
    parametri = {"file": {k: f"{REL}/{v}" for k, v in FILE.items()}, "residenziale": "/".join(FA_RES),
                 "anni": list(ANNI_CAPITALE), "ipotesi": ["H6", "H11", "H12", "H18", "H18a", "H20"]}
    with Esecuzione(NOME, cfg, parametri=parametri) as es:
        conc = leggi_concordanza(CONCORDANZA)
        s = {k: leggi_fa_dettaglio(percorso_dati(cfg, REL, v), anni=ANNI_CAPITALE) for k, v in FILE.items()}
        el = {m: a_prezzi_2012(s[m + "1"], s[m + "2"]) for m in "KID"}
        p = pannello(*(aggrega_io(el[m], conc, m) for m in "KID"))
        res = pannello_residenziale(percorso_dati(cfg, *FA_RES), ANNI_CAPITALE)
        tutto = pd.concat([p, res], ignore_index=True)
        ident = sintesi_identita(tutto)
        prezzi_mancanti = pd.DataFrame([{"misura": m, "serie_senza_prezzo_2012": int(el[m]["prezzo_non_base"].sum())}
                                        for m in "KID"])
        delta = (tutto.dropna(subset=["delta"]).groupby(["industria_io", "tipo"])
                 .apply(lambda g: g["D_2012"].sum() / g["K_inizio_2012"].sum(), include_groups=False)
                 .rename("delta_2012_2016").reset_index())
        es.scrivi_testo("pannello_capitale.csv", _csv(tutto))
        es.scrivi_testo("identita_accumulazione.csv", _csv(ident))
        es.scrivi_testo("delta_industria_tipo.csv", _csv(delta))
        es.scrivi_testo("serie_senza_prezzo_2012.csv", _csv(prezzi_mancanti))
        es.scrivi_testo("sintesi.md", sintesi(ident, delta, tutto))
    return es


def sintesi(ident: pd.DataFrame, delta: pd.DataFrame, p: pd.DataFrame) -> str:
    r = ["# M71-C5 — capitale a prezzi 2012 (milioni di dollari 2012)", "",
         "## Identità di accumulazione: K_fine − K_inizio − I + D = altre variazioni", "",
         "| Tipo | Anno | K inizio | I | D | Altre variazioni | % di K (aggregato) | % di K (somma dei valori assoluti) | δ |",
         "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for _, x in ident.iterrows():
        r.append(f"| {x.tipo} | {x.anno} | {x.K_inizio:,.0f} | {x.I:,.0f} | {x.D:,.0f} | {x.altre:,.0f} | "
                 f"{100 * x.altre_rel_aggregato:.3f} | {100 * x.altre_abs_rel:.3f} | {x.delta_aggregato:.4f} |")
    d = delta.groupby("tipo")["delta_2012_2016"].describe()[["min", "50%", "max"]]
    r += ["", "## δ per industria e tipo (media 2012–2016)", "", "```", d.to_string(float_format=lambda v: f"{v:.4f}"), "```"]
    k = p[p["anno"] == 2016].groupby("tipo")["K_2012"].sum()
    r += ["", "## Stock netto a fine 2016 per tipo", "", "```", k.to_string(float_format=lambda v: f"{v:,.0f}"), "```"]
    return "\n".join(r) + "\n"
