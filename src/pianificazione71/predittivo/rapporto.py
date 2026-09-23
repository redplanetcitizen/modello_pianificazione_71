"""Rapporto tecnico in Markdown per un'esecuzione M71-E6-predittivo."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .audit import classificazione_md, tabella_audit
from .formulazioni import RIFERIMENTO_P1


def _md(df: pd.DataFrame, fmt="{:,.3f}") -> str:
    d = df.copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].map(lambda v: "" if pd.isna(v) else fmt.format(v))
    righe = ["| " + " | ".join(str(c) for c in d.columns) + " |", "|" + "---|" * len(d.columns)]
    righe += ["| " + " | ".join(str(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join(righe)


def genera(cartella: Path, stabilita: dict[str, pd.DataFrame] | None = None, e6_insample: pd.DataFrame | None = None) -> str:
    cartella = Path(cartella)
    es = json.loads((cartella / "esecuzione.json").read_text(encoding="utf-8"))
    sel = pd.read_csv(cartella / "selezione_annidata.csv")
    tempi = pd.read_csv(cartella / "tempi.csv")
    diag = json.loads((cartella / "diagnostica.json").read_text(encoding="utf-8"))
    par = es.get("parametri", {})
    R = ["# M71-E6-predittivo — rapporto tecnico", "",
         f"Esecuzione `{es['id']}`; commit `{es.get('codice', {}).get('commit')}`; ambiente {es.get('ambiente', {}).get('pacchetti')}.", "",
         "## 1. Natura dell'esperimento", "",
         "- **Pseudo-previsione fuori campione:** i dati BEA, Fed e BLS sono le versioni revisionate dell'archivio (2025-2026), non i vintage "
         "disponibili alle rispettive date. Nessun vintage storico è nell'archivio: la previsione real-time non è possibile.",
         "- **Previsione completa:** tutte le grandezze future sono previste da dati ≤ τ (previsori preliminari selezionati su origini < τ).",
         "- **Previsione condizionata:** solo il caso `condizionata|…` riceve le esogene future osservate (lavoro, domanda pubblica, esportazioni, "
         "importazioni, obiettivi di consumo, coefficienti tecnici). Misura l'allocazione, non la previsione ex ante.",
         "- **Adattamento in-sample:** E6 originale (2012-2016) usa dati 2012-2019 nella calibrazione ed è riportato come confronto in-sample.",
         "- **Orizzonte mobile (closed loop):** a ogni origine lo stato è quello osservato; nessuna simulazione open-loop è usata nelle metriche.",
         f"- **Intervallo ammesso:** {par.get('SIMULATION_YEAR_MIN')} ≤ τ < τ+h ≤ {par.get('SIMULATION_YEAR_MAX')}; origini {par.get('origini')}; H massimo {par.get('H_max')}.",
         "- **Regime di shock:** origini 2008 e 2009 (obiettivi 2009-2010) contrassegnate; protocollo B = obiettivi 2010-2019; C = 2012-2016.", "",
         "## 2. Audit dell'informazione", "", _md(tabella_audit(), "{}"), "",
         "Regole applicate: nessuna tendenza di capacità stimata oltre τ; crescita degli FTE prevista, non osservata; obiettivi O2 = consumo previsto; "
         "B, D, Φ, μ, σ persistenti dall'anno τ; iperparametri scelti solo su origini precedenti l'origine di test.", "",
         "## 3. Classificazione delle variabili", "", classificazione_md(), "",
         "## 4. Formulazioni e griglia", "",
         "- P0: previsioni preliminari (metodo selezionato per serie) senza riconciliazione.",
         "- P1: O2 con obiettivi ĉ; tratti (E6, stretto, largo, tetto100, tetto110) × gradualità (agg, agg+ind, ind, nessuna) × chiusura (T1, T2, T3).",
         "- P2: tracking L1 (LP con deviazioni assolute; nessun QP): λ_x ∈ {0,5; 2}, λ_I ∈ {0,1; 0,5}, T1/T3; varianti con tracking di investimento, "
         "importazioni e scorte previsti; variante a pesi uniformi.",
         "- P3: P1 di riferimento con lavoro e importazioni totali al quantile 0,25 / 0,75 dei rapporti osservato/previsto di validazione.",
         "- Benchmark: persistenza, ultimo tasso, trend mobile (5 anni), P0; E6 in-sample.",
         f"- Configurazioni LP per origine: {len(par.get('configurazioni', {}))} + {len(par.get('robuste', {}))} robuste + 1 condizionata; "
         f"risoluzioni totali {len(tempi)}, tempo medio {tempi['secondi'].mean():.1f} s, massimo {tempi['secondi'].max():.1f} s.", ""]
    # risultati per finestra
    R += ["## 5. Risultati (indicatore S = Σ α_g WMAE_g / WMAE_g(persistenza); < 1 batte la persistenza)", "",
          "Pesi α: produzione 0,30; consumo 0,30; investimento per tipo 0,20; stock per tipo 0,10; importazioni 0,05; scorte 0,05. "
          "Le componenti r_g sono riportate accanto a S.", ""]
    for fin in ("A_2008_2019", "B_2010_2019", "C_2012_2016", "C_2012_2016_origine_2011"):
        f = cartella / f"sintesi_S_{fin}.csv"
        if not f.is_file():
            continue
        s = pd.read_csv(f)
        R += [f"### {fin}", ""]
        for h, g in s.groupby("h"):
            g = g.sort_values("S")
            testa = g.head(10)
            rif = g[g["caso"].isin(["persistenza", "ultimo_tasso", "trend_mobile", "P0", RIFERIMENTO_P1, "selezionata",
                                    "condizionata|" + RIFERIMENTO_P1])]
            tab = pd.concat([testa, rif]).drop_duplicates("caso").sort_values("S")
            R += [f"h = {h}:", "", _md(tab[["caso", "S"] + [c for c in tab.columns if c.startswith("r_")]]), ""]
        m = pd.read_csv(cartella / f"metriche_{fin}.csv")
        m1 = m[(m["h"] == 1) & (m["gruppo"] == "aggregati")].sort_values("WMAE")
        R += ["Aggregati, h = 1 (MAE, RMSE, sMAPE, errore sui tassi, accuratezza del segno, Theil U):", "",
              _md(m1[["caso", "MAE", "RMSE", "sMAPE", "errore_tassi", "segno", "theil_U"]].head(14)), ""]
        ms = m[(m["h"] == 1) & (m["caso"].isin(["persistenza", "P0", RIFERIMENTO_P1, "selezionata"]))]
        R += ["Per gruppo, h = 1 (WMAE e rapporto con la persistenza):", "",
              _md(ms.pivot_table(index="gruppo", columns="caso", values="rapporto_WMAE").reset_index()), ""]
    if e6_insample is not None:
        R += ["### E6 originale (in-sample, 2012-2016)", "", _md(e6_insample), ""]
    R += ["## 6. Selezione annidata degli iperparametri (h = 1)", "", _md(sel, "{:,.3f}"), "",
          "La configurazione scelta per l'origine τ minimizza S medio sulle origini < τ (almeno 2); le origini senza storia sufficiente usano la "
          "configurazione predefinita. La riga `selezionata` nelle tabelle è la sequenza risultante, mai scelta sul periodo di test.", ""]
    # diagnostica
    d = pd.DataFrame([{k: v for k, v in x.items() if not isinstance(v, dict)} for x in diag if x.get("stato") == "Optimal"])
    if len(d):
        dd = d[d["caso"].isin([RIFERIMENTO_P1, *sel["scelta"].unique()])]
        cols = [c for c in ("caso", "origine", "utilizzo_capacita_medio", "utilizzo_capacita_quota_piena", "duale_lavoro_medio",
                            "duale_capacita_medio", "quota_variabili_a_zero", "quota_=1.2", "quota_=1.0", "quota_<0.9") if c in dd]
        R += ["## 7. Diagnostica della soluzione", "", _md(dd[cols].groupby("caso").mean(numeric_only=True).reset_index()), ""]
        lav = pd.DataFrame([{"caso": x["caso"], "origine": x["origine"], "lavoro_h1": list(x["utilizzo_lavoro"].values())[0],
                             "import_su_tetto_h1": list(x["importazioni_su_tetto"].values())[0],
                             "residuo_h1": list(x["residuo_materiale"].values())[0], "inv_netto_h1": list(x["investimento_netto"].values())[0]}
                            for x in diag if x.get("stato") == "Optimal" and x["caso"] in (RIFERIMENTO_P1, *sel["scelta"].unique())])
        R += ["Utilizzo del lavoro, importazioni sul tetto, residuo materiale e investimento netto (h = 1), medie per caso:", "",
              _md(lav.groupby("caso").mean(numeric_only=True).reset_index()), ""]
    if stabilita:
        R += ["## 8. Stabilità numerica (origine 2013, H = 2)", ""]
        for nome, t in stabilita.items():
            R += [f"**{nome}**", "", _md(t, "{:,.4f}"), ""]
    R += ["## 9. Tempi di calcolo", "", _md(tempi.groupby("H")["secondi"].describe()[["count", "mean", "max"]].reset_index()), ""]
    return "\n".join(R) + "\n"


def completa(cfg, cartella: Path, cache: str = "cache", stabilita_origine: int = 2013) -> Path:
    """Verifiche di stabilità sulle configurazioni principali, confronto E6 in-sample e scrittura di rapporto.md."""
    from .formulazioni import griglia
    from .origine import fattori_terminali, parametri_origine
    from .stabilita import verifica
    from .storico import costruisci_storico
    cartella = Path(cartella)
    sel = pd.read_csv(cartella / "selezione_annidata.csv")
    casi = [RIFERIMENTO_P1] + [c for c in sel["scelta"].unique() if c != RIFERIMENTO_P1 and not c.startswith("P3")]
    S = costruisci_storico(cfg, cache=cache, verbose=False)
    P, note = parametri_origine(S, stabilita_origine, 2)
    f = fattori_terminali(P, note)
    g = griglia()
    stab = {}
    for c in casi[:3]:
        if c in g:
            o = dict(g[c]["opzioni"])
            stab[c] = verifica(P, stabilita_origine, o, f if o.get("terminale", True) else None)
            stab[c].to_csv(cartella / f"stabilita_{c.replace('|', '_').replace('%', 'pc')}.csv", index=False)
    e6 = e6_in_sample(cartella)
    from .grafici_predittivo import genera as grafici
    figure = grafici(cartella)
    testo = genera(cartella, stab, e6)
    testo += "\n## 10. Grafici\n\n" + "\n".join(f"![{f.stem}]({f.name})" for f in figure) + "\n"
    (cartella / "rapporto.md").write_text(testo, encoding="utf-8")
    return cartella / "rapporto.md"


def e6_in_sample(cartella: Path) -> pd.DataFrame | None:
    """Errori dello scenario E6 originale (2012-2016, in-sample) sugli aggregati, dalle esecuzioni M71-E6 registrate."""
    runs = sorted((cartella.parent).glob("*_M71-E6-taratura-gradualita"))
    if not runs:
        return None
    f = runs[-1] / "serie_2012-2016.csv"
    if not f.is_file():
        return None
    s = pd.read_csv(f)
    oss = s[s["caso"] == "osservato"].set_index(["variabile", "anno"])["valore"]
    mod = s[s["caso"] == "O2 penalita"].set_index(["variabile", "anno"])["valore"]
    m = pd.concat([oss.rename("osservato"), mod.rename("E6")], axis=1).dropna().reset_index()
    m = m[m["anno"] <= 2016]
    righe = []
    for var, g in m.groupby("variabile"):
        e = g["E6"] - g["osservato"]
        righe.append({"variabile": var, "MAE": float(e.abs().mean()), "sMAPE": float((2 * e.abs() / (g["E6"].abs() + g["osservato"].abs())).mean()),
                      "nota": "in-sample: calibrazione con dati 2012-2019 (H9c 1997-2019, H29 con FTE osservati 2012-2016)"})
    return pd.DataFrame(righe)
