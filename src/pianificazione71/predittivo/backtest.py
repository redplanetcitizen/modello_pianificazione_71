"""Backtest a origine mobile (model predictive control) per M71-E6-predittivo.

Per ogni origine τ ∈ [2008, 2018] (τ + H ≤ 2019):
  1. parametri non anticipativi a τ (`origine.parametri_origine`);
  2. previsioni preliminari e benchmark (persistenza, ultimo tasso, trend mobile, P0);
  3. soluzione di ogni configurazione LP sull'orizzonte τ+1..τ+H; previsioni registrate per ogni h;
  4. lo stato all'origine successiva è quello osservato (closed loop); nessuna soluzione prevista è riusata come dato.
Le metriche sono calcolate contro i valori BEA osservati (revisionati: pseudo-previsione fuori campione).
La selezione degli iperparametri è annidata: per l'origine di test τ si usa la configurazione con il miglior
indicatore S medio sulle origini di validazione < τ (h = 1). Il periodo di test non entra mai nella selezione.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from ..archivio import Configurazione
from ..blocchi import COMPARTI
from ..modello import Opzioni, costruisci_e_risolvi
from ..passo_c1 import _csv
from ..registro import Esecuzione
from .formulazioni import RIFERIMENTO_P1, ROBUSTE, griglia
from .metriche import ALFA, tabella_metriche, theil_e_sintesi, unisci
from .origine import fattori_terminali, parametri_origine
from .previsori import METODI, prevedi, prevedi_selezionando
from .storico import SIMULATION_YEAR_MAX, SIMULATION_YEAR_MIN, Storico, costruisci_storico

TIPI4 = ("E", "S", "N", "R")
FINESTRE = {"A_2008_2019": (2009, 2019), "B_2010_2019": (2010, 2019), "C_2012_2016": (2012, 2016)}
ORIGINI_SHOCK = (2008, 2009)


# ------------------------------------------------------------------ valori osservati e livelli a τ
def _stock_fine(S: Storico, anno: int) -> pd.Series:
    p = S.pan[S.pan["anno"] == anno].set_index(["industria_io", "tipo"])["K_2012"] / 1000.0
    return p


def _inv(S: Storico, anno: int) -> pd.Series:
    return S.pan[S.pan["anno"] == anno].set_index(["industria_io", "tipo"])["I_2012"] / 1000.0


def serie_osservate(S: Storico, anni) -> pd.DataFrame:
    righe = []
    for t in anni:
        for j in S.industrie:
            righe.append((t, "produzione", j, float(S.x[t][j])))
        for c in S.prodotti:
            righe.append((t, "consumo", c, float(S.consumo[t][c])))
            righe.append((t, "importazioni", c, float(S.importazioni[t][c])))
        I, K = _inv(S, t), _stock_fine(S, t)
        for a in TIPI4:
            righe.append((t, "investimento_tipo", a, float(I[I.index.get_level_values(1) == a].sum())))
            righe.append((t, "stock_tipo", a, float(K[K.index.get_level_values(1) == a].sum())))
        for (j, a), v in I.items():
            righe.append((t, "investimento_ind", f"{j}|{a}", float(v)))
        for (j, a), v in K.items():
            righe.append((t, "stock_ind", f"{j}|{a}", float(v)))
        sc = S.scorte[S.scorte["anno"] == t].set_index("riga")["stock_2012"]
        for z in COMPARTI:
            righe.append((t, "scorte", str(z), float(sc[z])))
        righe += [(t, "aggregati", "produzione_tot", float(S.x[t].sum())), (t, "aggregati", "consumo_tot", float(S.consumo[t].sum())),
                  (t, "aggregati", "investimento_tot", float(I.sum())), (t, "aggregati", "importazioni_tot", float(S.importazioni[t].sum())),
                  (t, "aggregati", "scorte_tot", float(sc.sum()))]
    return pd.DataFrame(righe, columns=["anno", "gruppo", "chiave", "valore"])


def livelli_e_pesi(oss: pd.DataFrame, tau: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Livello osservato a τ e peso (quota nel gruppo a τ) per ogni chiave."""
    b = oss[oss["anno"] == tau].copy()
    b["origine"] = tau
    tot = b.groupby("gruppo")["valore"].transform(lambda v: v.abs().sum())
    pesi = b.assign(valore=(b["valore"].abs() / tot.where(tot > 0)).fillna(0.0))[["origine", "gruppo", "chiave", "valore"]]
    return b[["origine", "gruppo", "chiave", "valore"]], pesi


# ------------------------------------------------------------------ benchmark e P0
def previsioni_benchmark(oss: pd.DataFrame, tau: int, H: int, metodo: str, caso: str) -> pd.DataFrame:
    """Applica un previsore a ogni serie osservata (troncata a τ)."""
    piv = oss[oss["anno"] <= tau].pivot_table(index="anno", columns=["gruppo", "chiave"], values="valore")
    righe = []
    for (g, k) in piv.columns:
        s = piv[(g, k)].dropna()
        if len(s) == 0:
            continue
        if metodo == "P0":
            p, _ = prevedi_selezionando(s, tau, H)
        else:
            p = prevedi(s, tau, H, metodo)
        for h, (t, v) in enumerate(p.items(), start=1):
            righe.append((caso, tau, h, int(t), g, k, float(v)))
    return pd.DataFrame(righe, columns=["caso", "origine", "h", "anno", "gruppo", "chiave", "valore"])


# ------------------------------------------------------------------ estrazione dalla soluzione LP
def previsioni_modello(P, R, tau: int, caso: str) -> pd.DataFrame:
    anni = list(P.anni)
    v, xv = R.grezzi["v"], R.grezzi["valori"]
    val = lambda k: float(xv[v[k]]) if v.get(k) is not None else 0.0
    ind = R.tabelle["industrie"].set_index(["anno", "industria"])["x"]
    inv = R.tabelle["investimento"]
    K = {c: float(P.K0[c]) for c in P.K0.index}
    righe = []
    for h, t in enumerate(anni, start=1):
        for j in P.industrie:
            righe.append((caso, tau, h, t, "produzione", j, float(ind[(t, j)])))
        for c in P.prodotti:
            righe.append((caso, tau, h, t, "consumo", c, val(("c", c, t))))
            righe.append((caso, tau, h, t, "importazioni", c, val(("m", c, t))))
        it = inv[inv["anno"] == t].set_index(["industria", "tipo"])["I"]
        for a in TIPI4:
            righe.append((caso, tau, h, t, "investimento_tipo", a, float(it[it.index.get_level_values(1) == a].sum())))
        for (j, a), val_i in it.items():
            righe.append((caso, tau, h, t, "investimento_ind", f"{j}|{a}", float(val_i)))
        # stock di fine anno t = K_{t+1} dall'identità del modello
        for c in list(K):
            K[c] = (1 - float(P.delta[c])) * K[c] + float(it.get(c, 0.0))
        for a in TIPI4:
            righe.append((caso, tau, h, t, "stock_tipo", a, float(sum(k for (j, b), k in K.items() if b == a))))
        for (j, a), k in K.items():
            righe.append((caso, tau, h, t, "stock_ind", f"{j}|{a}", float(k)))
        stot = 0.0
        for z in COMPARTI:
            s = val(("S", z, t))
            stot += s
            righe.append((caso, tau, h, t, "scorte", str(z), s))
        ag = R.tabelle["aggregati"].set_index("anno").loc[t]
        righe += [(caso, tau, h, t, "aggregati", "produzione_tot", float(ag["produzione_lorda"])),
                  (caso, tau, h, t, "aggregati", "consumo_tot", float(ag["consumo_privato"])),
                  (caso, tau, h, t, "aggregati", "investimento_tot", float(it.sum())),
                  (caso, tau, h, t, "aggregati", "importazioni_tot", float(ag["importazioni"])),
                  (caso, tau, h, t, "aggregati", "scorte_tot", stot)]
    return pd.DataFrame(righe, columns=["caso", "origine", "h", "anno", "gruppo", "chiave", "valore"])


def diagnostica(P, R, o: Opzioni) -> dict:
    du = R.grezzi["duali"]
    fam = du.index.str.split("[").str[0]
    v, xv = R.grezzi["v"], R.grezzi["valori"]
    anni = list(P.anni)
    a = R.tabelle["aggregati"]
    attivi = du[du.abs() > 1e-9].groupby(fam[du.abs() > 1e-9]).size().to_dict()
    # utilizzo del lavoro e importazioni sul tetto
    lav = {t: float(sum(float(P.ell[t][j]) * float(xv[v[("x", j, t)]]) for j in P.industrie)) / P.lavoro_tot[t] for t in anni}
    imp = {t: float(sum(float(xv[v[("m", c, t)]]) for c in P.prodotti)) / P.import_tot[t] for t in anni}
    # utilizzo della capacità: x κ / (K^cap (1+θ)^(t−a0)); K ricostruito
    K = {c: float(P.K0[c]) for c in P.K0.index}
    util = []
    inv = R.tabelle["investimento"]
    for t in anni:
        it = inv[inv["anno"] == t].set_index(["industria", "tipo"])["I"]
        for j in P.kappa.index:
            tipi = ["R"] if j == "HS" else [a_ for a_ in ("E", "S", "N") if (j, a_) in P.K0.index]
            kcap = sum((1.0 if a_ == "R" else float(P.w[(j, a_)])) * K[(j, a_)] for a_ in tipi)
            if kcap > 0:
                util.append(float(xv[v[("x", j, t)]]) * float(P.kappa[j]) / (1 + float(P.theta.get(j, 0))) ** (t - anni[0]) / kcap)
        for c in list(K):
            K[c] = (1 - float(P.delta[c])) * K[c] + float(it.get(c, 0.0))
    util = np.array(util)
    ai_limiti = float(np.mean(np.abs(xv) < 1e-9))
    # consumo per classe (se O2/P2)
    classi = {}
    if ("c", P.prodotti[0], anni[0]) in v:
        rho = []
        pesi = []
        for t in anni:
            ob = P.consumo_oss[t].clip(lower=0)
            for c in P.prodotti:
                if ob[c] > 0:
                    rho.append(float(xv[v[("c", c, t)]]) / float(ob[c])); pesi.append(float(ob[c]))
        rho, pesi = np.array(rho), np.array(pesi) / (np.sum(pesi) or 1)
        classi = {"quota_<0.9": float(pesi[rho < 0.9 - 1e-6].sum()), "quota_=0.9": float(pesi[np.abs(rho - 0.9) < 1e-6].sum()),
                  "quota_=1.0": float(pesi[np.abs(rho - 1.0) < 1e-6].sum()), "quota_=1.2": float(pesi[np.abs(rho - 1.2) < 1e-6].sum()),
                  "quota_>1.2": float(pesi[rho > 1.2 + 1e-6].sum())}
    return {"stato": R.stato, "obiettivo": R.obiettivo, "n_var": R.n_var, "n_vincoli": R.n_vincoli,
            "vincoli_attivi": attivi, "duale_lavoro_medio": float(du[fam == "lavoro"].abs().mean()) if (fam == "lavoro").any() else np.nan,
            "duale_capacita_medio": float(du[fam == "capacita"].abs().mean()) if (fam == "capacita").any() else np.nan,
            "utilizzo_lavoro": lav, "importazioni_su_tetto": imp,
            "utilizzo_capacita_medio": float(util.mean()) if len(util) else np.nan,
            "utilizzo_capacita_quota_piena": float(np.mean(util > 0.999)) if len(util) else np.nan,
            "variazione_scorte": a.set_index("anno")["variazione_scorte"].to_dict(),
            "investimento_netto": a.set_index("anno")["investimento_netto"].to_dict(),
            "residuo_materiale": a.set_index("anno")["residuo_materiale"].to_dict(),
            "stock_terminale": {b: float(sum(k for (j, bb), k in K.items() if bb == b)) for b in TIPI4},
            "quota_variabili_a_zero": ai_limiti, **classi}


# ------------------------------------------------------------------ robustezza P3
def fattore_quantile(serie: pd.Series, tau: int, metodo: str, q: float, min_storia: int = 4) -> float:
    """Quantile q dei rapporti osservato/previsto a un passo sulle origini di validazione < τ."""
    s = serie.dropna(); s = s[s.index <= tau].sort_index()
    rapp = []
    for o in [o for o in s.index if o + 1 <= tau and (o - int(s.index[0])) >= min_storia]:
        try:
            p = float(prevedi(s, o, 1, metodo).iloc[0])
            if p > 0:
                rapp.append(float(s[o + 1]) / p)
        except ValueError:
            pass
    return float(np.quantile(rapp, q)) if len(rapp) >= 3 else 1.0


def applica_robustezza(P, note, S: Storico, tau: int, q: float):
    """Scala le esogene principali (lavoro totale, importazioni totali) al quantile q dei residui di validazione."""
    f = S.fte[S.fte["anno"] <= tau].groupby("anno")["fte_migliaia"].sum()
    imp = pd.Series({a: float(v.sum()) for a, v in S.importazioni.items() if a <= tau})
    fL = fattore_quantile(f, tau, note["metodi"]["lavoro_tot"], q)
    fM = fattore_quantile(imp, tau, note["metodi"]["import_tot"], q)
    for t in P.anni:
        P.lavoro_tot[t] *= fL
        P.import_tot[t] *= fM
    return {"fattore_lavoro": fL, "fattore_importazioni": fM}


# ------------------------------------------------------------------ backtest
def esegui(cfg: Configurazione, rapida: bool = False, H_max: int = 5, origini=None, cache: str = "cache",
           condizionata: bool = True, verbose: bool = True, rapporto: bool = True) -> Esecuzione:
    t_inizio = time.time()
    S = costruisci_storico(cfg, cache=cache, verbose=verbose)
    oss = serie_osservate(S, S.anni)
    configs = griglia(rapida)
    if origini:
        origini = list(origini)
    elif rapida:
        origini = [2009, 2011, 2013, 2015, 2017]
    else:
        origini = list(range(SIMULATION_YEAR_MIN, SIMULATION_YEAR_MAX))
    origini = [t for t in origini if SIMULATION_YEAR_MIN <= t < SIMULATION_YEAR_MAX]
    parametri = {"rapida": rapida, "H_max": H_max, "origini": origini, "SIMULATION_YEAR_MIN": SIMULATION_YEAR_MIN,
                 "SIMULATION_YEAR_MAX": SIMULATION_YEAR_MAX, "configurazioni": {k: {kk: (list(vv) if isinstance(vv, tuple) else vv)
                 for kk, vv in c["opzioni"].items()} for k, c in configs.items()}, "robuste": ROBUSTE, "alfa": ALFA}
    with Esecuzione("M71-E6-predittivo", cfg, parametri=parametri) as es:
        prev_tutte, diag, tempi, note_orig, livelli, pesi = [], [], [], {}, [], []
        for tau in origini:
            H = min(H_max, SIMULATION_YEAR_MAX - tau)
            t0 = time.time()
            P, note = parametri_origine(S, tau, H)
            note_orig[tau] = note
            liv, pe = livelli_e_pesi(oss, tau)
            livelli.append(liv); pesi.append(pe)
            for m, nome in (("persistenza", "persistenza"), ("ultimo_tasso", "ultimo_tasso"), ("trend_mobile_5", "trend_mobile"), ("P0", "P0")):
                prev_tutte.append(previsioni_benchmark(oss, tau, H, m, nome))
            fT1 = fattori_terminali(P, note)
            for nome, c in configs.items():
                o = Opzioni(**c["opzioni"], terminale_fattori=(fT1 if c["opzioni"].get("terminale", True) else None))
                t1 = time.time()
                R = costruisci_e_risolvi(P, o)
                tempi.append({"caso": nome, "origine": tau, "H": H, "secondi": time.time() - t1, "stato": R.stato})
                if R.stato != "Optimal":
                    diag.append({"caso": nome, "origine": tau, "stato": R.stato}); continue
                prev_tutte.append(previsioni_modello(P, R, tau, nome))
                diag.append({"caso": nome, "origine": tau, **diagnostica(P, R, o)})
            # P3: robustezza sulla configurazione di riferimento P1
            for nome, q in ROBUSTE.items():
                P3, n3 = parametri_origine(S, tau, H)
                fatt = applica_robustezza(P3, n3, S, tau, q)
                o = Opzioni(**configs[RIFERIMENTO_P1]["opzioni"], terminale_fattori=fattori_terminali(P3, n3))
                t1 = time.time()
                R = costruisci_e_risolvi(P3, o)
                tempi.append({"caso": nome, "origine": tau, "H": H, "secondi": time.time() - t1, "stato": R.stato})
                if R.stato == "Optimal":
                    prev_tutte.append(previsioni_modello(P3, R, tau, nome))
                    diag.append({"caso": nome, "origine": tau, **fatt, **diagnostica(P3, R, o)})
            # previsione condizionata (esogene future osservate) per la configurazione di riferimento
            if condizionata:
                Pc, nc = parametri_origine(S, tau, H, condizionata=True)
                o = Opzioni(**configs[RIFERIMENTO_P1]["opzioni"], terminale_fattori=fattori_terminali(Pc, nc))
                R = costruisci_e_risolvi(Pc, o)
                if R.stato == "Optimal":
                    prev_tutte.append(previsioni_modello(Pc, R, tau, "condizionata|" + RIFERIMENTO_P1))
            if verbose:
                print(f"origine {tau} (H={H}) completata in {time.time() - t0:.0f} s", flush=True)
        prev = pd.concat(prev_tutte, ignore_index=True)
        liv, pe = pd.concat(livelli, ignore_index=True), pd.concat(pesi, ignore_index=True)
        m = unisci(prev, oss, pe, liv)
        m["shock"] = m["origine"].isin(ORIGINI_SHOCK)
        # metriche per finestra
        risultati = {}
        for fin, (a, b) in FINESTRE.items():
            mf = m[(m["anno"] >= a) & (m["anno"] <= b)]
            if fin == "C_2012_2016":
                mf_multi = mf[mf["origine"] == 2011]        # esperimento centrale: origine 2011, h = 1..5
                mf = mf[mf["h"] == 1]                        # un passo, obiettivi 2012-2016
                if len(mf_multi):
                    tab_m = tabella_metriche(mf_multi)
                    tab_m, sint_m = theil_e_sintesi(tab_m)
                    risultati["C_2012_2016_origine_2011"] = (tab_m, sint_m)
            if len(mf) == 0:
                continue
            tab = tabella_metriche(mf)
            tab, sint = theil_e_sintesi(tab)
            risultati[fin] = (tab, sint)
        # metriche per origine (per la selezione annidata) — h = 1
        per_orig = tabella_metriche(m[m["h"] == 1], per=("caso", "origine", "h", "gruppo"))
        po = []
        for tau, g in per_orig.groupby("origine"):
            gg, ss = theil_e_sintesi(g.drop(columns="origine"))
            ss["origine"] = tau
            po.append(ss)
        S_orig = pd.concat(po, ignore_index=True)
        selezione = selezione_annidata(S_orig, [k for k in configs] + list(ROBUSTE))
        # sequenza selezionata: previsioni della configurazione scelta a ogni origine
        sel = [prev[(prev["caso"] == r["scelta"]) & (prev["origine"] == r["origine"])].assign(caso="selezionata")
               for _, r in selezione.iterrows()]
        if sel:
            ms = unisci(pd.concat(sel, ignore_index=True), oss, pe, liv)
            pers = m[m["caso"] == "persistenza"]
            for fin, (a, b) in FINESTRE.items():
                mf = ms[(ms["anno"] >= a) & (ms["anno"] <= b)]
                pf = pers[(pers["anno"] >= a) & (pers["anno"] <= b)]
                if fin == "C_2012_2016":
                    mf, pf = mf[mf["h"] == 1], pf[pf["h"] == 1]
                if len(mf) and fin in risultati:
                    tab_s, sint_s = theil_e_sintesi(tabella_metriche(pd.concat([mf, pf])))
                    tab, sint = risultati[fin]
                    risultati[fin] = (pd.concat([tab, tab_s[tab_s["caso"] == "selezionata"]], ignore_index=True),
                                      pd.concat([sint, sint_s[sint_s["caso"] == "selezionata"]], ignore_index=True))
        # scrittura
        es.scrivi_testo("osservato.csv", _csv(oss[oss["anno"] >= SIMULATION_YEAR_MIN]))
        casi_da_salvare = {"persistenza", "ultimo_tasso", "trend_mobile", "P0", RIFERIMENTO_P1, "condizionata|" + RIFERIMENTO_P1,
                           *ROBUSTE, *set(selezione["scelta"])}
        es.scrivi_testo("previsioni_aggregati_tutti_i_casi.csv", _csv(prev[prev["gruppo"].isin(["aggregati", "investimento_tipo", "stock_tipo"])]))
        es.scrivi_testo("previsioni_dettaglio_casi_principali.csv", _csv(prev[prev["caso"].isin(casi_da_salvare)]))
        es.scrivi_testo("errori_dettaglio_casi_principali.csv", _csv(m[m["caso"].isin(casi_da_salvare)].assign(errore=lambda d: d["valore"] - d["osservato"])))
        for fin, (tab, sint) in risultati.items():
            es.scrivi_testo(f"metriche_{fin}.csv", _csv(tab))
            es.scrivi_testo(f"sintesi_S_{fin}.csv", _csv(sint.sort_values(["h", "S"])))
        es.scrivi_testo("S_per_origine_h1.csv", _csv(S_orig))
        es.scrivi_testo("selezione_annidata.csv", _csv(selezione))
        es.scrivi_testo("diagnostica.json", json.dumps(diag, indent=1, default=str))
        es.scrivi_testo("tempi.csv", _csv(pd.DataFrame(tempi)))
        es.scrivi_testo("note_origini.json", json.dumps(note_orig, indent=1, default=str))
        es.scrivi_testo("sintesi.md", sintesi_md(risultati, selezione, tempi, t_inizio, S_orig))
    if rapporto:
        from .rapporto import completa
        completa(cfg, es.cartella, cache=cache)
    return es


def selezione_annidata(S_orig: pd.DataFrame, candidati: list[str], min_validazione: int = 2,
                       predefinita: str = RIFERIMENTO_P1) -> pd.DataFrame:
    """Per ogni origine di test τ: configurazione con S medio minimo sulle origini < τ (h = 1)."""
    s = S_orig[(S_orig["h"] == 1) & S_orig["caso"].isin(candidati)]
    righe = []
    for tau in sorted(s["origine"].unique()):
        val = s[s["origine"] < tau]
        if val["origine"].nunique() < min_validazione:
            righe.append({"origine": tau, "scelta": predefinita, "S_validazione": np.nan, "n_validazione": int(val["origine"].nunique()),
                          "motivo": "storia di validazione insufficiente: configurazione predefinita"})
            continue
        media = val.groupby("caso")["S"].mean().dropna()
        # candidati valutati su tutte le origini di validazione
        conteggio = val.groupby("caso")["origine"].nunique()
        media = media[conteggio[media.index] == val["origine"].nunique()]
        if media.empty:
            righe.append({"origine": tau, "scelta": predefinita, "S_validazione": np.nan, "n_validazione": int(val["origine"].nunique()), "motivo": "nessun candidato completo"})
            continue
        best = str(media.idxmin())
        righe.append({"origine": tau, "scelta": best, "S_validazione": float(media.min()), "n_validazione": int(val["origine"].nunique()), "motivo": ""})
    return pd.DataFrame(righe)


def sintesi_md(risultati: dict, selezione: pd.DataFrame, tempi: list, t_inizio: float, S_orig: pd.DataFrame) -> str:
    righe = ["# M71-E6-predittivo — sintesi del backtest", "",
             f"Tempo totale {time.time() - t_inizio:.0f} s; risoluzioni LP {len(tempi)}, tempo medio "
             f"{np.mean([t['secondi'] for t in tempi]):.1f} s.", ""]
    for fin, (tab, sint) in risultati.items():
        righe += [f"## {fin}", "", "Indicatore S (< 1: meglio della persistenza) per caso e orizzonte h — primi 12 per h = 1:", "", "```",
                  sint[sint["h"] == 1].sort_values("S").head(12).to_string(index=False, float_format=lambda v: f"{v:,.3f}"), "```", ""]
        if (sint["h"] > 1).any():
            righe += ["Per h > 1 (primi 8 per ogni h):", "", "```"]
            for h, g in sint[sint["h"] > 1].groupby("h"):
                righe += [f"h = {h}", g.sort_values("S").head(8).to_string(index=False, float_format=lambda v: f"{v:,.3f}")]
            righe += ["```", ""]
    righe += ["## Selezione annidata (h = 1)", "", "```", selezione.to_string(index=False), "```", ""]
    return "\n".join(righe) + "\n"
