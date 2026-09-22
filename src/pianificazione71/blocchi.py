"""Passo C7: lavoro, scorte ed estero a 71 industrie (specifica §4.5-§4.7, §5.4-§5.5).

Lavoro (decisione D3): occupati equivalenti a tempo pieno (FTE, NIPA 6.5D, migliaia) come unità
fisica del lavoro; ℓ_{j,t} = FTE_{j,t} / x_{j,t} (migliaia di FTE per milione di dollari 2012).
Controllo: crescita FTE contro indice delle ore KLEMS per gruppo.

Scorte: stock di fine anno (IV trimestre, NIPA 5.8.5B) per 11 comparti, a prezzi del IV trimestre 2012
con i deflatori 5.8.9B; σ_z = S_z / Σ_{j∈z} x_j nel 2012 (H13); corrispondenza comparti → industrie (H22);
composizione per prodotto comune = parte positiva della colonna F030 (H21, primo test).

Estero: esportazioni e importazioni per prodotto a prezzi 2012 dalla Use; quota d'importazione
μ_c = m_c / (uso interno_c); voci positive di F050 (margini su importazioni) come usi esterni fissi.
"""
from __future__ import annotations

import pandas as pd

# NIPA 6.5D, numero di riga → industria I/O (H14a: nessun FTE per HS; immobiliare tutto su ORE;
# federale generale: civili → GFGN, militari → GFGD)
FTE_RIGHE = {
    5: "111CA", 6: "113FF", 8: "211", 9: "212", 10: "213", 11: "22", 12: "23", 15: "321", 16: "327", 17: "331",
    18: "332", 19: "333", 20: "334", 21: "335", 22: "3361MV", 23: "3364OT", 24: "337", 25: "339", 27: "311FT",
    28: "313TT", 29: "315AL", 30: "322", 31: "323", 32: "324", 33: "325", 34: "326", 35: "42", 39: "441",
    40: "445", 41: "452", 42: "4A0", 44: "481", 45: "482", 46: "483", 47: "484", 48: "485", 49: "486",
    50: "487OS", 51: "493", 53: "511", 54: "512", 55: "513", 56: "514", 58: "521CI", 59: "523", 60: "524",
    61: "525", 63: "ORE", 64: "532RL", 66: "5411", 67: "5415", 68: "5412OP", 69: "55", 71: "561", 72: "562",
    73: "61", 75: "621", 76: "622", 77: "623", 78: "624", 80: "711AS", 81: "713", 83: "721", 84: "722",
    85: "81", 89: "GFGN", 90: "GFGD", 91: "GFE", 93: "GSLG", 96: "GSLE",
}

# NIPA 5.8.5B / 5.8.9B, righe dei comparti → industrie I/O (H22)
DUREVOLI = ["321", "327", "331", "332", "333", "334", "335", "3361MV", "3364OT", "337", "339"]
NON_DUREVOLI = ["311FT", "313TT", "315AL", "322", "323", "324", "325", "326"]
COMPARTI = {
    2: ("Agricoltura", ["111CA"]),
    3: ("Estrattivo, utility, costruzioni", ["211", "212", "213", "22", "23"]),
    5: ("Manifattura durevole", DUREVOLI),
    6: ("Manifattura non durevole", NON_DUREVOLI),
    8: ("Ingrosso durevole", ["42"]),
    9: ("Ingrosso non durevole", ["42"]),
    11: ("Concessionari auto", ["441"]),
    12: ("Alimentari al dettaglio", ["445"]),
    13: ("Grandi magazzini", ["452"]),
    14: ("Altro dettaglio", ["4A0"]),
    15: ("Altre industrie", None),  # tutte le industrie private non elencate sopra
}


def fte(tidy: pd.DataFrame, anni) -> pd.DataFrame:
    t = tidy[tidy["TimePeriod"].astype(int).isin(list(anni)) & tidy["LineNumber"].isin(FTE_RIGHE)]
    t = t.assign(industria_io=t["LineNumber"].map(FTE_RIGHE), anno=t["TimePeriod"].astype(int))
    return t[["industria_io", "anno", "value_num"]].rename(columns={"value_num": "fte_migliaia"})


def coefficienti_lavoro(f: pd.DataFrame, x_reale: pd.DataFrame, industrie: list[str]) -> pd.DataFrame:
    m = x_reale.merge(f, on=["industria_io", "anno"], how="left").fillna({"fte_migliaia": 0.0})
    m = m[m["industria_io"].isin(industrie)]
    m["ell"] = m["fte_migliaia"] / m["x_reale"]
    return m


def industrie_comparto(riga: int, private: list[str]) -> list[str]:
    nome, inds = COMPARTI[riga]
    if inds is not None:
        return inds
    elencate = {j for r, (_, i) in COMPARTI.items() if i for j in i}
    return [j for j in private if j not in elencate]


def scorte(stock: pd.DataFrame, deflatori: pd.DataFrame, anni) -> pd.DataFrame:
    """Stock di fine anno per comparto, correnti e a prezzi del IV trimestre 2012 (deflatore del comparto)."""
    righe = []
    for riga, (nome, _) in COMPARTI.items():
        s = stock[stock["LineNumber"] == riga].set_index("TimePeriod")["value_num"]
        p = deflatori[deflatori["LineNumber"] == riga].set_index("TimePeriod")["value_num"]
        for a in anni:
            q = f"{a}Q4"
            righe.append({"riga": riga, "comparto": nome, "anno": a, "stock_corrente": s[q],
                          "stock_2012": s[q] / (p[q] / p["2012Q4"])})
    return pd.DataFrame(righe)


def sigma(sc: pd.DataFrame, x_reale: pd.DataFrame, private: list[str], anno: int = 2012) -> pd.DataFrame:
    x = x_reale[x_reale["anno"] == anno].set_index("industria_io")["x_reale"]
    out = []
    for riga, (nome, _) in COMPARTI.items():
        inds = industrie_comparto(riga, private)
        s = sc[(sc["riga"] == riga) & (sc["anno"] == anno)]["stock_2012"].iloc[0]
        # l'ingrosso ha due comparti sulla stessa industria: il σ si riferisce alla somma
        out.append({"riga": riga, "comparto": nome, "industrie": " ".join(inds), "stock_2012": s,
                    "x_2012": float(x.reindex(inds).sum()), "sigma": s / float(x.reindex(inds).sum())})
    return pd.DataFrame(out)


def estero(F_reale: pd.DataFrame, U_reale: pd.DataFrame, anno: int) -> pd.DataFrame:
    f050 = F_reale["F050"]
    importazioni = (-f050).clip(lower=0)
    margini_importati = f050.clip(lower=0)
    interni = [c for c in F_reale.columns if c not in ("F040", "F050")]
    uso_interno = U_reale.sum(axis=1) + F_reale[interni].sum(axis=1)
    return pd.DataFrame({"anno": anno, "prodotto": F_reale.index, "esportazioni": F_reale["F040"].values,
                         "importazioni": importazioni.values, "voci_positive_F050": margini_importati.values,
                         "uso_interno": uso_interno.values,
                         "quota_importazioni": (importazioni / uso_interno.where(uso_interno > 0)).values})
