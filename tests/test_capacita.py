from __future__ import annotations

import pandas as pd
import pytest

from pianificazione71.capacita import capitale_capacita, gruppo_klems, pesi_costo_uso


def test_pesi_costo_uso():
    pan = pd.DataFrame({"industria_io": ["211"] * 3, "tipo": ["E", "S", "N"], "anno": 2012,
                        "K_inizio_2012": [100.0, 300.0, 50.0], "delta": [0.14, 0.03, 0.25]})
    rem = pd.Series({"211": 0.10 * 450 + 0.14 * 100 + 0.03 * 300 + 0.25 * 50})  # r = 0,10
    pesi, tassi = pesi_costo_uso(pan, rem)
    assert tassi.loc[0, "r"] == pytest.approx(0.10)
    kc = capitale_capacita(pan, pesi)
    assert kc["K_cap"].iloc[0] == pytest.approx(450.0)  # nel 2012 K^cap = ΣK
    w = pesi.set_index("tipo")["w"]
    assert w["N"] / w["S"] == pytest.approx((0.10 + 0.25) / (0.10 + 0.03))


def test_gruppi_klems():
    assert gruppo_klems("445") == "44RT" and gruppo_klems("HS") == "531" and gruppo_klems("211") == "211"
