from __future__ import annotations

import json

import pytest

from pianificazione71.__main__ import risolvi_lp_di_prova
from pianificazione71.archivio import ErroreArchivio, carica_configurazione
from pianificazione71.registro import Esecuzione


def test_esecuzione_registrata(archivio, tmp_path):
    cfg = carica_configurazione(archivio["config"])
    with Esecuzione("prova", cfg, parametri={"a": 1}, cartella_runs=tmp_path / "runs") as es:
        es.scrivi_testo("esito.txt", "ok\n")
    dati = json.loads((es.cartella / "esecuzione.json").read_text(encoding="utf-8"))
    assert dati["esito"] == "completata"
    assert dati["parametri"] == {"a": 1}
    assert dati["verifica_dati"]["release"] == {"bea-prova": 1}
    assert dati["output"]["esito.txt"]["bytes"] == 3
    assert dati["configurazione"]["sha256"]
    assert "highspy" in dati["ambiente"]["pacchetti"]


def test_errore_registrato(archivio, tmp_path):
    cfg = carica_configurazione(archivio["config"])
    with pytest.raises(ZeroDivisionError):
        with Esecuzione("errore", cfg, cartella_runs=tmp_path / "runs") as es:
            1 / 0
    dati = json.loads((es.cartella / "esecuzione.json").read_text(encoding="utf-8"))
    assert dati["esito"].startswith("errore: ZeroDivisionError")


def test_archivio_non_integro_blocca_esecuzione(archivio, tmp_path):
    (archivio["release"] / "manual/M1/use.xlsx").write_bytes(b"alterato")
    cfg = carica_configurazione(archivio["config"])
    with pytest.raises(ErroreArchivio):
        with Esecuzione("bloccata", cfg, cartella_runs=tmp_path / "runs"):
            pass
    assert not (tmp_path / "runs").exists()


def test_nome_non_valido(archivio):
    cfg = carica_configurazione(archivio["config"])
    with pytest.raises(ValueError):
        Esecuzione("nome con spazi", cfg)


def test_solver():
    stato, valore, x = risolvi_lp_di_prova()
    assert stato == "Optimal"
    assert valore == pytest.approx(2.8)
    assert x == pytest.approx([1.6, 1.2])
