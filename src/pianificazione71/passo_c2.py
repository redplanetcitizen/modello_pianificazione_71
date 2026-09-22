"""Esecuzione registrata del passo C2 (margini dell'investimento)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .archivio import Configurazione, percorso_dati
from .margini import (
    confronto_totali,
    investimento_per_industria_io,
    leggi_concordanza,
    leggi_fa_dettaglio,
    leggi_residenziale,
)
from .passo_c1 import MAKE, USE, _csv
from .registro import Esecuzione
from .sistema import ANNI, leggi_use

FA_INV = ("bea-2026-09-22", "manual/M3/detailnonres_inv1.xlsx")
FA_RES = ("bea-2026-09-22", "manual/M3/detailresidential.xlsx")
NIPA_535 = ("bea-2026-09-23", "api/tidy/NIPA/T50305.csv")
CONCORDANZA = Path(__file__).resolve().parents[2] / "config" / "concordanza_fa_io.csv"
NOME = "M71-C2-margini"


def esegui(cfg: Configurazione) -> Esecuzione:
    parametri = {"fa": "/".join(FA_INV), "residenziale": "/".join(FA_RES), "nipa": "/".join(NIPA_535),
                 "use": "/".join(USE), "concordanza": CONCORDANZA.name, "ipotesi": ["H18", "H18a"]}
    with Esecuzione(NOME, cfg, parametri=parametri) as es:
        fa = leggi_fa_dettaglio(percorso_dati(cfg, *FA_INV))
        res = leggi_residenziale(percorso_dati(cfg, *FA_RES))
        nipa = pd.read_csv(percorso_dati(cfg, *NIPA_535))
        use_f = {a: leggi_use(percorso_dati(cfg, *USE), a).F for a in ANNI}
        conc = leggi_concordanza(CONCORDANZA)
        es.scrivi_byte("concordanza_fa_io.csv", CONCORDANZA.read_bytes())
        conf = confronto_totali(fa, res, use_f, nipa)
        io = investimento_per_industria_io(fa, conc)
        largo = io.pivot_table(index=["anno", "industria_io"], columns="tipo", values="valore").reset_index()
        es.scrivi_testo("confronto_totali.csv", _csv(conf))
        es.scrivi_testo("investimento_fa_per_industria_io.csv", _csv(largo))
        es.scrivi_testo("sintesi.md", sintesi(conf, largo))
    return es


def sintesi(conf: pd.DataFrame, largo: pd.DataFrame) -> str:
    r = ["# M71-C2 — margini dell'investimento (milioni di dollari correnti)", "",
         "| Anno | Tipo | Fixed Assets | Use (con Used) | riga Used | NIPA 5.3.5 | FA − Use | % |",
         "|---:|---|---:|---:|---:|---:|---:|---:|"]
    for _, x in conf.iterrows():
        r.append(f"| {x.anno} | {x.tipo} | {x.fixed_assets:,.0f} | {x.use_totale:,.0f} | {x.use_riga_used:,.0f} | "
                 f"{x.nipa_535:,.0f} | {x.scarto_fa_use:,.0f} | {100 * x.scarto_relativo:.2f} |")
    n_ind = largo["industria_io"].nunique()
    r += ["", f"Industrie I/O con investimento FA: {n_ind} (74 industrie FA aggregate con la concordanza)."]
    return "\n".join(r) + "\n"
