from __future__ import annotations

import pytest

from pianificazione71.archivio import (
    ErroreArchivio,
    carica_configurazione,
    esigi_archivio_integro,
    percorso_dati,
    verifica_archivio,
)


def test_archivio_integro(archivio):
    cfg = carica_configurazione(archivio["config"])
    esiti = esigi_archivio_integro(cfg)
    assert esiti[0].ok and esiti[0].file_verificati == 1
    completa = verifica_archivio(cfg, completa=True)
    assert completa[0].ok and completa[0].file_verificati == 3


def test_file_usato_modificato(archivio):
    (archivio["release"] / "manual/M1/use.xlsx").write_bytes(b"dati alterati")
    cfg = carica_configurazione(archivio["config"])
    with pytest.raises(ErroreArchivio, match="dimensione diversa|contenuto modificato"):
        esigi_archivio_integro(cfg)


def test_stessa_dimensione_contenuto_diverso(archivio):
    (archivio["release"] / "manual/M1/use.xlsx").write_bytes(b"dati USE")
    cfg = carica_configurazione(archivio["config"])
    esito = verifica_archivio(cfg)[0]
    assert not esito.ok and "contenuto modificato" in esito.problemi[0]


def test_file_non_usato_modificato_solo_verifica_completa(archivio):
    (archivio["release"] / "manual/M1/make.xlsx").write_bytes(b"make alterato!")
    cfg = carica_configurazione(archivio["config"])
    assert verifica_archivio(cfg)[0].ok
    assert not verifica_archivio(cfg, completa=True)[0].ok


def test_file_aggiunto(archivio):
    (archivio["release"] / "nuovo.csv").write_text("x")
    cfg = carica_configurazione(archivio["config"])
    esito = verifica_archivio(cfg, completa=True)[0]
    assert any(p.startswith("aggiunto") for p in esito.problemi)


def test_manifest_alterato(archivio):
    m = archivio["release"] / "MANIFEST_RELEASE.json"
    m.write_text(m.read_text() + " ")
    cfg = carica_configurazione(archivio["config"])
    esito = verifica_archivio(cfg)[0]
    assert not esito.ok and "impronta del manifest" in esito.problemi[0]


def test_percorso_non_dichiarato(archivio):
    cfg = carica_configurazione(archivio["config"])
    assert percorso_dati(cfg, "bea-prova", "manual/M1/use.xlsx").is_file()
    with pytest.raises(ErroreArchivio, match="non è dichiarato"):
        percorso_dati(cfg, "bea-prova", "manual/M1/make.xlsx")


def test_radice_da_variabile_ambiente(archivio, monkeypatch, tmp_path):
    monkeypatch.setenv("DATI_ECONOMICI", str(tmp_path / "altrove"))
    cfg = carica_configurazione(archivio["config"])
    assert cfg.radice == tmp_path / "altrove"
    assert not verifica_archivio(cfg)[0].ok
