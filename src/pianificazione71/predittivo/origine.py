"""Parametri del modello per una previsione originata in τ (M71-E6-predittivo).

Regola di non anticipazione: tutto ciò che entra in `Parametri` deriva dallo storico troncato a τ (`storico.tronca`),
tranne le grandezze future esplicitamente previste con i previsori preliminari (anch'essi troncati a τ).
Nel modo `condizionata=True` le variabili esogene future (lavoro, domanda pubblica, esportazioni, importazioni,
obiettivi di consumo, coefficienti tecnici) sono sostituite dai valori osservati: misura la capacità di
allocazione del modello, non una previsione ex ante.

Classificazione delle grandezze (vedi anche `audit.CLASSIFICAZIONE`):
  stato noto a τ        K0 (stock di fine τ), S0 (scorte di fine τ), I_prec (investimento di τ), capacità (κ, θ)
  parametro strutturale B, D, x_speciali, Φ, φR, δ, w, ℓ (persistenza o tendenza), σ, ψ, μ
  esogena prevista      L_t, G_t, X_t, F⁺_t, importazioni totali, obiettivi di consumo ĉ, x̂ (per P2 e P0)
  endogena              x, q, c, I, K, m, S, r
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..capacita import capitale_capacita, controllo_g17, deriva_capacita, inviluppo_capacita, pesi_costo_uso
from ..dati_modello import TIPI, Parametri
from .previsori import prevedi, prevedi_quote, prevedi_selezionando, seleziona
from .storico import SIMULATION_YEAR_MAX, SIMULATION_YEAR_MIN, Storico, tronca

FINESTRA_DELTA = 5       # anni per δ medio e ψ
FINESTRA_DERIVA = 5      # anni per la deriva G.17 (τ−5 → τ)


def _serie(dizionario: dict, chiave=None) -> pd.Series:
    """Serie annuale (indice anni) da un dict anno → Series/scalare."""
    if chiave is None:
        return pd.Series({a: float(v) for a, v in dizionario.items()}).sort_index()
    return pd.Series({a: float(v[chiave]) for a, v in dizionario.items()}).sort_index()


def _tabella(dizionario: dict, colonne) -> pd.DataFrame:
    return pd.DataFrame({a: v.reindex(colonne).fillna(0.0) for a, v in dizionario.items()}).T.sort_index()


def previsione_tabella(diz: dict, colonne, tau: int, H: int, metodo: str | None, inizio: int | None,
                       per_voce: bool) -> tuple[dict, dict]:
    """Previsione anno → Series per una tabella (anni × voci). per_voce: metodo selezionato voce per voce;
    altrimenti totale × quote (quote persistenti)."""
    tab = _tabella(diz, colonne)
    tab = tab[tab.index <= tau]
    out, scelte = {}, {}
    if per_voce:
        prev = {}
        for c in colonne:
            s = tab[c]
            if (s.abs() < 1e-12).all():
                prev[c] = pd.Series(0.0, index=range(tau + 1, tau + H + 1))
                continue
            if metodo is None:
                p, m = prevedi_selezionando(s, tau, H, inizio=inizio)
            else:
                p, m = prevedi(s, tau, H, metodo, inizio=inizio), metodo
            prev[c], scelte[c] = p, m
        df = pd.DataFrame(prev)
    else:
        df, scelte = prevedi_quote(tab, tau, H, metodo, "persistenza", inizio=inizio)
    for t in df.index:
        out[int(t)] = df.loc[t].reindex(colonne).fillna(0.0)
    return out, scelte


def parametri_origine(S_pieno: Storico, tau: int, H: int, condizionata: bool = False,
                      inizio_storia: int | None = None, metodo_esogene: str | None = None,
                      metodo_lavoro: str | None = None, inizio_inviluppo: int = 1997) -> tuple[Parametri, dict]:
    """Parametri per la previsione τ+1..τ+H. Restituisce (P, note) con i metodi selezionati e i controlli."""
    assert SIMULATION_YEAR_MIN <= tau < tau + H <= SIMULATION_YEAR_MAX, "orizzonte fuori da [2008, 2019]"
    S = tronca(S_pieno, tau)
    anni = tuple(range(tau + 1, tau + H + 1))
    ind, prod, priv = S.industrie, S.prodotti, S.private
    P = Parametri(anni, ind, prod, priv)
    note = {"tau": tau, "H": H, "condizionata": condizionata, "metodi": {}}
    cap_ind = [j for j in ind if j in priv and j != "HS"]

    # --- parametri strutturali: persistenza dell'ultimo anno osservato ---------------------------
    for t in anni:
        P.B[t], P.D[t], P.x_speciali[t] = S.B[tau], S.D[tau], S.x_speciali[tau]
        for a in TIPI:
            P.phi[(t, a)] = S.phi[(tau, a)]
        P.phi_R[t] = S.phi_R[tau]
        P.scorte_oss[t] = S.scorte_prodotti[tau]
        for a in ("E", "S", "N", "R"):
            P.inv_oss_prodotti[(t, a)] = S.inv_prodotti[(tau, a)]

    # --- esogene previste ------------------------------------------------------------------------
    gruppi = {"consumo": S.consumo, "pubblica": S.pubblica, "esportazioni": S.esportazioni,
              "usi_esterni_fissi": S.usi_esterni_fissi, "import_oss": S.importazioni, "x_oss": S.x, "q_oss": S.q}
    for nome, diz in gruppi.items():
        colonne = ind if nome == "x_oss" else prod
        per_voce = nome in ("x_oss", "q_oss")
        pr, sc = previsione_tabella(diz, colonne, tau, H, metodo_esogene, inizio_storia, per_voce)
        note["metodi"][nome] = sc
        setattr(P, "consumo_oss" if nome == "consumo" else nome, pr)
    tot_imp = pd.Series({a: float(v.sum()) for a, v in S.importazioni.items()})
    p_imp, m_imp = prevedi_selezionando(tot_imp, tau, H, inizio=inizio_storia) if metodo_esogene is None else (
        prevedi(tot_imp, tau, H, metodo_esogene, inizio=inizio_storia), metodo_esogene)
    note["metodi"]["import_tot"] = m_imp
    uso_tau = S.B[tau] @ S.x[tau] + S.consumo[tau] + S.pubblica[tau] + sum(S.inv_prodotti[(tau, a)] for a in ("E", "S", "N", "R"))
    mu_tau = (S.importazioni[tau] / uso_tau.where(uso_tau > 0)).fillna(0.0).clip(upper=1.0)
    for t in anni:
        P.mu[t] = mu_tau
        P.import_tot[t] = float(p_imp[t])
        # coerenza: importazioni per prodotto previste riscalate al totale previsto
        somma = float(P.import_oss[t].sum())
        if somma > 0:
            P.import_oss[t] = P.import_oss[t] * P.import_tot[t] / somma

    # --- lavoro: FTE totale previsto e coefficienti per industria ------------------------------------
    f = S.fte.pivot(index="anno", columns="industria_io", values="fte_migliaia").reindex(columns=ind).fillna(0.0)
    f = f[f.index <= tau]
    L = f.sum(axis=1)
    pL, mL = prevedi_selezionando(L, tau, H, inizio=inizio_storia) if metodo_lavoro is None else (
        prevedi(L, tau, H, metodo_lavoro, inizio=inizio_storia), metodo_lavoro)
    note["metodi"]["lavoro_tot"] = mL
    note["L_tau"] = float(L[tau])
    note["x_HS_tau"] = float(S.x[tau]["HS"])
    ell = pd.DataFrame({j: f[j] / _tabella(S.x, ind)[j].reindex(f.index) for j in ind}).replace([np.inf, -np.inf], np.nan)
    ell_prev, sc_ell = {}, {}
    for j in ind:
        s = ell[j].dropna()
        if len(s) == 0 or (s <= 0).all():
            ell_prev[j] = pd.Series(0.0, index=list(anni))
            continue
        if metodo_lavoro is None:
            m = seleziona(s, tau, inizio=inizio_storia)
        else:
            m = metodo_lavoro
        ell_prev[j], sc_ell[j] = prevedi(s, tau, H, m, inizio=inizio_storia), m
    note["metodi"]["ell"] = sc_ell
    for t in anni:
        P.ell[t] = pd.Series({j: float(ell_prev[j][t]) for j in ind})
        P.lavoro_tot[t] = float(pL[t])

    # --- capitale: stato noto a τ ------------------------------------------------------------------
    pan = S.pan
    fine_tau = pan[pan["anno"] == tau].set_index(["industria_io", "tipo"])
    P.K0 = fine_tau["K_2012"] / 1000.0                       # stock di fine τ = inizio τ+1 (miliardi)
    P.I_prec = fine_tau["I_2012"] / 1000.0
    fin = pan[(pan["anno"] > tau - FINESTRA_DELTA) & (pan["anno"] <= tau)].dropna(subset=["delta"])
    g = fin.groupby(["industria_io", "tipo"])
    P.delta = (g["D_2012"].sum() / g["K_inizio_2012"].sum()).reindex(P.K0.index).fillna(0.0)
    P.I_oss = pd.DataFrame(columns=["industria_io", "tipo", "anno", "I"])   # nessun valore futuro nel modello
    # stock osservato: solo fino a τ+1 (inizio anno = fine τ), per l'identità; nulla oltre
    P.K_oss = (pan.assign(anno=pan["anno"] + 1).set_index(["industria_io", "tipo", "anno"])["K_2012"] / 1000.0).sort_index()

    # --- pesi di capacità w: costi d'uso con KLEMS dell'anno τ ---------------------------------------
    rem = S.klems[tau]
    # pesi_costo_uso richiede K_inizio_2012 e delta per l'anno di calibrazione: usa la riga di τ
    pesi, _ = pesi_costo_uso(pan, rem, anno=tau)
    P.w = pesi.set_index(["industria_io", "tipo"])["w"]
    kcap = capitale_capacita(pan, pesi)                       # K^cap di inizio anno, anni ≤ τ

    # --- capacità: κ calibrato a τ, deriva da dati ≤ τ ------------------------------------------------
    xr = pd.DataFrame([{"industria_io": j, "anno": a, "x_reale": float(S.x[a][j]) * 1000.0}
                       for a in S.anni for j in ind])
    u_g17 = S.g17_u[S.g17_u["anno"] <= tau]
    kappa_rows, theta = {}, {}
    # G.17: m_τ = x_τ / (K^cap_τ · u_τ); θ dalla deriva sulla finestra [τ−n, τ]
    k_tau = kcap[kcap["anno"] == tau].set_index("industria_io")["K_cap"]
    from ..capacita import kappa as _kappa
    kap = _kappa(kcap, xr, u_g17, anno=tau)
    base = max(tau - FINESTRA_DERIVA, min(S.anni))
    cap = S.g17_cap[[c for c in S.g17_cap.columns if base <= c <= tau]]
    ctrl = controllo_g17(kcap[(kcap["anno"] >= base) & (kcap["anno"] <= tau)], xr[(xr["anno"] >= base) & (xr["anno"] <= tau)],
                         kap, u_g17[u_g17["anno"] >= base], cap, base=base)
    der, _ = deriva_capacita(ctrl, fine_stima=tau, base=base)
    der = der.set_index("industria_io")
    col = f"deriva_annua_{base}_{tau % 100}"
    for j in S.g17:
        th = float(der[col].get(j, 0.0)) if j in der.index else 0.0
        k = float(kap.set_index("industria_io")["kappa"].get(j, np.nan))
        if not np.isfinite(k) or k <= 0:
            continue
        kappa_rows[j] = k / (1 + th)          # anni[0] = τ+1: fattore (1+θ)^(t−anni[0]) parte da 1
        theta[j] = th
    # fuori G.17 e HS: inviluppo con tendenza su [inizio_inviluppo, τ]
    non = [j for j in cap_ind if j not in set(S.g17)] + ["HS"]
    x_dict = {a: S.x[a] * 1000.0 for a in S.anni}
    inv = inviluppo_capacita(pan[pan["anno"] >= inizio_inviluppo - 1], x_dict, P.w, non,
                             [a for a in S.anni if a >= inizio_inviluppo], tau).set_index("industria_io")
    for j in non:
        if j not in inv.index:
            continue
        r0, u, th = float(inv.at[j, "r_a0"]), float(inv.at[j, "u_inviluppo_tendenza"]), float(inv.at[j, "theta_inviluppo_tendenza"])
        m_tau = r0 / u                                          # rapporto di capacità a τ
        kappa_rows[j] = 1.0 / (m_tau * (1 + th))
        theta[j] = th
    P.kappa = pd.Series(kappa_rows)
    P.theta = pd.Series(theta).reindex(P.kappa.index).fillna(0.0)
    P.g17 = list(P.kappa.index)                                  # tutte le industrie con capacità calibrata: u = 1
    P.capacita_inviluppo = inv.reset_index()
    note["inviluppo_tendenza_u_medio"] = float((inv["u_inviluppo_tendenza"] * pd.Series({j: float(S.x[tau][j]) for j in inv.index})).sum()
                                              / sum(float(S.x[tau][j]) for j in inv.index))

    # --- scorte: stato di fine τ e σ a τ ------------------------------------------------------------
    sc = S.scorte
    P.S_oss = sc
    P.S0 = sc[sc["anno"] == tau].set_index("riga")["stock_2012"]
    from ..blocchi import COMPARTI, industrie_comparto
    righe = []
    for z, (nome, _) in COMPARTI.items():
        inds = industrie_comparto(z, priv)
        xs = sum(float(S.x[tau][j]) for j in inds)
        righe.append({"riga": z, "comparto": nome, "sigma": float(P.S0[z]) / xs if xs > 0 else 0.0})
    P.sigma = pd.DataFrame(righe)
    pos = sum(S.scorte_prodotti[a].clip(lower=0) for a in S.anni if a > tau - FINESTRA_DELTA)
    P.psi = pos / pos.sum()

    # --- previsioni preliminari di investimento per tipo e scorte per comparto (per P0/P2) ----------
    inv_tipo = pan[pan["anno"] <= tau].groupby(["anno", "tipo"])["I_2012"].sum().unstack() / 1000.0
    prev_inv, sc_inv = {}, {}
    for a in inv_tipo.columns:
        prev_inv[a], sc_inv[a] = prevedi_selezionando(inv_tipo[a], tau, H, inizio=inizio_storia)
    prev_inv = pd.DataFrame(prev_inv)
    st = sc[sc["anno"] <= tau].pivot(index="anno", columns="riga", values="stock_2012")
    prev_sc, sc_sc = {}, {}
    for z in st.columns:
        prev_sc[z], sc_sc[z] = prevedi_selezionando(st[z], tau, H, inizio=inizio_storia)
    prev_sc = pd.DataFrame(prev_sc)
    P.previsioni = {"investimento_tipo": prev_inv, "scorte": prev_sc}
    note["metodi"]["investimento_tipo"] = sc_inv
    note["metodi"]["scorte"] = sc_sc

    # --- modo condizionato: esogene future osservate ------------------------------------------------
    if condizionata:
        for t in anni:
            P.B[t], P.D[t], P.x_speciali[t] = S_pieno.B[t], S_pieno.D[t], S_pieno.x_speciali[t]
            for a in TIPI:
                P.phi[(t, a)] = S_pieno.phi[(t, a)]
            P.phi_R[t] = S_pieno.phi_R[t]
            P.consumo_oss[t], P.pubblica[t] = S_pieno.consumo[t], S_pieno.pubblica[t]
            P.esportazioni[t], P.usi_esterni_fissi[t] = S_pieno.esportazioni[t], S_pieno.usi_esterni_fissi[t]
            P.import_oss[t], P.x_oss[t], P.q_oss[t] = S_pieno.importazioni[t], S_pieno.x[t], S_pieno.q[t]
            P.import_tot[t] = float(S_pieno.importazioni[t].sum())
            uso = S_pieno.B[t] @ S_pieno.x[t] + S_pieno.consumo[t] + S_pieno.pubblica[t] + sum(
                S_pieno.inv_prodotti[(t, a)] for a in ("E", "S", "N", "R"))
            P.mu[t] = (S_pieno.importazioni[t] / uso.where(uso > 0)).fillna(0.0).clip(upper=1.0)
            fp = S_pieno.fte[S_pieno.fte["anno"] == t].set_index("industria_io")["fte_migliaia"].reindex(ind).fillna(0.0)
            P.lavoro_tot[t] = float(fp.sum())
            P.ell[t] = (fp / S_pieno.x[t]).replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return P, note


def fattori_terminali(P: Parametri, note: dict) -> dict:
    """T1 non anticipativo: stock finale (fine τ+H) ≥ fattore × stock iniziale (fine τ), con
    fattore E+S+N = L̂_{τ+H} / L_τ (FTE previsti / FTE osservati a τ) e fattore R = x̂_{HS,τ+H} / x_{HS,τ}.
    Usa solo previsioni fatte a τ e il valore osservato in τ."""
    T = list(P.anni)[-1]
    return {"ESN": float(P.lavoro_tot[T] / note["L_tau"]), "R": float(P.x_oss[T]["HS"] / note["x_HS_tau"])}
