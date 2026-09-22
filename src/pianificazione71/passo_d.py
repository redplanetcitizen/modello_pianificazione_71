"""Esecuzioni registrate del passo D: controllo al punto osservato, O4, obiettivi O1-O3, sensibilità."""
from __future__ import annotations

import dataclasses
import io
import time

import pandas as pd

from .archivio import Configurazione
from .controllo_osservato import controlla
from .dati_modello import Parametri, costruisci
from .modello import Opzioni, costruisci_e_risolvi
from .passo_c1 import _csv
from .registro import Esecuzione

# Varianti di calibrazione (registro delle decisioni): base della specifica e variante proposta dopo il controllo D0
BASE = {"u_non_g17": 1.0, "sigma_fattore": 1.0}               # H9, H13
VARIANTE = {"u_non_g17": 0.772, "sigma_fattore": 0.85}         # H9b (utilizzo 2012 dell'industria G.17), H13b
COLONNE = ["anno", "produzione_lorda", "consumo_privato", "gamma", "investimento_E", "investimento_S",
           "investimento_N", "investimento_R", "investimento_netto", "ammortamento", "variazione_scorte",
           "importazioni", "residuo_materiale", "surplus_economico"]


def _scrivi_risultato(es: Esecuzione, cartella: str, R) -> dict:
    riga = {"caso": cartella, "stato": R.stato, "valore_obiettivo": R.obiettivo, "variabili": R.n_var, "vincoli": R.n_vincoli,
            **{k: v for k, v in dataclasses.asdict(R.opzioni).items()}}
    if R.stato == "Optimal":
        for nome, df in R.tabelle.items():
            es.scrivi_testo(f"{cartella}/{nome}.csv", _csv(df if isinstance(df, pd.DataFrame) else df.to_frame("valore"),
                                                          index=not isinstance(df, pd.DataFrame)))
        a = R.tabelle["aggregati"]
        riga.update({"gamma_2016": float(a["gamma"].iloc[-1]), "consumo_cumulato": float(a["consumo_privato"].sum()),
                     "investimento_netto_min": float(a["investimento_netto"].min()),
                     "anni_disinvestimento_netto": int((a["investimento_netto"] < 0).sum()),
                     "residuo_materiale_totale": float(a["residuo_materiale"].sum())})
    return riga


def _tabella(a: pd.DataFrame) -> str:
    return "```\n" + a[COLONNE].to_string(index=False, float_format=lambda v: f"{v:,.1f}") + "\n```"


def esegui(cfg: Configurazione) -> list[Esecuzione]:
    t0 = time.time()
    P = costruisci(cfg)
    esecuzioni = [controllo(cfg, P), obiettivo_o4(cfg, P), obiettivi(cfg, P), sensibilita(cfg, P)]
    print(f"passo D completato in {time.time() - t0:.0f} s")
    return esecuzioni


def controllo(cfg, P: Parametri) -> Esecuzione:
    with Esecuzione("M71-D0-controllo-osservato", cfg, parametri={"varianti": {"base": BASE, "variante": VARIANTE}}) as es:
        righe = ["# M71-D0 — vincoli del modello al punto osservato", ""]
        for nome, var in (("base", BASE), ("variante", VARIANTE)):
            r = controlla(P, **var)
            for k, df in r.items():
                es.scrivi_testo(f"{nome}/{k}.csv", _csv(df))
            b, c, s = r["bilanci"], r["capacita"], r["scorte"]
            righe += [f"## Calibrazione {nome}: {var}", "",
                      f"- bilanci materiali: residuo aggregato per anno {b.groupby('anno')['residuo'].sum().round(1).to_dict()} miliardi; "
                      f"residui negativi (somma) {b[b.residuo < 0].groupby('anno')['residuo'].sum().round(1).to_dict()}",
                      f"- capacità: industrie con utilizzo implicito > 1 per anno {c.groupby('anno')['violato'].sum().to_dict()}; "
                      f"massimo {c['utilizzo_implicito'].max():.3f}",
                      f"- scorte minime violate (comparti) {s.groupby('anno')['violato'].sum().to_dict()}",
                      f"- lavoro usato/disponibile e importazioni/tetto: 1 per costruzione", ""]
        es.scrivi_testo("sintesi.md", "\n".join(righe) + "\n")
    return es


def obiettivo_o4(cfg, P) -> Esecuzione:
    with Esecuzione("M71-D1-O4-distanza", cfg, parametri={"varianti": {"base": BASE, "variante": VARIANTE}}) as es:
        righe, tab = ["# M71-D1 — O4: traiettoria ammissibile più vicina a quella osservata", ""], []
        for nome, var in (("base", BASE), ("variante", VARIANTE)):
            R = costruisci_e_risolvi(P, Opzioni(obiettivo="O4", **var))
            tab.append(_scrivi_risultato(es, nome, R))
            righe += [f"## {nome}: {var} — stato {R.stato}, distanza {R.obiettivo:.4f}", "", _tabella(R.tabelle["aggregati"]), ""]
        es.scrivi_testo("casi.csv", _csv(pd.DataFrame(tab)))
        es.scrivi_testo("sintesi.md", "\n".join(righe) + "\n")
    return es


def obiettivi(cfg, P) -> Esecuzione:
    casi = {"O1": Opzioni(obiettivo="O1", **VARIANTE), "O2": Opzioni(obiettivo="O2", **VARIANTE),
            "O3": Opzioni(obiettivo="O3", **VARIANTE), "O1_base": Opzioni(obiettivo="O1", **BASE)}
    with Esecuzione("M71-D2-obiettivi", cfg, parametri={k: dataclasses.asdict(v) for k, v in casi.items()}) as es:
        righe, tab = ["# M71-D2 — obiettivi O1, O2, O3", ""], []
        for nome, o in casi.items():
            R = costruisci_e_risolvi(P, o)
            tab.append(_scrivi_risultato(es, nome, R))
            righe += [f"## {nome} — stato {R.stato}, obiettivo {R.obiettivo}", ""]
            if R.stato == "Optimal":
                righe += [_tabella(R.tabelle["aggregati"]), ""]
        es.scrivi_testo("casi.csv", _csv(pd.DataFrame(tab)))
        es.scrivi_testo("sintesi.md", "\n".join(righe) + "\n")
    return es


def sensibilita(cfg, P) -> Esecuzione:
    base = dict(obiettivo="O1", **VARIANTE)
    casi = {
        "riferimento": {},
        "capacita_leontief": {"capacita_tipo": "leontief"},
        "deriva_servizi_-1.8%": {"theta_non_g17": -0.018},
        "senza_deriva": {"deriva": False},
        "bande_import_0": {"epsilon": 0.0},
        "bande_import_25%": {"epsilon": 0.25},
        "lavoro_+2%": {"lavoro_scala": 1.02},
        "terminale_+5%": {"crescita_terminale": 0.05},
        "beta_0.97": {"beta": 0.97},
        "senza_capacita": {"capacita": False},
        "senza_terminale": {"terminale": False},
        "senza_terminale_scorte": {"terminale_scorte": False},
        "senza_massimo_scorte": {"sigma_max_fattore": None},
    }
    with Esecuzione("M71-D3-sensibilita", cfg, parametri={"base": base, "casi": casi}) as es:
        tab = []
        for nome, mod in casi.items():
            R = costruisci_e_risolvi(P, Opzioni(**{**base, **mod}))
            tab.append(_scrivi_risultato(es, nome, R))
        t = pd.DataFrame(tab)
        es.scrivi_testo("casi.csv", _csv(t))
        cols = ["caso", "stato", "gamma_2016", "consumo_cumulato", "anni_disinvestimento_netto", "investimento_netto_min"]
        es.scrivi_testo("sintesi.md", "# M71-D3 — sensibilità (obiettivo O1, calibrazione variante)\n\n```\n"
                        + t[[c for c in cols if c in t]].to_string(index=False, float_format=lambda v: f"{v:,.3f}") + "\n```\n")
    return es
