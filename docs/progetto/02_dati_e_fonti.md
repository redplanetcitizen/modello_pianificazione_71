# Dati e fonti

Aggiornato il 22/09/2026. Archivio: `C:\Users\franc\Documents\dati_economici` (inventario completo in `INVENTARIO_BEA.md` / `.csv`).

## Release congelate

| Release | Contenuto | Note |
|---|---|---|
| `bea/2025-09` | Make e Use Summary 71 (1997–2024), Fixed Assets Sez. 3 e 7, capital flow table 1997 e rettifiche, concordanze NAICS | Annual update BEA settembre 2025 |
| `bea/2026-09-22` | Fixed Assets dettagliati (74 industrie × tipo di bene: investimenti, stock, ammortamenti, tassi); zip Make/Use/Import (Summary 1997–2024, Detail 2007/2012/2017); raccordi PEQ e PCE | Stessa release BEA della precedente |
| `bea/2026-09-23` | API: 226 tabelle (NIPA, NI Underlying, Fixed Assets, GDP by Industry, Underlying GDP by Industry, Input-Output). 698 file | Manifest SHA-256 `C660B7AD…817DAF` |
| `bls/2026-09-18` | Account integrato BEA-BLS (KLEMS) 1997–2024 | Prezzi, lavoro, ore; dettaglio per asset da verificare |
| `fed_g17/2026-09-18` | Capacità e utilizzo (Fed G.17) | Solo manifattura, estrattivo, utility |

## Copertura per blocco del modello (71 industrie, 73 prodotti)

| Blocco | Fonte | Stato |
|---|---|---|
| Matrici tecniche annuali 2012–2016 | Make/Use/Import Summary | Complete |
| Consumo finale | Use (colonne F), raccordo PCE Summary | Complete |
| Investimento per prodotto | Use (F02E, F02N, F02S, F02R), raccordo PEQ Summary | Complete |
| Investimento, stock, ammortamenti per industria | Fixed Assets dettagliati | Complete (74 industrie) |
| Composizione dell'investimento Φ | **Da stimare**: RAS condizionato alla struttura iniziale, dopo verifica dei margini | Vedi sotto |
| Pesi del capitale per la capacità | KLEMS (costi d'uso per asset) | **Da verificare**; eventualmente tavole KLEMS a dettaglio ampliato |
| Scorte | NIPA 5.7.5B/5.7.6B (variazioni), 5.8.5B/5.8.6B/5.8.9B (stock trimestrali, deflatori) | 11 comparti, non 71 |
| Lavoro e prezzi | KLEMS; NIPA 6.4D, 6.5D | Complete (la 6.9, ore, non è più nell'API) |
| Capacità osservata | Fed G.17 | Parziale; controllo esterno solo parziale |

## Capital flow table: esito della verifica

- BEA non pubblica tavole dei flussi di capitale oltre il 1997 (anche 1992 e 1982). Il 1997 è a 180 prodotti × 123 industrie ed è una stima di ricerca.
- Non esiste una tavola a 402/411 prodotti. La Use Detail 2012 ha 402 righe di prodotto, compresi i codici speciali; il numero 411 non viene da questa release.
- Strada adottata: stima di Φ a 71 industrie per ogni anno con RAS. Il risultato dipende dalla struttura iniziale, dichiarata come ipotesi (H19). La tavola 1997 serve come confronto solo per attrezzature e strutture: precede la capitalizzazione della R&S.

## Raccordi da costruire

- 74 industrie Fixed Assets → 71 industrie I/O.
- Prezzi: tutto a prezzi 2012, deflazionando componente per componente. Le serie in dollari concatenati (2017) non si sommano tra componenti.
- Scorte: ripartizione dagli 11 comparti NIPA alle 71 industrie (ipotesi da dichiarare). La variazione NIPA include l'aggiustamento di valutazione: la differenza tra stock consecutivi non coincide con la variazione pubblicata.
- Valori negativi e celle "..." soppresse nella Use Summary: elenco e trattamento esplicito.
