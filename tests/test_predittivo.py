"""Test della pipeline predittiva M71-E6-predittivo."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pianificazione71.predittivo import backtest as bt
from pianificazione71.predittivo.formulazioni import RIFERIMENTO_P1, TRATTI, griglia
from pianificazione71.predittivo.metriche import tabella_metriche, theil_e_sintesi, unisci
from pianificazione71.predittivo.previsori import METODI, errori_validazione, prevedi, seleziona
from pianificazione71.predittivo.storico import ANNO_MAX, SIMULATION_YEAR_MAX, SIMULATION_YEAR_MIN

ARCHIVIO = Path(os.environ.get("DATI_ECONOMICI", r"C:\Users\franc\Documents\dati_economici"))
dati = pytest.mark.skipif(not (ARCHIVIO / "bea/2026-09-22/manual/M3/detailnonres_stk1.xlsx").is_file(),
                          reason="archivio dati non disponibile")


# ------------------------------------------------------------------ senza dati
def test_previsori_di_base():
    s = pd.Series([100.0, 110.0, 121.0, 133.1], index=[2005, 2006, 2007, 2008])
    assert prevedi(s, 2008, 2, "persistenza").tolist() == [133.1, 133.1]
    p = prevedi(s, 2008, 2, "ultimo_tasso")
    assert p.index.tolist() == [2009, 2010] and abs(p.iloc[0] - 146.41) < 1e-6
    p = prevedi(s, 2008, 1, "trend_espandente")
    assert abs(p.iloc[0] - 146.41) < 1e-3
    # nessun uso di anni > τ: aggiungere anni futuri non cambia la previsione
    s2 = pd.concat([s, pd.Series([999.0, 5.0], index=[2009, 2010])])
    for m in METODI:
        assert prevedi(s2, 2008, 2, m).tolist() == prevedi(s, 2008, 2, m).tolist()
    assert seleziona(s2, 2008) in METODI


def test_intervallo_simulazione():
    assert SIMULATION_YEAR_MIN == 2008 and SIMULATION_YEAR_MAX == 2019 and ANNO_MAX == 2019
    assert bt.ORIGINI_SHOCK == (2008, 2009)
    assert bt.FINESTRE["B_2010_2019"] == (2010, 2019) and bt.FINESTRE["A_2008_2019"][1] == 2019
    assert bt.FINESTRE["C_2012_2016"] == (2012, 2016)


def test_metriche_persistenza_uguale_uno():
    oss = pd.DataFrame({"anno": [2011, 2012] * 2, "gruppo": ["produzione"] * 2 + ["consumo"] * 2,
                        "chiave": ["a", "a", "b", "b"], "valore": [10.0, 12.0, 5.0, 4.0]})
    prev = pd.DataFrame({"caso": ["persistenza"] * 2 + ["modello"] * 2, "origine": 2011, "h": 1, "anno": 2012,
                         "gruppo": ["produzione", "consumo"] * 2, "chiave": ["a", "b"] * 2, "valore": [10.0, 5.0, 11.0, 4.5]})
    liv, pesi = bt.livelli_e_pesi(oss, 2011)
    m = unisci(prev, oss, pesi, liv)
    tab, sint = theil_e_sintesi(tabella_metriche(m))
    s = sint.set_index("caso")["S"]
    assert abs(s["persistenza"] - 1.0) < 1e-12 and s["modello"] == pytest.approx(0.5)


def test_selezione_annidata_non_usa_il_test():
    righe = []
    for tau in (2008, 2009, 2010, 2011):
        righe += [{"caso": "A", "h": 1, "S": 0.5 if tau < 2011 else 5.0, "origine": tau},
                  {"caso": "B", "h": 1, "S": 0.8, "origine": tau}]
    sel = bt.selezione_annidata(pd.DataFrame(righe), ["A", "B"], min_validazione=2, predefinita="B")
    sel = sel.set_index("origine")
    assert sel.loc[2008, "scelta"] == "B" and sel.loc[2009, "scelta"] == "B"     # storia insufficiente → predefinita
    assert sel.loc[2011, "scelta"] == "A"                                          # scelto su 2008-2010, non sul 2011


def test_griglia_coerente():
    g = griglia()
    assert RIFERIMENTO_P1 in g
    for nome, c in g.items():
        assert c["opzioni"]["obiettivo"] in ("O2", "P2")
        if c["famiglia"] == "P1":
            assert c["opzioni"]["tratti_o2"] == TRATTI[c["tratti"]]


# ------------------------------------------------------------------ con dati
@pytest.fixture(scope="module")
def storico():
    from pianificazione71.archivio import carica_configurazione
    from pianificazione71.predittivo.storico import costruisci_storico
    cfg = carica_configurazione(Path(__file__).resolve().parents[1] / "config" / "dati.toml")
    return costruisci_storico(cfg, cache=Path(__file__).resolve().parents[1] / "cache", verbose=False)


def _perturba(S, tau):
    """Copia dello storico con tutti i dati successivi a τ alterati (moltiplicati per 1,37 e permutati)."""
    T = copy.deepcopy(S)
    for nome in ("B", "D", "x_speciali", "x", "q", "consumo", "pubblica", "esportazioni", "importazioni",
                 "usi_esterni_fissi", "scorte_prodotti", "phi_R"):
        d = getattr(T, nome)
        for a in d:
            if a > tau:
                d[a] = d[a] * 1.37 + 3.0
    for k in T.phi:
        if k[0] > tau:
            T.phi[k] = T.phi[k] * 0.5
    for k in T.inv_prodotti:
        if k[0] > tau:
            T.inv_prodotti[k] = T.inv_prodotti[k] * 2.0
    for df, col in ((T.pan, "anno"), (T.fte, "anno"), (T.scorte, "anno"), (T.g17_u, "anno")):
        num = df.select_dtypes("float").columns.difference([col])
        df.loc[df[col] > tau, num] = df.loc[df[col] > tau, num] * 1.37 + 1.0
    for c in T.g17_cap.columns:
        if c > tau:
            T.g17_cap[c] = T.g17_cap[c] * 1.5
    for c in T.klems.columns:
        if c > tau:
            T.klems[c] = T.klems[c] * 1.5
    return T


def _confronta_parametri(P, Q):
    for nome in ("B", "D", "x_speciali", "consumo_oss", "pubblica", "esportazioni", "import_oss", "x_oss", "ell", "mu"):
        a, b = getattr(P, nome), getattr(Q, nome)
        for t in a:
            assert np.allclose(a[t].values, b[t].values), nome
    for nome in ("K0", "I_prec", "delta", "w", "kappa", "theta", "S0", "psi"):
        assert np.allclose(getattr(P, nome).sort_index().values, getattr(Q, nome).sort_index().values), nome
    assert P.lavoro_tot == Q.lavoro_tot and P.import_tot == Q.import_tot
    assert np.allclose(P.previsioni["investimento_tipo"].values, Q.previsioni["investimento_tipo"].values)


@dati
@pytest.mark.lento
def test_storico_senza_anni_oltre_2019(storico):
    from pianificazione71.predittivo.storico import verifica_limiti
    verifica_limiti(storico)
    assert max(storico.anni) == 2019 and 2020 not in storico.x


@dati
@pytest.mark.lento
def test_non_anticipazione_e_identita(storico):
    from pianificazione71.modello import Opzioni, costruisci_e_risolvi
    from pianificazione71.predittivo.origine import fattori_terminali, parametri_origine
    tau, H = 2013, 2
    P, note = parametri_origine(storico, tau, H)
    Q, note_q = parametri_origine(_perturba(storico, tau), tau, H)
    _confronta_parametri(P, Q)
    assert fattori_terminali(P, note) == fattori_terminali(Q, note_q)
    with pytest.raises(AssertionError):
        parametri_origine(storico, 2018, 2)          # 2020 oltre il limite
    with pytest.raises(AssertionError):
        parametri_origine(storico, 2007, 1)          # prima del 2008
    o = Opzioni(**griglia()[RIFERIMENTO_P1]["opzioni"], terminale_fattori=fattori_terminali(P, note))
    R = costruisci_e_risolvi(P, o)
    R2 = costruisci_e_risolvi(Q, Opzioni(**griglia()[RIFERIMENTO_P1]["opzioni"], terminale_fattori=fattori_terminali(Q, note_q)))
    assert R.stato == "Optimal" and R.obiettivo == R2.obiettivo                    # previsione invariante
    assert np.array_equal(R.grezzi["valori"], R2.grezzi["valori"])
    R3 = costruisci_e_risolvi(P, o)
    assert np.array_equal(R.grezzi["valori"], R3.grezzi["valori"])                  # determinismo
    v, xv = R.grezzi["v"], R.grezzi["valori"]
    assert np.all(np.isfinite(xv)) and float(np.min(xv[[i for k, i in v.items() if k[0] != "dS"]])) >= -1e-9  # non negatività
    anni = list(P.anni)
    val = lambda k: float(xv[v[k]])
    # identità di accumulazione
    for (j, a) in P.K0.index:
        if (j, a, anni[0] + 1) not in v:
            continue
        k = float(P.K0[(j, a)])
        for t in anni:
            k = (1 - float(P.delta[(j, a)])) * k + val(("I", j, a, t))
            assert abs(val(("K", j, a, t + 1)) - k) < 1e-6
    # bilanci materiali, lavoro, importazioni, capacità, scorte
    cap_ind = [j for j in P.kappa.index if j != "HS"]
    for t in anni:
        x = pd.Series({j: val(("x", j, t)) for j in P.industrie})
        q = pd.Series({c: val(("q", c, t)) for c in P.prodotti})
        m = pd.Series({c: val(("m", c, t)) for c in P.prodotti})
        c_ = pd.Series({c: val(("c", c, t)) for c in P.prodotti})
        r = pd.Series({c: val(("r", c, t)) for c in P.prodotti})
        inv = pd.Series(0.0, index=P.prodotti)
        for a in ("E", "S", "N"):
            I = pd.Series({j: val(("I", j, a, t)) if ("I", j, a, t) in v else 0.0 for j in P.industrie})
            inv += P.phi[(t, a)].fillna(0.0) @ I.reindex(P.phi[(t, a)].columns).fillna(0.0)
        inv += val(("I", "HS", "R", t)) * P.phi_R[t]
        dS = sum(val(("dS", z, t)) for z in P.sigma["riga"])
        lhs = q + m - r - P.B[t] @ x - c_ - inv - P.psi * dS
        rhs = P.pubblica[t] + P.esportazioni[t] + P.usi_esterni_fissi[t]
        assert float((lhs - rhs).abs().max()) < 1e-6
        assert float((P.ell[t] * x).sum()) <= P.lavoro_tot[t] * (1 + 1e-9)
        assert float(m.sum()) <= P.import_tot[t] * (1 + 1e-9)
        for z in P.sigma["riga"]:
            assert val(("S", z, t)) >= -1e-9
    # unità: stock in miliardi di dollari 2012
    assert 1e3 < float(P.K0.sum()) < 1e5
    # nessun anno oltre il 2019 nelle previsioni estratte
    prev = bt.previsioni_modello(P, R, tau, "prova")
    assert prev["anno"].max() <= 2019 and np.all(np.isfinite(prev["valore"]))


@dati
@pytest.mark.lento
def test_valore_terminale_nell_obiettivo(storico):
    """T2: obiettivo = punteggio O2 + λ_K Σ K_{T+1} (con K in miliardi 2012, v = 1) e senza penalità."""
    from pianificazione71.modello import Opzioni, costruisci_e_risolvi
    from pianificazione71.predittivo.origine import parametri_origine
    P, _ = parametri_origine(storico, 2014, 1)
    lam = 1e-5
    o = Opzioni(obiettivo="O2", u_non_g17=1.0, sigma_fattore=0.85, terminale=False, valore_terminale=lam, tratti_o2=TRATTI["E6"])
    R = costruisci_e_risolvi(P, o)
    v, xv = R.grezzi["v"], R.grezzi["valori"]
    t = P.anni[0]
    ob = P.consumo_oss[t].clip(lower=0)
    peso = ob / ob.sum()
    punteggio = 0.0
    for c in P.prodotti:
        if ob[c] <= 0:
            continue
        rho = float(xv[v[("c", c, t)]]) / float(ob[c])
        resto, s = rho, 0.0
        for amp, pun in TRATTI["E6"]:
            s += min(resto, amp) * pun
            resto = max(resto - amp, 0.0)
        punteggio += float(peso[c]) * s
    K_fin = sum(float(xv[v[("K", j, a, t + 1)]]) for (j, a) in P.K0.index if ("K", j, a, t + 1) in v)
    assert R.obiettivo == pytest.approx(punteggio + lam * K_fin, rel=1e-6)


@dati
@pytest.mark.lento
def test_e6_originale_invariato():
    """Lo scenario E6 (2012-2016_penalita) si riproduce con il codice esteso."""
    from pianificazione71.archivio import carica_configurazione
    from pianificazione71.dati_modello import costruisci
    from pianificazione71.modello import Opzioni, costruisci_e_risolvi
    from pianificazione71.passo_e5 import fattori
    cfg = carica_configurazione(Path(__file__).resolve().parents[1] / "config" / "dati.toml")
    P = costruisci(cfg, range(2012, 2017), inviluppo=True)
    f = fattori(P)["lavoro_aggregata"]
    R = costruisci_e_risolvi(P, Opzioni(obiettivo="O2", capacita_non_g17="inviluppo_tendenza", sigma_fattore=0.85,
                                        terminale_fattori=f, penalita_var_inv=0.10))
    assert R.stato == "Optimal" and R.obiettivo == pytest.approx(4.786993543584568, abs=1e-6)


@dati
@pytest.mark.lento
def test_backtest_comando_unico(tmp_path):
    from pianificazione71.archivio import carica_configurazione
    cfg = carica_configurazione(Path(__file__).resolve().parents[1] / "config" / "dati.toml")
    es = bt.esegui(cfg, rapida=True, H_max=1, origini=[2018], cache=str(Path(__file__).resolve().parents[1] / "cache"),
                   condizionata=False, verbose=False)
    for f in ("sintesi.md", "metriche_A_2008_2019.csv", "selezione_annidata.csv", "diagnostica.json", "osservato.csv"):
        assert (es.cartella / f).is_file()
    oss = pd.read_csv(es.cartella / "osservato.csv")
    assert oss["anno"].max() <= 2019
