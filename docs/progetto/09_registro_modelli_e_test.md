# Registro dei modelli, dei test e delle modifiche

Aggiornato il 23/09/2026. Il documento raccoglie tutto il lavoro fatto sui modelli a 71 industrie, in modo che ogni variante si possa ritrovare e rieseguire. I dettagli dei risultati sono in:

- `06_passo_C_note.md`;
- `07_passo_D_note.md` (D0–D5);
- `08_passo_E_note.md` (E1–E7).

Le decisioni sono in `03_registro_decisioni.md`.

## 1. Codice, esecuzione, stato ufficiale

- **Repository:** `C:\Users\franc\Documents\GitHub\modello_pianificazione_71` (pacchetto `pianificazione71`, Python + HiGHS 1.15.1).
- **Archivio dati:** `C:\Users\franc\Documents\dati_economici`, con release congelate e verificate da SHA-256.
- **Esecuzione:** `.\.venv\Scripts\python.exe -m pianificazione71 <comando>`. Ogni comando crea un'esecuzione registrata in `runs/<data-ora>_<nome>/` con `esecuzione.json` (commit, ambiente, dati, parametri, impronte degli output).
- **Comandi disponibili:**
  - `verifica-dati`, `ambiente`, `controllo-solver`;
  - `c1` `c2` `c4` `c4b` `c5` `c6` `c7` `passo-c`;
  - `d` `d4` `d5`;
  - `e1` `e2` `e3` `e4` `e5` `e6` `e7`;
  - `predittivo` (comando unico del backtest M71-E6-predittivo, ~1,5 h), `predittivo --rapida`, `predittivo-rapporto <cartella>`, `predittivo-grafici <cartella>`;
  - `pacchetto` (cartella `condivisione/` per la revisione esterna), `zip-dati <file>` (zip dei soli file dell'archivio letti dal modello).

| Passo | Esecuzione ufficiale sul computer | Stato |
|---|---|---|
| B (infrastruttura) | commit `ea4f722` | ufficiale |
| C (dati) | commit `e1e5845`, `passo-c` | ufficiale, replicato in cloud (identico salvo 1e-10) |
| D (D0–D3) | commit `2725bd8`, `d` | ufficiale, replicato in cloud (differenze ≤ 2e-7 relative) |
| D4, D5, E1–E4 | commit del 22/09 sera (`D4-D5, E1-E7…`), esecuzioni sul computer in `runs/` | ufficiale |
| E6-predittivo | commit `4e16359`, esecuzione `20260923-072127` | ufficiale; replica in cloud con differenze di circa l'1% sugli indicatori delle formulazioni LP (ottimi multipli), graduatorie identiche (`11_predittivo_note.md`) |
| E5–E7 | da rieseguire sul computer dopo il commit del pacchetto di condivisione | in cloud |
| Pacchetto di condivisione | comando `pacchetto` (cartella `condivisione/`) e `zip-dati` | 23/09/2026 |

**Comandi per allineare il computer:**

```
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m pytest
git add .
git commit -m "D4-D5, E1-E7"
```

Poi, uno per volta: `d4`, `d5`, `e1`, `e2`, `e3`, `e4`, `e5`, `e6`, `e7`.

**Garanzia di recupero.** Tutte le estensioni introdotte dopo il passo D sono opzioni disattivate per default. Con le opzioni predefinite, `costruisci(cfg)` e `costruisci_e_risolvi` riproducono esattamente i parametri e le soluzioni del passo D. Verifiche fatte:

- parametri: differenza 0 su B, D, Φ, K0, δ, w, κ, θ, ℓ, σ, μ;
- O2 di E1 identico a O2 di D2.

## 2. Struttura del modello (`modello.py`)

- **Variabili per anno:** x (industrie), q (prodotti), m (importazioni), r (residuo), consumo (γ per O1/O3; c per prodotto per O2), I per industria e tipo (E, S, N; R per HS), K di inizio anno, scorte per comparto.
- **Vincoli:** bilancio materiale per prodotto; quote di mercato; capacità; accumulazione; scorte (minimo, massimo, terminale); lavoro; importazioni (tetto e bande); condizione terminale del capitale.
- **Obiettivi:**
  - O1: max Σ γ_t, paniere fisso;
  - O2: programmazione per obiettivi per prodotto, tratti (0,9 → 1), (0,1 → 0,5), (0,2 → 0,1), pesi = quote osservate;
  - O3: max stock finale;
  - O4: distanza L1 dall'osservato, solo diagnostica.

### Parametri (`dati_modello.costruisci(cfg, anni=2012-2016, inviluppo=False)`)

- **`anni`:** orizzonte, che deve contenere il 2012. La calibrazione (stock iniziale, κ, σ, base di θ) si fa sul primo anno; δ è la media sull'orizzonte; w resta al 2012.
- **`inviluppo=True`:** aggiunge `capacita_inviluppo` (H9c), calcolata sul 1997–2019.
- **Altri campi aggiunti:** `I_prec` (investimento dell'anno precedente l'orizzonte), `K_oss` (stock osservato di inizio anno, solo per il confronto), `g17` (industrie con dati G.17).

### Opzioni (`Opzioni`) e ipotesi

| Opzione | Default | Ipotesi | Introdotta in |
|---|---|---|---|
| `obiettivo` | "O1" | O1–O4 | D |
| `capacita`, `capacita_tipo` | True, "lineare" | H8 (lineare) / Leontief | D |
| `deriva`, `theta_non_g17` | True, 0 | calibrazione (a), deriva G.17 | D |
| `u_non_g17` | 1,0 | H9 (1), H9b (0,772 nel 2012; 0,734 nel 2010) | D |
| `capacita_non_g17` | "uniforme" | H9c: "inviluppo" / "inviluppo_tendenza" | E4 |
| `sigma_fattore`, `sigma_max_fattore` | 1,0; 1,20 | H13 / H13b (0,85); H13c | D |
| `terminale`, `crescita_terminale` | True, 0 | H17 mantenimento per tipo | D |
| `terminale_fattori` | None | H29: {gruppo: fattore} | E5 |
| `terminale_pesi` | "valore" | H29b/H29c "capacita" (scartate) | E7 |
| `terminale_scorte` | True | scorte finali ≥ iniziali | D |
| `lavoro_scala`, `import_scala`, `epsilon`, `bande_import` | 1, 1, 0,10, True | lavoro, estero | D |
| `beta`, `gamma_min` | 1, 1 | sconto, pavimento O3 | D |
| `pesi_o3` | "valore" | O3 a valore (D4) / "costo_uso" (D2) | D4 |
| `limite_var_inv` | None | H25a limite ±g | E1 |
| `penalita_var_inv`, `soglia_var_inv` | 0, 0,05 | H25b penalità a gradini | E1 |
| `tempi_costruzione`, `quota_primo_anno` | (), 0,5 | H26 | E1 |
| `regola_inv`, `regola_modo`, `regola_eps`, `regola_tratti` | None, "banda", 0,10, … | H28 funzione d'investimento | E3 |
| `elastico` | False | diagnostica di fattibilità | D |
| `tratti_o2`, `omega_h` | None | tratti di O2 e pesi per orizzonte (predittivo) | E6-predittivo |
| `penalita_var_inv_ind` | 0 | penalità L1 settoriale (industria × tipo) | E6-predittivo |
| `valore_terminale` | 0 | T2: + λ_K Σ K_{T+1} nell'obiettivo | E6-predittivo |
| `p2_lambda_c/x/inv/m/S`, `p2_pesi` | 1, 1, 0, 0, 0, "quote" | obiettivo "P2" (tracking L1) | E6-predittivo |
| `opzioni_highs`, `perturba_costi` | None, 0 | verifiche di stabilità | E6-predittivo |

## 3. Configurazioni nominate (per ritrovarle)

| Nome | Orizzonte | Opzioni |
|---|---|---|
| **O2-D** (passo D) | 2012–16 | `obiettivo="O2", u_non_g17=0.772, sigma_fattore=0.85` |
| **O2-D 2010–19** (E2) | 2010–19 | `obiettivo="O2", u_non_g17=0.734, sigma_fattore=0.85` |
| **O2 + penalità** (E1) | 2012–16 | O2-D + `penalita_var_inv=0.1` |
| **O2 + regola tasso costante** (E3) | 2010–19 | O2-D 2010–19 + `regola_inv={a: {"k": i_a}}`, i_a = tasso medio 2005–09 (E 0,163; S 0,044; N 0,284; R 0,041) |
| **O2 H9c** (E4) | entrambi | `obiettivo="O2", capacita_non_g17="inviluppo_tendenza", sigma_fattore=0.85`; parametri con `inviluppo=True` |
| **O2 tarato** (E5) | entrambi | O2 H9c + `terminale_fattori={"ESN": f_FTE, "R": f_HS}` (2012–16: 1,1006 e 1,0155; 2010–19: 1,1928 e 1,0529) |
| **O2 tarato + penalità** (E6, il più aderente finora) | entrambi | O2 tarato + `penalita_var_inv=0.1` |

## 4. Cronologia dei passi e delle modifiche

| Passo | Contenuto | Esito principale |
|---|---|---|
| A | Scheda di provenienza delle linee precedenti (411 commodity, 71 settori) | `05_linee_precedenti.md` |
| B | Infrastruttura: verifica dati, registro esecuzioni, test, solver | commit `ea4f722` |
| C1–C7 | Sistema prodotti–industrie, margini dell'investimento, Φ (GRAS), confronto 1997, capitale a prezzi 2012, capacità (κ, w, G.17, deriva), lavoro, scorte, estero | commit `e1e5845`; capacità: scelta l'opzione (a) |
| D0 | Vincoli al punto osservato | H9 incompatibile con i dati: H9b e H13b, approvate |
| D1 | O4 | 0,374 (base) → 0,013 (variante) |
| D2 | O1, O2, O3 | O1 +7,5% di consumo; O3 degenere (N concentrato alla fine) |
| D3 | Sensibilità O1 (13 casi) | contano capacità e lavoro |
| D4 | O3 a valore dello stock (decisione dell'utente) | ancora degenere: concentrazione per industria e alla fine |
| D5 | Grafici modello / osservato (linee e barre O2) | — |
| E1 | Gradualità su O2 (H25a, H25b, H26) | scarto sull'investimento da 64% a 26–32%; direzione ancora errata |
| E2 | Orizzonte 2010–2019, confronto sul 2012–16 (H27) | nessun avvicinamento; il modello non accumula (capacità libera 36% nel 2010) |
| E3 | Funzione d'investimento stimata sul 1998–2009 (H28) | a investimento osservato, consumo +6,2% (parte dovuta alla riallocazione) |
| E4 | Capacità fuori G.17 sull'inviluppo 1997–2019 (H9c) | O4 molto migliore; O2 quasi invariato. H9c adottata come standard |
| E5 | Condizione terminale tarata (H29) | solo la variante aggregata legata agli FTE lascia ammissibile l'osservato |
| E6 | H9c + H29 + gradualità | con la penalità, 2012–16: investimento 10%, stock 1,3%, consumo +7,4% |
| E7 | Terminale in servizi produttivi (H29b, H29c) | scartate: più lasche o aggirabili tra industrie; resta H29 a valore |
| E6-predittivo | Pipeline predittiva non anticipativa 2008–2019 (P0, P1, P2, P3; T1–T3; backtest a origine mobile; selezione annidata; stabilità) | nessuna formulazione LP batte i previsori semplici (P0, S = 0,72); E6 tradotto S = 2,1; vedi `11_predittivo_note.md` |

### Correzioni al codice dopo il passo D

- Parametrizzazione dell'orizzonte:
  - `indici_prezzo(…, anni)`;
  - `controllo_g17(…, base)` e `deriva_capacita(…, base)`, con nomi delle colonne invariati per la base 2012;
  - `costruisci(cfg, anni, inviluppo)`.
- `Risultato.grezzi`: valori e duali in memoria, non scritti su disco, così gli output del passo D restano identici.
- `controllo_osservato.controlla(…, capacita_non_g17)`, con correzione di una variabile sovrascritta.
- Moduli nuovi: `grafici.py` (D5), `passo_e1.py` … `passo_e7.py`, `capacita.inviluppo_capacita`.
- Dipendenza aggiunta: matplotlib.
- 23/09: il coefficiente del vincolo di capacità è calcolato da `modello.coefficiente_capacita` (stessa formula, spostata in una funzione), usato anche dal pacchetto di condivisione per esportare i coefficienti effettivi; E6 e i test del modello riprodotti identici.

## 5. Stato delle ipotesi di taratura

| Ipotesi | Stato |
|---|---|
| H9b | approvata (22/09); superata da H9c come standard dei nuovi test |
| H13b | approvata (22/09) |
| H9c (inviluppo con tendenza) | adottata (22/09) come standard |
| O3 a valore dello stock | adottato su richiesta; resta degenere |
| H29 (E+S+N ≥ crescita FTE, R ≥ crescita HS) | usata come taratura in E5–E7; conferma formale da dare |
| H25b (penalità) | usata in E6 come correttivo di gradualità; parametri (soglia 5%, p = 0,1) da dichiarare |
| H29b, H29c | scartate |

## 6. Aperto

- Distorsione di composizione nel 2010–19 (S sopra, E e N sotto): pavimento per industria e tipo accanto a H29.
- O2 quasi saturo (99% del punteggio massimo). Gli obiettivi pari al consumo osservato non mettono alla prova la scarsità: da rivedere dopo la taratura (stress test).
- Eccesso di consumo residuo circa +7%, dovuto alla riallocazione della produzione corrente: da scomporre per prodotto e industria.
- Esecuzione ufficiale sul computer di E5–E7.
- Passo F: rapporto finale in italiano.
