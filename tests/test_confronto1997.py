from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from pianificazione71.confronto1997 import INDUSTRIE_1997, dissomiglianza, prodotto_1997_a_io


def test_dissomiglianza():
    a = pd.DataFrame({"j": [0.5, 0.5, 0.0]}, index=["x", "y", "z"])
    b = pd.DataFrame({"j": [0.0, 0.5, 0.5]}, index=["x", "y", "z"])
    assert dissomiglianza(a, a)["j"] == 0.0 and dissomiglianza(a, b)["j"] == pytest.approx(0.5)


def test_esclusioni_e_corrispondenze():
    assert prodotto_1997_a_io("511200") is None and prodotto_1997_a_io("233511*") is None
    assert prodotto_1997_a_io("336411") == "3364OT" and prodotto_1997_a_io("233612") == "23"
    with pytest.raises(ValueError):
        prodotto_1997_a_io("999999")


ARCHIVIO = Path(os.environ.get("DATI_ECONOMICI", r"C:\Users\franc\Documents\dati_economici"))
FLOW = ARCHIVIO / "bea/2025-09/manual/M5/flow1997.xls"


@pytest.mark.skipif(not FLOW.is_file(), reason="archivio dati non disponibile")
def test_copertura_tavola_1997():
    from pianificazione71.confronto1997 import leggi_cft1997
    t = leggi_cft1997(FLOW, FLOW.with_name("changes_to_180x123combined.xls"))
    assert t.shape == (180, 123)
    assert set(t.columns) == set(INDUSTRIE_1997)
    for c in t.index:  # ogni prodotto è mappato o escluso esplicitamente, senza errori
        prodotto_1997_a_io(c)
