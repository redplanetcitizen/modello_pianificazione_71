# Passo D — modello dinamico 2012–2016: note sui risultati

Aggiornato il 22/09/2026. Esecuzione ufficiale sul computer (commit `2725bd8`), replicata in cloud:

| Esecuzione | Contenuto |
|---|---|
| `M71-D0-controllo-osservato` | Vincoli del modello valutati al punto osservato (specifica §6) |
| `M71-D1-O4-distanza` | O4: traiettoria ammissibile più vicina a quella osservata |
| `M71-D2-obiettivi` | O1, O2, O3 (calibrazione variante) e O1 (calibrazione base) |
| `M71-D3-sensibilita` | O1 con 13 varianti di vincoli e parametri |

Codice: `dati_modello.py`, `modello.py`, `controllo_osservato.py`, `passo_d.py`; comando `python -m pianificazione71 d` (≈ 140 s). Unità: miliardi di dollari 2012. LP di circa 1,5·10⁴ variabili, risolto con HiGHS 1.15.1; tutte le esecuzioni hanno stato Optimal.

**Replica computer / cloud.** Sono stati confrontati 131 file di output, escluso `esecuzione.json`. L'esito:

- 66 file hanno impronta SHA-256 identica;
- 65 differiscono solo nelle ultime cifre dei numeri, per l'aritmetica in virgola mobile. La differenza massima è 1e-6 in valore assoluto e 2,1e-7 in valore relativo;
- le colonne di testo, gli stati del solver e i vincoli attivi coincidono;
- i valori degli obiettivi coincidono fino alla 12ª cifra significativa.

Cartelle sul computer: `20260922-191936_M71-D0`, `…191936_M71-D1`, `…191946_M71-D2`, `…192006_M71-D3`.

## Calibrazione della capacità: opzione (a)

κ_j calibrato sul 2012; per le industrie coperte dalla Fed G.17 si aggiunge una deriva θ_j stimata sul rapporto tra capacità G.17 e K^cap (verifica fuori campione in C6: errore sull'utilizzo 2015–16 da 5,0/7,4 a 2,9/5,0 punti). Fuori dalla copertura G.17 θ = 0.

## D0 — il punto osservato rispetta i vincoli?

| Vincolo | Calibrazione base (H9: u = 1; H13: σ 2012) | Variante (H9b: u = 0,772; H13b: σ × 0,85) |
|---|---|---|
| Bilanci materiali (residuo aggregato) | −9,6…+5,4 mld l'anno; somma dei residui negativi −17…−31 mld (≈ 0,1% della produzione) | identico |
| Capacità: industrie oltre il limite | 0 / 23 / 26 / 21 / 24 (2012–16); massimo 1,57 (441, 2016) | 0 / 1 / 0 / 2 / 1; massimo 1,21 (441, 2016) |
| Scorte minime violate (comparti) | 0 / 1 / 4 / 3 / 4 | 0 in tutti gli anni |
| Lavoro, tetto delle importazioni | pari a 1 per costruzione | idem |
| Bande delle importazioni (ε = 10%) | 0 violazioni | 0 violazioni |

Tutte le violazioni di capacità della base riguardano industrie **fuori** dalla copertura G.17 (commercio, finanza, servizi). Con u = 1 nel 2012, ogni crescita della produzione superiore a quella di K^cap diventa infattibile: H9 non è compatibile con i dati osservati. Nella variante le violazioni residue sono 441 (commercio auto, 2015–16), 525 (fondi, 2015) e HS (abitazioni, 2013, 1,006).

**Variante adottata (approvata il 22/09):**

- **H9b.** u_2012 = 0,772 per le industrie private fuori dalla copertura G.17, escluso HS: è l'utilizzo 2012 dell'industria totale G.17. Implica un margine di capacità iniziale del 30% (1/0,772 − 1) nei servizi. Il valore è preso in prestito dall'industria e non è misurato nei servizi.
- **H13b.** σ_z × 0,85: minimo del rapporto scorte/produzione pari all'85% del livello 2012.

Resta separata la questione se il vincolo di capacità nei servizi abbia un contenuto empirico: si veda la sensibilità `senza_capacita` più sotto.

## D1 — O4, distanza dalla traiettoria osservata

| Calibrazione | Distanza L1 normalizzata |
|---|---|
| Base | 0,3737 |
| Variante | 0,0129 |

Con la variante la traiettoria osservata è quasi ammissibile. Gli scarti residui sono:

- il residuo materiale, pari a 34–121 mld;
- una parte della variazione delle scorte;
- l'attrezzatura 2012, che torna al valore osservato (980).

O4 include ora anche l'investimento residenziale R. Senza R, il modello spostava l'edilizia abitativa nel residuo materiale.

## D2 — obiettivi (calibrazione variante)

Valori osservati di riferimento, 2012 → 2016:

- produzione 29.232 → 32.016;
- consumo 11.065 → 12.190 (γ 2016 = 1,102; consumo cumulato 57.837);
- investimento E 980 → 1.160, S 461 → 495, N 656 → 846, R 432 → 602.

| Caso | γ 2016 | Consumo cumulato | Anni con investimento netto < 0 | Osservazioni |
|---|---|---|---|---|
| O1 (max Σ γ_t) | 1,191 | 62.196 | 3 | R 1.301/1.784 nel 2012–13 poi 0; N quasi nullo nel 2012–13; disinvestimento netto −424 nel 2014 |
| O2 (obiettivi per prodotto) | 1,236 (consumo totale / 2012) | 64.728 | 4 | Profilo dell'investimento simile a O1; ricomposizione del consumo verso i prodotti con capacità libera |
| O3 (max Σ w K_T+1, γ ≥ 1) | 1,000 | 55.327 | 1 | **Degenere**: N ≈ 4.900–5.000 nel 2015–16, consumo fermo al pavimento |
| O1, calibrazione base | 1,170 | 60.348 | 2 | Stessa forma, meno margine di capacità |

**Lettura.**

1. **Fattibilità.** Tutti i casi sono ammissibili e i bilanci chiudono con residuo materiale nullo o quasi.
2. **Qualità economica.** O1 supera il consumo osservato di circa il 7,5% cumulato perché:
   - usa il margine di capacità del 30% ipotizzato nei servizi (H9b);
   - consuma capitale netto per tre anni, con il solo vincolo di non depauperamento a fine orizzonte;
   - ha previsione perfetta e non sostiene costi di aggiustamento.

   Il picco di R nel 2012–13 dipende dalla composizione fissa del consumo: l'abitazione (HS) è il primo collo di bottiglia e il modello lo scioglie subito. Questi risultati non indicano un vantaggio del piano sull'economia osservata. Indicano che cosa i vincoli dichiarati permettono.
3. **O3 è mal posto.** Con i pesi da costo d'uso, w_N (proprietà intellettuale, δ alto) è elevato e il modello concentra l'investimento in N negli ultimi due anni per massimizzare lo stock terminale ponderato. Riformulazioni possibili, da scegliere:
   - (i) O1 con crescita terminale minima per tipo (già provato come sensibilità);
   - (ii) massimizzazione della crescita minima di K^cap tra le industrie (max-min);
   - (iii) pesi a valore dello stock anziché a costo d'uso.

## D3 — sensibilità (O1, variante)

| Caso | γ 2016 | Consumo cumulato | Anni con inv. netto < 0 | Inv. netto minimo |
|---|---|---|---|---|
| Riferimento | 1,191 | 62.196 | 3 | −424 |
| Capacità Leontief per tipo | 1,185 | 61.844 | 3 | −288 |
| Deriva servizi −1,8%/anno | 1,144 | 61.104 | 2 | −737 |
| Senza deriva G.17 | 1,192 | 62.232 | 3 | −432 |
| Bande importazioni 0 | 1,177 | 61.746 | 3 | −298 |
| Bande importazioni 25% | 1,202 | 62.545 | 3 | −530 |
| Lavoro +2% | 1,223 | 63.249 | 2 | −467 |
| Crescita terminale +5% | 1,176 | 61.705 | 2 | −256 |
| β = 0,97 | 1,191 | 62.196 | 3 | −413 |
| Senza capacità | 1,038 | 64.705 | 3 | −2.094 |
| Senza condizione terminale | 1,252 | 63.506 | 4 | −1.814 |
| Senza condizione terminale sulle scorte | 1,194 | 62.323 | 3 | −443 |
| Senza massimo delle scorte | 1,192 | 62.240 | 3 | −561 |

**Osservazioni.**

- Il lavoro (vincolante in tutti gli anni) e la capacità (156 vincoli attivi su circa 350 industria-anno in O1) sono i vincoli che contano.
- Senza capacità il consumo cumulato sale del 4%. Il modello anticipa il consumo e lascia azzerare l'investimento lordo: l'ammortamento non viene reintegrato. Ne segue che la dinamica dell'accumulazione è determinata dal vincolo di capacità.
- La condizione terminale limita il disinvestimento solo in aggregato: senza di essa si hanno 4 anni negativi.
- Il tipo di vincolo di capacità (lineare o Leontief), la deriva G.17 e β hanno effetti piccoli, sotto l'1%.
- Con O1 lineare nel consumo β incide poco perché il consumo tra anni è quasi un sostituto perfetto.

## Nuove ipotesi e correzioni introdotte nel passo D

- **H13c.** Massimo del rapporto scorte/produzione a 1,20·σ (la banda 0,85–1,20 contiene tutti i rapporti osservati 2012–16, massimo 1,164) e scorte finali ≥ scorte 2011. Senza questi vincoli il modello usava le scorte come deposito gratuito.
- **HS** è escluso dalla capacità aggregata delle industrie e trattato col proprio vincolo sul capitale R.
- Il vincolo terminale sulle scorte e il massimo delle scorte hanno effetti piccoli su γ (D3), ma eliminano oscillazioni prive di significato economico.

## D4 — O3 riformulato: capitale terminale a valore dello stock

Esecuzione `M71-D4-O3-valore` (comando `python -m pianificazione71 d4`). Si confrontano tre casi: O3 a valore, O3 a costo d'uso (come in D2) e O1. Lo stock 2017 è ricostruito con l'identità di accumulazione del modello.

| Caso | γ 2016 | Consumo cumulato | K_2017 E | K_2017 N | K_2017 S | K_2017 R |
|---|---|---|---|---|---|---|
| Stock 2012 | — | — | 5.483 | 2.308 | 12.035 | 16.321 |
| O3 a valore | 1,000 | 55.327 | 14.957 | 4.264 | 12.035 | 16.321 |
| O3 a costo d'uso | 1,000 | 55.327 | 5.483 | 8.379 | 12.035 | 16.321 |
| O1 | 1,191 | 62.196 | 5.483 | 2.308 | 12.035 | 17.367 |

**Esito: la riformulazione elimina la preferenza per N ma non la degenerazione.**

- **Concentrazione nel tempo.** L'investimento E è di 4.991 mld nel 2015 e di 5.311 nel 2016; N vale 3.155 nel 2016. Il consumo resta al pavimento (γ = 1) e le scorte scendono di 1.220 nell'ultimo anno.
- **Concentrazione per industria.** Lo stock E dell'industria 513 (telecomunicazioni) passa da 318 a 8.624 mld. Lo stock N dell'agricoltura (111CA) passa da circa 0 a 3.145. Nel frattempo 92 stock industria-tipo su 196 scendono sotto l'80% del livello 2012.
- **Causa.** L'obiettivo è lineare nello stock finale e pesa allo stesso modo un dollaro di capitale in qualunque industria. La condizione terminale vincola solo i totali per tipo. Il modello quindi investe il più tardi possibile, per non perdere nulla in ammortamento, e nelle industrie in cui un dollaro di capitale costa meno risorse. Non c'è alcun legame tra il capitale accumulato e la capacità che servirà dopo il 2016.
- **Condizione terminale.** S e R restano esattamente al livello 2012 in tutti i casi: il vincolo di non depauperamento è attivo.

**Correttivi possibili (da decidere):**

- (a) non depauperamento per industria e tipo, K_{j,a,2017} ≥ K_{j,a,2012}, oppure una soglia più bassa;
- (b) limiti alla variazione annua dell'investimento per tipo;
- (c) O3 come vincolo dentro O1 (opzione i).

Senza (a), nessun obiettivo sullo stock finale ha una ripartizione per industria economicamente interpretabile.

## D5 — grafici modello / osservato

Esecuzione `M71-D5-grafici` (comando `python -m pianificazione71 d5`). Produce tre figure e le relative serie (`serie.csv`, `serie_confronto.csv`):

1. produzione lorda e consumo privato;
2. investimento fisso per tipo (E, S, N, R);
3. stock netto di inizio anno per tipo, 2012–2017.

Casi rappresentati: O1, O2, O3 a valore, O4 e l'osservato, con la calibrazione adottata. Il perimetro del capitale è lo stesso per modello e osservato. Lo stock del modello è ricostruito con l'identità di accumulazione; quello osservato è lo stock netto Fixed Assets a prezzi 2012.

## Aperto per il passo E

- Correttivo per O3 (D4): non depauperamento per industria, limiti di variazione dell'investimento, oppure O3 come vincolo in O1.
- Sensibilità di H9b: u fuori da G.17 per gruppo di industrie, oppure u stimato dal massimo storico di x/K^cap.
- Costi di aggiustamento o limiti alla variazione annua dell'investimento per tipo, per attenuare il profilo a scatti.
- Catena del surplus con prezzi ombra (bilanci, capacità, lavoro).
- Diagnostica di fattibilità e confronto sistematico con i dati osservati a prezzi 2012.
