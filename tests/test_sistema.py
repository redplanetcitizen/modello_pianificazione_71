from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pianificazione71.sistema import (
    SPECIALI,
    TavolaMake,
    TavolaUse,
    a_prezzi_2012,
    controlli_reali,
    identita,
    negativi,
)


def _sistema_piccolo():
    """2 industrie, 2 prodotti ordinari + Used, Other; tavole coerenti per costruzione."""
    ind = ["A", "B"]
    prod = ind + list(SPECIALI)
    V = pd.DataFrame([[90.0, 10.0, 0, 0], [5.0, 95.0, 0, 0]], index=ind, columns=prod)
    q = V.sum(axis=0)
    U = pd.DataFrame([[10.0, 20.0], [15.0, 5.0], [0, 0], [0, 0]], index=prod, columns=ind)
    F = pd.DataFrame(0.0, index=prod, columns=["F010", "F050"])
    F["F050"] = [-5.0, 0, 0, 0]
    F["F010"] = q - U.sum(axis=1) - F["F050"]
    x = V.sum(axis=1)
    VA = pd.DataFrame([x - U.sum(axis=0), 0 * x, 0 * x], index=["V001", "V002", "V003"])
    use = TavolaUse(2013, U, F, VA, U.sum(axis=1), F.sum(axis=1), q, U.sum(axis=0), VA.sum(axis=0), x, pd.DataFrame())
    make = TavolaMake(2013, V, x, q, pd.DataFrame())
    return use, make


def test_identita_chiudono():
    use, make = _sistema_piccolo()
    ident = identita(use, make)
    assert ident["max_abs"].max() < 1e-9


def test_negativi_classificati():
    use, make = _sistema_piccolo()
    neg = negativi(use, make)
    assert list(neg["categoria"]) == ["importazioni (segno negativo per convenzione)"]


def test_prezzi_unitari_lasciano_invariato():
    use, make = _sistema_piccolo()
    s = a_prezzi_2012(use, make, pd.Series(1.0, index=use.U.index))
    assert np.allclose(s.x, make.x) and np.allclose(s.q, make.q)
    assert np.allclose(s.B.values, (use.U / make.x).values)


def test_deflazione_per_componente():
    use, make = _sistema_piccolo()
    p = pd.Series({"A": 2.0, "B": 1.0, "Used": 1.0, "Other": 1.0})
    s = a_prezzi_2012(use, make, p)
    # x reale = somma dei prodotti deflazionati, non x nominale / prezzo dell'industria
    assert s.x["A"] == pytest.approx(90 / 2 + 10 / 1)
    assert s.q["A"] == pytest.approx((90 + 5) / 2)
    c = controlli_reali(s)
    assert c["bilancio_prodotti_max_abs"] < 1e-9
    assert c["x_eq_Dq_max_abs"] < 1e-9
    assert c["D_colonne_somma_1_max_scarto"] < 1e-12


ARCHIVIO = Path(os.environ.get("DATI_ECONOMICI", r"C:\Users\franc\Documents\dati_economici"))
USE = ARCHIVIO / "bea/2025-09/manual/M1/IOUse_Before_Redefinitions_PRO_Summary.xlsx"
MAKE = ARCHIVIO / "bea/2025-09/manual/M1/IOMake_Before_Redefinitions_PRO_Summary.xlsx"


@pytest.mark.skipif(not (USE.is_file() and MAKE.is_file()), reason="archivio dati non disponibile")
def test_tavole_reali_2012():
    from pianificazione71.sistema import leggi_make, leggi_use
    u, m = leggi_use(USE, 2012), leggi_make(MAKE, 2012)
    assert u.U.shape == (73, 71) and u.F.shape == (73, 20) and m.V.shape == (71, 73)
    ident = identita(u, m)
    # scarti di arrotondamento delle tavole pubblicate, in milioni di dollari
    assert ident["max_abs"].max() <= 20
    assert u.x.sum() == pytest.approx(29_232_148, abs=5)
