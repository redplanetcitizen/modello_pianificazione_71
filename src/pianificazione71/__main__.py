"""Comandi da riga di comando.

    python -m pianificazione71 verifica-dati [--completa]
    python -m pianificazione71 ambiente
    python -m pianificazione71 controllo-solver
    python -m pianificazione71 c1
    python -m pianificazione71 c2
    python -m pianificazione71 c4
    python -m pianificazione71 c4b
    python -m pianificazione71 c5
    python -m pianificazione71 c6
    python -m pianificazione71 c7
    python -m pianificazione71 passo-c
    python -m pianificazione71 d
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
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


def cmd_c4(a: argparse.Namespace) -> int:
    from .passo_c4 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_c4b(a: argparse.Namespace) -> int:
    from .passo_c4b import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_c5(a: argparse.Namespace) -> int:
    from .passo_c5 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_c6(a: argparse.Namespace) -> int:
    from .passo_c6 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_c7(a: argparse.Namespace) -> int:
    from .passo_c7 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_d(a: argparse.Namespace) -> int:
    from .passo_d import esegui
    for es in esegui(carica_configurazione(a.config)):
        print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
        print(f"Registro: {es.cartella}\n")
    return 0


def cmd_d4(a: argparse.Namespace) -> int:
    from .dati_modello import costruisci
    from .passo_d import o3_valore
    cfg = carica_configurazione(a.config)
    es = o3_valore(cfg, costruisci(cfg))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_d5(a: argparse.Namespace) -> int:
    from .grafici import esegui
    es = esegui(carica_configurazione(a.config))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_e1(a: argparse.Namespace) -> int:
    from .passo_e1 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_e2(a: argparse.Namespace) -> int:
    from .passo_e2 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_e3(a: argparse.Namespace) -> int:
    from .passo_e3 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_e4(a: argparse.Namespace) -> int:
    from .passo_e4 import esegui
    es = esegui(carica_configurazione(a.config))
    print((es.cartella / "sintesi.md").read_text(encoding="utf-8"))
    print(f"Registro: {es.cartella}")
    return 0


def cmd_passo_c(a: argparse.Namespace) -> int:
    """Esegue in sequenza C1, C2, C4, C4b, C5, C6, C7, ciascuno con la propria esecuzione registrata."""
    import importlib
    cfg = carica_configurazione(a.config)
    for passo in ("c1", "c2", "c4", "c4b", "c5", "c6", "c7"):
        es = importlib.import_module(f".passo_{passo}", __package__).esegui(cfg)
        print(f"{passo}: {es.cartella}")
    return 0


def main(argv: list[str] | None = None) -> int:
    # avviso innocuo di openpyxl sulle intestazioni di stampa dei file BEA
    warnings.filterwarnings("ignore", message="Cannot parse header or footer")
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
    sub.add_parser("c4", help="passo C4: stima di Phi").set_defaults(f=cmd_c4)
    sub.add_parser("c4b", help="passo C4b: confronto di Phi con la tavola 1997").set_defaults(f=cmd_c4b)
    sub.add_parser("c5", help="passo C5: capitale a prezzi 2012").set_defaults(f=cmd_c5)
    sub.add_parser("c6", help="passo C6: capacita' legata al capitale").set_defaults(f=cmd_c6)
    sub.add_parser("c7", help="passo C7: lavoro, scorte, estero").set_defaults(f=cmd_c7)
    sub.add_parser("d", help="passo D: modello (controllo, O4, obiettivi, sensibilita')").set_defaults(f=cmd_d)
    sub.add_parser("d4", help="passo D4: O3 con capitale terminale a valore dello stock").set_defaults(f=cmd_d4)
    sub.add_parser("d5", help="passo D5: grafici modello / economia osservata").set_defaults(f=cmd_d5)
    sub.add_parser("e1", help="passo E1: gradualita' dell'investimento su O2").set_defaults(f=cmd_e1)
    sub.add_parser("e2", help="passo E2: orizzonte 2010-2019, confronto sul 2012-2016").set_defaults(f=cmd_e2)
    sub.add_parser("e3", help="passo E3: funzione d'investimento stimata in O2").set_defaults(f=cmd_e3)
    sub.add_parser("e4", help="passo E4: taratura della capacita' fuori G.17 sull'inviluppo 1997-2019").set_defaults(f=cmd_e4)
    sub.add_parser("passo-c", help="esegue tutti i sotto-passi del passo C").set_defaults(f=cmd_passo_c)
    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
