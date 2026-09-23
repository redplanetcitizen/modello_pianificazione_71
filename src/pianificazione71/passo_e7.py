"""Passo E7: condizione terminale in servizi produttivi (H29b, H29c) nella taratura standard con penalità.

H29b: Σ_{j,a∈{E,S,N}} w_{j,a} K_{j,a,T+1} ≥ f_FTE · Σ w_{j,a} K_{j,a,a0}, con w i pesi di capacità (costi d'uso 2012,
passo C6); R a valore come in H29. Rispetto a H29 (valore) il vincolo non premia i beni di lunga durata.
H29c: come H29b ma con il fattore dalla crescita della produzione privata (capitale in servizi proporzionale al prodotto).
Casi su 2012-2016 e 2010-2019, tutti con H9c e penalità H25b: H29 (valore, FTE), H29b (capacità, FTE), H29c (capacità, produzione).
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
from .passo_e5 import ORIZZONTI, TARATURA, fattori, rapporto_osservato
from .registro import Esecuzione

CASI = {"H29_valore": ({"terminale_pesi": "valore"}, "lavoro_aggregata"),
        "H29b_capacita": ({"terminale_pesi": "capacita"}, "lavoro_aggregata"),
        "H29c_capacita_produzione": ({"terminale_pesi": "capacita"}, "produzione_aggregata")}
PENALITA = {"penalita_var_inv": 0.10}


def rapporto_osservato_capacita(P, f: dict) -> dict:
    anni = list(P.anni)
    T1 = anni[-1] + 1
    out = {}
    for gruppo, fatt in f.items():
        k0 = kt = 0.0
        for (j, a) in P.K0.index:
            if a not in gruppo:
                continue
            pw = float(P.w.get((j, a), 1.0)) if a != "R" else 1.0
            k0 += pw * float(P.K0[(j, a)])
            kt += pw * float(P.K_oss.get((j, a, T1), 0.0))
        out[gruppo] = kt / (k0 * fatt)
    return out


def esegui(cfg: Configurazione) -> Esecuzione:
    max_o2 = sum(a * p for a, p in TRATTI_O2)
    with Esecuzione("M71-E7-terminale-servizi", cfg, parametri={"orizzonti": {k: list(v) for k, v in ORIZZONTI.items()},
                                                               "taratura": TARATURA, "penalita": PENALITA,
                                                               "casi": {k: {**m, "fattori": f} for k, (m, f) in CASI.items()}}) as es:
        tab, sintesi, ris_tutti = [], ["# M71-E7 — condizione terminale in servizi produttivi (H29b)", ""], {}
        for h, anni in ORIZZONTI.items():
            P = costruisci(cfg, anni, inviluppo=True)
            ft = fattori(P)
            ris = {}
            for nome, (mod, fonte) in CASI.items():
                h29 = ft[fonte]
                cal = dict(TARATURA, terminale_fattori=h29, **PENALITA, **mod)
                r4 = costruisci_e_risolvi(P, Opzioni(obiettivo="O4", **cal))
                r4n = costruisci_e_risolvi(P, Opzioni(obiettivo="O4", **dict(cal, penalita_var_inv=0.0)))
                r2 = costruisci_e_risolvi(P, Opzioni(obiettivo="O2", **cal))
                _scrivi_risultato(es, f"{h}_{nome}/O4", r4)
                riga = _scrivi_risultato(es, f"{h}_{nome}/O2", r2)
                oss = (rapporto_osservato_capacita(P, h29) if mod["terminale_pesi"] == "capacita"
                       else rapporto_osservato(P, h29))
                riga.update({"orizzonte": h, "caso": nome, "fattori": str({k: round(v, 4) for k, v in h29.items()}),
                             "osservato_su_richiesto": str({k: round(v, 3) for k, v in oss.items()}),
                             "distanza_O4_senza_penalita": r4n.obiettivo, "O4_con_penalita": r4.obiettivo})
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
        cols = ["orizzonte", "caso", "stato", "fattori", "osservato_su_richiesto", "distanza_O4_senza_penalita", "O4_con_penalita",
                "punteggio_su_massimo", "quota_consumo_a_1,2", "eccesso_consumo_cumulato_%", "anni_disinvestimento_netto"]
        sintesi = sintesi[:2] + ["```", t[[c for c in cols if c in t]].to_string(index=False, float_format=lambda v: f"{v:,.4g}"),
                                 "```", ""] + sintesi[2:]
        for h, n0 in (("2010-2019", 1), ("2012-2016", 4)):
            s, ris = ris_tutti[h]
            caso = "O2 H29c_capacita_produzione"
            if caso not in ris:
                continue
            chiave = f"{caso} {h}"
            NOMI[chiave], COLORI[chiave] = f"O2 tarato (H9c, H29c, penalità), {h}", "#393b79"
            se = pd.concat([s[s.caso == "osservato"], s[s.caso == caso].assign(caso=chiave)], ignore_index=True)
            nota = f"Orizzonte {h}; H9c; stock finale E+S+N in servizi produttivi ≥ crescita della produzione (H29c); penalità H25b."
            es.scrivi_byte(f"{n0}_H29c_{h}_produzione_consumo.png", _figura(
                se, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
                f"O2 tarato ed economia osservata, {h}: produzione e consumo", 1, 2, (16, 5.8), [chiave], nota))
            es.scrivi_byte(f"{n0 + 1}_H29c_{h}_investimento_per_tipo.png", _figura(
                se, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
                f"O2 tarato ed economia osservata, {h}: investimento per tipo", 2, 2, (16, 10), [chiave], nota))
            es.scrivi_byte(f"{n0 + 2}_H29c_{h}_stock_per_tipo.png", _figura(
                se, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
                f"O2 tarato ed economia osservata, {h}: stock per tipo", 2, 2, (16, 10), [chiave], nota))
        es.scrivi_testo("sintesi.md", "\n".join(sintesi) + "\n")
    return es
