"""Passo C4: composizione per prodotto dell'investimento di ciascuna industria (matrice Φ).

Per anno e tipo di bene a ∈ {E, S, N} si stima X_a (prodotti ordinari × industrie I/O),
i cui totali di riga sono la colonna F02a della Use e i cui totali di colonna sono
l'investimento delle industrie nei Fixed Assets, riscalato al totale della Use (decisione D1).

La struttura iniziale (H19) viene dal dettaglio dei Fixed Assets per tipo di bene:
- E: tipi di attrezzatura FA → categorie NIPA del raccordo PEQ → prodotti I/O (margini compresi);
- S: esplorazione mineraria → 213; tutte le altre strutture → 23;
- N: R&S → 5412OP; software pacchettizzato → 511; software su commessa e in proprio → 5415;
     film e musica → 512; programmi televisivi → 512; libri → 511; altri originali → 711AS.
A questa si somma una quota λ della composizione comune della colonna F02 (supporto su tutte le righe).
Il bilanciamento è GRAS (Junius e Oosterhaven 2003), che coincide con il RAS in assenza di negativi.

Il risultato è una stima condizionata alla struttura iniziale: il bilanciamento non identifica
le celle, ripartisce totali coerenti.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import openpyxl
import pandas as pd

LAMBDA = 0.05  # peso della composizione comune nella struttura iniziale (sensibilità prevista)

MAPPA_E = {  # tipo di attrezzatura FA → riga NIPA del raccordo PEQ
    **{c: 4 for c in ("EP1A", "EP1B", "EP1C", "EP1D", "EP1E", "EP1F", "EP1G", "EP1H")},
    "EP20": 5, "EP34": 6, "EP35": 6, "EP36": 7, "EP31": 8, "EP12": 9,
    "EI11": 11, "EI12": 11, "EI21": 12, "EI22": 12, "EI30": 13, "EI40": 14, "EI50": 15, "EI60": 16,
    "ET11": 19, "ET12": 20, "ET20": 21, "ET30": 22, "ET40": 23, "ET50": 24,
    "EO11": 26, "EO12": 26, "EO21": 27, "EO30": 27, "EO22": 28, "EO40": 28, "EO50": 29, "EO60": 30,
    "EO71": 31, "EO72": 31, "EO80": 32,
}
RIGHE_PEQ_ESCLUSE = (33, 34)  # vendita di rottami (riga Used) e attrezzature residenziali (F02R)
MAPPA_S = {"SM01": "213", "SM02": "213"}  # tutte le altre strutture → "23"
MAPPA_N = {
    "ENS1": "511", "ENS2": "5415", "ENS3": "5415",
    "AE10": "512", "AE20": "512", "AE30": "511", "AE40": "512", "AE50": "711AS",
}  # R&S (RD**) → "5412OP"
TOTALI_FA = {"E": "EQ00", "S": "ST00", "N": "IP00"}
COLONNE_USE = {"E": "F02E", "S": "F02S", "N": "F02N"}
TRASPORTI = ("481", "482", "483", "484", "485", "486", "487OS", "493")
DETTAGLIO = ("441", "445", "452", "4A0")


# ---------------------------------------------------------------------------
# GRAS
# ---------------------------------------------------------------------------
@dataclass
class EsitoGras:
    X: np.ndarray
    iterazioni: int
    scarto_righe: float
    scarto_colonne: float
    convergenza: bool


def gras(A0: np.ndarray, u: np.ndarray, v: np.ndarray, tol: float = 1e-9, max_iter: int = 20000) -> EsitoGras:
    """Bilanciamento GRAS: X = diag(r) P diag(s) − diag(1/r) N diag(1/s), con A0 = P − N.

    u: totali di riga, v: totali di colonna (stessa somma). Righe o colonne con totale nullo
    e struttura nulla restano nulle.
    """
    A0 = np.asarray(A0, float)
    P, N = np.where(A0 > 0, A0, 0.0), np.where(A0 < 0, -A0, 0.0)
    if abs(u.sum() - v.sum()) > 1e-6 * max(1.0, abs(u.sum())):
        raise ValueError(f"GRAS: totali incoerenti ({u.sum():.3f} contro {v.sum():.3f})")
    for nome, marg, asse in (("riga", u, 1), ("colonna", v, 0)):
        vuote = (np.abs(A0).sum(axis=asse) == 0) & (np.abs(marg) > 0)
        if vuote.any():
            raise ValueError(f"GRAS: {int(vuote.sum())} {nome} con totale non nullo e struttura iniziale nulla")
    r, s = np.ones(A0.shape[0]), np.ones(A0.shape[1])

    def moltiplicatori(p, n, t):
        out = np.ones_like(t)
        pos = p > 0
        out[pos] = (t[pos] + np.sqrt(t[pos] ** 2 + 4 * p[pos] * n[pos])) / (2 * p[pos])
        solo_neg = (~pos) & (n > 0)
        out[solo_neg] = -n[solo_neg] / t[solo_neg]
        return out

    for it in range(1, max_iter + 1):
        r = moltiplicatori(P @ s, N @ (1 / s), u)
        s = moltiplicatori(P.T @ r, N.T @ (1 / r), v)
        X = r[:, None] * P * s[None, :] - (1 / r)[:, None] * N * (1 / s)[None, :]
        er, ec = np.abs(X.sum(axis=1) - u).max(), np.abs(X.sum(axis=0) - v).max()
        if max(er, ec) <= tol * max(1.0, np.abs(u).max()):
            return EsitoGras(X, it, float(er), float(ec), True)
    return EsitoGras(X, max_iter, float(er), float(ec), False)


# ---------------------------------------------------------------------------
# Raccordo PEQ
# ---------------------------------------------------------------------------
def leggi_peq(percorso, anno: int) -> pd.DataFrame:
    wb = openpyxl.load_workbook(percorso, read_only=True, data_only=True)
    righe = list(wb[str(anno)].iter_rows(values_only=True))
    wb.close()
    i = next(k for k, r in enumerate(righe) if r and r[0] == "NIPA Line")
    dati = [r[:9] for r in righe[i + 1:] if r and isinstance(r[0], (int, float))]
    df = pd.DataFrame(dati, columns=["riga", "categoria", "prodotto", "descrizione", "produttore",
                                     "trasporto", "ingrosso", "dettaglio", "acquirente"])
    df["riga"] = df["riga"].astype(int)
    df["prodotto"] = df["prodotto"].astype(str).str.strip()
    for c in ("produttore", "trasporto", "ingrosso", "dettaglio", "acquirente"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


def composizione_peq(peq: pd.DataFrame, f02e: pd.Series, prodotti: list[str]) -> pd.DataFrame:
    """Categorie PEQ × prodotti ordinari: composizione ai prezzi alla produzione, margini compresi.

    Trasporto e dettaglio sono ripartiti sui prodotti di trasporto e del commercio al dettaglio
    in proporzione alla loro presenza nella colonna F02E della Use; l'ingrosso va a 42.
    Le righe Used e le categorie escluse non entrano.
    """
    p = peq[~peq["riga"].isin(RIGHE_PEQ_ESCLUSE) & (peq["prodotto"] != "Used")]
    base = p.pivot_table(index="riga", columns="prodotto", values="produttore", aggfunc="sum").fillna(0.0)
    base = base.reindex(columns=prodotti, fill_value=0.0)
    margini = p.groupby("riga")[["trasporto", "ingrosso", "dettaglio"]].sum()

    def quote(codici):
        w = f02e.reindex(list(codici)).clip(lower=0).fillna(0.0)
        return w / w.sum() if w.sum() > 0 else pd.Series(1 / len(codici), index=list(codici))

    for codice, q in quote(TRASPORTI).items():
        base[codice] += margini["trasporto"] * q
    base["42"] += margini["ingrosso"]
    for codice, q in quote(DETTAGLIO).items():
        base[codice] += margini["dettaglio"] * q
    tot = base.sum(axis=1)
    return base.div(tot.where(tot != 0), axis=0).fillna(0.0)


# ---------------------------------------------------------------------------
# Strutture iniziali
# ---------------------------------------------------------------------------
def struttura_iniziale(tipo: str, fa_anno: pd.DataFrame, conc: pd.DataFrame, industrie: list[str],
                       prodotti: list[str], comp_peq: pd.DataFrame | None, comune: pd.Series,
                       lam: float = LAMBDA) -> pd.DataFrame:
    """Prodotti × industrie I/O, in dollari FA (prima della scala). fa_anno: righe FA di un anno."""
    f = fa_anno.merge(conc[["industria_fa", "industria_io"]], on="industria_fa")
    totale = TOTALI_FA[tipo]
    A = pd.DataFrame(0.0, index=prodotti, columns=industrie)
    if tipo == "E":
        fe = f[f["bene"].isin(MAPPA_E)]
        fe = fe.assign(riga=fe["bene"].map(MAPPA_E))
        per_riga = fe.groupby(["industria_io", "riga"])["valore"].sum().unstack(fill_value=0.0)
        per_riga = per_riga.reindex(columns=comp_peq.index, fill_value=0.0)
        A.loc[:, per_riga.index] = (comp_peq.T.reindex(prodotti).fillna(0.0).values @ per_riga.T.values)
    else:
        if tipo == "N":
            comp = f[f["bene"].str.match(r"^(ENS|RD|AE)")]
            dest = comp["bene"].map(MAPPA_N).fillna("5412OP")
        else:
            comp = f[f["bene"].str.match(r"^S(?!T00)")]
            dest = comp["bene"].map(MAPPA_S).fillna("23")
        g = comp.assign(prodotto=dest).groupby(["prodotto", "industria_io"])["valore"].sum().unstack(fill_value=0.0)
        g = g.reindex(index=prodotti, columns=industrie, fill_value=0.0)
        A += g
    # quota comune: garantisce che ogni riga con domanda abbia supporto in ogni industria che investe
    tot_ind = f[f["bene"] == totale].groupby("industria_io")["valore"].sum().reindex(industrie, fill_value=0.0)
    A = (1 - lam) * A.div(A.sum(axis=0).where(A.sum(axis=0) != 0), axis=1).fillna(0.0).mul(tot_ind, axis=1) \
        + lam * np.outer(comune.reindex(prodotti).fillna(0.0), tot_ind.values)
    return A


@dataclass
class StimaPhi:
    anno: int
    tipo: str
    X: pd.DataFrame           # flussi stimati, dollari correnti
    A0: pd.DataFrame          # struttura iniziale riscalata
    esito: EsitoGras
    scala_colonne: float      # totale Use / totale FA


def stima_phi(tipo: str, anno: int, F: pd.DataFrame, fa: pd.DataFrame, conc: pd.DataFrame,
              industrie: list[str], prodotti: list[str], comp_peq: pd.DataFrame | None,
              lam: float = LAMBDA) -> StimaPhi:
    riga = F[COLONNE_USE[tipo]].reindex(prodotti).fillna(0.0)
    comune = riga.clip(lower=0) / riga.clip(lower=0).sum()
    fa_anno = fa[fa["anno"] == anno]
    A = struttura_iniziale(tipo, fa_anno, conc, industrie, prodotti, comp_peq, comune, lam)
    col_fa = A.sum(axis=0)
    scala = riga.sum() / col_fa.sum()
    A0 = A * (riga.sum() / A.values.sum())
    esito = gras(A0.values, riga.values, (col_fa * scala).values)
    X = pd.DataFrame(esito.X, index=prodotti, columns=industrie)
    return StimaPhi(anno, tipo, X, A0, esito, float(scala))


def composizione(X: pd.DataFrame) -> pd.DataFrame:
    tot = X.sum(axis=0)
    return X.div(tot.where(tot != 0), axis=1).fillna(0.0)


def diagnostica(st: StimaPhi) -> dict:
    X, A0 = st.X.values, st.A0.values
    return {
        "anno": st.anno, "tipo": st.tipo, "iterazioni": st.esito.iterazioni, "convergenza": st.esito.convergenza,
        "scarto_righe": st.esito.scarto_righe, "scarto_colonne": st.esito.scarto_colonne,
        "scala_colonne_use_su_fa": st.scala_colonne,
        "spostamento_relativo_da_struttura_iniziale": float(np.abs(X - A0).sum() / np.abs(A0).sum()),
        "celle_negative": int((X < 0).sum()), "industrie_con_investimento": int((X.sum(axis=0) > 0).sum()),
    }
