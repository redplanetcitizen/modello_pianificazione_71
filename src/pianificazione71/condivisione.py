"""Pacchetto di condivisione per la revisione esterna (cartella `condivisione/` del repository).

Genera, dai soli dati dell'archivio verificati contro i manifest, le serie e i parametri richiesti per la revisione,
copia i risultati delle esecuzioni UFFICIALI (commit registrato, nessuna modifica non registrata, esito completato) e
scrive un manifest con l'impronta SHA-256 di ogni file. Nessun numero è scritto a mano: ogni CSV è rigenerabile con
`python -m pianificazione71 pacchetto`.

Unità: le serie derivate dai dati (cartella `dati/`) sono in MILIONI di dollari, come nelle fonti BEA; i parametri e
i risultati del modello (cartelle `modello_E6/`, `risultati/`) sono in MILIARDI di dollari 2012, come nel modello.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .archivio import MANIFEST, Configurazione, percorso_dati, sha256_file
from .blocchi import COMPARTI, FTE_RIGHE, fte, industrie_comparto, scorte
from .capacita import G17_IO, METODO_G17, gruppo_klems, leggi_g17
from .capitale import FOGLI_RES, a_prezzi_2012, aggrega_io, leggi_residenziale_componenti, pannello, pannello_residenziale
from .dati_modello import costruisci
from .margini import leggi_concordanza, leggi_fa_dettaglio
from .modello import Opzioni, coefficiente_capacita
from .passo_c1 import MAKE, PREZZI, USE
from .passo_c2 import CONCORDANZA, FA_RES
from .passo_c5 import FILE, REL
from .passo_c6 import G17_CAP, G17_U
from .passo_c7 import DEFL_T, FTE_T, STOCK_T
from .passo_e5 import TARATURA, fattori
from .passo_e6 import MECCANISMI
from .registro import ambiente, stato_git
from .sistema import a_prezzi_2012 as sistema_reale, indici_prezzo, leggi_make, leggi_use

ANNI = range(2008, 2020)                 # serie richieste: 2008-2019
ANNI_G17 = range(1997, 2020)
ORIZZONTI_E6 = {"2012-2016": range(2012, 2017), "2010-2019": range(2010, 2020)}
LIMITE_BYTE = 10 * 1024 * 1024           # file di risultato più grandi: esclusi dal repository, elencati con impronta
PREFISSI = {("K", "1"): "K1N", ("K", "2"): "K2N", ("I", "1"): "I3N", ("I", "2"): "I2N", ("D", "1"): "M1N", ("D", "2"): "M2N"}


def _csv(df: pd.DataFrame, p: Path) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False, lineterminator="\n", float_format="%.10g")
    return p


# ---------------------------------------------------------------------------------------------------------------------
# Dati osservati (milioni di dollari)
# ---------------------------------------------------------------------------------------------------------------------
def nomi_industrie(cfg: Configurazione) -> pd.DataFrame:
    d = pd.read_excel(percorso_dati(cfg, *USE), sheet_name="2012", header=None, dtype=object)
    return pd.DataFrame({"industria_io": [str(c) for c in d.iloc[5, 2:73]], "nome": [str(n).strip() for n in d.iloc[6, 2:73]]})


def capitale(cfg: Configurazione) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pannello industria I/O × tipo × anno (2008-2019) e serie elementari FA (industria FA × bene) usate per costruirlo."""
    anni_k = range(ANNI[0] - 1, ANNI[-1] + 1)          # 2007: stock di fine anno = stock di inizio 2008
    conc = leggi_concordanza(CONCORDANZA)
    ser = {k: leggi_fa_dettaglio(percorso_dati(cfg, REL, v), anni=anni_k) for k, v in FILE.items()}
    el = {m: a_prezzi_2012(ser[m + "1"], ser[m + "2"]) for m in "KID"}
    pan = pd.concat([pannello(*(aggrega_io(el[m], conc, m) for m in "KID")),
                     pannello_residenziale(percorso_dati(cfg, *FA_RES), anni_k)], ignore_index=True)
    pan = pan.sort_values(["industria_io", "tipo", "anno"]).reset_index(drop=True)
    pan["K_inizio_corrente"] = pan.groupby(["industria_io", "tipo"])["K_corrente"].shift(1)
    pan["rivalutazioni_e_altre_variazioni_corrente"] = pan["K_corrente"] - pan["K_inizio_corrente"] - pan["I_corrente"] + pan["D_corrente"]
    pan = pan[pan["anno"].isin(ANNI)]
    col = ["industria_io", "tipo", "anno", "K_inizio_2012", "I_2012", "D_2012", "K_2012", "delta", "altre_variazioni_2012",
           "altre_variazioni_rel", "K_inizio_corrente", "I_corrente", "D_corrente", "K_corrente",
           "rivalutazioni_e_altre_variazioni_corrente"]
    pan = pan[col].rename(columns={"K_2012": "K_fine_2012", "K_corrente": "K_fine_corrente", "delta": "delta_annuo"})
    # serie elementari non residenziali: corrente, costo fisso (dollari 2017 BEA) e valore a prezzi 2012
    righe = []
    fa_io = conc.set_index("industria_fa")["industria_io"]
    for m in "KID":
        c = ser[m + "1"].rename(columns={"valore": "corrente"})[["industria_fa", "bene", "anno", "corrente"]]
        f = ser[m + "2"].rename(columns={"valore": "costo_fisso_2017"})[["industria_fa", "bene", "anno", "costo_fisso_2017"]]
        e = el[m][["industria_fa", "bene", "anno", "tipo", "valore_2012", "prezzo_non_base"]]
        x = c.merge(f, on=["industria_fa", "bene", "anno"]).merge(e, on=["industria_fa", "bene", "anno"])
        x.insert(0, "misura", m)
        x["serie_corrente"] = PREFISSI[(m, "1")] + x["industria_fa"] + "1" + x["bene"] + ".A"
        x["serie_costo_fisso"] = PREFISSI[(m, "2")] + x["industria_fa"] + "1" + x["bene"] + ".A"
        righe.append(x)
    elem = pd.concat(righe, ignore_index=True)
    elem.insert(2, "industria_io", elem["industria_fa"].map(fa_io))
    elem = elem[elem["anno"].isin(ANNI) & ((elem["corrente"] != 0) | (elem["costo_fisso_2017"] != 0))]
    # serie elementari residenziali (tutte su HS)
    for m, (corr, fisso) in FOGLI_RES.items():
        c = leggi_residenziale_componenti(percorso_dati(cfg, *FA_RES), corr, anni_k).rename(columns={"valore": "corrente"})
        f = leggi_residenziale_componenti(percorso_dati(cfg, *FA_RES), fisso, anni_k).rename(columns={"valore": "costo_fisso_2017"})
        x = c.merge(f, on=["industria_fa", "bene", "anno"])
        p = x[x["anno"] == 2012].set_index("bene")
        prezzo = (p["corrente"] / p["costo_fisso_2017"]).replace([float("inf"), -float("inf")], float("nan"))
        x["valore_2012"] = x["costo_fisso_2017"] * x["bene"].map(prezzo).fillna(0.0)
        x = x[x["anno"].isin(ANNI) & ((x["corrente"] != 0) | (x["costo_fisso_2017"] != 0))]
        x = x.assign(misura=m, industria_io="HS", tipo="R", prezzo_non_base=x["bene"].map(prezzo).isna(),
                     serie_corrente=f"detailresidential.xlsx / {corr.strip()}", serie_costo_fisso=f"detailresidential.xlsx / {fisso.strip()}")
        elem = pd.concat([elem, x[elem.columns]], ignore_index=True)
    return pan, elem


def produzione_lavoro(cfg: Configurazione) -> pd.DataFrame:
    tidy = pd.read_csv(percorso_dati(cfg, *PREZZI))
    righe, prezzi = [], None
    for a in ANNI:
        u, m = leggi_use(percorso_dati(cfg, *USE), a), leggi_make(percorso_dati(cfg, *MAKE), a)
        prezzi = indici_prezzo(tidy, list(u.U.columns), ANNI) if prezzi is None else prezzi
        s = sistema_reale(u, m, prezzi[a])
        x_make = m.V.sum(axis=1)
        for j in u.U.columns:
            righe.append({"industria_io": j, "anno": a, "x_corrente_use": float(u.x[j]), "x_corrente_make": float(x_make[j]),
                          "indice_prezzo_2012": float(prezzi.at[j, a]), "x_2012": float(s.x[j])})
    x = pd.DataFrame(righe)
    f = fte(pd.read_csv(percorso_dati(cfg, *FTE_T)), ANNI)
    return x.merge(f, on=["industria_io", "anno"], how="left")


def scorte_comparti(cfg: Configurazione) -> pd.DataFrame:
    s = scorte(pd.read_csv(percorso_dati(cfg, *STOCK_T)), pd.read_csv(percorso_dati(cfg, *DEFL_T)), [ANNI[0] - 1] + list(ANNI))
    return s.rename(columns={"stock_corrente": "stock_fine_anno_corrente", "stock_2012": "stock_fine_anno_2012"})


def g17(cfg: Configurazione) -> pd.DataFrame:
    """Medie annue delle serie mensili G.17. Capacità in % della produzione media 2017 (unità dell'indice di produzione);
    utilizzo in %. Produzione approssimata = prodotto delle medie annue (l'identità produzione = u × capacità vale mese per mese)."""
    serie = list(G17_IO)
    cap = leggi_g17(percorso_dati(cfg, *G17_CAP), serie, list(ANNI_G17))
    u = leggi_g17(percorso_dati(cfg, *G17_U), serie, list(ANNI_G17))
    righe = []
    for s in serie:
        for a in ANNI_G17:
            righe.append({"serie_g17": s, "industrie_io": ";".join(G17_IO[s]), "metodo_capacita_fed": METODO_G17.get(s, "indagine+capitale"),
                          "anno": a, "capacita_perc_produzione_2017": cap.at[s, a], "utilizzo_percento": u.at[s, a],
                          "produzione_approssimata_perc_2017": cap.at[s, a] * u.at[s, a] / 100})
    return pd.DataFrame(righe)


def mappatura(cfg: Configurazione, P) -> pd.DataFrame:
    conc = leggi_concordanza(CONCORDANZA)
    nomi = nomi_industrie(cfg)
    fa = conc.groupby("industria_io")["industria_fa"].apply(lambda s: ";".join(s))
    g17_di = {j: s for s, inds in G17_IO.items() for j in inds}
    fte_di = {j: r for r, j in FTE_RIGHE.items()}
    comp = {}
    for r, (nome, _) in COMPARTI.items():
        for j in industrie_comparto(r, P.private):
            comp.setdefault(j, []).append(nome)
    cap_ind = [j for j in P.kappa.index if j in P.private and j != "HS"]
    out = []
    for j, nome in zip(nomi["industria_io"], nomi["nome"]):
        pubblica = j.startswith("G")
        out.append({
            "industria_io": j, "nome": nome,
            "settore": "pubblico (esogeno)" if pubblica else ("abitazioni (HS)" if j == "HS" else "privato"),
            "industrie_fixed_assets": "detailresidential (tutto il residenziale privato)" if j == "HS" else fa.get(j, ""),
            "capitale_nel_modello": "R" if j == "HS" else ("E,S,N" if j in cap_ind else "no"),
            "vincolo_di_capacita": "si" if (j in cap_ind or j == "HS") else "no",
            "serie_g17": g17_di.get(j, ""), "metodo_capacita_fed": METODO_G17.get(g17_di.get(j, ""), "indagine+capitale") if j in g17_di else "",
            "gruppo_klems": gruppo_klems(j), "riga_fte_nipa_6_5D": str(fte_di.get(j, "")),
            "comparto_scorte": ";".join(comp.get(j, [])),
        })
    return pd.DataFrame(out)


# ---------------------------------------------------------------------------------------------------------------------
# Parametri effettivi di E6 (miliardi di dollari 2012)
# ---------------------------------------------------------------------------------------------------------------------
def opzioni_e6(P, meccanismo: str = "penalita") -> Opzioni:
    return Opzioni(obiettivo="O2", **dict(TARATURA, terminale_fattori=fattori(P)["lavoro_aggregata"], **MECCANISMI[meccanismo]))


def parametri_e6(cfg: Configurazione, cartella: Path) -> list[Path]:
    scritti = []
    for h, anni in ORIZZONTI_E6.items():
        P = costruisci(cfg, anni, inviluppo=True)
        o = opzioni_e6(P)
        a0 = P.anni[0]
        cap_ind = [j for j in P.kappa.index if j in P.private and j != "HS"]
        righe = []
        for j in cap_ind + ["HS"]:
            c = coefficiente_capacita(P, o, j, a0)
            tipi = ["R"] if j == "HS" else [a for a in ("E", "S", "N") if (j, a) in P.K0.index and P.K0[(j, a)] > 0]
            kcap = sum((1.0 if a == "R" else float(P.w[(j, a)])) * float(P.K0[(j, a)]) for a in tipi)
            capacita = kcap / c["kappa_t"]
            x0 = float(P.x_oss[a0][j])
            r = {"industria_io": j, "fonte_calibrazione": c["fonte"], "kappa_calibrato": c["kappa_base"],
                 "moltiplicatore_u_nel_vincolo": c["u"], "theta_deriva_annua": c["theta"],
                 "K_cap_a0": kcap, "capacita_a0": capacita, "x_osservato_a0": x0, "utilizzo_implicito_a0": x0 / capacita}
            for t in anni:
                r[f"kappa_{t}"] = coefficiente_capacita(P, o, j, t)["kappa_t"]
            righe.append(r)
        scritti.append(_csv(pd.DataFrame(righe), cartella / f"capacita_{h}.csv"))
        k = pd.DataFrame({"K_inizio_a0": P.K0, "delta": P.delta, "w_costo_uso": P.w, "I_anno_precedente": P.I_prec}).reset_index()
        k = k.rename(columns={"level_0": "industria_io", "level_1": "tipo"})
        k["w_costo_uso"] = k.apply(lambda z: 1.0 if z["tipo"] == "R" else z["w_costo_uso"], axis=1)
        scritti.append(_csv(k, cartella / f"capitale_{h}.csv"))
        if P.capacita_inviluppo is not None:
            scritti.append(_csv(P.capacita_inviluppo, cartella / f"inviluppo_H9c_{h}.csv"))
        glob = {
            "orizzonte": list(anni), "anno_calibrazione_a0": a0, "unita": "miliardi di dollari 2012; lavoro in migliaia di FTE",
            "opzioni": {k2: (list(v) if isinstance(v, tuple) else v) for k2, v in asdict(o).items()},
            "fattori_terminali_H29": o.terminale_fattori,
            "stock_iniziale_per_tipo": {t: float(P.K0[P.K0.index.get_level_values(1) == t].sum()) for t in ("E", "S", "N", "R")},
            "minimo_terminale_per_gruppo": {g: float(f) * float(P.K0[P.K0.index.get_level_values(1).isin(list(g))].sum())
                                            for g, f in o.terminale_fattori.items()},
            "lavoro_totale_fte_migliaia": {str(t): P.lavoro_tot[t] for t in anni},
            "importazioni_totali": {str(t): P.import_tot[t] for t in anni},
            "industrie_con_capitale_non_residenziale": cap_ind,
            "industrie_con_capacita_G17": sorted(P.g17),
        }
        p = cartella / f"configurazione_{h}.json"
        p.write_text(json.dumps(glob, ensure_ascii=False, indent=1), encoding="utf-8")
        scritti.append(p)
    return scritti


# ---------------------------------------------------------------------------------------------------------------------
# Risultati delle esecuzioni ufficiali
# ---------------------------------------------------------------------------------------------------------------------
def esecuzioni_ufficiali(runs: Path, includi_non_ufficiali: bool = False) -> dict[str, Path]:
    """Ultima esecuzione di ogni nome con commit registrato, nessuna modifica non registrata ed esito completato."""
    scelte = {}
    for d in sorted(runs.glob("*_*")):
        f = d / "esecuzione.json"
        if not f.is_file():
            continue
        e = json.loads(f.read_text(encoding="utf-8"))
        cod = e.get("codice", {})
        ufficiale = cod.get("commit") and cod.get("modifiche_non_registrate") is False and e.get("esito") == "completata"
        if ufficiale or (includi_non_ufficiali and e.get("esito") == "completata"):
            scelte[e["nome"]] = d
    return scelte


def copia_risultati(scelte: dict[str, Path], dest: Path) -> list[dict]:
    esclusi = []
    for nome, d in sorted(scelte.items()):
        for f in sorted(d.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(d.parent)
            if f.stat().st_size > LIMITE_BYTE:
                esclusi.append({"file": rel.as_posix(), "bytes": f.stat().st_size, "sha256": sha256_file(f)})
                continue
            q = dest / rel
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, q)
    return esclusi


# ---------------------------------------------------------------------------------------------------------------------
# Controlli e manifest
# ---------------------------------------------------------------------------------------------------------------------
def controlli(pan: pd.DataFrame, elem: pd.DataFrame, prod: pd.DataFrame) -> str:
    r = ["# Controlli automatici sul pacchetto", "",
         "Generati da `python -m pianificazione71 pacchetto`. Tutti i valori in milioni di dollari.", ""]
    # 1. aggregazione: somma delle serie elementari a prezzi 2012 = pannello
    e = elem[elem["misura"] == "K"].groupby(["industria_io", "tipo", "anno"])["valore_2012"].sum()
    p = pan.set_index(["industria_io", "tipo", "anno"])["K_fine_2012"]
    d = (e.reindex(p.index).fillna(0) - p).abs()
    r += [f"1. Somma delle serie elementari K a prezzi 2012 contro il pannello per industria e tipo: scarto massimo {d.max():.6g}."]
    # 2. nel 2012 valore a prezzi 2012 = valore corrente
    q = pan[pan["anno"] == 2012]
    r += [f"2. Anno base 2012: |K_fine_2012 − K_fine_corrente| massimo {float((q['K_fine_2012'] - q['K_fine_corrente']).abs().max()):.6g}."]
    # 3. identità di accumulazione a prezzi 2012
    g = pan.groupby(["tipo", "anno"])[["K_inizio_2012", "altre_variazioni_2012"]].sum()
    g["rel"] = g["altre_variazioni_2012"] / g["K_inizio_2012"]
    r += [f"3. Identità K_fine − K_inizio − I + D a prezzi 2012 (altre variazioni), aggregata per tipo: massimo |rel| {g['rel'].abs().max():.4%} "
          f"(tipo {g['rel'].abs().idxmax()[0]}, anno {g['rel'].abs().idxmax()[1]})."]
    gc = pan.groupby(["tipo", "anno"])[["K_inizio_corrente", "rivalutazioni_e_altre_variazioni_corrente"]].sum()
    gc["rel"] = gc["rivalutazioni_e_altre_variazioni_corrente"] / gc["K_inizio_corrente"]
    r += [f"4. Stessa identità a costo corrente (rivalutazioni + altre variazioni): da {gc['rel'].min():.2%} a {gc['rel'].max():.2%} dello stock iniziale per tipo e anno."]
    r += [f"5. Produzione: {prod['industria_io'].nunique()} industrie × {prod['anno'].nunique()} anni; "
          f"nel 2012 x_2012 = x_corrente_make (scarto massimo {float((prod[prod.anno == 2012]['x_2012'] - prod[prod.anno == 2012]['x_corrente_make']).abs().max()):.6g}); "
          f"x_corrente_make − x_corrente_use (arrotondamenti delle tavole BEA): massimo {float((prod['x_corrente_make'] - prod['x_corrente_use']).abs().max()):.6g}."]
    r += ["", "## Altre variazioni a prezzi 2012 per tipo e anno (quota dello stock iniziale)", "",
          "| tipo | " + " | ".join(str(a) for a in ANNI) + " |", "|---|" + "---:|" * len(ANNI)]
    for t in ("E", "S", "N", "R"):
        r.append(f"| {t} | " + " | ".join(f"{g.at[(t, a), 'rel']:.3%}" for a in ANNI) + " |")
    r += ["", "## Rivalutazioni e altre variazioni a costo corrente per tipo e anno (quota dello stock iniziale)", "",
          "| tipo | " + " | ".join(str(a) for a in ANNI) + " |", "|---|" + "---:|" * len(ANNI)]
    for t in ("E", "S", "N", "R"):
        r.append(f"| {t} | " + " | ".join(f"{gc.at[(t, a), 'rel']:.2%}" for a in ANNI) + " |")
    return "\n".join(r) + "\n"


def manifest(cartella: Path, cfg: Configurazione, esclusi: list[dict], scelte: dict[str, Path], codice: dict) -> dict:
    file = {}
    for f in sorted(cartella.rglob("*")):
        if f.is_file() and f.name != "MANIFEST.json":
            file[f.relative_to(cartella).as_posix()] = {"bytes": f.stat().st_size, "sha256": sha256_file(f)}
    return {
        "creato_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "codice": codice, "ambiente": ambiente(),
        "release_dati": {r.id: {"percorso": r.percorso, "sha256_manifest": r.sha256_manifest} for r in cfg.release.values()},
        "esecuzioni_incluse": {k: v.name for k, v in sorted(scelte.items())},
        "file_esclusi_per_dimensione": esclusi, "file": file,
    }


def genera(cfg: Configurazione, cartella: Path | None = None, includi_non_ufficiali: bool = False, test: bool = True) -> Path:
    radice = Path(__file__).resolve().parents[2]
    codice = stato_git(radice)   # stato del codice PRIMA di scrivere il pacchetto (i file generati non sono ancora registrati)
    codice["nota"] = "stato di git all'avvio del comando pacchetto"
    cartella = Path(cartella) if cartella else radice / "condivisione"
    for sotto in ("dati", "modello_E6", "risultati"):
        if (cartella / sotto).exists():
            shutil.rmtree(cartella / sotto)
    dati, mod = cartella / "dati", cartella / "modello_E6"
    pan, elem = capitale(cfg)
    _csv(pan, dati / "capitale_industria_tipo_2008_2019.csv")
    _csv(elem, dati / "capitale_serie_elementari_2008_2019.csv")
    prod = produzione_lavoro(cfg)
    _csv(prod, dati / "produzione_lavoro_2008_2019.csv")
    _csv(scorte_comparti(cfg), dati / "scorte_comparti_2007_2019.csv")
    _csv(g17(cfg), dati / "g17_capacita_utilizzo_1997_2019.csv")
    shutil.copy2(CONCORDANZA, dati / "concordanza_fixed_assets_io.csv")
    P = costruisci(cfg)
    _csv(mappatura(cfg, P), dati / "mappatura_71_industrie.csv")
    parametri_e6(cfg, mod)
    (cartella / "controlli.md").write_text(controlli(pan, elem, prod), encoding="utf-8")
    scelte = esecuzioni_ufficiali(radice / "runs", includi_non_ufficiali)
    esclusi = copia_risultati(scelte, cartella / "risultati")
    if test:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=radice, capture_output=True, text=True)
        (cartella / "esito_test.txt").write_text(r.stdout[-20000:] + r.stderr[-5000:], encoding="utf-8")
    m = manifest(cartella, cfg, esclusi, scelte, codice)
    (cartella / "MANIFEST.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    return cartella


def zip_dati(cfg: Configurazione, destinazione: Path) -> tuple[Path, str]:
    """Zip dei soli file dell'archivio letti dal modello, con i MANIFEST_RELEASE.json e le NOTE delle release.

    Estratto in una cartella X e con DATI_ECONOMICI=X, la verifica ordinaria (`verifica-dati`) passa; la verifica completa
    no, perché lo zip non contiene i file delle release che il modello non legge.
    """
    destinazione = Path(destinazione)
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destinazione, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for r in cfg.release.values():
            base = cfg.radice / r.percorso
            for nome in (MANIFEST, "NOTE.md"):
                if (base / nome).is_file():
                    z.write(base / nome, f"dati_economici/{r.percorso}/{nome}")
        for v in cfg.file:
            z.write(percorso_dati(cfg, v.release, v.percorso), f"dati_economici/{cfg.release[v.release].percorso}/{v.percorso}")
    h = hashlib.sha256(destinazione.read_bytes()).hexdigest()
    return destinazione, h
