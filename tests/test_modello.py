from __future__ import annotations

import os
from pathlib import Path

import pytest

from pianificazione71.modello import INF, Costruttore


def test_costruttore_lp():
    # max 3a + 2b  s.v.  a + b <= 4,  a + 3b <= 7,  a <= 3
    C = Costruttore()
    a, b = C.var("a", ub=3.0, costo=3.0), C.var("b", costo=2.0)
    C.riga({a: 1.0, b: 1.0}, -INF, 4.0, "r1")
    C.riga({a: 1.0, b: 3.0}, -INF, 7.0, "r2")
    h = C.risolvi(massimizza=True)
    assert h.modelStatusToString(h.getModelStatus()) == "Optimal"
    assert h.getInfo().objective_function_value == pytest.approx(11.0)
    duali = h.getSolution().row_dual
    assert duali[0] == pytest.approx(2.0)  # prezzo ombra del primo vincolo


ARCHIVIO = Path(os.environ.get("DATI_ECONOMICI", r"C:\Users\franc\Documents\dati_economici"))


@pytest.mark.skipif(not (ARCHIVIO / "bea/2026-09-22/manual/M3/detailnonres_stk1.xlsx").is_file(),
                    reason="archivio dati non disponibile")
@pytest.mark.lento
def test_modello_completo_fattibile():
    from pianificazione71.archivio import carica_configurazione
    from pianificazione71.dati_modello import costruisci
    from pianificazione71.modello import Opzioni, costruisci_e_risolvi
    cfg = carica_configurazione(Path(__file__).resolve().parents[1] / "config" / "dati.toml")
    P = costruisci(cfg)
    R = costruisci_e_risolvi(P, Opzioni(obiettivo="O4", u_non_g17=0.772, sigma_fattore=0.85))
    assert R.stato == "Optimal" and R.obiettivo < 0.05
