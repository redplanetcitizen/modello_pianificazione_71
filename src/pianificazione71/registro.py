"""Registro delle esecuzioni.

Ogni esecuzione crea runs/AAAAMMGG-HHMMSS_<nome>/ con un file esecuzione.json che
contiene: versione del codice (commit git e modifiche non registrate), ambiente
(Python, pacchetti, sistema), impronta della configurazione, esito della verifica
dei dati, parametri, file prodotti con le loro impronte, esito finale.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
import re
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from . import __version__
from .archivio import Configurazione, esigi_archivio_integro, sha256_file

PACCHETTI = ("numpy", "pandas", "openpyxl", "highspy")


def _ora() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def stato_git(cartella: Path) -> dict[str, Any]:
    def git(*args: str) -> str | None:
        try:
            r = subprocess.run(["git", *args], cwd=cartella, capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return r.stdout.strip() if r.returncode == 0 else None

    commit = git("rev-parse", "HEAD")
    modifiche = git("status", "--porcelain")
    return {
        "commit": commit,
        "modifiche_non_registrate": None if modifiche is None else bool(modifiche),
        "nota": None if commit else "repository git non inizializzato o git non disponibile",
    }


def ambiente() -> dict[str, Any]:
    versioni = {}
    for p in PACCHETTI:
        try:
            versioni[p] = metadata.version(p)
        except metadata.PackageNotFoundError:
            versioni[p] = None
    return {
        "pianificazione71": __version__,
        "python": sys.version.split()[0],
        "piattaforma": platform.platform(),
        "processore": platform.processor(),
        "pacchetti": versioni,
    }


class Esecuzione:
    """Contesto di un'esecuzione registrata.

    with Esecuzione("controllo-2012", cfg, parametri={...}) as es:
        es.scrivi_testo("sintesi.md", testo)
    """

    def __init__(self, nome: str, cfg: Configurazione, parametri: dict | None = None,
                 cartella_runs: str | Path | None = None, verifica_completa: bool = False):
        if not re.fullmatch(r"[A-Za-z0-9._-]+", nome):
            raise ValueError("Il nome dell'esecuzione ammette solo lettere, cifre, '.', '_' e '-'.")
        self.cfg = cfg
        self.nome = nome
        self.parametri = parametri or {}
        self.verifica_completa = verifica_completa
        self.radice_repo = Path(__file__).resolve().parents[2]
        istante = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        base = Path(cartella_runs) if cartella_runs is not None else self.radice_repo / "runs"
        self.cartella = base / f"{istante}_{nome}"
        self.output: dict[str, dict] = {}
        self.dati: dict[str, Any] = {}

    def __enter__(self) -> "Esecuzione":
        # Prima la verifica dei dati: se l'archivio non è integro l'esecuzione non parte.
        esiti = esigi_archivio_integro(self.cfg, self.verifica_completa)
        self.cartella.mkdir(parents=True, exist_ok=False)
        self.dati = {
            "id": self.cartella.name,
            "nome": self.nome,
            "inizio_utc": _ora(),
            "codice": stato_git(self.radice_repo),
            "ambiente": ambiente(),
            "configurazione": {
                "file": str(self.cfg.origine) if self.cfg.origine else None,
                "sha256": sha256_file(self.cfg.origine) if self.cfg.origine else None,
                "radice_archivio": str(self.cfg.radice),
            },
            "verifica_dati": {
                "completa": self.verifica_completa,
                "release": {e.release: e.file_verificati for e in esiti},
            },
            "parametri": self.parametri,
        }
        self._salva()
        return self

    def scrivi_testo(self, nome_file: str, testo: str) -> Path:
        return self.scrivi_byte(nome_file, testo.encode("utf-8"))

    def scrivi_byte(self, nome_file: str, contenuto: bytes) -> Path:
        p = self.cartella / nome_file
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(contenuto)
        self.output[nome_file] = {"bytes": len(contenuto), "sha256": hashlib.sha256(contenuto).hexdigest()}
        return p

    def registra_file(self, nome_file: str) -> None:
        """Registra un file scritto da altro codice nella cartella dell'esecuzione."""
        p = self.cartella / nome_file
        self.output[nome_file] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}

    def _salva(self) -> None:
        (self.cartella / "esecuzione.json").write_text(
            json.dumps(self.dati, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    def __exit__(self, tipo, valore, traccia) -> bool:
        self.dati["fine_utc"] = _ora()
        self.dati["esito"] = "completata" if tipo is None else f"errore: {tipo.__name__}: {valore}"
        self.dati["output"] = self.output
        self._salva()
        return False
