"""Esecuzione registrata del passo C4b: confronto diagnostico di Φ 2012 con la tavola dei flussi di capitale 1997."""
from __future__ import annotations

import pandas as pd

from .archivio import Configurazione, percorso_dati
from .confronto1997 import confronto, leggi_cft1997
from .margini import leggi_concordanza, leggi_fa_dettaglio
from .passo_c1 import USE, _csv
from .passo_c2 import CONCORDANZA, FA_INV
from .passo_c4 import PEQ
from .phi import composizione_peq, leggi_peq, stima_phi
from .registro import Esecuzione
from .sistema import leggi_use

CFT = ("bea-2025-09", "manual/M5/flow1997.xls")
RETTIFICHE = ("bea-2025-09", "manual/M5/changes_to_180x123combined.xls")
NOME = "M71-C4b-confronto-1997"
ANNO = 2012


def esegui(cfg: Configurazione) -> Esecuzione:
    parametri = {"cft": "/".join(CFT), "rettifiche": "/".join(RETTIFICHE), "anno_phi": ANNO,
                 "perimetro": "attrezzature + strutture non residenziali, senza software"}
    with Esecuzione(NOME, cfg, parametri=parametri) as es:
        t97 = leggi_cft1997(percorso_dati(cfg, *CFT), percorso_dati(cfg, *RETTIFICHE))
        u = leggi_use(percorso_dati(cfg, *USE), ANNO)
        ind = list(u.U.columns)
        fa = leggi_fa_dettaglio(percorso_dati(cfg, *FA_INV))
        conc = leggi_concordanza(CONCORDANZA)
        cp = composizione_peq(leggi_peq(percorso_dati(cfg, *PEQ), ANNO), u.F["F02E"], ind)
        X = {t: stima_phi(t, ANNO, u.F, fa, conc, ind, ind, cp if t == "E" else None).X for t in "ES"}
        c = confronto(t97, X["E"], X["S"])
        es.scrivi_testo("confronto_1997.csv", _csv(c))
        es.scrivi_testo("sintesi.md", sintesi(c))
    return es


def sintesi(c: pd.DataFrame) -> str:
    w = c["investimento_2012"]
    mp = (c["dissomiglianza_phi_1997"] * w).sum() / w.sum()
    mc = (c["dissomiglianza_comune_1997"] * w).sum() / w.sum()
    peggiori = c[~c["phi_piu_vicina"]]["industria_io"].tolist()
    return "\n".join([
        "# M71-C4b — confronto di Φ 2012 con la tavola dei flussi di capitale 1997", "",
        "Perimetro: attrezzature e strutture non residenziali, senza software. Indice di dissomiglianza ½Σ|a−b|.", "",
        f"- industrie confrontabili: {len(c)}",
        f"- Φ più vicina al 1997 della composizione comune: {int(c['phi_piu_vicina'].sum())} industrie su {len(c)}",
        f"- dissomiglianza media ponderata con l'investimento 2012: Φ {mp:.3f}; composizione comune {mc:.3f}",
        f"- industrie in cui la composizione comune è più vicina al 1997: {', '.join(peggiori)}", "",
        "Lettura: la somiglianza con una fonte indipendente (di 15 anni prima) è un controllo di plausibilità "
        "della struttura iniziale, non una validazione delle celle: tecnologie e prezzi relativi sono cambiati.",
    ]) + "\n"
