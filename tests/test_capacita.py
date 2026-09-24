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


def _cartella_klems(percorso, fogli: dict):
    """Cartella KLEMS sintetica: foglio dei codici (con la stessa intestazione del file BEA-BLS) e fogli dati."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "NAICS codes"
    for r in (["Table A. Industries in the Production Account"], [], ["Descriptions", "Production Account Codes", "2017 NAICS codes"], [],
              ["Farms", "111CA ", "111, 112"], ["Utilities", 22, "2211-2213"], ["Federal government", "GF", "NA"],
              ["NA -- Not applicable"]):
        ws.append(r)
    for nome, righe in fogli.items():
        f = wb.create_sheet(nome)
        for r in righe:
            f.append(r)
    wb.save(percorso)


def test_leggi_klems_ignora_note_e_verifica_etichette(tmp_path):
    from pianificazione71.capacita import leggi_klems
    intest = [["Integrated Labor Productivity* (2017=100)"], ["Industry Description", "2012", "2013"]]
    dati = [["Farms", 90.0, 95.0], ["Utilities", 98.0, 99.0], ["Federal", 97.0, 98.0]]
    note = [[None], ["Note:"], ["* Integrated labor productivity estimates differ from official estimates."], [None]]
    f = tmp_path / "klems.xlsx"
    _cartella_klems(f, {"ILP": intest + dati + note, "Sbagliato": intest + [dati[1], dati[0], dati[2]]})
    v = leggi_klems(f, ["ILP"], [2012, 2013])
    assert list(v.index) == ["111CA", "22", "GF"] and v.loc["GF", 2013] == 98.0
    with pytest.raises(ValueError, match="non corrisponde"):
        leggi_klems(f, ["Sbagliato"], [2012])


def test_produttivita_lavoro_klems_ricostruita():
    """Sul file archiviato: il foglio Integrated Labor Productivity ha 63 righe di dati ed è
    produzione lorda in quantità / ore lavorate, indice 2017 = 100 (scarto dovuto solo agli arrotondamenti)."""
    import os
    from pathlib import Path
    from pianificazione71.capacita import leggi_klems
    f = Path(os.environ.get("DATI_ECONOMICI", "")) / "bls/2026-09-18/BEA-BLS-industry-level-production-account-1997-2024.xlsx"
    if not os.environ.get("DATI_ECONOMICI") or not f.exists():
        pytest.skip("archivio KLEMS non disponibile")
    anni = list(range(1997, 2025))
    ilp = leggi_klems(f, ["Integrated Labor Productivity"], anni)
    go = leggi_klems(f, ["Gross Output_Quantity"], anni)
    ore = leggi_klems(f, ["Labor Hours_Quantity"], anni)
    r = go / ore
    r = r.div(r[2017], axis=0) * 100
    assert ilp.shape == (63, 28)
    assert float((r - ilp).abs().max().max()) < 0.01
