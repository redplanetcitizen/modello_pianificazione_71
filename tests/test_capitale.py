from __future__ import annotations

import pandas as pd
import pytest

from pianificazione71.capitale import a_prezzi_2012, aggrega_io, pannello, tipo_bene


def test_tipo_bene():
    assert tipo_bene("EP1A") == "E" and tipo_bene("ENS1") == "N" and tipo_bene("RD11") == "N"
    assert tipo_bene("AE10") == "N" and tipo_bene("SI00") == "S" and tipo_bene("EQ00") is None


def _serie(valori, bene="EP1A", ind="2110"):
    return pd.DataFrame([{"industria_fa": ind, "bene": bene, "anno": a, "valore": v} for a, v in valori.items()])


def test_prezzi_2012_e_accumulazione():
    # quantità a costo fisso (base 2017) e valori correnti: prezzo 2012 = 2 (corrente/fisso)
    Kf, Kc = _serie({2011: 100.0, 2012: 105.0}), _serie({2011: 190.0, 2012: 210.0})
    If, Ic = _serie({2011: 20.0, 2012: 20.0}), _serie({2011: 38.0, 2012: 40.0})
    Df, Dc = _serie({2011: 15.0, 2012: 15.0}), _serie({2011: 28.5, 2012: 30.0})
    el = {m: a_prezzi_2012(c, f) for m, (c, f) in {"K": (Kc, Kf), "I": (Ic, If), "D": (Dc, Df)}.items()}
    k = el["K"].set_index("anno")["valore_2012"]
    assert k[2012] == pytest.approx(210.0) and k[2011] == pytest.approx(200.0)  # 2011 valutato a prezzi 2012
    conc = pd.DataFrame({"industria_fa": ["2110"], "industria_io": ["211"]})
    p = pannello(*(aggrega_io(el[m], conc, m) for m in "KID"))
    r = p[p["anno"] == 2012].iloc[0]
    assert r["K_inizio_2012"] == pytest.approx(200.0)
    assert r["altre_variazioni_2012"] == pytest.approx(210 - 200 - 40 + 30)
    assert r["delta"] == pytest.approx(30 / 200)
