"""Comandi da riga di comando.

    python -m pianificazione71 verifica-dati [--completa]
    python -m pianificazione71 ambiente
    python -m pianificazione71 controllo-solver
    python -m pianificazione71 c1
    python -m pianificazione71 c2
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .archivio import carica_configurazione, verifica_archivio
from .registro import Esecuzione, ambiente

CONFIG = Path(__file__).resolve().parents[2] / "config" / "dati.toml"


def cmd_verifica_dati(a: argparse.Namespace) -> int:
    cfg = carica_configurazione(a.config)
    print(f"Archivio: {cfg.radice}")
    esiti = verifica_archivio(cfg, completa=a.completa)
    for e in esiti:
        stato = "OK " if e.ok else "ERR"
        print(f"  [{stato}] {e.release}: {e.file_verificati} file verificati")
        for p in e.problemi[:20]:
            print(f"        {p}")
    ok = all(e.ok for e in esiti)
    print("Archivio integro." if ok else "Archivio NON integro.")
    return 0 if ok else 1


def cmd_ambiente(a: argparse.Namespace) -> int:
    print(json.dumps(ambiente(), ensure_ascii=False, indent=1))
    return 0


def risolvi_lp_di_prova() -> tuple[str, float, list[float]]:
    """max x + y  s.v.  x + 2y <= 4,  3x + y <= 6,  x, y >= 0.  Ottimo: x = 1,6, y = 1,2, valore 2,8."""
    import highspy
    import numpy as np

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    inf = highspy.kHighsInf
    h.addVars(2, np.array([0.0, 0.0]), np.array([inf, inf]))
    h.changeColsCost(2, np.array([0, 1], dtype=np.int32), np.array([1.0, 1.0]))
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)
    h.addRows(2, np.array([-inf, -inf]), np.array([4.0, 6.0]), 4,
              np.array([0, 2], dtype=np.int32), np.array([0, 1, 0, 1], dtype=np.int32),
              np.array([1.0, 2.0, 3.0, 1.0]))
    h.run()
    stato = h.modelStatusToString(h.getModelStatus())
    return stato, h.getInfo().objective_function_value, list(h.getSolution().col_value)


def cmd_controllo_solver(a: argparse.Namespace) -> int:
    cfg = carica_configurazione(a.config)
    with Esecuzione("controllo-solver", cfg, parametri={"problema": "LP 2x2 di prova"}) as es:
        stato, valore, x = risolvi_lp_di_prova()
        ok = stato == "Optimal" and abs(valore - 2.8) < 1e-9
        testo = f"stato: {stato}\nvalore: {valore}\nsoluzione: {x}\nesito: {'OK' if ok else 'ERRATO'}\n"
        es.scrivi_testo("esito.txt", testo)
    print(testo + f"Registro: {es.cartella}")
    return 0 if ok else 1


def cmd_c1(a: argparse.Namespace) -> int:
    from .passo_c1 import esegui
    cfg = carica_configurazione(a.config)
    es = esegui(cfg)
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_c2(a: argparse.Namespace) -> int:
    from .passo_c2 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pianificazione71")
    ap.add_argument("--config", type=Path, default=CONFIG)
    sub = ap.add_subparsers(dest="comando", required=True)
    v = sub.add_parser("verifica-dati", help="verifica le impronte delle release e dei file usati")
    v.add_argument("--completa", action="store_true", help="verifica tutti i file di ogni release")
    v.set_defaults(f=cmd_verifica_dati)
    sub.add_parser("ambiente", help="versioni di Python e pacchetti").set_defaults(f=cmd_ambiente)
    sub.add_parser("controllo-solver", help="risolve un LP di prova e registra l'esecuzione").set_defaults(
        f=cmd_controllo_solver)
    sub.add_parser("c1", help="passo C1: sistema prodotti-industrie 2012-2016").set_defaults(f=cmd_c1)
    sub.add_parser("c2", help="passo C2: margini dell'investimento").set_defaults(f=cmd_c2)
    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
