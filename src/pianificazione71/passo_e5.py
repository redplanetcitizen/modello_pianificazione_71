"""Passo E5: taratura standard H9c (capacità fuori G.17 dall'inviluppo con tendenza) e condizione terminale tarata (H29).

Condizione terminale: stock finale del gruppo di tipi ≥ fattore × stock iniziale, con fattore dalla crescita osservata
di una grandezza di flusso (non dallo stock osservato, per non incorporare la traiettoria storica nel risultato):
  - produzione: industrie private per E, S, N; HS per R;
  - lavoro (FTE) per E, S, N; produzione di HS per R.
La crescita osservata tra il primo e l'ultimo anno (T − a0 anni) è estesa all'intervallo dello stock (a0 → T+1):
fattore = (y_T / y_a0)^((T + 1 − a0) / (T − a0)).
Varianti: per tipo (E, S, N separati) o aggregata (E+S+N insieme, R a parte).
Verifiche: O4 (la traiettoria osservata deve restare ammissibile), rapporto tra stock finale osservato e richiesto,
O2 puro (obiettivi = consumo osservato).
"""
from __future__ import annotations

import pandas as pd

from .archivio import Configurazione
from .dati_modello import costruisci
from .grafici import TIPI_TUTTI, serie
from .modello import TRATTI_O2, Opzioni, costruisci_e_risolvi
from .passo_c1 import _csv
from .passo_d import VARIANTE, _scrivi_risultato
from .passo_e1 import scarti
from .passo_e2 import COLORI, NOMI, _figura
from .passo_e4 import soddisfazione
from .registro import Esecuzione

ORIZZONTI = {"2012-2016": range(2012, 2017), "2010-2019": range(2010, 2020)}
TARATURA = {"capacita_non_g17": "inviluppo_tendenza", "sigma_fattore": VARIANTE["sigma_fattore"]}


def fattori(P) -> dict:
    anni = list(P.anni)
    a0, T = anni[0], anni[-1]
    esp = (T + 1 - a0) / (T - a0)
    x = lambda t: float(P.x_oss[t].reindex(P.private).sum())
    f_x = (x(T) / x(a0)) ** esp
    f_l = (P.lavoro_tot[T] / P.lavoro_tot[a0]) ** esp
    f_hs = (float(P.x_oss[T]["HS"]) / float(P.x_oss[a0]["HS"])) ** esp
    return {
        "mantenimento": None,
        "produzione_per_tipo": {"E": f_x, "S": f_x, "N": f_x, "R": f_hs},
        "produzione_aggregata": {"ESN": f_x, "R": f_hs},
        "lavoro_aggregata": {"ESN": f_l, "R": f_hs},
    }


def rapporto_osservato(P, fatt: dict | None) -> dict:
    """Stock osservato a T+1 / stock richiesto dalla condizione terminale, per gruppo (≥ 1: osservato ammissibile)."""
    anni = list(P.anni)
    T1 = anni[-1] + 1
    fatt = fatt or {"E": 1.0, "S": 1.0, "N": 1.0, "R": 1.0}
    chiavi = [(j, a) for (j, a) in P.K0.index]
    out = {}
    for gruppo, f in fatt.items():
        k0 = sum(float(P.K0[(j, a)]) for (j, a) in chiavi if a in gruppo)
        kt = sum(float(P.K_oss.get((j, a, T1), 0.0)) for (j, a) in chiavi if a in gruppo)
        out[gruppo] = kt / (k0 * f)
    return out


def esegui(cfg: Configurazione) -> Esecuzione:
    max_o2 = sum(a * p for a, p in TRATTI_O2)
    with Esecuzione("M71-E5-taratura-terminale", cfg, parametri={"orizzonti": {k: list(v) for k, v in ORIZZONTI.items()},
                                                                "taratura": TARATURA}) as es:
        tab, ris_tutti, sintesi = [], {}, ["# M71-E5 — taratura standard H9c e condizione terminale tarata (H29)", ""]
        for h, anni in ORIZZONTI.items():
            P = costruisci(cfg, anni, inviluppo=True)
            ft = fattori(P)
            ris = {}
            for nome, f in ft.items():
                cal = dict(TARATURA, terminale_fattori=f)
                r4 = costruisci_e_risolvi(P, Opzioni(obiettivo="O4", **cal))
                r2 = costruisci_e_risolvi(P, Opzioni(obiettivo="O2", **cal))
                _scrivi_risultato(es, f"{h}_{nome}/O4", r4)
                riga = _scrivi_risultato(es, f"{h}_{nome}/O2", r2)
                riga.update({"orizzonte": h, "terminale": nome, "fattori": str({k: round(v, 4) for k, v in (f or {}).items()}),
                             "distanza_O4": r4.obiettivo,
                             "osservato_su_richiesto": str({k: round(v, 3) for k, v in rapporto_osservato(P, f).items()})})
                if r2.stato == "Optimal":
                    d = soddisfazione(P, r2)
                    q = d.groupby("classe", observed=False)["peso"].sum() / len(P.anni)
                    du = r2.grezzi["duali"]
                    fam = du.index.str.split("[").str[0]
                    a = r2.tabelle["aggregati"]
                    oss_c = sum(float(P.consumo_oss[t].sum()) for t in anni)
                    riga.update({"punteggio_su_massimo": r2.obiettivo / (max_o2 * len(anni)),
                                 "quota_consumo_a_1,2": float(q["=1,2"]),
                                 "quota_sotto_obiettivo": float(q["<0,9"] + q["0,9-1"]),
                                 "eccesso_consumo_cumulato_%": (float(a["consumo_privato"].sum()) / oss_c - 1) * 100,
                                 "duale_lavoro_medio": float(du[fam == "lavoro"].abs().mean()),
                                 "duale_terminale": str(du[fam == "terminale"].round(4).to_dict())})
                    ris[f"O2 {nome}"] = r2
                tab.append(riga)
            s = serie(P, ris)
            es.scrivi_testo(f"serie_{h}.csv", _csv(s))
            sc = scarti(s)
            es.scrivi_testo(f"scarti_{h}.csv", _csv(sc.rename_axis("caso").reset_index()))
            sintesi += [f"## Scarti dall'osservato, orizzonte {h}", "", "```", sc.round(1).to_string(), "```", ""]
            ris_tutti[h] = (P, s, ris)
        t = pd.DataFrame(tab)
        es.scrivi_testo("casi.csv", _csv(t))
        cols = ["orizzonte", "terminale", "stato", "fattori", "osservato_su_richiesto", "distanza_O4", "punteggio_su_massimo",
                "quota_consumo_a_1,2", "quota_sotto_obiettivo", "eccesso_consumo_cumulato_%", "duale_lavoro_medio",
                "anni_disinvestimento_netto", "duale_terminale"]
        sintesi = sintesi[:2] + ["```", t[[c for c in cols if c in t]].to_string(index=False, float_format=lambda v: f"{v:,.4g}"),
                                 "```", ""] + sintesi[2:]
        # grafici: O2 con terminale tarato sul lavoro (aggregato: l'unica variante che lascia ammissibile l'osservato), 2010-2019
        P, s, ris = ris_tutti["2010-2019"]
        caso = "O2 lavoro_aggregata"
        if caso in ris:
            NOMI[caso], COLORI[caso] = "O2, H9c + terminale tarato sul lavoro, 2010-19", "#17becf"
            se = s[s.caso.isin(["osservato", caso])]
            nota = "Orizzonte 2010-2019; capacità H9c; stock finale E+S+N ≥ crescita del lavoro (FTE), R ≥ crescita di HS."
            es.scrivi_byte("1_O2_terminale_produzione_consumo.png", _figura(
                se, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
                "O2 con taratura H9c e terminale tarato ed economia osservata: produzione e consumo", 1, 2, (16, 5.8), [caso], nota))
            es.scrivi_byte("2_O2_terminale_investimento_per_tipo.png", _figura(
                se, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
                "O2 con taratura H9c e terminale tarato ed economia osservata: investimento per tipo", 2, 2, (16, 10), [caso], nota))
            es.scrivi_byte("3_O2_terminale_stock_per_tipo.png", _figura(
                se, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
                "O2 con taratura H9c e terminale tarato ed economia osservata: stock per tipo", 2, 2, (16, 10), [caso], nota))
        es.scrivi_testo("sintesi.md", "\n".join(sintesi) + "\n")
    return es
