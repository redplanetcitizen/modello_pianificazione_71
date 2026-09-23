"""Passo C1: sistema prodotti-industrie 2012-2016 a 71 industrie / 73 prodotti.

Legge le tavole BEA Summary Make e Use (prima delle ridefinizioni, prezzi alla produzione),
misura le identità contabili, elenca valori negativi e celle "...", costruisce i prezzi
di prodotto e le tavole a prezzi 2012, e da queste i coefficienti B_t e le quote D_t.

Specifica v0.2.1, §2 e §5.1; ipotesi H1-H6. Nessun dato viene corretto in silenzio:
ogni scostamento è misurato e scritto negli output.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ANNI = (2012, 2013, 2014, 2015, 2016)
ANNO_BASE = 2012
SPECIALI = ("Used", "Other")
CODICE_PREZZO_SPECIALI = "PVT"  # indice del prodotto lordo delle industrie private (H24)

# Posizioni nel foglio annuale (verificate contro le etichette in _controlla_etichette).
USE_RIGA_CODICI, USE_RIGA_NOMI, USE_PRIMA_RIGA = 5, 6, 7


@dataclass
class TavolaUse:
    anno: int
    U: pd.DataFrame          # prodotti (73) x industrie (71)
    F: pd.DataFrame          # prodotti (73) x domanda finale (20)
    VA: pd.DataFrame         # 3 componenti x industrie (71)
    tot_intermedi_riga: pd.Series
    tot_finali: pd.Series
    q: pd.Series             # Total Commodity Output (73)
    tot_intermedi_col: pd.Series
    tot_va: pd.Series
    x: pd.Series             # Total Industry Output (71)
    puntini: pd.DataFrame    # celle "..." (riga, colonna)


@dataclass
class TavolaMake:
    anno: int
    V: pd.DataFrame          # industrie (71) x prodotti (73)
    x: pd.Series             # Total Industry Output
    q: pd.Series             # Total Commodity Output
    puntini: pd.DataFrame


def _numeri(blocco: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    testo = blocco.astype(str).apply(lambda s: s.str.strip())
    puntini = testo == "..."
    valori = blocco.mask(puntini, 0.0)
    valori = valori.apply(pd.to_numeric, errors="raise").fillna(0.0).astype(float)
    return valori, puntini


def _elenco_puntini(maschera: pd.DataFrame, tavola: str, anno: int) -> pd.DataFrame:
    r, c = np.nonzero(maschera.values)
    return pd.DataFrame({"tavola": tavola, "anno": anno,
                         "riga": maschera.index[r], "colonna": maschera.columns[c]})


def leggi_use(percorso, anno: int) -> TavolaUse:
    d = pd.read_excel(percorso, sheet_name=str(anno), header=None, dtype=object)
    codici_col = d.iloc[USE_RIGA_CODICI]
    nomi_col = d.iloc[USE_RIGA_NOMI]
    codici_riga = d.iloc[:, 0]
    nomi_riga = d.iloc[:, 1]

    col_ind = [i for i in range(2, 73)]
    i_tot_int = _posizione(nomi_col, "Total Intermediate")
    i_tot_fin = _posizione(nomi_col, "Total Final Uses (GDP)")
    i_q = _posizione(nomi_col, "Total Commodity Output")
    col_fin = list(range(i_tot_int + 1, i_tot_fin))
    r_prod = list(range(USE_PRIMA_RIGA, USE_PRIMA_RIGA + 73))
    r_tot_int = _posizione(nomi_riga, "Total Intermediate")
    r_va = [i for i in range(r_tot_int + 1, r_tot_int + 4)]
    r_tot_va = _posizione(nomi_riga, "Total Value Added")
    r_x = _posizione(nomi_riga, "Total Industry Output")

    ind = [str(c) for c in codici_col.iloc[col_ind]]
    fin = [str(c) for c in codici_col.iloc[col_fin]]
    prod = [str(c) for c in codici_riga.iloc[r_prod]]
    va = [str(c) for c in codici_riga.iloc[r_va]]
    _controlla_etichette(ind, fin, prod, va)

    corpo = d.iloc[r_prod + [r_tot_int] + r_va + [r_tot_va, r_x], col_ind + [i_tot_int] + col_fin + [i_tot_fin, i_q]]
    corpo.index = prod + ["TOT_INT"] + va + ["TOT_VA", "X"]
    corpo.columns = ind + ["TOT_INT"] + fin + ["TOT_FIN", "Q"]
    val, dots = _numeri(corpo)

    return TavolaUse(
        anno=anno,
        U=val.loc[prod, ind], F=val.loc[prod, fin], VA=val.loc[va, ind],
        tot_intermedi_riga=val.loc[prod, "TOT_INT"], tot_finali=val.loc[prod, "TOT_FIN"],
        q=val.loc[prod, "Q"], tot_intermedi_col=val.loc["TOT_INT", ind],
        tot_va=val.loc["TOT_VA", ind], x=val.loc["X", ind],
        puntini=_elenco_puntini(dots, "Use", anno),
    )


def leggi_make(percorso, anno: int) -> TavolaMake:
    d = pd.read_excel(percorso, sheet_name=str(anno), header=None, dtype=object)
    codici_col, nomi_col = d.iloc[USE_RIGA_CODICI], d.iloc[USE_RIGA_NOMI]
    nomi_riga = d.iloc[:, 1]
    col_prod = list(range(2, 2 + 73))
    i_x = _posizione(nomi_col, "Total Industry Output")
    r_ind = list(range(USE_PRIMA_RIGA, USE_PRIMA_RIGA + 71))
    r_q = _posizione(nomi_riga, "Total Commodity Output")
    prod = [str(c) for c in codici_col.iloc[col_prod]]
    ind = [str(c) for c in d.iloc[r_ind, 0]]
    if prod[-2:] != list(SPECIALI) or len(set(ind)) != 71:
        raise ValueError(f"Make {anno}: intestazioni inattese")
    corpo = d.iloc[r_ind + [r_q], col_prod + [i_x]]
    corpo.index = ind + ["Q"]
    corpo.columns = prod + ["X"]
    val, dots = _numeri(corpo)
    return TavolaMake(anno, V=val.loc[ind, prod], x=val.loc[ind, "X"], q=val.loc["Q", prod],
                      puntini=_elenco_puntini(dots, "Make", anno))


def _posizione(etichette: pd.Series, testo: str) -> int:
    trovate = [i for i, v in etichette.items() if isinstance(v, str) and v.strip() == testo]
    if len(trovate) != 1:
        raise ValueError(f"Etichetta '{testo}' trovata {len(trovate)} volte")
    return int(trovate[0])


def _controlla_etichette(ind, fin, prod, va) -> None:
    if len(ind) != 71 or len(set(ind)) != 71:
        raise ValueError("Use: attese 71 industrie")
    if len(prod) != 73 or prod[:71] != ind or tuple(prod[71:]) != SPECIALI:
        raise ValueError("Use: attesi 73 prodotti (71 + Used, Other) nello stesso ordine delle industrie")
    if len(fin) != 20 or fin[0] != "F010" or "F050" not in fin:
        raise ValueError("Use: attese 20 colonne di domanda finale")
    if va != ["V001", "V002", "V003"]:
        raise ValueError("Use: attese le righe V001, V002, V003")


# ---------------------------------------------------------------------------
# Identità contabili
# ---------------------------------------------------------------------------
def identita(use: TavolaUse, make: TavolaMake) -> pd.DataFrame:
    """Scarti delle identità pubblicate (milioni di dollari correnti)."""
    righe = []

    def aggiungi(nome, scarto: pd.Series, descrizione):
        a = scarto.abs()
        righe.append({"anno": use.anno, "identita": nome, "descrizione": descrizione,
                      "max_abs": float(a.max()), "somma_abs": float(a.sum()),
                      "voce_max": str(a.idxmax()), "n_voci": int(a.size)})

    aggiungi("use_riga_intermedi", use.U.sum(axis=1) - use.tot_intermedi_riga, "somma U per prodotto - Total Intermediate")
    aggiungi("use_riga_finali", use.F.sum(axis=1) - use.tot_finali, "somma F per prodotto - Total Final Uses")
    aggiungi("use_riga_bilancio", use.U.sum(axis=1) + use.F.sum(axis=1) - use.q,
             "intermedi + finali (importazioni con segno negativo) - Total Commodity Output")
    aggiungi("use_col_intermedi", use.U.sum(axis=0) - use.tot_intermedi_col, "somma U per industria - Total Intermediate")
    aggiungi("use_col_va", use.VA.sum(axis=0) - use.tot_va, "somma V001-V003 - Total Value Added")
    aggiungi("use_col_bilancio", use.U.sum(axis=0) + use.VA.sum(axis=0) - use.x,
             "intermedi + valore aggiunto - Total Industry Output")
    aggiungi("make_riga", make.V.sum(axis=1) - make.x, "somma V per industria - Total Industry Output (Make)")
    aggiungi("make_col", make.V.sum(axis=0) - make.q, "somma V per prodotto - Total Commodity Output (Make)")
    aggiungi("x_use_make", use.x - make.x, "produzione per industria: Use - Make")
    aggiungi("q_use_make", use.q - make.q, "produzione per prodotto: Use - Make")
    return pd.DataFrame(righe)


def negativi(use: TavolaUse, make: TavolaMake) -> pd.DataFrame:
    parti = []
    for nome, df in (("U", use.U), ("F", use.F), ("VA", use.VA), ("V", make.V)):
        r, c = np.nonzero(df.values < 0)
        parti.append(pd.DataFrame({"anno": use.anno, "blocco": nome, "riga": df.index[r],
                                   "colonna": df.columns[c], "valore": df.values[r, c]}))
    out = pd.concat(parti, ignore_index=True)
    out["categoria"] = out.apply(_categoria_negativo, axis=1)
    return out


def _categoria_negativo(r) -> str:
    if r.blocco == "F" and r.colonna == "F050":
        return "importazioni (segno negativo per convenzione)"
    if r.blocco == "F" and r.colonna == "F030":
        return "riduzione delle scorte"
    if r.blocco == "VA" and r.riga == "V002":
        return "sussidi superiori alle imposte"
    if r.riga in SPECIALI or r.colonna in SPECIALI:
        return "riga o colonna speciale (Used/Other)"
    return "da esaminare"


def importazioni_positive(use: TavolaUse) -> pd.DataFrame:
    f = use.F["F050"]
    pos = f[f > 0]
    return pd.DataFrame({"anno": use.anno, "prodotto": pos.index, "F050": pos.values})


# ---------------------------------------------------------------------------
# Prezzi e tavole a prezzi 2012
# ---------------------------------------------------------------------------
def indici_prezzo(tidy_go_prezzi: pd.DataFrame, industrie: list[str], anni=ANNI) -> pd.DataFrame:
    """Indici di prezzo della produzione lorda (GDP by Industry, tavola 18), ribasati al 2012 = 1.

    Righe: 71 prodotti ordinari (prezzo dell'industria con lo stesso codice, H5) + Used e Other
    (prezzo delle industrie private, H24). Colonne: anni.
    """
    t = tidy_go_prezzi
    t = t[(t["Frequency"] == "A") & (t["Year"].isin(list(anni)))]
    tab = t.pivot_table(index="Industry", columns="Year", values="value_num", aggfunc="first")
    codici = list(industrie) + [CODICE_PREZZO_SPECIALI]
    mancanti = [c for c in codici if c not in tab.index]
    if mancanti:
        raise ValueError(f"Indici di prezzo mancanti per: {mancanti}")
    p = tab.loc[codici, list(anni)]
    p = p.div(p[ANNO_BASE], axis=0)
    p.index = list(industrie) + [CODICE_PREZZO_SPECIALI]
    speciali = pd.DataFrame([p.loc[CODICE_PREZZO_SPECIALI]] * 2, index=list(SPECIALI))
    return pd.concat([p.loc[list(industrie)], speciali])


def prevalenza_prodotto(make: TavolaMake) -> pd.DataFrame:
    """Quota della produzione di ciascun prodotto ordinario realizzata dall'industria con lo stesso codice."""
    prod = [c for c in make.V.columns if c not in SPECIALI]
    quota = pd.Series({c: make.V.loc[c, c] / make.V[c].sum() if make.V[c].sum() else np.nan for c in prod})
    principale = make.V[prod].idxmax(axis=0)
    return pd.DataFrame({"anno": make.anno, "prodotto": prod, "quota_stesso_codice": quota.values,
                         "industria_principale": principale.values,
                         "principale_coincide": (principale.values == np.array(prod))})


@dataclass
class SistemaReale:
    anno: int
    U: pd.DataFrame
    F: pd.DataFrame
    V: pd.DataFrame
    x: pd.Series
    q: pd.Series
    B: pd.DataFrame
    D: pd.DataFrame


def a_prezzi_2012(use: TavolaUse, make: TavolaMake, p: pd.Series) -> SistemaReale:
    """Deflaziona per prodotto (H5) e costruisce gli aggregati per componente (H6).

    - U, F: ogni riga di prodotto divisa per il suo indice;
    - V: ogni colonna di prodotto divisa per il suo indice;
    - x reale = somma per riga di V reale (non x nominale / prezzo dell'industria);
    - q reale = somma per colonna di V reale;
    - B = U reale / x reale;  D = V reale / q reale (per colonna).
    """
    p = p.reindex(use.U.index)
    if p.isna().any():
        raise ValueError("Indici di prezzo mancanti per alcuni prodotti")
    U = use.U.div(p, axis=0)
    F = use.F.div(p, axis=0)
    V = make.V.div(p.reindex(make.V.columns), axis=1)
    x = V.sum(axis=1)
    q = V.sum(axis=0)
    B = U.div(x, axis=1)
    D = V.div(q.where(q != 0), axis=1).fillna(0.0)
    return SistemaReale(use.anno, U, F, V, x, q, B, D)


def controlli_reali(s: SistemaReale) -> dict:
    """Controlli sul sistema a prezzi 2012."""
    bil = s.U.sum(axis=1) + s.F.sum(axis=1) - s.q      # righe: come nel nominale, perché ogni riga ha un solo deflatore
    return {
        "anno": s.anno,
        "bilancio_prodotti_max_abs": float(bil.abs().max()),
        "x_eq_Dq_max_abs": float((s.D.values @ s.q.values - s.x.values).__abs__().max()),
        "D_colonne_somma_1_max_scarto": float((s.D.sum(axis=0)[s.q != 0] - 1).abs().max()),
        "B_min": float(s.B.values.min()),
        "B_somma_colonne_max": float(s.B.sum(axis=0).max()),
        "B_negativi": int((s.B.values < 0).sum()),
    }
