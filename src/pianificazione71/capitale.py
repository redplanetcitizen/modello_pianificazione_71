"""Passo C5: stock di capitale, investimento e ammortamento per industria I/O e tipo, a prezzi 2012.

Fonti: Fixed Assets dettagliati per industria e tipo di bene (costo corrente e costo fisso).
Per ogni serie elementare (industria FA × bene) il valore a prezzi 2012 è
    X_2012(t) = X_costo_fisso(t) · X_corrente(2012) / X_costo_fisso(2012),
cioè la quantità della serie valutata al prezzo del bene nel 2012. Queste serie elementari sono
additive: gli aggregati per tipo e industria I/O si ottengono sommandole (H6), mai sommando
serie concatenate. Il valore di ogni aggregato nel 2012 coincide con quello corrente.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TOTALI = ("EQ00", "ST00", "IP00")


def tipo_bene(codice: str) -> str | None:
    if codice in TOTALI:
        return None
    if codice.startswith(("ENS", "RD", "AE")):
        return "N"
    if codice.startswith("E"):
        return "E"
    if codice.startswith("S"):
        return "S"
    return None


def a_prezzi_2012(corrente: pd.DataFrame, fisso: pd.DataFrame, base: int = 2012) -> pd.DataFrame:
    """Serie elementari (industria_fa, bene, anno, valore) a prezzi dell'anno base.

    Se la serie è nulla a costo fisso nell'anno base ma non negli altri anni, si usa il rapporto
    corrente/fisso del primo anno disponibile (caso raro, contato in `prezzo_non_base`).
    """
    chiavi = ["industria_fa", "bene", "anno"]
    m = corrente.merge(fisso, on=chiavi, suffixes=("_corr", "_fisso"))
    m["tipo"] = m["bene"].map(tipo_bene)
    m = m[m["tipo"].notna()]
    rapp = m[m["anno"] == base].set_index(["industria_fa", "bene"])
    rapp = (rapp["valore_corr"] / rapp["valore_fisso"]).replace([np.inf, -np.inf], np.nan)
    m = m.join(rapp.rename("prezzo_base"), on=["industria_fa", "bene"])
    alt = (m["valore_corr"] / m["valore_fisso"]).replace([np.inf, -np.inf], np.nan)
    primo = alt.groupby([m["industria_fa"], m["bene"]]).transform("first")
    m["prezzo_non_base"] = m["prezzo_base"].isna() & (m["valore_fisso"] != 0)
    prezzo = m["prezzo_base"].fillna(primo).fillna(0.0)
    m["valore_2012"] = m["valore_fisso"] * prezzo
    return m[chiavi + ["tipo", "valore_corr", "valore_2012", "prezzo_non_base"]]


def aggrega_io(elem: pd.DataFrame, conc: pd.DataFrame, nome: str) -> pd.DataFrame:
    e = elem.merge(conc[["industria_fa", "industria_io"]], on="industria_fa")
    g = e.groupby(["industria_io", "tipo", "anno"], as_index=False)[["valore_corr", "valore_2012"]].sum()
    return g.rename(columns={"valore_corr": f"{nome}_corrente", "valore_2012": f"{nome}_2012"})


def pannello(K: pd.DataFrame, I: pd.DataFrame, D: pd.DataFrame) -> pd.DataFrame:
    """Pannello industria × tipo × anno con K fine anno, I, D a prezzi 2012 e le grandezze derivate.

    K_inizio(t) = K_fine(t−1). Identità misurata: K_fine(t) − K_inizio(t) − I(t) + D(t) = altre variazioni.
    δ del modello (H11, H12): D(t) / K_inizio(t).
    """
    p = K.merge(I, on=["industria_io", "tipo", "anno"], how="outer").merge(D, on=["industria_io", "tipo", "anno"], how="outer")
    p = p.fillna(0.0).sort_values(["industria_io", "tipo", "anno"])
    p["K_inizio_2012"] = p.groupby(["industria_io", "tipo"])["K_2012"].shift(1)
    p["altre_variazioni_2012"] = p["K_2012"] - p["K_inizio_2012"] - p["I_2012"] + p["D_2012"]
    p["delta"] = p["D_2012"] / p["K_inizio_2012"].where(p["K_inizio_2012"] > 0)
    p["altre_variazioni_rel"] = p["altre_variazioni_2012"] / p["K_inizio_2012"].where(p["K_inizio_2012"] > 0)
    return p


def sintesi_identita(p: pd.DataFrame) -> pd.DataFrame:
    q = p.dropna(subset=["K_inizio_2012"])
    g = q.groupby(["tipo", "anno"]).agg(K_inizio=("K_inizio_2012", "sum"), I=("I_2012", "sum"), D=("D_2012", "sum"),
                                        K_fine=("K_2012", "sum"), altre=("altre_variazioni_2012", "sum"),
                                        altre_abs=("altre_variazioni_2012", lambda s: s.abs().sum()))
    g["altre_rel_aggregato"] = g["altre"] / g["K_inizio"]
    g["altre_abs_rel"] = g["altre_abs"] / g["K_inizio"]
    g["delta_aggregato"] = g["D"] / g["K_inizio"]
    return g.reset_index()


# ---------------------------------------------------------------------------
# Residenziale (industria I/O HS)
# ---------------------------------------------------------------------------
FOGLI_RES = {
    "K": ("Net Stock (Current-Cost)", "Net Stock (Fixed-Cost) "),
    "D": ("Depreciation (Current-Cost)", "Depreciation (Fixed-Cost)"),
    "I": ("Investment ", "Investment (Fixed-Cost)"),
}


def leggi_residenziale_componenti(percorso, foglio: str, anni) -> pd.DataFrame:
    """Righe elementari (codice bene) del file detailresidential; la chiave è il codice senza il prefisso di misura."""
    import openpyxl

    wb = openpyxl.load_workbook(percorso, read_only=True, data_only=True)
    righe = list(wb[foglio].iter_rows(values_only=True))
    wb.close()
    intest = next(r for r in righe if r and r[0] == "Asset Codes")
    col = {str(v): i for i, v in enumerate(intest) if v is not None}
    out = []
    for r in righe:
        if r and isinstance(r[0], str) and r[0].strip()[:1].lower() in "kmi" and len(r[0].strip()) > 6:
            codice = r[0].strip()
            for a in anni:
                v = r[col[str(a)]]
                out.append({"industria_fa": "RES", "bene": codice[3:], "anno": a, "valore": float(v or 0.0)})
    return pd.DataFrame(out)


def pannello_residenziale(percorso, anni) -> pd.DataFrame:
    parti = {}
    for misura, (corr, fisso) in FOGLI_RES.items():
        c = leggi_residenziale_componenti(percorso, corr, anni)
        f = leggi_residenziale_componenti(percorso, fisso, anni)
        m = c.merge(f, on=["industria_fa", "bene", "anno"], suffixes=("_corr", "_fisso"))
        base = m[m["anno"] == 2012].set_index("bene")
        prezzo = (base["valore_corr"] / base["valore_fisso"]).replace([np.inf, -np.inf], np.nan)
        m = m.join(prezzo.rename("p"), on="bene")
        m["p"] = m["p"].fillna((m["valore_corr"] / m["valore_fisso"]).replace([np.inf, -np.inf], np.nan)).fillna(0.0)
        m["v2012"] = m["valore_fisso"] * m["p"]
        g = m.groupby("anno").agg(corr=("valore_corr", "sum"), r2012=("v2012", "sum"))
        parti[misura] = g.rename(columns={"corr": f"{misura}_corrente", "r2012": f"{misura}_2012"})
    p = pd.concat(parti.values(), axis=1).reset_index()
    p.insert(0, "tipo", "R")
    p.insert(0, "industria_io", "HS")
    p["K_inizio_2012"] = p["K_2012"].shift(1)
    p["altre_variazioni_2012"] = p["K_2012"] - p["K_inizio_2012"] - p["I_2012"] + p["D_2012"]
    p["delta"] = p["D_2012"] / p["K_inizio_2012"]
    p["altre_variazioni_rel"] = p["altre_variazioni_2012"] / p["K_inizio_2012"]
    return p
