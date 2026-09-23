"""Pacchetto di condivisione: selezione delle esecuzioni ufficiali e zip dei dati verificabile."""
from __future__ import annotations

import json
import zipfile

from pianificazione71.archivio import carica_configurazione, esigi_archivio_integro
from pianificazione71.condivisione import esecuzioni_ufficiali, zip_dati


def _run(runs, nome_cartella, nome, commit, sporco, esito="completata"):
    d = runs / nome_cartella
    d.mkdir(parents=True)
    (d / "esecuzione.json").write_text(json.dumps({"nome": nome, "esito": esito,
                                                   "codice": {"commit": commit, "modifiche_non_registrate": sporco}}))
    return d


def test_solo_esecuzioni_ufficiali(tmp_path):
    runs = tmp_path / "runs"
    _run(runs, "20260101-000000_A", "A", "abc", False)
    ultima = _run(runs, "20260102-000000_A", "A", "def", False)
    _run(runs, "20260103-000000_A", "A", "ghi", True)             # modifiche non registrate: esclusa
    _run(runs, "20260101-000000_B", "B", None, None)               # senza commit: esclusa
    _run(runs, "20260101-000000_C", "C", "abc", False, "errore")   # non completata: esclusa
    assert esecuzioni_ufficiali(runs) == {"A": ultima}
    assert set(esecuzioni_ufficiali(runs, includi_non_ufficiali=True)) == {"A", "B"}


def test_zip_dati_passa_la_verifica(archivio, tmp_path, monkeypatch):
    cfg = carica_configurazione(archivio["config"])
    f, h = zip_dati(cfg, tmp_path / "dati.zip")
    assert len(h) == 64
    with zipfile.ZipFile(f) as z:
        nomi = set(z.namelist())
        assert "dati_economici/bea/prova/manual/M1/use.xlsx" in nomi
        assert "dati_economici/bea/prova/manual/M1/make.xlsx" not in nomi   # non letto dal modello
        z.extractall(tmp_path / "estratto")
    monkeypatch.setenv("DATI_ECONOMICI", str(tmp_path / "estratto" / "dati_economici"))
    cfg2 = carica_configurazione(archivio["config"])
    assert esigi_archivio_integro(cfg2)[0].ok
