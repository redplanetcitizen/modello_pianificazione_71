"""Grafici dei risultati di un'esecuzione M71-E6-predittivo (PNG nella cartella dell'esecuzione).

1. S a un passo per caso (protocollo B): barre orizzontali, riferimento persistenza = 1.
2. S per orizzonte h (protocollo B): barre raggruppate per i casi principali.
3. Componenti r_g a un passo (protocollo B): barre raggruppate per gruppo di variabili.
4. Errore percentuale a un passo per anno su consumo e investimento totali: casi principali.
Colori: palette categorica validata (blu, arancio, verde acqua, viola, giallo) + grigio per i benchmark.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .formulazioni import RIFERIMENTO_P1  # noqa: E402

COL = {"P0": "#2a78d6", "P2": "#1baf7a", "P1": "#eb6834", "cond": "#4a3aa7", "sel": "#eda100", "bench": "#8a8987", "pers": "#52514e"}
NOMI = {"P0": "P0 — previsori preliminari", "ultimo_tasso": "Ultimo tasso", "trend_mobile": "Trend mobile", "persistenza": "Persistenza",
        "selezionata": "Sequenza selezionata (annidata)"}
GRUPPI = {"r_produzione": "Produzione", "r_consumo": "Consumo", "r_investimento_tipo": "Investimento per tipo",
          "r_stock_tipo": "Stock per tipo", "r_importazioni": "Importazioni", "r_scorte": "Scorte"}


def _famiglia(caso: str) -> str:
    if caso.startswith("condizionata"):
        return "cond"
    if caso == "selezionata":
        return "sel"
    if caso.startswith("P1") or caso.startswith("P3"):
        return "P1"
    if caso.startswith("P2"):
        return "P2"
    if caso == "P0":
        return "P0"
    return "pers" if caso == "persistenza" else "bench"


def _etichetta(caso: str) -> str:
    return NOMI.get(caso, caso.replace("|", " · "))


def _stile(ax):
    ax.grid(axis="x", alpha=0.25, linewidth=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(labelsize=8.5)


def s_per_caso(sint: pd.DataFrame, titolo: str, n: int = 16) -> plt.Figure:
    s1 = sint[sint["h"] == 1].sort_values("S")
    principali = s1[s1["caso"].isin(["P0", "ultimo_tasso", "trend_mobile", "persistenza", "selezionata", RIFERIMENTO_P1,
                                     "condizionata|" + RIFERIMENTO_P1, "P3|q25", "P3|q75"])]
    migliori = s1[s1["caso"].str.startswith(("P1", "P2"))].groupby(s1["caso"].str[:2]).head(3)
    d = pd.concat([principali, migliori]).drop_duplicates("caso").sort_values("S", ascending=False)
    fig, ax = plt.subplots(figsize=(12.5, 0.42 * len(d) + 1.8))
    col = [COL[_famiglia(c)] for c in d["caso"]]
    ax.barh(range(len(d)), d["S"], color=col, height=0.7)
    ax.set_yticks(range(len(d)), [_etichetta(c) for c in d["caso"]])
    ax.axvline(1.0, color=COL["pers"], linewidth=1.2, linestyle="--")
    ax.text(1.0, len(d) - 0.4, " persistenza = 1", fontsize=8, color=COL["pers"], ha="left", va="bottom")
    for i, v in enumerate(d["S"]):
        ax.text(v + 0.02, i, f"{v:.2f}", va="center", fontsize=8.5, color="#0b0b0b")
    ax.set_xlim(0, max(2.4, float(d["S"].max()) * 1.08))
    ax.set_xlabel("Indicatore S a un passo (errore pesato / errore della persistenza)", fontsize=9)
    ax.set_title(titolo, fontsize=11, fontweight="bold", loc="left")
    _stile(ax)
    fam = {"P0": "Previsori preliminari", "bench": "Benchmark", "P2": "Tracking (P2)", "P1": "O2 predittivo (P1, P3)",
           "cond": "Previsione condizionata", "sel": "Sequenza selezionata"}
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in fam], labels=list(fam.values()), fontsize=8, frameon=False,
              loc="upper left", bbox_to_anchor=(1.01, 1.0), title="Famiglia", title_fontsize=8.5)
    fig.tight_layout()
    return fig


def s_per_orizzonte(sint: pd.DataFrame, titolo: str) -> plt.Figure:
    casi = {"P0": COL["P0"], "ultimo_tasso": COL["bench"], "P2|inv1.0|m1.0|S1.0|T3": COL["P2"], "P1|tetto100|agg|T2": COL["P1"],
            "condizionata|" + RIFERIMENTO_P1: COL["cond"]}
    casi = {c: k for c, k in casi.items() if c in set(sint["caso"])}
    hs = sorted(sint["h"].unique())
    fig, ax = plt.subplots(figsize=(11, 5))
    larg = 0.8 / len(casi)
    for k, (c, colore) in enumerate(casi.items()):
        z = sint[sint["caso"] == c].set_index("h")["S"].reindex(hs)
        pos = [i - 0.4 + larg * (k + 0.5) for i in range(len(hs))]
        ax.bar(pos, z.values, larg * 0.92, color=colore, label=_etichetta(c))
        for p, v in zip(pos, z.values):
            if np.isfinite(v):
                ax.text(p, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5, rotation=90, color="#0b0b0b")
    ax.axhline(1.0, color=COL["pers"], linewidth=1.2, linestyle="--")
    ax.text(len(hs) - 0.5, 1.02, "persistenza = 1", fontsize=8, color=COL["pers"], ha="right")
    ax.set_xticks(range(len(hs)), [f"h = {h}" for h in hs])
    ax.set_ylabel("Indicatore S", fontsize=9)
    ax.set_ylim(0, max(2.0, float(sint[sint["caso"].isin(casi)]["S"].max()) * 1.25))
    ax.set_title(titolo, fontsize=11, fontweight="bold", loc="left")
    ax.grid(axis="y", alpha=0.25); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.legend(fontsize=8, frameon=False, ncol=3, loc="upper left")
    fig.tight_layout()
    return fig


def componenti(sint: pd.DataFrame, titolo: str) -> plt.Figure:
    casi = {"P0": COL["P0"], "P2|inv1.0|m1.0|S1.0|T3": COL["P2"], RIFERIMENTO_P1: COL["P1"]}
    casi = {c: k for c, k in casi.items() if c in set(sint["caso"])}
    s1 = sint[sint["h"] == 1].set_index("caso")
    gr = list(GRUPPI)
    fig, ax = plt.subplots(figsize=(11, 5))
    larg = 0.8 / len(casi)
    for k, (c, colore) in enumerate(casi.items()):
        vals = [float(s1.at[c, g]) if g in s1.columns else np.nan for g in gr]
        pos = [i - 0.4 + larg * (k + 0.5) for i in range(len(gr))]
        ax.bar(pos, vals, larg * 0.92, color=colore, label=_etichetta(c))
        for p, v in zip(pos, vals):
            if np.isfinite(v):
                ax.text(p, v + 0.03, f"{v:.2f}", ha="center", va="bottom", fontsize=7.5, color="#0b0b0b")
    ax.axhline(1.0, color=COL["pers"], linewidth=1.2, linestyle="--")
    ax.set_xticks(range(len(gr)), [GRUPPI[g] for g in gr])
    ax.set_ylabel("Errore pesato / errore della persistenza (h = 1)", fontsize=9)
    ax.set_title(titolo, fontsize=11, fontweight="bold", loc="left")
    ax.grid(axis="y", alpha=0.25); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.legend(fontsize=8, frameon=False, loc="upper left")
    fig.tight_layout()
    return fig


def errori_aggregati(prev: pd.DataFrame, oss: pd.DataFrame, titolo: str) -> plt.Figure:
    casi = {"P0": COL["P0"], "P2|inv1.0|m1.0|S1.0|T3": COL["P2"], RIFERIMENTO_P1: COL["P1"], "persistenza": COL["pers"]}
    casi = {c: k for c, k in casi.items() if c in set(prev["caso"])}
    fig, assi = plt.subplots(1, 2, figsize=(14, 5))
    for ax, (chiave, tit) in zip(assi, (("consumo_tot", "Consumo privato"), ("investimento_tot", "Investimento fisso totale"))):
        o = oss[(oss["gruppo"] == "aggregati") & (oss["chiave"] == chiave)].set_index("anno")["valore"]
        anni = sorted(prev[(prev["h"] == 1) & (prev["gruppo"] == "aggregati") & (prev["chiave"] == chiave)]["anno"].unique())
        larg = 0.8 / len(casi)
        for k, (c, colore) in enumerate(casi.items()):
            z = prev[(prev["caso"] == c) & (prev["h"] == 1) & (prev["gruppo"] == "aggregati") & (prev["chiave"] == chiave)].set_index("anno")["valore"].reindex(anni)
            err = (z / o.reindex(anni) - 1) * 100
            pos = [i - 0.4 + larg * (k + 0.5) for i in range(len(anni))]
            ax.bar(pos, err.values, larg * 0.92, color=colore, label=_etichetta(c))
        ax.axhline(0, color="#0b0b0b", linewidth=0.8)
        shock = [i for i, a in enumerate(anni) if a in (2009, 2010)]
        if shock:
            ax.axvspan(min(shock) - 0.5, max(shock) + 0.5, color="#8a8987", alpha=0.12, linewidth=0)
            ax.text(min(shock) - 0.45, ax.get_ylim()[1] * 0.97, "origini 2008–09\n(shock)", fontsize=7.5, color=COL["bench"], va="top")
        ax.set_xticks(range(len(anni)), [str(a) for a in anni])
        ax.set_title(f"{tit}: errore % della previsione a un passo", fontsize=10.5)
        ax.set_ylabel("errore % (previsto / osservato − 1)", fontsize=9)
        ax.grid(axis="y", alpha=0.25); ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=8.5)
    assi[0].legend(fontsize=8, frameon=False, loc="upper left")
    fig.suptitle(titolo, fontsize=11, fontweight="bold", x=0.01, ha="left")
    fig.tight_layout()
    return fig


def genera(cartella: Path) -> list[Path]:
    cartella = Path(cartella)
    out = []
    sB = pd.read_csv(cartella / "sintesi_S_B_2010_2019.csv")
    prev = pd.read_csv(cartella / "previsioni_aggregati_tutti_i_casi.csv")
    oss = pd.read_csv(cartella / "osservato.csv")
    figure = {
        "g1_S_per_caso_B.png": s_per_caso(sB, "Accuratezza fuori campione a un passo, obiettivi 2010–2019 (protocollo B)"),
        "g2_S_per_orizzonte_B.png": s_per_orizzonte(sB, "Accuratezza per orizzonte di previsione, obiettivi 2010–2019"),
        "g3_componenti_B.png": componenti(sB, "Componenti dell'indicatore S per gruppo di variabili (h = 1, 2010–2019)"),
        "g4_errori_aggregati.png": errori_aggregati(prev, oss, "Errori a un passo sugli aggregati, 2009–2019 (origini 2008–2018)"),
    }
    for nome, fig in figure.items():
        f = cartella / nome
        fig.savefig(f, dpi=160)
        plt.close(fig)
        out.append(f)
    if (cartella / "sintesi_S_C_2012_2016.csv").is_file():
        sC = pd.read_csv(cartella / "sintesi_S_C_2012_2016.csv")
        fig = s_per_caso(sC, "Accuratezza fuori campione a un passo, obiettivi 2012–2016 (caso C)")
        f = cartella / "g5_S_per_caso_C.png"
        fig.savefig(f, dpi=160); plt.close(fig); out.append(f)
    return out
