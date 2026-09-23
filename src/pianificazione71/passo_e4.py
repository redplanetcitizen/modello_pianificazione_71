"""Passo E4: taratura della capacità delle industrie senza dati G.17 sull'inviluppo dei massimi 1997-2019 (H9c).

Metodi confrontati (G.17 invariata dove esiste):
  - uniforme (H9b): utilizzo nell'anno di avvio = utilizzo G.17 dell'industria totale (0,772 nel 2012; 0,734 nel 2010);
  - inviluppo: capacità = K^cap × massimo storico 1997-2019 del rapporto produzione / K^cap;
  - inviluppo_tendenza (peak-to-peak): capacità = K^cap × tendenza log-lineare del rapporto spostata sul massimo
    storico, con deriva θ_j pari alla tendenza.
Anche HS è calibrata sull'inviluppo nei due metodi nuovi.

Verifiche di taratura (nessuno stress test; obiettivi O2 = consumo osservato):
  1. controllo al punto osservato (industrie oltre la capacità);
  2. O4 (distanza dalla traiettoria osservata);
  3. O2 puro: punteggio, quota di consumo a +20% (tetto del premio), eccesso di consumo, prezzi ombra.
"""
from __future__ import annotations

import pandas as pd

from .archivio import Configurazione
from .controllo_osservato import controlla
from .dati_modello import costruisci
from .grafici import TIPI_TUTTI, serie
from .modello import TRATTI_O2, Opzioni, costruisci_e_risolvi
from .passo_c1 import _csv
from .passo_d import VARIANTE, _scrivi_risultato
from .passo_e1 import scarti
from .passo_e2 import COLORI, NOMI, _figura, utilizzo_totale
from .registro import Esecuzione

ORIZZONTI = {"2012-2016": range(2012, 2017), "2010-2019": range(2010, 2020)}
METODI = ("uniforme", "inviluppo", "inviluppo_tendenza")


def soddisfazione(P, R) -> pd.DataFrame:
    """Quota del consumo (pesi = quote osservate) per classe di soddisfazione ρ = consumo / obiettivo."""
    v, xv = R.grezzi["v"], R.grezzi["valori"]
    righe = []
    for t in P.anni:
        ob = P.consumo_oss[t].clip(lower=0)
        for c in P.prodotti:
            if ob[c] > 0:
                righe.append({"anno": t, "prodotto": c, "rho": float(xv[v[("c", c, t)]]) / float(ob[c]), "peso": float(ob[c] / ob.sum())})
    d = pd.DataFrame(righe)
    d["classe"] = pd.cut(d["rho"], [-1, 0.899, 0.999, 1.001, 1.199, 1.201, 99],
                         labels=["<0,9", "0,9-1", "=1", "1-1,2", "=1,2", ">1,2"])
    return d


def esegui(cfg: Configurazione) -> Esecuzione:
    u_tot = {h: utilizzo_totale(cfg, a[0]) if a[0] != 2012 else VARIANTE["u_non_g17"] for h, a in ORIZZONTI.items()}
    max_o2 = sum(a * p for a, p in TRATTI_O2)
    with Esecuzione("M71-E4-taratura-capacita", cfg, parametri={"orizzonti": {k: list(v) for k, v in ORIZZONTI.items()},
                                                               "metodi": METODI, "u_uniforme": u_tot}) as es:
        tab, righe_sint = [], ["# M71-E4 — taratura della capacità fuori G.17 (inviluppo 1997-2019)", ""]
        for h, anni in ORIZZONTI.items():
            P = costruisci(cfg, anni, inviluppo=True)
            es.scrivi_testo(f"inviluppo_{h}.csv", _csv(P.capacita_inviluppo))
            ris = {}
            for m in METODI:
                cal = {"u_non_g17": u_tot[h], "sigma_fattore": VARIANTE["sigma_fattore"], "capacita_non_g17": m}
                ctrl = controlla(P, u_non_g17=u_tot[h], sigma_fattore=cal["sigma_fattore"], capacita_non_g17=m)
                es.scrivi_testo(f"{h}_{m}/controllo_capacita.csv", _csv(ctrl["capacita"]))
                viol = ctrl["capacita"].groupby("anno")["violato"].sum()
                r4 = costruisci_e_risolvi(P, Opzioni(obiettivo="O4", **cal))
                r2 = costruisci_e_risolvi(P, Opzioni(obiettivo="O2", **cal))
                riga = _scrivi_risultato(es, f"{h}_{m}/O2", r2)
                _scrivi_risultato(es, f"{h}_{m}/O4", r4)
                riga.update({"orizzonte": h, "metodo": m, "violazioni_capacita_oss": int(viol.sum()),
                             "industrie_max_violate": int(viol.max()), "distanza_O4": r4.obiettivo})
                if r2.stato == "Optimal":
                    d = soddisfazione(P, r2)
                    es.scrivi_testo(f"{h}_{m}/soddisfazione_O2.csv", _csv(d))
                    q = d.groupby("classe", observed=False)["peso"].sum() / len(P.anni)
                    du = r2.grezzi["duali"]
                    fam = du.index.str.split("[").str[0]
                    a = r2.tabelle["aggregati"]
                    oss_c = sum(float(P.consumo_oss[t].sum()) for t in anni)
                    riga.update({"punteggio_su_massimo": r2.obiettivo / (max_o2 * len(P.anni)),
                                 "quota_consumo_a_1,2": float(q["=1,2"]), "quota_consumo_a_1": float(q["=1"]),
                                 "quota_sotto_obiettivo": float(q["<0,9"] + q["0,9-1"]),
                                 "eccesso_consumo_cumulato_%": (float(a["consumo_privato"].sum()) / oss_c - 1) * 100,
                                 "duale_lavoro_medio": float(du[fam == "lavoro"].abs().mean()),
                                 "vincoli_capacita_attivi": int((du[fam == "capacita"].abs() > 1e-9).sum()),
                                 "duale_capacita_medio": float(du[fam == "capacita"].abs().mean())})
                    ris[f"O2 {m}"] = r2
                tab.append(riga)
            s = serie(P, ris)
            es.scrivi_testo(f"serie_{h}.csv", _csv(s))
            sc = scarti(s)
            es.scrivi_testo(f"scarti_{h}.csv", _csv(sc.rename_axis("caso").reset_index()))
            righe_sint += [f"## Orizzonte {h}", "", "```", sc.round(1).to_string(), "```", ""]
            if h == "2010-2019" and "O2 inviluppo_tendenza" in ris:
                caso = "O2 inviluppo_tendenza"
                NOMI[caso], COLORI[caso] = "O2, capacità da inviluppo con tendenza, 2010-19", "#8c564b"
                se = s[s.caso.isin(["osservato", caso])]
                nota = "Orizzonte 2010-2019; capacità fuori G.17 dall'inviluppo 1997-2019 (peak-to-peak)."
                es.scrivi_byte("1_O2_inviluppo_produzione_consumo.png", _figura(
                    se, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
                    "O2 con capacità tarata sull'inviluppo ed economia osservata: produzione e consumo", 1, 2, (16, 5.8), [caso], nota))
                es.scrivi_byte("2_O2_inviluppo_investimento_per_tipo.png", _figura(
                    se, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
                    "O2 con capacità tarata sull'inviluppo ed economia osservata: investimento per tipo", 2, 2, (16, 10), [caso], nota))
                es.scrivi_byte("3_O2_inviluppo_stock_per_tipo.png", _figura(
                    se, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
                    "O2 con capacità tarata sull'inviluppo ed economia osservata: stock per tipo", 2, 2, (16, 10), [caso], nota))
        t = pd.DataFrame(tab)
        es.scrivi_testo("casi.csv", _csv(t))
        cols = ["orizzonte", "metodo", "stato", "violazioni_capacita_oss", "distanza_O4", "punteggio_su_massimo",
                "quota_consumo_a_1,2", "quota_consumo_a_1", "quota_sotto_obiettivo", "eccesso_consumo_cumulato_%",
                "duale_lavoro_medio", "vincoli_capacita_attivi", "duale_capacita_medio", "anni_disinvestimento_netto"]
        righe_sint = righe_sint[:2] + ["```", t[[c for c in cols if c in t]].to_string(index=False, float_format=lambda v: f"{v:,.4g}"),
                                       "```", ""] + righe_sint[2:]
        es.scrivi_testo("sintesi.md", "\n".join(righe_sint) + "\n")
    return es
