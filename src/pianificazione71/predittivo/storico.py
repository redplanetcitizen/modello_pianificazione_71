"""Storico 1997-2019 per la pipeline predittiva M71-E6-predittivo.

Costruisce una sola volta, dai dati grezzi dell'archivio, tutte le serie annuali che il modello usa, per ogni anno
del periodo ammesso (1997-2019), a prezzi 2012 e in miliardi di dollari. È un pannello di dati osservati
(revisionati ex post, non vintage): ogni esperimento è quindi una pseudo-previsione fuori campione.

Il pannello non contiene alcun dato dal 2020 in poi (ANNO_MAX = 2019): la verifica è in `verifica_limiti`.
Il modulo `origine` tronca lo storico all'origine τ prima di assemblare i parametri di una previsione.
"""
from __future__ import annotations

import hashlib
import pickle
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ..archivio import Configurazione, percorso_dati
from ..blocchi import COMPARTI, fte, scorte
from ..capacita import CATEGORIE_CAPITALE, G17_IO, leggi_g17, leggi_klems, utilizzo_per_industria
from ..capitale import a_prezzi_2012 as elementari_2012, aggrega_io, pannello, pannello_residenziale
from ..dati_modello import COLONNE_PUBBLICHE, SCALA, TIPI
from ..margini import leggi_concordanza, leggi_fa_dettaglio
from ..passo_c1 import MAKE, PREZZI, USE
from ..passo_c2 import CONCORDANZA, FA_RES
from ..passo_c4 import PEQ
from ..passo_c5 import FILE, REL
from ..passo_c6 import G17_CAP, G17_U, KLEMS
from ..passo_c7 import DEFL_T, FTE_T, STOCK_T
from ..phi import composizione_peq, leggi_peq, stima_phi
from ..sistema import SPECIALI, a_prezzi_2012 as sistema_reale, indici_prezzo, leggi_make, leggi_use

ANNO_MIN = 1997          # primo anno delle tavole Summary annuali
ANNO_MAX = 2019          # ultimo anno ammesso (esclude il Covid); nessun dato successivo entra nello storico
SIMULATION_YEAR_MIN = 2008
SIMULATION_YEAR_MAX = 2019
VERSIONE = "storico-1"


@dataclass
class Storico:
    anni: tuple
    industrie: list[str]
    prodotti: list[str]
    private: list[str]
    g17: list[str]
    B: dict = field(default_factory=dict)
    D: dict = field(default_factory=dict)
    x_speciali: dict = field(default_factory=dict)
    x: dict = field(default_factory=dict)
    q: dict = field(default_factory=dict)
    consumo: dict = field(default_factory=dict)
    pubblica: dict = field(default_factory=dict)
    esportazioni: dict = field(default_factory=dict)
    importazioni: dict = field(default_factory=dict)
    usi_esterni_fissi: dict = field(default_factory=dict)
    scorte_prodotti: dict = field(default_factory=dict)
    inv_prodotti: dict = field(default_factory=dict)      # (anno, tipo) → F02 reale per prodotto
    phi: dict = field(default_factory=dict)               # (anno, tipo) → prodotti × industrie
    phi_R: dict = field(default_factory=dict)
    pan: pd.DataFrame | None = None                       # capitale: industria, tipo, anno, K_inizio_2012, I_2012, D_2012, delta
    fte: pd.DataFrame | None = None                       # industria_io, anno, fte_migliaia (dal 1998)
    scorte: pd.DataFrame | None = None                    # riga, comparto, anno, stock_2012 (in miliardi)
    g17_u: pd.DataFrame | None = None                     # industria_io, anno, u, serie_g17, metodo_g17
    g17_cap: pd.DataFrame | None = None                   # serie × anno, capacità G.17
    klems: pd.DataFrame | None = None                     # remunerazione del capitale KLEMS, codici × anni
    conc: pd.DataFrame | None = None
    impronta: str = ""


def _impronta(cfg: Configurazione) -> str:
    h = hashlib.sha256(VERSIONE.encode())
    for rel, nome in (USE, MAKE, PREZZI, PEQ, FA_RES, G17_U, G17_CAP, KLEMS, FTE_T, STOCK_T, DEFL_T):
        h.update(str(percorso_dati(cfg, rel, nome)).encode())
    for k, v in FILE.items():
        h.update(str(percorso_dati(cfg, REL, v)).encode())
    return h.hexdigest()[:16]


def costruisci_storico(cfg: Configurazione, cache: Path | None = None, verbose: bool = True) -> Storico:
    """Costruisce (o legge dalla cache) lo storico completo 1997-2019."""
    imp = _impronta(cfg)
    if cache is not None:
        f = Path(cache) / f"storico_{ANNO_MIN}_{ANNO_MAX}_{imp}.pkl"
        if f.is_file():
            with open(f, "rb") as fh:
                return pickle.load(fh)
    anni = tuple(range(ANNO_MIN, ANNO_MAX + 1))
    tidy = pd.read_csv(percorso_dati(cfg, *PREZZI))
    usi, reali, prezzi = {}, {}, None
    for a in anni:
        u, m = leggi_use(percorso_dati(cfg, *USE), a), leggi_make(percorso_dati(cfg, *MAKE), a)
        prezzi = indici_prezzo(tidy, list(u.U.columns), anni) if prezzi is None else prezzi
        usi[a], reali[a] = u, sistema_reale(u, m, prezzi[a])
        if verbose:
            print(f"  sistema {a}", flush=True)
    industrie = list(usi[anni[0]].U.columns)
    prodotti = industrie[:]
    private = [j for j in industrie if not j.startswith("G")]
    S = Storico(anni, industrie, prodotti, private, [], impronta=imp)
    for a in anni:
        s = reali[a]
        S.B[a] = s.B.loc[prodotti] * 1.0
        S.D[a] = s.D[prodotti] * 1.0
        S.x_speciali[a] = (s.D[list(SPECIALI)] @ s.q[list(SPECIALI)]) / SCALA
        S.x[a], S.q[a] = s.x / SCALA, s.q.loc[prodotti] / SCALA
        F = s.F.loc[prodotti] / SCALA
        S.consumo[a] = F["F010"]
        S.pubblica[a] = F[list(COLONNE_PUBBLICHE)].sum(axis=1)
        S.esportazioni[a] = F["F040"]
        S.importazioni[a] = (-F["F050"]).clip(lower=0)
        S.usi_esterni_fissi[a] = F["F050"].clip(lower=0)
        S.scorte_prodotti[a] = F["F030"]
        for t, col in zip(("E", "S", "N", "R"), ("F02E", "F02S", "F02N", "F02R")):
            S.inv_prodotti[(a, t)] = F[col]
    # capitale 1996-2019 (1996: stock di fine anno = inizio 1997)
    anni_k = range(ANNO_MIN - 1, ANNO_MAX + 1)
    S.conc = leggi_concordanza(CONCORDANZA)
    ser = {k: leggi_fa_dettaglio(percorso_dati(cfg, REL, v), anni=anni_k) for k, v in FILE.items()}
    el = {mm: elementari_2012(ser[mm + "1"], ser[mm + "2"]) for mm in "KID"}
    pan = pd.concat([pannello(*(aggrega_io(el[mm], S.conc, mm) for mm in "KID")),
                     pannello_residenziale(percorso_dati(cfg, *FA_RES), anni_k)], ignore_index=True)
    S.pan = pan
    if verbose:
        print("  capitale", flush=True)
    # Φ per anno e tipo (prezzi 2012, per unità di investimento FA reale)
    fa_inv = ser["I1"]
    for a in anni:
        u = usi[a]
        cp = composizione_peq(leggi_peq(percorso_dati(cfg, *PEQ), a), u.F["F02E"], prodotti)
        for t in TIPI:
            X = stima_phi(t, a, u.F, fa_inv, S.conc, industrie, prodotti, cp if t == "E" else None).X
            Xr = X.div(prezzi[a].reindex(prodotti), axis=0) / SCALA
            I = pan[(pan["anno"] == a) & (pan["tipo"] == t)].set_index("industria_io")["I_2012"] / SCALA
            I = I.reindex(industrie).fillna(0.0)
            S.phi[(a, t)] = Xr.div(I.where(I > 0), axis=1).fillna(0.0)
        fr = S.inv_prodotti[(a, "R")].clip(lower=0)
        IR = float(pan[(pan["anno"] == a) & (pan["tipo"] == "R")]["I_2012"].sum() / SCALA)
        S.phi_R[a] = fr / IR if IR > 0 else fr * 0.0
        if verbose:
            print(f"  phi {a}", flush=True)
    # lavoro, scorte, G.17, KLEMS
    S.fte = fte(pd.read_csv(percorso_dati(cfg, *FTE_T)), range(1998, ANNO_MAX + 1))
    sc = scorte(pd.read_csv(percorso_dati(cfg, *STOCK_T)), pd.read_csv(percorso_dati(cfg, *DEFL_T)), anni_k)
    sc["stock_2012"] = sc["stock_2012"] / SCALA
    S.scorte = sc
    S.g17_u = utilizzo_per_industria(leggi_g17(percorso_dati(cfg, *G17_U), list(G17_IO), list(anni)))
    S.g17_cap = leggi_g17(percorso_dati(cfg, *G17_CAP), list(G17_IO), list(anni))
    S.g17 = sorted(set(S.g17_u["industria_io"]) & set(industrie))
    S.klems = leggi_klems(percorso_dati(cfg, *KLEMS), CATEGORIE_CAPITALE, list(anni))
    verifica_limiti(S)
    if cache is not None:
        Path(cache).mkdir(parents=True, exist_ok=True)
        with open(f, "wb") as fh:
            pickle.dump(S, fh)
    return S


def verifica_limiti(S: Storico) -> None:
    """Nessun anno fuori da [1996, 2019] in nessuna tabella dello storico (1996 solo come stock iniziale)."""
    assert max(S.anni) <= ANNO_MAX and min(S.anni) >= ANNO_MIN
    for nome in ("B", "D", "x", "consumo", "phi_R"):
        assert max(getattr(S, nome)) <= ANNO_MAX, nome
    assert max(k[0] for k in S.phi) <= ANNO_MAX
    for df, col in ((S.pan, "anno"), (S.fte, "anno"), (S.scorte, "anno"), (S.g17_u, "anno")):
        assert int(df[col].max()) <= ANNO_MAX and int(df[col].min()) >= ANNO_MIN - 1, col
    assert int(max(S.g17_cap.columns)) <= ANNO_MAX and int(max(S.klems.columns)) <= ANNO_MAX


def tronca(S: Storico, tau: int) -> Storico:
    """Copia dello storico con i soli dati osservabili all'origine τ (anni ≤ τ). Base della non anticipazione."""
    T = Storico(tuple(a for a in S.anni if a <= tau), S.industrie, S.prodotti, S.private, S.g17, impronta=S.impronta)
    for nome in ("B", "D", "x_speciali", "x", "q", "consumo", "pubblica", "esportazioni", "importazioni",
                 "usi_esterni_fissi", "scorte_prodotti", "phi_R"):
        setattr(T, nome, {a: v for a, v in getattr(S, nome).items() if a <= tau})
    T.inv_prodotti = {k: v for k, v in S.inv_prodotti.items() if k[0] <= tau}
    T.phi = {k: v for k, v in S.phi.items() if k[0] <= tau}
    T.pan = S.pan[S.pan["anno"] <= tau].copy()          # K_inizio dell'anno τ+1 = K_2012 (fine anno) di τ
    T.fte = S.fte[S.fte["anno"] <= tau].copy()
    T.scorte = S.scorte[S.scorte["anno"] <= tau].copy()
    T.g17_u = S.g17_u[S.g17_u["anno"] <= tau].copy()
    T.g17_cap = S.g17_cap[[c for c in S.g17_cap.columns if c <= tau]].copy()
    T.klems = S.klems[[c for c in S.klems.columns if c <= tau]].copy()
    T.conc = S.conc
    return T
