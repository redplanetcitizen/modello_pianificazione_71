"""Passo E1: meccanismi di gradualità dell'investimento applicati a O2, senza modificare O2.

O2 del passo D resta il caso di riferimento (tutte le opzioni nuove disattivate). Le varianti aggiungono:
  H25a  limite alla variazione annua dell'investimento per tipo: (1−g) I_{a,t−1} ≤ I_{a,t} ≤ (1+g) I_{a,t−1},
        somma sulle industrie, base 2011 osservata (approssima costi di aggiustamento convessi con un vincolo);
  H25b  penalità lineare a tratti sulla variazione relativa annua per tipo oltre una soglia libera
        (approssima un costo di aggiustamento convesso senza uscire dall'LP); la penalità è nella stessa scala
        dei punteggi di O2 ed è dichiarata come parametro;
  H26   tempi di costruzione per S e R: la spesa di un progetto avviato in t cade per metà in t e per metà in t+1;
        avvii 2011 = spesa 2011 osservata (ipotesi di regime). Accumulazione e capacità restano quelle BEA
        (lo stock cresce con la spesa effettuata).
Misure di aderenza: scarto percentuale medio assoluto dall'osservato 2012-2016 (stock: 2012-2017) per variabile.
"""
from __future__ import annotations

import dataclasses
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .archivio import Configurazione  # noqa: E402
from .dati_modello import costruisci  # noqa: E402
from .grafici import TIPI_TUTTI, serie  # noqa: E402
from .modello import Opzioni, costruisci_e_risolvi  # noqa: E402
from .passo_c1 import _csv  # noqa: E402
from .passo_d import VARIANTE, _scrivi_risultato  # noqa: E402
from .registro import Esecuzione  # noqa: E402

BASE = dict(obiettivo="O2", **VARIANTE)
CASI = {
    "O2": {},
    "limite_10%": {"limite_var_inv": 0.10},
    "limite_15%": {"limite_var_inv": 0.15},
    "limite_25%": {"limite_var_inv": 0.25},
    "penalita_0.01": {"penalita_var_inv": 0.01},
    "penalita_0.1": {"penalita_var_inv": 0.10},
    "tempi_costruzione_S_R": {"tempi_costruzione": ("S", "R")},
    "combinato": {"limite_var_inv": 0.15, "tempi_costruzione": ("S", "R")},
}
CONFRONTO = ("O2", "combinato")
COLORI = {"osservato": "#4d4d4d", "O2": "#ff7f0e", "combinato": "#1f77b4"}
NOMI = {"osservato": "Economia osservata", "O2": "O2 (passo D)", "combinato": "O2 + limite ±15% + tempi di costruzione S, R"}


def scarti(s: pd.DataFrame) -> pd.DataFrame:
    """Scarto percentuale medio assoluto dall'osservato per caso e variabile."""
    oss = s[s.caso == "osservato"].set_index(["variabile", "anno"])["valore"]
    out = {}
    for caso, z in s[s.caso != "osservato"].groupby("caso"):
        z = z.set_index(["variabile", "anno"])["valore"]
        o = oss.reindex(z.index)
        out[caso] = ((z - o).abs() / o).groupby(level=0).mean() * 100
    t = pd.DataFrame(out).T
    t["media_investimento"] = t[[c for c in t if c.startswith("investimento_")]].mean(axis=1)
    t["media_stock"] = t[[c for c in t if c.startswith("stock_")]].mean(axis=1)
    return t


def _figura(s, variabili: dict, titolo: str, righe: int = 2, colonne: int = 2, dim=(12, 9)):
    fig, assi = plt.subplots(righe, colonne, figsize=dim, squeeze=False)
    casi = ["osservato", *CONFRONTO]
    for ax, (var, tit) in zip(assi.flat, variabili.items()):
        anni = sorted(s[s.variabile == var]["anno"].unique())
        oss = s[(s.caso == "osservato") & (s.variabile == var)].set_index("anno")["valore"]
        larg = 0.8 / len(casi)
        alto = float(s[(s.variabile == var) & s.caso.isin(casi)]["valore"].max())
        for k, caso in enumerate(casi):
            z = s[(s.caso == caso) & (s.variabile == var)].set_index("anno")["valore"].reindex(anni)
            pos = [i - 0.4 + larg * (k + 0.5) for i in range(len(anni))]
            ax.bar(pos, z.values, larg, color=COLORI[caso], label=NOMI[caso])
            if caso != "osservato":
                for p, a, m in zip(pos, anni, z.values):
                    ax.text(p, m + alto * 0.012, f"{round((m / oss[a] - 1) * 100) + 0:+d}%", ha="center",
                            va="bottom", fontsize=6.8 if righe > 1 else 6.0, color="#333333")
        ax.set_xticks(range(len(anni)), [str(a) for a in anni])
        ax.set_ylim(0, alto * 1.13)
        ax.set_title(tit, fontsize=10.5)
        ax.set_ylabel("miliardi di dollari 2012", fontsize=8.5)
        ax.grid(axis="y", alpha=0.3)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        ax.tick_params(labelsize=8.5)
    h, l = assi.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=9, frameon=False)
    fig.suptitle(titolo, fontsize=12.5, fontweight="bold")
    fig.text(0.5, 0.07 if righe > 1 else 0.13, "Etichette: scarto percentuale rispetto all'osservato. Calibrazione adottata (H9b, H13b), prezzi 2012.",
             ha="center", va="center", fontsize=7.8, color="#444444")
    fig.tight_layout(rect=(0, 0.09 if righe > 1 else 0.17, 1, 0.95))
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=160)
    plt.close(fig)
    return b.getvalue()


def esegui(cfg: Configurazione) -> Esecuzione:
    P = costruisci(cfg)
    opzioni = {k: Opzioni(**{**BASE, **m}) for k, m in CASI.items()}
    with Esecuzione("M71-E1-gradualita-O2", cfg, parametri={k: dataclasses.asdict(v) for k, v in opzioni.items()}) as es:
        tab, ris = [], {}
        for nome, o in opzioni.items():
            R = costruisci_e_risolvi(P, o)
            tab.append(_scrivi_risultato(es, nome, R))
            if R.stato == "Optimal":
                ris[nome] = R
        s = serie(P, ris)
        es.scrivi_testo("serie.csv", _csv(s))
        sc = scarti(s)
        es.scrivi_testo("scarti_dall_osservato.csv", _csv(sc.rename_axis("caso").reset_index()))
        t = pd.DataFrame(tab).set_index("caso")
        cols = ["stato", "valore_obiettivo", "gamma_2016", "consumo_cumulato", "anni_disinvestimento_netto"]
        sint = t[[c for c in cols if c in t]].join(sc[["produzione_lorda", "consumo_privato", "media_investimento", "media_stock"]])
        es.scrivi_testo("casi.csv", _csv(t.reset_index()))
        es.scrivi_byte("0_produzione_consumo_O2_graduale.png", _figura(
            s, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
            "Produzione e consumo: osservato, O2 e O2 con gradualità", 1, 2, (14, 5.6)))
        es.scrivi_byte("1_investimento_O2_graduale.png", _figura(
            s, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
            "Investimento per tipo: osservato, O2 e O2 con gradualità"))
        es.scrivi_byte("2_stock_O2_graduale.png", _figura(
            s, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
            "Stock per tipo: osservato, O2 e O2 con gradualità"))
        es.scrivi_testo("sintesi.md", "# M71-E1 — gradualità dell'investimento su O2\n\nScarto % medio assoluto dall'osservato.\n\n```\n"
                        + sint.to_string(float_format=lambda v: f"{v:,.3f}") + "\n```\n\n```\n"
                        + sc.round(1).to_string() + "\n```\n")
    return es
