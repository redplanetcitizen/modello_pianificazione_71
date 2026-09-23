"""Audit dell'informazione e classificazione delle variabili per M71-E6-predittivo.

Ogni riga: nome, definizione, fonte, unità, frequenza, periodo disponibile nell'archivio, data massima usata nella
pipeline, data alla quale l'informazione sarebbe stata disponibile (pubblicazione BEA/Fed/BLS, ordine di grandezza),
ruolo nel modello, anticipazione informativa residua. I dati sono revisionati ex post (vintage 2025-2026): ogni
esperimento è una pseudo-previsione fuori campione, non una previsione real-time.
"""
from __future__ import annotations

import pandas as pd

from .storico import ANNO_MAX, ANNO_MIN

AUDIT = [
    # nome, definizione, fonte, unità, frequenza, periodo disponibile, data massima usata, disponibilità reale, ruolo, anticipazione
    ("B_t", "coefficienti di uso intermedio per unità di produzione (Use/Make Summary, prezzi 2012)", "BEA IO Summary before redefinitions (release 2025-09)", "adimensionale", "annuale", f"{ANNO_MIN}-2024", "τ", "tavole annuali t pubblicate ~t+1 (fine), riviste per ~3 anni", "parametro strutturale (persistenza di B_τ)", "nessuna: valori revisionati (pseudo-real-time)"),
    ("D_t", "quote di mercato industria × prodotto (Make)", "BEA IO Summary", "adimensionale", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "parametro strutturale (persistenza)", "revisioni ex post"),
    ("x_speciali", "produzione dovuta a Used/Other", "BEA IO Summary", "mld $ 2012", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "parametro strutturale (persistenza)", "revisioni ex post"),
    ("consumo per prodotto", "F010 a prezzi 2012", "BEA IO Summary + GDPbyIndustry tab. 18", "mld $ 2012", "annuale", f"{ANNO_MIN}-2024", "τ (previsto oltre)", "come B_t", "esogena prevista: obiettivi O2 = ĉ_{c,t|τ} (totale previsto × quote a τ)", "nessuna (previsioni da dati ≤ τ)"),
    ("obiettivi O2", "ĉ_{c,t|τ}", "derivati", "mld $ 2012", "annuale", "-", "τ", "-", "esogena prevista", "nessuna"),
    ("FTE per industria", "occupati equivalenti a tempo pieno (NIPA 6.5D)", "BEA NIPA T60500D (API 2026-09-23)", "migliaia", "annuale", "1998-2024", "τ", "NIPA annuale pubblicato ~t+1 (luglio), rivisto", "esogena prevista (L_t) e parametro (ℓ_j, coefficienti previsti)", "revisioni ex post"),
    ("importazioni totali", "somma di −F050 (voci negative)", "BEA IO Summary", "mld $ 2012", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "esogena prevista (tetto M̄_t)", "revisioni ex post"),
    ("quote d'importazione μ", "importazioni / usi per prodotto", "derivate", "adimensionale", "annuale", "-", "τ", "-", "parametro strutturale (persistenza di μ_τ)", "nessuna"),
    ("spesa pubblica", "F06C/S/E/N, F07*, F10* (consumi e investimenti pubblici)", "BEA IO Summary", "mld $ 2012", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "esogena prevista (totale × quote a τ)", "revisioni ex post"),
    ("investimento pubblico", "compreso nelle colonne F06E/N, F07E/N, F10E/N", "BEA IO Summary", "mld $ 2012", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "esogena prevista", "revisioni ex post"),
    ("esportazioni", "F040", "BEA IO Summary", "mld $ 2012", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "esogena prevista", "revisioni ex post"),
    ("componenti esogene di F050", "voci positive di F050", "BEA IO Summary", "mld $ 2012", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "esogena prevista", "revisioni ex post"),
    ("stock di capitale K", "stock netto di fine anno per industria FA × tipo, a prezzi 2012 (serie elementari)", "BEA Fixed Assets detailnonres_stk1/2, detailresidential", "mld $ 2012", "annuale", "1947-2024 (usato 1996-2019)", "τ (fine anno)", "FA annuali pubblicati ~t+1 (agosto-settembre), rivisti", "stato noto a τ (K0 = fine τ); osservato oltre τ solo per la valutazione", "revisioni ex post"),
    ("investimento per industria e tipo", "FA detailnonres_inv1/2, residenziale", "BEA Fixed Assets", "mld $ 2012", "annuale", "1947-2024", "τ", "come K", "stato noto (I_τ per la gradualità); previsto per P0/P2; endogeno nel modello", "revisioni ex post"),
    ("tassi di deprezzamento δ", "D/K medio degli ultimi 5 anni ≤ τ", "BEA Fixed Assets dep1/2", "annuo", "annuale", "1947-2024", "τ", "come K", "parametro strutturale", "nessuna"),
    ("Φ per tipo", "composizione per prodotto dell'investimento (GRAS su Use F02*, bridge PEQ, dettaglio FA)", "BEA IO Summary + PEQ bridge + FA", "prodotti per unità di I", "annuale", f"{ANNO_MIN}-2024", "τ", "come B_t", "parametro strutturale (persistenza di Φ_τ)", "revisioni ex post"),
    ("pesi di capacità w", "costi d'uso (r di gruppo KLEMS + δ) calibrati nell'anno τ", "BEA-BLS KLEMS 1997-2024 (release 2026-09-18)", "adimensionale", "annuale", "1997-2024", "τ", "KLEMS pubblicato ~t+1/t+2", "parametro strutturale", "revisioni ex post"),
    ("coefficienti di capacità κ, θ (G.17)", "κ da K^cap_τ, u_τ, x_τ; θ dalla deriva capacità G.17 / K^cap su [τ−5, τ]", "Fed G.17 capacity, utilization (release 2026-09-18)", "adimensionale", "mensile → media annua", "1967/1972-2026 (usato 1997-2019)", "τ", "G.17 mensile con ritardo ~1 mese, rivisto annualmente", "stato noto / parametro strutturale", "revisioni ex post"),
    ("tendenze non-G.17 (inviluppo)", "log r = α + g t + e su [1997, τ], massimo residuo", "derivate", "adimensionale", "annuale", "-", "τ", "-", "parametro strutturale (H9c non anticipativa)", "nessuna: stimata solo su dati ≤ τ"),
    ("scorte per comparto", "stock di fine anno IV trim., 11 comparti, prezzi 2012 (5.8.5B, 5.8.9B)", "BEA NIPA T50805B, T50809B", "mld $ 2012", "trimestrale → fine anno", "1996Q4-2026Q2 (usato ≤ 2019)", "τ", "NIPA trimestrale ~t+1 mese", "stato noto (S0 = fine τ); previsto per P2/P0", "revisioni ex post"),
    ("rapporti scorte/produzione σ", "S_z,τ / Σ x_j,τ", "derivate", "adimensionale", "annuale", "-", "τ", "-", "parametro strutturale (persistenza)", "nessuna"),
    ("fattori terminali", "T1: L̂_{τ+H}/L_τ (FTE previsti), x̂_HS/x_HS; T2/T3: valore v = 1", "derivati da previsioni a τ", "adimensionale", "-", "-", "τ", "-", "chiusura terminale non anticipativa", "nessuna"),
    ("prezzi / valore dello stock", "stock in miliardi di dollari 2012: v = 1 (T2); nessun costo d'uso come valore", "-", "mld $ 2012", "-", "-", "-", "-", "chiusura T2/T3", "nessuna"),
    ("indici di prezzo (deflazione)", "indici della produzione lorda per industria, base 2012 = 1", "BEA GDPbyIndustry tab. 18", "indice", "annuale", "1997-2025", "τ (anno da deflazionare)", "pubblicati ~t+1", "convenzione di unità: prezzi 2012 anche per τ < 2012 (riscalatura, non informazione sui volumi)", "la base 2012 è una scelta di unità; le quantità reali di ogni anno usano solo il deflatore di quell'anno"),
]

COLONNE = ["nome", "definizione", "fonte", "unita", "frequenza", "periodo_disponibile", "data_massima_usata",
           "disponibilita_reale", "ruolo", "anticipazione"]

CLASSIFICAZIONE = {
    "stato_noto_a_tau": ["K0 (stock di fine τ)", "S0 (scorte di fine τ)", "I_prec (investimento di τ)", "capacità installata (κ da K^cap_τ, x_τ, u_τ)"],
    "parametro_strutturale": ["B_τ", "D_τ", "x_speciali_τ", "δ (media 5 anni)", "Φ_τ, φR_τ", "ℓ_j (coefficienti di lavoro, previsti per industria)",
                              "w (costi d'uso a τ)", "θ (deriva G.17 e tendenza inviluppo)", "σ_z", "ψ (composizione delle scorte)", "μ_c (quote d'importazione)"],
    "esogena_prevista": ["L_t (FTE totali)", "G_t (spesa e investimento pubblici)", "X_t (esportazioni)", "F⁺_t", "M̄_t (importazioni totali)",
                         "ĉ_{c,t|τ} (obiettivi O2)", "x̂_{j,t|τ} (tracking P2)", "Î_{a,t|τ}, Ŝ_{z,t|τ} (tracking P2 esteso)"],
    "endogena": ["x", "q", "c", "I_{j,a}", "K_{t+1}", "m", "S_z, ΔS_z", "r (residuo materiale)"],
}


def tabella_audit() -> pd.DataFrame:
    return pd.DataFrame(AUDIT, columns=COLONNE)


def classificazione_md() -> str:
    righe = ["| Categoria | Grandezze |", "|---|---|"]
    for k, v in CLASSIFICAZIONE.items():
        righe.append(f"| {k.replace('_', ' ')} | {'; '.join(v)} |")
    return "\n".join(righe)
