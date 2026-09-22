from __future__ import annotations

import numpy as np
import pytest

from pianificazione71.phi import gras


def test_ras_rispetta_i_margini():
    A0 = np.array([[1.0, 2.0], [3.0, 4.0]])
    u, v = np.array([5.0, 5.0]), np.array([4.0, 6.0])
    e = gras(A0, u, v)
    assert e.convergenza
    assert np.allclose(e.X.sum(axis=1), u) and np.allclose(e.X.sum(axis=0), v)
    # RAS: la soluzione è biproporzionale alla struttura iniziale (rapporto incrociato invariato)
    assert (e.X[0, 0] * e.X[1, 1]) / (e.X[0, 1] * e.X[1, 0]) == pytest.approx((1 * 4) / (2 * 3))


def test_gras_con_negativi():
    A0 = np.array([[4.0, -1.0, 2.0], [1.0, 3.0, 1.0], [2.0, 2.0, -0.5]])
    u = np.array([6.0, 5.5, 4.0])
    v = np.array([7.0, 4.5, 4.0])
    e = gras(A0, u, v)
    assert e.convergenza
    assert np.allclose(e.X.sum(axis=1), u, atol=1e-8) and np.allclose(e.X.sum(axis=0), v, atol=1e-8)
    assert np.all(np.sign(e.X) == np.sign(A0))  # GRAS conserva i segni


def test_struttura_iniziale_vuota_con_totale():
    with pytest.raises(ValueError, match="struttura iniziale nulla"):
        gras(np.array([[1.0, 0.0], [0.0, 0.0]]), np.array([1.0, 1.0]), np.array([1.0, 1.0]))


def test_totali_incoerenti():
    with pytest.raises(ValueError, match="incoerenti"):
        gras(np.ones((2, 2)), np.array([1.0, 1.0]), np.array([1.0, 2.0]))
