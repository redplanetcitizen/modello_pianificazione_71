"""Passo E6: taratura standard (H9c + H29 legata al lavoro) con i meccanismi di gradualità dell'investimento (H25, H26).

Casi, su 2012-2016 e 2010-2019:
  - taratura: H9c + H29 (E+S+N ≥ crescita FTE; R ≥ crescita di HS);
  - + penalità a gradini sulle variazioni annue per tipo (H25b: libera fino al 5%, poi p = 0,1);
  - + limite ±15% alla variazione annua per tipo (H25a);
  - + penalità e tempi di costruzione per S e R (H25b + H26).
Verifiche: O4 (ammissibilità dell'osservato con gli stessi vincoli), O2 puro (obiettivi = consumo osservato).
"""
from __future__ import annotations

import pandas as pd

from .archivio import Configurazione
from .dati_modello import costruisci
from .grafici import TIPI_TUTTI, serie
from .modello import TRATTI_O2, Opzioni, costruisci_e_risolvi
from .passo_c1 import _csv
from .passo_d import _scrivi_risultato
from .passo_e1 import scarti
from .passo_e2 import COLORI, NOMI, _figura
from .passo_e4 import soddisfazione
from .passo_e5 import ORIZZONTI, TARATURA, fattori
from .registro import Esecuzione

MECCANISMI = {
    "taratura": {},
    "penalita": {"penalita_var_inv": 0.10},
    "limite_15%": {"limite_var_inv": 0.15},
    "penalita_tempi_costruzione": {"penalita_var_inv": 0.10, "tempi_costruzione": ("S", "R")},
}


def esegui(cfg: Configurazione) -> Esecuzione:
    max_o2 = sum(a * p for a, p in TRATTI_O2)
    with Esecuzione("M71-E6-taratura-gradualita", cfg, parametri={"orizzonti": {k: list(v) for k, v in ORIZZONTI.items()},
                                                                 "taratura": TARATURA, "meccanismi": MECCANISMI}) as es:
        tab, sintesi, ris_tutti = [], ["# M71-E6 — taratura standard (H9c + H29) con gradualità dell'investimento", ""], {}
        for h, anni in ORIZZONTI.items():
            P = costruisci(cfg, anni, inviluppo=True)
            h29 = fattori(P)["lavoro_aggregata"]
            ris = {}
            for nome, mod in MECCANISMI.items():
                cal = dict(TARATURA, terminale_fattori=h29, **mod)
                r4 = costruisci_e_risolvi(P, Opzioni(obiettivo="O4", **cal))
                r2 = costruisci_e_risolvi(P, Opzioni(obiettivo="O2", **cal))
                _scrivi_risultato(es, f"{h}_{nome}/O4", r4)
                riga = _scrivi_risultato(es, f"{h}_{nome}/O2", r2)
                riga.update({"orizzonte": h, "meccanismo": nome, "distanza_O4": r4.obiettivo, "stato_O4": r4.stato})
                if r2.stato == "Optimal":
                    d = soddisfazione(P, r2)
                    q = d.groupby("classe", observed=False)["peso"].sum() / len(anni)
                    a = r2.tabelle["aggregati"]
                    oss_c = sum(float(P.consumo_oss[t].sum()) for t in anni)
                    riga.update({"punteggio_su_massimo": r2.obiettivo / (max_o2 * len(anni)),
                                 "quota_consumo_a_1,2": float(q["=1,2"]),
                                 "eccesso_consumo_cumulato_%": (float(a["consumo_privato"].sum()) / oss_c - 1) * 100})
                    ris[f"O2 {nome}"] = r2
                tab.append(riga)
            s = serie(P, ris)
            es.scrivi_testo(f"serie_{h}.csv", _csv(s))
            sc = scarti(s)
            es.scrivi_testo(f"scarti_{h}.csv", _csv(sc.rename_axis("caso").reset_index()))
            sintesi += [f"## Scarti dall'osservato, orizzonte {h}", "", "```", sc.round(1).to_string(), "```", ""]
            ris_tutti[h] = (s, ris)
        t = pd.DataFrame(tab)
        es.scrivi_testo("casi.csv", _csv(t))
        cols = ["orizzonte", "meccanismo", "stato", "stato_O4", "distanza_O4", "punteggio_su_massimo", "quota_consumo_a_1,2",
                "eccesso_consumo_cumulato_%", "anni_disinvestimento_netto", "investimento_netto_min"]
        sintesi = sintesi[:2] + ["```", t[[c for c in cols if c in t]].to_string(index=False, float_format=lambda v: f"{v:,.4g}"),
                                 "```", ""] + sintesi[2:]
        s, ris = ris_tutti["2010-2019"]
        for n0, caso, titolo in ((1, "O2 penalita", "O2 tarato + penalità"), (4, "O2 penalita_tempi_costruzione",
                                                                               "O2 tarato + penalità + tempi di costruzione")):
            if caso not in ris:
                continue
            NOMI[caso], COLORI[caso] = f"{titolo}, 2010-19", "#bcbd22" if n0 == 1 else "#e377c2"
            se = s[s.caso.isin(["osservato", caso])]
            nota = "Orizzonte 2010-2019; H9c; H29 (E+S+N ≥ crescita FTE, R ≥ crescita HS); penalità sulle variazioni (H25b)."
            pref = caso.replace("O2 ", "")
            es.scrivi_byte(f"{n0}_{pref}_produzione_consumo.png", _figura(
                se, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
                f"{titolo} ed economia osservata: produzione e consumo", 1, 2, (16, 5.8), [caso], nota))
            es.scrivi_byte(f"{n0 + 1}_{pref}_investimento_per_tipo.png", _figura(
                se, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
                f"{titolo} ed economia osservata: investimento per tipo", 2, 2, (16, 10), [caso], nota))
            es.scrivi_byte(f"{n0 + 2}_{pref}_stock_per_tipo.png", _figura(
                se, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
                f"{titolo} ed economia osservata: stock per tipo", 2, 2, (16, 10), [caso], nota))
        es.scrivi_testo("sintesi.md", "\n".join(sintesi) + "\n")
    return es
