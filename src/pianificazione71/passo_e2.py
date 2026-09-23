"""Passo E2: orizzonte esteso 2010-2019 (variante b), confronto riportato solo sul 2012-2016.

Motivazione: in un modello a orizzonte finito gli anni vicini agli estremi sono distorti dalle condizioni
iniziali (stock dato, capacità libera imposta) e terminali (non depauperamento a fine orizzonte). Negli anni
centrali di un orizzonte più lungo la traiettoria ottima dipende meno da entrambi (proprietà di turnpike).

Calibrazione sull'anno di avvio (2010): stock iniziale 2010, κ con l'utilizzo G.17 del 2010, σ delle scorte 2010,
deriva θ stimata sul 2010-2019, δ medio 2010-2019, pesi w invariati (2012). H9b applicata all'anno di avvio:
u fuori G.17 = utilizzo G.17 dell'industria totale nel 2010 (serie B50001), letto dall'archivio. H13b invariata
(σ × 0,85). Lavoro disponibile = FTE osservati (anche nel 2010-2011, anni di disoccupazione elevata).
Condizione terminale: stock 2020 ≥ stock 2010 per tipo.

Casi: O2 invariato, O2 con limite ±15% alla variazione annua dell'investimento per tipo (H25a), O2 con penalità
lineare a tratti oltre il 5% (H25b, p = 0,1); ciascuno sull'orizzonte 2012-2016 (passo D/E1) e 2010-2019.
"""
from __future__ import annotations

import dataclasses
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from .archivio import Configurazione, percorso_dati  # noqa: E402
from .capacita import leggi_g17  # noqa: E402
from .controllo_osservato import controlla  # noqa: E402
from .dati_modello import costruisci  # noqa: E402
from .grafici import TIPI_TUTTI, serie  # noqa: E402
from .modello import Opzioni, costruisci_e_risolvi  # noqa: E402
from .passo_c1 import _csv  # noqa: E402
from .passo_c6 import G17_U  # noqa: E402
from .passo_d import VARIANTE, _scrivi_risultato  # noqa: E402
from .passo_e1 import scarti  # noqa: E402
from .registro import Esecuzione  # noqa: E402

ORIZZONTI = {"2012-2016": range(2012, 2017), "2010-2019": range(2010, 2020)}
RIPORTATI = range(2012, 2017)
MECCANISMI = {"O2": {}, "limite_15%": {"limite_var_inv": 0.15}, "penalita_0.1": {"penalita_var_inv": 0.10}}
FIGURA = ["O2 2012-2016", "O2 2010-2019", "limite_15% 2010-2019", "penalita_0.1 2010-2019"]
COLORI = {"osservato": "#4d4d4d", "O2 2012-2016": "#ff7f0e", "O2 2010-2019": "#9467bd",
          "limite_15% 2010-2019": "#1f77b4", "penalita_0.1 2010-2019": "#2ca02c"}
NOMI = {"osservato": "Economia osservata", "O2 2012-2016": "O2, orizzonte 2012-16 (passo D)",
        "O2 2010-2019": "O2, orizzonte 2010-19", "limite_15% 2010-2019": "O2 + limite ±15%, 2010-19",
        "penalita_0.1 2010-2019": "O2 + penalità, 2010-19"}


def utilizzo_totale(cfg: Configurazione, anno: int) -> float:
    u = leggi_g17(percorso_dati(cfg, *G17_U), ["B50001"], [anno])
    return round(float(u.loc["B50001", anno]) / 100, 3)


def _figura(s, variabili: dict, titolo: str, righe: int, colonne: int, dim, casi=None,
            nota="Solo anni 2012-2016 (stock: inizio 2012-2017)."):
    fig, assi = plt.subplots(righe, colonne, figsize=dim, squeeze=False)
    casi = ["osservato", *(casi or FIGURA)]
    ruota = len(casi) > 2
    for ax, (var, tit) in zip(assi.flat, variabili.items()):
        anni = sorted(s[s.variabile == var]["anno"].unique())
        oss = s[(s.caso == "osservato") & (s.variabile == var)].set_index("anno")["valore"]
        larg = 0.84 / len(casi)
        alto = float(s[(s.variabile == var) & s.caso.isin(casi)]["valore"].max())
        for k, caso in enumerate(casi):
            z = s[(s.caso == caso) & (s.variabile == var)].set_index("anno")["valore"].reindex(anni)
            pos = [i - 0.42 + larg * (k + 0.5) for i in range(len(anni))]
            ax.bar(pos, z.values, larg, color=COLORI[caso], label=NOMI[caso])
            if caso != "osservato":
                for p, a, m in zip(pos, anni, z.values):
                    ax.text(p, m + alto * 0.012, f"{round((m / oss[a] - 1) * 100) + 0:+d}" + ("" if ruota else "%"),
                            ha="center", va="bottom", fontsize=5.6 if ruota else 6.3, color="#333333",
                            rotation=90 if ruota else 0)
        ax.set_xticks(range(len(anni)), [str(a) for a in anni])
        ax.set_ylim(0, alto * 1.2)
        ax.set_title(tit, fontsize=10.5)
        ax.set_ylabel("miliardi di dollari 2012", fontsize=8.5)
        ax.grid(axis="y", alpha=0.3)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
        ax.tick_params(labelsize=8.5)
    h, l = assi.flat[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=8.5, frameon=False)
    fig.suptitle(titolo, fontsize=12.5, fontweight="bold")
    fig.text(0.5, 0.075 if righe > 1 else 0.15, f"Etichette: scarto % rispetto all'osservato. {nota} Prezzi 2012.", ha="center", va="center", fontsize=7.8, color="#444444")
    fig.tight_layout(rect=(0, 0.1 if righe > 1 else 0.2, 1, 0.95))
    b = io.BytesIO()
    fig.savefig(b, format="png", dpi=160)
    plt.close(fig)
    return b.getvalue()


def esegui(cfg: Configurazione) -> Esecuzione:
    u2010 = utilizzo_totale(cfg, 2010)
    calibrazioni = {"2012-2016": dict(VARIANTE), "2010-2019": {"u_non_g17": u2010, "sigma_fattore": VARIANTE["sigma_fattore"]}}
    casi = {f"{m} {h}": Opzioni(obiettivo="O2", **calibrazioni[h], **mod) for h in ORIZZONTI for m, mod in MECCANISMI.items()}
    with Esecuzione("M71-E2-orizzonte-2010-2019", cfg,
                    parametri={"orizzonti": {k: list(v) for k, v in ORIZZONTI.items()}, "calibrazioni": calibrazioni,
                               "casi": {k: dataclasses.asdict(v) for k, v in casi.items()}}) as es:
        tab, pezzi = [], []
        righe_sint = ["# M71-E2 — orizzonte 2010-2019, confronto sul 2012-2016", "",
                      f"Utilizzo G.17 industria totale 2010 (H9b all'anno di avvio): {u2010}", ""]
        for h, anni in ORIZZONTI.items():
            P = costruisci(cfg, anni)
            ctrl = controlla(P, u_non_g17=calibrazioni[h]["u_non_g17"], sigma_fattore=calibrazioni[h]["sigma_fattore"])
            for k, df in ctrl.items():
                es.scrivi_testo(f"controllo_osservato_{h}/{k}.csv", _csv(df))
            righe_sint += [f"Controllo al punto osservato {h}: industrie oltre la capacità per anno "
                           f"{ctrl['capacita'].groupby('anno')['violato'].sum().to_dict()}; comparti sotto il minimo delle scorte "
                           f"{ctrl['scorte'].groupby('anno')['violato'].sum().to_dict()}", ""]
            ris = {}
            for nome, o in casi.items():
                if not nome.endswith(h):
                    continue
                R = costruisci_e_risolvi(P, o)
                riga = _scrivi_risultato(es, nome.replace(" ", "_"), R)
                if R.stato == "Optimal":
                    ris[nome] = R
                    a = R.tabelle["aggregati"].set_index("anno").loc[list(RIPORTATI)]
                    riga.update({"consumo_cumulato_2012_16": float(a["consumo_privato"].sum()),
                                 "anni_disinv_netto_2012_16": int((a["investimento_netto"] < 0).sum())})
                tab.append(riga)
            s = serie(P, ris)
            if h == "2010-2019":
                s_esteso = s
            pezzi.append(s if h == "2012-2016" else s[s.caso != "osservato"])
        s = pd.concat(pezzi, ignore_index=True)
        s = s[s["anno"].isin(list(RIPORTATI) + [RIPORTATI[-1] + 1])]
        s = s[~(s["variabile"].str.startswith(("produzione", "consumo", "investimento")) & (s["anno"] > RIPORTATI[-1]))]
        es.scrivi_testo("serie_2012_2016.csv", _csv(s))
        sc = scarti(s)
        es.scrivi_testo("scarti_dall_osservato.csv", _csv(sc.rename_axis("caso").reset_index()))
        t = pd.DataFrame(tab).set_index("caso")
        es.scrivi_testo("casi.csv", _csv(t.reset_index()))
        sint = t[["stato", "consumo_cumulato_2012_16", "anni_disinv_netto_2012_16"]].copy()
        sint.index = sint.index.str.replace("_2012-2016", " 2012-2016").str.replace("_2010-2019", " 2010-2019")
        sint = sint.join(sc[["produzione_lorda", "consumo_privato", "media_investimento", "media_stock"]])
        righe_sint += ["Scarto % medio assoluto dall'osservato, anni 2012-2016.", "", "```",
                       sint.to_string(float_format=lambda v: f"{v:,.2f}"), "```", "", "```", sc.round(1).to_string(), "```"]
        es.scrivi_byte("1_produzione_consumo.png", _figura(
            s, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
            "Produzione e consumo 2012-2016: orizzonte breve e orizzonte esteso", 1, 2, (14, 5.8)))
        es.scrivi_byte("2_investimento_per_tipo.png", _figura(
            s, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
            "Investimento per tipo 2012-2016: orizzonte breve e orizzonte esteso", 2, 2, (14, 10)))
        es.scrivi_byte("3_stock_per_tipo.png", _figura(
            s, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
            "Stock per tipo 2012-2017: orizzonte breve e orizzonte esteso", 2, 2, (14, 10)))
        # figure dell'intero orizzonte 2010-2019: O2 invariato contro l'economia osservata
        NOMI["O2 2010-2019 intero"] = "O2, orizzonte 2010-19"
        COLORI["O2 2010-2019 intero"] = COLORI["O2 2010-2019"]
        se = pd.concat([s_esteso[s_esteso.caso == "osservato"],
                        s_esteso[s_esteso.caso == "O2 2010-2019"].assign(caso="O2 2010-2019 intero")], ignore_index=True)
        es.scrivi_testo("serie_2010_2019.csv", _csv(s_esteso))
        nota = "Orizzonte intero 2010-2019 (stock: inizio 2010-2020); calibrazione sul 2010."
        es.scrivi_byte("4_O2_2010_2019_produzione_consumo.png", _figura(
            se, {"produzione_lorda": "Produzione lorda (71 industrie)", "consumo_privato": "Consumo privato"},
            "O2 2010-2019 ed economia osservata: produzione e consumo", 1, 2, (16, 5.8), ["O2 2010-2019 intero"], nota))
        es.scrivi_byte("5_O2_2010_2019_investimento_per_tipo.png", _figura(
            se, {f"investimento_{a}": f"Investimento — {n}" for a, n in TIPI_TUTTI.items()},
            "O2 2010-2019 ed economia osservata: investimento fisso per tipo", 2, 2, (16, 10), ["O2 2010-2019 intero"], nota))
        es.scrivi_byte("6_O2_2010_2019_stock_per_tipo.png", _figura(
            se, {f"stock_{a}": f"Stock netto di inizio anno — {n}" for a, n in TIPI_TUTTI.items()},
            "O2 2010-2019 ed economia osservata: stock di capitale per tipo (2020 = fine orizzonte)", 2, 2, (16, 10),
            ["O2 2010-2019 intero"], nota))
        es.scrivi_testo("sintesi.md", "\n".join(righe_sint) + "\n")
    return es
