"""Esecuzione registrata del passo C6: pesi di costo d'uso, capitale per la capacità, κ, controllo G.17."""
from __future__ import annotations

import pandas as pd

from .archivio import Configurazione, percorso_dati
from .capacita import (
    CATEGORIE_CAPITALE,
    G17_IO,
    capitale_capacita,
    deriva_capacita,
    controllo_g17,
    kappa,
    leggi_g17,
    leggi_klems,
    pesi_costo_uso,
    utilizzo_per_industria,
)
from .capitale import a_prezzi_2012, aggrega_io, pannello, pannello_residenziale
from .margini import leggi_concordanza, leggi_fa_dettaglio
from .passo_c1 import MAKE, PREZZI, USE, _csv
from .passo_c2 import CONCORDANZA, FA_RES
from .passo_c5 import ANNI_CAPITALE, FILE, REL
from .registro import Esecuzione
from .sistema import ANNI, a_prezzi_2012 as sistema_reale, indici_prezzo, leggi_make, leggi_use

KLEMS = ("bls-2026-09-18", "BEA-BLS-industry-level-production-account-1997-2024.xlsx")
G17_U = ("fed-g17-2026-09-18", "FRB-g17-capacity-utilization.txt")
G17_CAP = ("fed-g17-2026-09-18", "FRB-g17-industrial-capacity.txt")
NOME = "M71-C6-capacita"


def x_reale_per_anno(cfg: Configurazione) -> pd.DataFrame:
    tidy = pd.read_csv(percorso_dati(cfg, *PREZZI))
    righe, prezzi = [], None
    for a in ANNI:
        u, m = leggi_use(percorso_dati(cfg, *USE), a), leggi_make(percorso_dati(cfg, *MAKE), a)
        prezzi = indici_prezzo(tidy, list(u.U.columns)) if prezzi is None else prezzi
        s = sistema_reale(u, m, prezzi[a])
        righe += [{"industria_io": j, "anno": a, "x_reale": v} for j, v in s.x.items()]
    return pd.DataFrame(righe)


def esegui(cfg: Configurazione) -> Esecuzione:
    parametri = {"klems": "/".join(KLEMS), "g17_utilizzo": "/".join(G17_U), "g17_capacita": "/".join(G17_CAP),
                 "anno_calibrazione": 2012, "ipotesi": ["H8", "H8b", "H9", "H9a", "H10"]}
    with Esecuzione(NOME, cfg, parametri=parametri) as es:
        conc = leggi_concordanza(CONCORDANZA)
        s = {k: leggi_fa_dettaglio(percorso_dati(cfg, REL, v), anni=ANNI_CAPITALE) for k, v in FILE.items()}
        el = {m: a_prezzi_2012(s[m + "1"], s[m + "2"]) for m in "KID"}
        pan = pd.concat([pannello(*(aggrega_io(el[m], conc, m) for m in "KID")),
                         pannello_residenziale(percorso_dati(cfg, *FA_RES), ANNI_CAPITALE)], ignore_index=True)
        rem = leggi_klems(percorso_dati(cfg, *KLEMS), CATEGORIE_CAPITALE, [2012])[2012]
        pesi, tassi = pesi_costo_uso(pan, rem)
        kcap = capitale_capacita(pan, pesi)
        xr = x_reale_per_anno(cfg)
        u = utilizzo_per_industria(leggi_g17(percorso_dati(cfg, *G17_U), list(G17_IO), list(ANNI)))
        cap = leggi_g17(percorso_dati(cfg, *G17_CAP), list(G17_IO), list(ANNI))
        kap = kappa(kcap, xr, u)
        ctrl = controllo_g17(kcap, xr, kap, u, cap)
        der, fuori = deriva_capacita(ctrl)
        es.scrivi_testo("deriva_capacita.csv", _csv(der))
        es.scrivi_testo("deriva_fuori_campione.csv", _csv(fuori))
        for nome, df in (("pesi_costo_uso.csv", pesi), ("tassi_rendimento_klems.csv", tassi),
                         ("capitale_capacita.csv", kcap), ("kappa.csv", kap), ("controllo_g17.csv", ctrl)):
            es.scrivi_testo(nome, _csv(df))
        es.scrivi_testo("sintesi.md", sintesi(pesi, tassi, kap, ctrl) + sintesi_deriva(der, fuori))
    return es


def sintesi(pesi, tassi, kap, ctrl) -> str:
    r = ["# M71-C6 — capacità legata al capitale", "",
         "## Tassi di rendimento per gruppo KLEMS (2012)", "",
         f"- gruppi: {len(tassi)}; mediana r = {tassi['r'].median():.3f}; "
         f"min {tassi['r'].min():.3f} ({tassi.loc[tassi['r'].idxmin(), 'gruppo']}); "
         f"max {tassi['r'].max():.3f} ({tassi.loc[tassi['r'].idxmax(), 'gruppo']})",
         f"- gruppi con r negativo, troncato a 0: {int(tassi['r_negativo_troncato'].sum())}", "",
         "## Pesi w per tipo (mediana tra industrie)", "", "```",
         pesi.groupby("tipo")["w"].describe()[["min", "50%", "max"]].to_string(float_format=lambda v: f"{v:.3f}"), "```", "",
         "## κ (capitale per la capacità / produzione a piena capacità, 2012)", "",
         f"- industrie: {len(kap)}; con utilizzo G.17: {int(kap['u_da_g17'].sum())}; "
         f"κ mediano {kap['kappa'].median():.2f}", "",
         "## Controllo esterno parziale G.17 (2013–2016)", "",
         "Utilizzo implicito u* = x·κ/K^cap contro utilizzo G.17; crescita di K^cap contro crescita della capacità G.17.", "",
         "| Metodo G.17 | Industrie | Scarto medio assoluto u* − u (punti) | Correlazione u*, u | Crescita K^cap 2012–16 | Crescita capacità G.17 |",
         "|---|---:|---:|---:|---:|---:|"]
    c = ctrl[ctrl["anno"] > 2012]
    for met, g in c.groupby("metodo_g17"):
        fin = ctrl[(ctrl["anno"] == 2016) & (ctrl["metodo_g17"] == met)]
        r.append(f"| {met} | {g['industria_io'].nunique()} | {100 * g['scarto_u'].abs().mean():.1f} | "
                 f"{g[['u_implicito', 'u']].corr().iloc[0, 1]:.2f} | {100 * (fin['crescita_Kcap'].mean() - 1):.1f}% | "
                 f"{100 * (fin['crescita_cap_g17'].mean() - 1):.1f}% |")
    return "\n".join(r) + "\n"


def sintesi_deriva(der: pd.DataFrame, fuori: pd.DataFrame) -> str:
    r = ["", "## Deriva tra capacità G.17 e capitale (opzione di calibrazione a)", "",
         "Deriva annua θ = (crescita capacità G.17 / crescita K^cap)^(1/4) − 1, 2012–2016:", "", "```",
         der.groupby("metodo_g17")["deriva_annua_2012_16"].describe()[["count", "mean", "min", "50%", "max"]]
         .to_string(float_format=lambda v: f"{v:.4f}"), "```", "",
         "Verifica fuori campione (θ stimata 2012–2014): errore medio assoluto sull'utilizzo, punti percentuali:", "",
         "| Anno | Gruppo | Senza deriva | Con deriva |", "|---:|---|---:|---:|"]
    for _, x in fuori.iterrows():
        r.append(f"| {x.anno} | {x.metodo_g17} | {100 * x.errore_u_senza_deriva:.1f} | {100 * x.errore_u_con_deriva:.1f} |")
    return "\n".join(r) + "\n"
