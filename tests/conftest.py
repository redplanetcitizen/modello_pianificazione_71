"""Archivio di prova, costruito con la stessa struttura di dati_economici."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@pytest.fixture
def archivio(tmp_path: Path):
    radice = tmp_path / "dati_economici"
    rel = radice / "bea" / "prova"
    (rel / "manual" / "M1").mkdir(parents=True)
    contenuti = {"NOTE.md": b"note\n", "manual/M1/use.xlsx": b"dati use", "manual/M1/make.xlsx": b"dati make"}
    voci = {}
    for nome, b in contenuti.items():
        (rel / nome).write_bytes(b)
        voci[nome] = {"bytes": len(b), "sha256": _sha(b)}
    manifest = json.dumps({"release": "prova", "numero_file": len(voci), "file": voci}).encode()
    (rel / "MANIFEST_RELEASE.json").write_bytes(manifest)
    config = tmp_path / "dati.toml"
    config.write_text(
        f"""
[archivio]
radice = '{radice.as_posix()}'

[[release]]
id = "bea-prova"
percorso = "bea/prova"
sha256_manifest = "{_sha(manifest)}"

[[file]]
release = "bea-prova"
percorso = "manual/M1/use.xlsx"
""",
        encoding="utf-8",
    )
    return {"radice": radice, "release": rel, "config": config}
