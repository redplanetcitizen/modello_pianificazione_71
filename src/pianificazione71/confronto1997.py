"""Passo C4b: confronto diagnostico di Φ (2012) con la tavola dei flussi di capitale 1997 (attrezzature e strutture).

La tavola 1997 è una stima di ricerca BEA (180 prodotti × 123 industrie, prezzi alla produzione, dollari 1997),
qui con le rettifiche pubblicate nel 2018 per 5 industrie. Non entra nella stima di Φ: serve a verificare se la
composizione stimata per industria somiglia a una fonte indipendente più di quanto le somigli una composizione
comune a tutte le industrie (λ = 1).

Esclusioni, per rendere comparabili le due fonti: software (511200, 541511, 541512: nel 2012 è proprietà
intellettuale, tipo N), costruzioni residenziali (23351x: nel 2012 tipo R), importazioni non comparabili (S00300).
Il commercio al dettaglio è aggregato in un gruppo (RET) perché la tavola 1997 non lo distingue.
Indice di dissomiglianza: ½ Σ_c |a_c − b_c| (0 = composizioni identiche, 1 = disgiunte).
"""
from __future__ import annotations

import pandas as pd

ESCLUSI = {"511200", "541511", "541512", "S00300"}
RETAIL = {"441", "445", "452", "4A0"}


def prodotto_1997_a_io(codice: str) -> str | None:
    c = codice.strip().rstrip("*")
    if c in ESCLUSI or c.startswith("23351"):
        return None
    tabella = {"420000": "42", "4A0000": "RET", "481000": "481", "482000": "482", "483000": "483", "484000": "484",
               "513300": "513", "531210": "ORE", "541330": "5412OP"}
    if c in tabella:
        return tabella[c]
    if c.startswith("233"):
        return "23"
    if c.startswith("2122"):
        return "212"
    if c.startswith("2131"):
        return "213"
    if c.startswith(("3361", "3362", "3363")):
        return "3361MV"
    if c.startswith(("3364", "3365", "3366", "3369")):
        return "3364OT"
    if c.startswith(("313", "314")):
        return "313TT"
    tre = c[:3]
    if tre in {"321", "325", "326", "332", "333", "334", "335", "337", "339"}:
        return tre
    raise ValueError(f"Prodotto 1997 senza corrispondenza: {codice}")


INDUSTRIE_1997 = {
    "1110": "111CA", "1120": "111CA", "1130": "113FF", "1140": "113FF", "1150": "113FF", "2110": "211",
    "2121": "212", "2122": "212", "2123": "212", "2130": "213", "2211": "22", "2212": "22", "2213": "22",
    "2300": "23", "3110": "311FT", "3121": "311FT", "3122": "311FT", "3130": "313TT", "3140": "313TT",
    "3150": "315AL", "3160": "315AL", "3210": "321", "3221": "322", "3222": "322", "3230": "323", "3240": "324",
    "3251": "325", "3252": "325", "3253": "325", "3254": "325", "3255": "325", "3256": "325", "3259": "325",
    "3260": "326", "3270": "327", "331A": "331", "331B": "331", "3315": "331", "3321": "332", "3322": "332",
    "3323": "332", "3324": "332", "332A": "332", "332B": "332", "3331": "333", "3332": "333", "3333": "333",
    "3334": "333", "3335": "333", "3336": "333", "3339": "333", "3341": "334", "334A": "334", "3344": "334",
    "3345": "334", "3346": "334", "3351": "335", "3352": "335", "3353": "335", "3359": "335", "3361": "3361MV",
    "336A": "3361MV", "3364": "3364OT", "336B": "3364OT", "3370": "337", "3391": "339", "3399": "339",
    "4200": "42", "4A00": "RET", "4810": "481", "4820": "482", "4830": "483", "4840": "484", "4850": "485",
    "4860": "486", "48A0": "487OS", "4920": "487OS", "4930": "493", "5111": "511", "5112": "511", "5120": "512",
    "5131": "513", "5132": "513", "5133": "513", "5141": "514", "5142": "514", "52A0": "521CI", "5230": "523",
    "5240": "524", "5250": "525", "5310": "ORE", "5321": "532RL", "532A": "532RL", "5324": "532RL",
    "5330": "532RL", "5411": "5411", "5415": "5415", "5412": "5412OP", "5413": "5412OP", "5414": "5412OP",
    "5416": "5412OP", "5417": "5412OP", "5418": "5412OP", "5419": "5412OP", "5500": "55", "5613": "561",
    "5615": "561", "561A": "561", "5620": "562", "6100": "61", "6210": "621", "6220": "622", "6230": "623",
    "6240": "624", "71A0": "711AS", "7130": "713", "7210": "721", "7220": "722", "8111": "81", "811A": "81",
    "8120": "81", "813A": "81", "813B": "81",
}


def leggi_cft1997(percorso_flow, percorso_rettifiche) -> pd.DataFrame:
    """Tavola 180 × 123 (milioni di dollari 1997) con le colonne rettificate nel 2018 sostituite."""
    x = pd.read_excel(percorso_flow, sheet_name="180x123Combined", header=None, dtype=object)
    codici_ind = [str(v).strip() for v in x.iloc[3, 3:126]]
    righe = x.iloc[4:184]
    prodotti = [str(v).strip() for v in righe[1]]
    t = pd.DataFrame(righe.iloc[:, 3:126].values, index=prodotti, columns=codici_ind).apply(pd.to_numeric).fillna(0.0)
    r = pd.read_excel(percorso_rettifiche, sheet_name="Changes to 180x123Combined", header=None, dtype=object)
    ind_r = [str(v).strip() for v in r.iloc[2, 3:8]]
    corpo = r.iloc[3:].dropna(subset=[1])
    nuove = pd.DataFrame(corpo.iloc[:, 3:8].values, index=[str(v).strip() for v in corpo[1]], columns=ind_r)
    nuove = nuove.apply(pd.to_numeric, errors="coerce").fillna(0.0)
    for j in ind_r:
        t[j] = nuove[j].reindex(t.index).fillna(0.0)
    return t


def composizioni_1997(t: pd.DataFrame) -> pd.DataFrame:
    """Gruppi di prodotto × industrie I/O (quote per colonna)."""
    gruppi = pd.Series({c: prodotto_1997_a_io(c) for c in t.index})
    t = t.loc[gruppi.notna()]
    g = t.groupby(gruppi.dropna()).sum()
    g = g.T.groupby(pd.Series(INDUSTRIE_1997)).sum().T
    return g.div(g.sum(axis=0), axis=1)


def composizioni_2012(X_E: pd.DataFrame, X_S: pd.DataFrame) -> pd.DataFrame:
    X = X_E + X_S
    X = X.rename(index=lambda c: "RET" if c in RETAIL else c).groupby(level=0).sum()
    X = X.rename(columns=lambda c: "RET" if c in RETAIL else c).T.groupby(level=0).sum().T
    return X


def dissomiglianza(a: pd.DataFrame, b: pd.DataFrame) -> pd.Series:
    righe = a.index.union(b.index)
    a, b = a.reindex(righe, fill_value=0.0), b.reindex(righe, fill_value=0.0)
    return 0.5 * (a - b).abs().sum(axis=0)


def confronto(t97: pd.DataFrame, X_E: pd.DataFrame, X_S: pd.DataFrame) -> pd.DataFrame:
    c97 = composizioni_1997(t97)
    X = composizioni_2012(X_E, X_S)
    peso = X.sum(axis=0)
    comuni = [j for j in c97.columns if j in X.columns and peso.get(j, 0) > 0]
    stima = X[comuni].div(peso[comuni], axis=1)
    comune = X.sum(axis=1) / X.values.sum()
    base = pd.DataFrame({j: comune for j in comuni})
    out = pd.DataFrame({"dissomiglianza_phi_1997": dissomiglianza(stima, c97[comuni]),
                        "dissomiglianza_comune_1997": dissomiglianza(base, c97[comuni]),
                        "investimento_2012": peso[comuni]})
    out["phi_piu_vicina"] = out["dissomiglianza_phi_1997"] < out["dissomiglianza_comune_1997"]
    return out.rename_axis("industria_io").reset_index()
