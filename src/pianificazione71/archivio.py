"""Accesso verificato all'archivio dati_economici.

Il modello non copia dati grezzi: li legge dall'archivio, dopo averne verificato
l'integrità contro i manifest congelati (MANIFEST_RELEASE.json).

Due livelli di verifica:
- ordinaria: impronta del manifest di ogni release + impronta dei soli file usati;
- completa: in più, tutti i file di ogni manifest (nessuno aggiunto, mancante o modificato).
"""
from __future__ import annotations

import hashlib
import json
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

MANIFEST = "MANIFEST_RELEASE.json"
IGNORATI = {MANIFEST, "desktop.ini", "Thumbs.db", ".DS_Store"}


class ErroreArchivio(RuntimeError):
    """L'archivio non corrisponde a quanto dichiarato in configurazione."""


@dataclass(frozen=True)
class Release:
    id: str
    percorso: str
    sha256_manifest: str
    contenuto: str = ""


@dataclass(frozen=True)
class FileUsato:
    release: str
    percorso: str


@dataclass
class Configurazione:
    radice: Path
    release: dict[str, Release]
    file: list[FileUsato]
    origine: Path | None = None

    def cartella(self, release_id: str) -> Path:
        return self.radice / self.release[release_id].percorso


@dataclass
class EsitoRelease:
    release: str
    ok: bool
    file_verificati: int = 0
    problemi: list[str] = field(default_factory=list)


def sha256_file(percorso: Path) -> str:
    h = hashlib.sha256()
    with percorso.open("rb") as f:
        for blocco in iter(lambda: f.read(1 << 20), b""):
            h.update(blocco)
    return h.hexdigest()


def carica_configurazione(percorso: str | Path) -> Configurazione:
    percorso = Path(percorso)
    with percorso.open("rb") as f:
        dati = tomllib.load(f)
    radice = Path(os.environ.get("DATI_ECONOMICI", dati["archivio"]["radice"]))
    release = {}
    for r in dati.get("release", []):
        rel = Release(r["id"], r["percorso"], r["sha256_manifest"].lower(), r.get("contenuto", ""))
        if rel.id in release:
            raise ErroreArchivio(f"Release duplicata in configurazione: {rel.id}")
        release[rel.id] = rel
    file = [FileUsato(v["release"], v["percorso"]) for v in dati.get("file", [])]
    for v in file:
        if v.release not in release:
            raise ErroreArchivio(f"File {v.percorso}: release sconosciuta {v.release}")
    return Configurazione(radice, release, file, percorso)


def _leggi_manifest(cfg: Configurazione, rel: Release) -> tuple[dict | None, list[str]]:
    p = cfg.radice / rel.percorso / MANIFEST
    if not p.is_file():
        return None, [f"manca {p}"]
    impronta = sha256_file(p)
    if impronta != rel.sha256_manifest:
        return None, [f"impronta del manifest diversa: attesa {rel.sha256_manifest}, trovata {impronta}"]
    return json.loads(p.read_text(encoding="utf-8")), []


def _verifica_voce(cartella: Path, rel_path: str, attesa: dict) -> str | None:
    p = cartella / rel_path
    if not p.is_file():
        return f"mancante: {rel_path}"
    if p.stat().st_size != attesa["bytes"]:
        return f"dimensione diversa: {rel_path}"
    if sha256_file(p) != attesa["sha256"].lower():
        return f"contenuto modificato: {rel_path}"
    return None


def verifica_release(cfg: Configurazione, release_id: str, completa: bool = False) -> EsitoRelease:
    rel = cfg.release[release_id]
    esito = EsitoRelease(release_id, ok=False)
    manifest, problemi = _leggi_manifest(cfg, rel)
    if manifest is None:
        esito.problemi = problemi
        return esito
    voci = manifest["file"]
    cartella = cfg.radice / rel.percorso
    if completa:
        presenti = {
            p.relative_to(cartella).as_posix()
            for p in cartella.rglob("*")
            if p.is_file() and p.name not in IGNORATI
        }
        esito.problemi += [f"aggiunto: {x}" for x in sorted(presenti - set(voci))]
        da_controllare = sorted(voci)
    else:
        da_controllare = [v.percorso for v in cfg.file if v.release == release_id]
    for rel_path in da_controllare:
        if rel_path not in voci:
            esito.problemi.append(f"non presente nel manifest: {rel_path}")
            continue
        problema = _verifica_voce(cartella, rel_path, voci[rel_path])
        if problema:
            esito.problemi.append(problema)
        else:
            esito.file_verificati += 1
    esito.ok = not esito.problemi
    return esito


def verifica_archivio(cfg: Configurazione, completa: bool = False) -> list[EsitoRelease]:
    return [verifica_release(cfg, rid, completa) for rid in cfg.release]


def esigi_archivio_integro(cfg: Configurazione, completa: bool = False) -> list[EsitoRelease]:
    """Verifica l'archivio e solleva ErroreArchivio al primo scostamento."""
    esiti = verifica_archivio(cfg, completa)
    errati = [e for e in esiti if not e.ok]
    if errati:
        righe = [f"{e.release}: " + "; ".join(e.problemi[:5]) for e in errati]
        raise ErroreArchivio("Archivio non integro:\n" + "\n".join(righe))
    return esiti


def percorso_dati(cfg: Configurazione, release_id: str, rel_path: str) -> Path:
    """Percorso di un file dell'archivio. Ammesso solo se dichiarato in configurazione."""
    if FileUsato(release_id, rel_path) not in cfg.file:
        raise ErroreArchivio(
            f"{release_id}/{rel_path} non è dichiarato in config/dati.toml: "
            "aggiungerlo prima di leggerlo, così che venga verificato."
        )
    return cfg.cartella(release_id) / rel_path
