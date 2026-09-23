"""Passo D5: grafici delle traiettorie del modello a confronto con l'economia osservata (prezzi 2012).

Casi (calibrazione adottata H9b/H13b): O1, O2, O3 (capitale terminale a valore dello stock) e O4
(traiettoria ammissibile più vicina a quella osservata). Serie: produzione lorda, consumo privato,
investimento FA per tipo (E, S, N, R), stock netto di inizio anno per tipo (2012-2017).

Perimetro: industrie private del modello con capitale (vincolo di capacità) più HS per il residenziale;
lo stesso perimetro è usato per il modello e per i dati osservati. Lo stock del modello è ricostruito
con l'identità di accumulazione del modello; quello osservato è lo stock netto Fixed Assets a prezzi 2012
(le due serie differiscono al più per le altre variazioni di volume, ≤ 0,1%: passo C5).
"""
from __future__ import annotations

import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .archivio import Configurazione  # noqa: E402
from .dati_modello import Parametri, costruisci  # noqa: E402
from .modello import Opzioni, costruisci_e_risolvi  # noqa: E402
from .passo_c1 import _csv  # noqa: E402
from .passo_d import VARIANTE  # noqa: E402
from .registro import Esecuzione  # noqa: E402

CASI = {
    "O1": Opzioni(obiettivo="O1", **VARIANTE),
    "O2": Opzioni(obiettivo="O2", **VARIANTE),
    "O3": Opzioni(obiettivo="O3", pesi_o3="valore", **VARIANTE),
    "O4": Opzioni(obiettivo="O4", **VARIANTE),
}
ETICHETTE = {"osservato": "Economia osservata", "O1": "O1 — max consumo (paniere fisso)",
             "O2": "O2 — obiettivi per prodotto", "O3": "O3 — max stock finale (a valore)",
             "O4": "O4 — ammissibile più vicina all'osservato"}
STILI = {"osservato": dict(color="black", lw=2.6, marker="o", ms=4, zorder=5),
         "O1": dict(color="#1f77b4", lw=1.8, marker="s", ms=3.5),
         "O2": dict(color="#ff7f0e", lw=1.8, marker="^", ms=3.5),
         "O3": dict(color="#2ca02c", lw=1.8, marker="D", ms=3.5),
         "O4": dict(color="#7f7f7f", lw=1.4, ls="--")}
TIPI_TUTTI = {"E": "Attrezzature (E)", "S": "Strutture non residenziali (S)",
              "N": "Proprietà intellettuale (N)", "R": "Residenziale (R)"}


def serie(P: Parametri, risultati: dict) -> pd.DataFrame:
    """Tabella lunga: caso, variabile, anno, valore (miliardi di dollari 2012)."""
    anni = list(P.anni)
    righe = []
    # perimetro del capitale: coppie (industria, tipo) presenti nella soluzione
    inv0 = next(iter(risultati.values())).tabelle["investimento"]
    coppie = sorted({(j, a) for j, a in zip(inv0["industria"], inv0["tipo"])})
    Ioss = P.I_oss.set_index(["industria_io", "tipo", "anno"])["I"]
    for t in anni:
        righe.append(("osservato", "produzione_lorda", t, float(P.x_oss[t].sum())))
        righe.append(("osservato", "consumo_privato", t, float(P.consumo_oss[t].sum())))
        for a in TIPI_TUTTI:
            righe.append(("osservato", f"investimento_{a}", t,
                          float(sum(Ioss.get((j, b, t), 0.0) for j, b in coppie if b == a))))
    for t in anni + [anni[-1] + 1]:
        for a in TIPI_TUTTI:
            righe.append(("osservato", f"stock_{a}", t,
                          float(sum(P.K_oss.get((j, b, t), 0.0) for j, b in coppie if b == a))))
    for nome, R in risultati.items():
        ag = R.tabelle["aggregati"].set_index("anno")
        inv = R.tabelle["investimento"]
        for t in anni:
            righe.append((nome, "produzione_lorda", t, float(ag.at[t, "produzione_lorda"])))
            righe.append((nome, "consumo_privato", t, float(ag.at[t, "consumo_privato"])))
            for a in TIPI_TUTTI:
                righe.append((nome, f"investimento_{a}", t, float(inv[(inv.anno == t) & (inv.tipo == a)]["I"].sum())))
        # stock di inizio anno: identità del modello K_{t+1} = (1 − δ) K_t + I_t
        K = {(j, a): float(P.K0[(j, a)]) for j, a in coppie}
        I = inv.set_index(["industria", "tipo", "anno"])["I"]
        for t in anni + [anni[-1] + 1]:
            for a in TIPI_TUTTI:
                righe.append((nome, f"stock_{a}", t, sum(k for (j, b), k in K.items() if b == a)))
            if t <= anni[-1]:
                K = {(j, a): (1 - float(P.delta[(j, a)])) * k + float(I.get((j, a, t), 0.0)) for (j, a), k in K.items()}
    return pd.DataFrame(righe, columns=["caso", "variabile", "anno", "valore"])


def _pannello(ax, s: pd.DataFrame, variabile: str, titolo: str):
    for caso in ["O4", "O1", "O2", "O3", "osservato"]:
        z = s[(s.caso == caso) & (s.variabile == variabile)].sort_values("anno")
        if len(z):
            ax.plot(z["anno"], z["valore"], label=ETICHETTE[caso], **STILI[caso])
    ax.set_title(titolo, fontsize=10.5)
    ax.grid(alpha=0.3)
    ax.set_xticks(sorted(s[s.variabile == variabile]["anno"].unique()))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.tick_params(labelsize=8.5)


def _figura(s, variabili: dict, titolo: str, nota: str, righe: int, colonne: int, dim):
    fig, assi = plt.subplots(righe, colonne, figsize=dim, squeeze=False)
    for ax, (var, tit) in zip(assi.flat, variabili.items()):
        _pannello(ax, s, var, tit)
    for ax in assi.flat:
        ax.set_ylabel("miliardi di dollari 2012", fontsize=8.5)
    h, l = assi.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(titolo, fontsize=12.5, fontweight="bold")
    fig.text(0.5, 0.075 if righe > 1 else 0.13, nota, ha="center", va="center", fontsize=7.8, color="#444444")
    fig.tight_layout(rect=(0, 0.12 if righe > 1 else 0.2, 1, 0.95))
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=160)
    plt.close(fig)
    return b.getvalue()


def _pannello_barre(ax, s: pd.DataFrame, variabile: str, titolo: str, caso: str):
    oss = s[(s.caso == "osservato") & (s.variabile == variabile)].set_index("anno")["valore"]
    mod = s[(s.caso == caso) & (s.variabile == variabile)].set_index("anno")["valore"].reindex(oss.index)
    x = range(len(oss))
    ax.bar([i - 0.2 for i in x], oss.values, 0.4, color="#4d4d4d", label="Economia osservata")
    ax.bar([i + 0.2 for i in x], mod.values, 0.4, color=STILI[caso]["color"], label=ETICHETTE[caso])
    alto = max(float(oss.max()), float(mod.max()))
    for i, (o, m) in enumerate(zip(oss.values, mod.values)):
        if o:
            ax.text(i + 0.2, m + alto * 0.012, f"{round((m / o - 1) * 100) + 0:+d}%", ha="center", va="bottom", fontsize=7.5,
                    color="#333333")
    ax.set_xticks(list(x), [str(a) for a in oss.index])
    ax.set_ylim(0, alto * 1.12)
    ax.set_title(titolo, fontsize=10.5)
    ax.grid(axis="y", alpha=0.3)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.tick_params(labelsize=8.5)


def _figura_barre(s, caso: str, variabili: dict, titolo: str, righe: int, colonne: int, dim):
    fig, assi = plt.subplots(righe, colonne, figsize=dim, squeeze=False)
    for ax, (var, tit) in zip(assi.flat, variabili.items()):
        _pannello_barre(ax, s, var, tit, caso)
        ax.set_ylabel("miliardi di dollari 2012", fontsize=8.5)
    h, l = assi.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle(titolo, fontsize=12.5, fontweight="bold")
    fig.text(0.5, 0.075 if righe > 1 else 0.13,
             "Etichette: scarto percentuale del modello rispetto all'osservato. Calibrazione adottata (H9b, H13b), prezzi 2012.",
             ha="center", va="center", fontsize=7.8, color="#444444")
    fig.tight_layout(rect=(0, 0.1 if righe > 1 else 0.18, 1, 0.95))
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=160)
    plt.close(fig)
    return b.getvalue()


NOTA = ("Calibrazione adottata (H9b, H13b), prezzi 2012. Modello: soluzioni LP 2012–2016 con previsione perfetta. "
        "Osservato: BEA Input-Output e Fixed Assets deflazionati.\n"
        "O4 quasi coincide con l'osservato (distanza 0,013) e ne resta in gran parte coperta.")


def esegui(cfg: Configurazione) -> Esecuzione:
    P = costruisci(cfg)
    with Esecuzione("M71-D5-grafici", cfg, parametri={k: vars(v) for k, v in CASI.items()}) as es:
        ris = {}
        for nome, o in CASI.items():
            R = costruisci_e_risolvi(P, o)
            if R.stato != "Optimal":
                raise RuntimeError(f"{nome}: stato {R.stato}")
            ris[nome] = R
        s = serie(P, ris)
        es.scrivi_testo("serie.csv", _csv(s))
        largo = s.pivot_table(index=["variabile", "anno"], columns="caso", values="valore").reset_index()
        es.scrivi_testo("serie_confronto.csv", _csv(largo))
        figure = {
            "1_produzione_consumo.png": _figura(
                s, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
                "Produzione e consumo: modello ed economia osservata", NOTA, 1, 2, (12, 5.2)),
            "2_investimento_per_tipo.png": _figura(
                s, {f"investimento_{a}": f"Investimento — {t}" for a, t in TIPI_TUTTI.items()},
                "Investimento fisso per tipo: modello ed economia osservata", NOTA, 2, 2, (12, 9)),
            "3_stock_per_tipo.png": _figura(
                s, {f"stock_{a}": f"Stock netto di inizio anno — {t}" for a, t in TIPI_TUTTI.items()},
                "Stock di capitale per tipo (inizio anno, 2017 = fine orizzonte)", NOTA, 2, 2, (12, 9)),
        }
        figure.update({
            "4_O2_produzione_consumo.png": _figura_barre(
                s, "O2", {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
                "O2 ed economia osservata: produzione e consumo", 1, 2, (12, 5.2)),
            "5_O2_investimento_per_tipo.png": _figura_barre(
                s, "O2", {f"investimento_{a}": f"Investimento — {t}" for a, t in TIPI_TUTTI.items()},
                "O2 ed economia osservata: investimento fisso per tipo", 2, 2, (12, 9)),
            "6_O2_stock_per_tipo.png": _figura_barre(
                s, "O2", {f"stock_{a}": f"Stock netto di inizio anno — {t}" for a, t in TIPI_TUTTI.items()},
                "O2 ed economia osservata: stock di capitale per tipo (2017 = fine orizzonte)", 2, 2, (12, 9)),
        })
        for nome, dati in figure.items():
            es.scrivi_byte(nome, dati)
        es.scrivi_testo("sintesi.md", "# M71-D5 — grafici modello / osservato\n\n" + "\n".join(f"- {n}" for n in figure) + "\n")
    return es
