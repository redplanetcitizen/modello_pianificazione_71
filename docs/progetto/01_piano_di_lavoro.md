# Piano di lavoro

Aggiornato il 23/09/2026.

## Impostazione

- Il modello si scrive **da zero**. `csvplan.jl` è superato e non si usa come riferimento né per confronti.
- Per ora si lavora **a 71 industrie e 73 prodotti** (livello Summary BEA), periodo 2012–2016.
- Strumenti: Python + HiGHS (highspy 1.15.1). Repository `C:\Users\franc\Documents\GitHub\modello_pianificazione_71`; identificativi delle esecuzioni `M71-…`.
- Livelli di valutazione tenuti sempre separati:
  1. fattibilità dei bilanci;
  2. qualità economica della soluzione;
  3. capacità esplicativa rispetto all'economia osservata;
  4. questioni sociali e istituzionali (scelta degli obiettivi), fuori dalle verifiche tecniche; il loro effetto numerico resta una verifica tecnica.

## Fasi

| # | Fase | Stato |
|---|---|---|
| 0 | Archivio dati grezzi congelato con impronte SHA-256 | **Fatto** (vedi `02_dati_e_fonti.md`) |
| A | Scheda di provenienza delle linee precedenti (411 e 71) | **Fatto** (`05_linee_precedenti.md`) |
| B | Infrastruttura: repository, verifica dei dati, registro delle esecuzioni, test, controllo del solver | **Fatto**: sul computer 13 test superati, archivio integro, solver Optimal (Python 3.14, highspy 1.15.1, numpy 2.5.3, pandas 3.0.6); primo commit `ea4f722` |
| 1 | Specifica formale | **v0.2** (`04_specifica_modello.md`); verifiche aperte in `03_registro_decisioni.md`, sezione C |
| 2 | Sistema prodotti–industrie: B, D per anno, negativi e celle soppresse, deflazione, identità di bilancio | **Fatto** (C1, ufficiale) |
| 3 | Margini dell'investimento: perimetro, valutazione, totali (Fixed Assets contro Use F02) | **Fatto** (C2, ufficiale) |
| 4 | Stima di Φ per anno e tipo, con strutture iniziali alternative | **Fatto** (C4 e confronto 1997, C4b) |
| 5 | Capitale: stock, ammortamento, identità di accumulazione | **Fatto** (C5) |
| 6 | Rapporto capitale–capacità: κ, pesi, confronto G.17 (controllo esterno parziale) | **Fatto** (C6, C7); esecuzione ufficiale del passo C: commit `e1e5845`. Resta la scelta di calibrazione della capacità |
| 7 | Modello dinamico 2012–2016 a blocchi attivabili; controllo al punto osservato | **Fatto** (D0, D1; `07_passo_D_note.md`); esecuzione ufficiale commit `2725bd8`, replicata in cloud (differenze ≤ 2e-7 relative). H9b/H13b approvate il 22/09 |
| 8 | Obiettivi O1–O4 e sensibilità, con distribuzione annuale dell'investimento | **Fatto** (D2, D3; O3 riformulato a valore in D4, ancora degenere). Passo E: diagnostica di fattibilità, catena del surplus con prezzi ombra, confronto sistematico con l'osservato |
| E | Test: gradualità dell'investimento (E1), diagnostica, sensibilità, catena del surplus | **Fatto** (E1–E7, `08_passo_E_note.md`; esecuzioni ufficiali E1–E4, E5–E7 da rieseguire sul computer) |
| E-pred | Trasformazione di E6 in modello predittivo (M71-E6-predittivo): backtest 2008–2019 | **Fatto**: esecuzione ufficiale `20260923-072127` (`11_predittivo_note.md`, `rapporto_M71-E6-predittivo.md`) |
| R | Pacchetto per la revisione esterna (`condivisione/`, repository GitHub privato) | In corso (23/09/2026) |
| 9 | Rapporto finale sui quattro livelli, con tabella risolto / parziale / aperto | Da fare |

## Regole di riproducibilità

- I progetti leggono dall'archivio `dati_economici` senza copiare; la release usata è in configurazione e gli hash si verificano all'avvio.
- Ogni esecuzione registra modello, dati, parametri e output.
- Ogni raccordo o ipotesi è dichiarato con fonte e limiti.
