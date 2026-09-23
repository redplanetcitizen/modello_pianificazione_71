"""Previsori preliminari (benchmark) per serie annuali, non anticipativi: usano solo valori con anno ≤ τ.

Metodi (tutti sui livelli y_t, con crescita moltiplicativa dove i livelli sono positivi):
  persistenza        ŷ_{τ+h} = y_τ
  ultimo_tasso       ŷ_{τ+h} = y_τ · (y_τ / y_{τ−1})^h
  media_mobile_k     ŷ_{τ+h} = y_τ · (1 + ḡ_k)^h, ḡ_k media dei tassi di crescita degli ultimi k anni
  smorzamento_a      ŷ_{τ+h} = y_τ · (1 + g̃)^h, g̃ media esponenziale dei tassi (parametro a)
  trend_mobile_k     retta su log y degli ultimi k anni, estrapolata
  trend_espandente   retta su log y su tutta la storia disponibile (dall'anno `inizio`)
Se la serie ha valori ≤ 0 nella finestra usata, il metodo ricade sulla persistenza (nessuna crescita moltiplicativa).
La selezione del metodo (`seleziona`) usa solo errori di previsioni a un passo fatte a origini s < τ con obiettivo ≤ τ.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

METODI = ("persistenza", "ultimo_tasso", "media_mobile_3", "media_mobile_5", "smorzamento_0.5",
          "trend_mobile_5", "trend_mobile_8", "trend_espandente")


def _positiva(v: np.ndarray) -> bool:
    return bool(np.all(np.isfinite(v)) and np.all(v > 0))


def prevedi(serie: pd.Series, tau: int, H: int, metodo: str = "persistenza", inizio: int | None = None) -> pd.Series:
    """Previsione per τ+1..τ+H dalla serie (indice: anni) usando solo anni ≤ τ."""
    s = serie.dropna()
    s = s[s.index <= tau].sort_index()
    if inizio is not None:
        s = s[s.index >= inizio]
    if len(s) == 0:
        raise ValueError("serie vuota all'origine")
    y_tau = float(s.iloc[-1])
    anni = [tau + h for h in range(1, H + 1)]
    h = np.arange(1, H + 1, dtype=float)
    pers = pd.Series(y_tau, index=anni)
    if metodo == "persistenza" or len(s) < 2:
        return pers
    if metodo == "ultimo_tasso":
        v = s.iloc[-2:].to_numpy(float)
        return pd.Series(y_tau * (v[1] / v[0]) ** h, index=anni) if _positiva(v) else pers
    if metodo.startswith("media_mobile_"):
        k = int(metodo.split("_")[-1])
        v = s.iloc[-(k + 1):].to_numpy(float)
        if not _positiva(v) or len(v) < 2:
            return pers
        g = np.mean(v[1:] / v[:-1] - 1)
        return pd.Series(y_tau * (1 + g) ** h, index=anni)
    if metodo.startswith("smorzamento_"):
        a = float(metodo.split("_")[-1])
        v = s.to_numpy(float)
        if not _positiva(v):
            return pers
        tassi = v[1:] / v[:-1] - 1
        g = tassi[0]
        for r in tassi[1:]:
            g = a * r + (1 - a) * g
        return pd.Series(y_tau * (1 + g) ** h, index=anni)
    if metodo.startswith("trend_mobile_") or metodo == "trend_espandente":
        v = s.to_numpy(float) if metodo == "trend_espandente" else s.iloc[-int(metodo.split("_")[-1]):].to_numpy(float)
        t = np.arange(len(v), dtype=float)
        if not _positiva(v) or len(v) < 3:
            return pers
        b = np.polyfit(t, np.log(v), 1)
        # livello ancorato all'ultimo valore osservato, pendenza dal trend
        return pd.Series(y_tau * np.exp(b[0] * h), index=anni)
    raise ValueError(f"metodo sconosciuto: {metodo}")


def errori_validazione(serie: pd.Series, tau: int, metodi=METODI, min_storia: int = 4, inizio: int | None = None) -> pd.Series:
    """MAE delle previsioni a un passo fatte alle origini s ∈ [primo+min_storia, τ−1] con obiettivo s+1 ≤ τ."""
    s = serie.dropna()
    s = s[s.index <= tau].sort_index()
    if inizio is not None:
        s = s[s.index >= inizio]
    origini = [o for o in s.index if o + 1 <= tau and (o - int(s.index[0])) >= min_storia]
    out = {}
    for m in metodi:
        err = []
        for o in origini:
            try:
                p = prevedi(s, o, 1, m)
                err.append(abs(float(p.iloc[0]) - float(s[o + 1])))
            except ValueError:
                continue
        out[m] = float(np.mean(err)) if err else np.inf
    return pd.Series(out)


def seleziona(serie: pd.Series, tau: int, metodi=METODI, inizio: int | None = None) -> str:
    """Metodo con MAE di validazione minimo; a parità (o senza storia) la persistenza."""
    e = errori_validazione(serie, tau, metodi, inizio=inizio)
    if not np.isfinite(e.min()) or e.min() >= e.get("persistenza", np.inf) * (1 - 1e-9):
        return "persistenza"
    return str(e.idxmin())


def prevedi_selezionando(serie: pd.Series, tau: int, H: int, metodi=METODI, inizio: int | None = None) -> tuple[pd.Series, str]:
    m = seleziona(serie, tau, metodi, inizio=inizio)
    return prevedi(serie, tau, H, m, inizio=inizio), m


def prevedi_quote(tabella: pd.DataFrame, tau: int, H: int, metodo_totale: str | None = None,
                  metodo_quote: str = "persistenza", inizio: int | None = None) -> tuple[pd.DataFrame, dict]:
    """Previsione di una tabella anni × voci come totale × quote: quote ≥ 0 a somma 1, totale con metodo selezionato."""
    tab = tabella[tabella.index <= tau].sort_index()
    tot = tab.sum(axis=1)
    if metodo_totale is None:
        tot_prev, metodo_totale = prevedi_selezionando(tot, tau, H, inizio=inizio)
    else:
        tot_prev = prevedi(tot, tau, H, metodo_totale, inizio=inizio)
    quote = tab.div(tot.where(tot != 0), axis=0).fillna(0.0).clip(lower=0)
    if metodo_quote == "persistenza":
        q = quote.iloc[-1]
        qp = pd.DataFrame([q.values] * H, index=tot_prev.index, columns=quote.columns)
    else:  # trend mobile sulle quote, poi normalizzazione
        qp = pd.DataFrame({c: prevedi(quote[c].where(quote[c] > 0), tau, H, metodo_quote) if (quote[c] > 0).any()
                           else pd.Series(0.0, index=tot_prev.index) for c in quote.columns})
        qp = qp.clip(lower=0)
    qp = qp.div(qp.sum(axis=1).where(qp.sum(axis=1) > 0), axis=0).fillna(0.0)
    return qp.mul(tot_prev, axis=0), {"totale": metodo_totale, "quote": metodo_quote}
