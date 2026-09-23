# Scheda di provenienza delle linee di modello precedenti

22/09/2026. Passo A del piano di lavoro.

**Scopo.** Censire i modelli e i benchmark costruiti prima del nuovo modello a 71 industrie, con posizione, impronte e caratteristiche. Servono come termini di confronto metodologico. **Nessun risultato elencato qui va attribuito al nuovo modello, e nessuno va attribuito a `csvplan.jl` se non dove indicato.**

**Fonti della scheda:** README, `docs/*.md`, manifest e file `.sha256.txt` del progetto LP. Non ho eseguito il codice né verificato i risultati: la scheda riporta ciò che il progetto dichiara e le impronte degli archivi.

---

## 1. Posizione e ambiente

| Elemento | Valore |
|---|---|
| Progetto LP (motore e linee derivate) | `C:\Users\franc\Documents\Codex\2026-09-08\co` |
| Linguaggio e solver | Python (runtime incorporato di Codex), numpy 2.3.5, pandas 3.0.1, HiGHS via highspy 1.15.1 incluso in `vendor/` (`config/runtime.json`) |
| Programma storico `csvplan.jl` | `C:\Users\franc\Documents\Codex\2026-09-07\svi\work\phase3_factors\csvplan.jl`, SHA-256 `D9CE2255…43BD54`; immutato, non copiato |
| Dati della linea 411 | Asse delle commodity **USEEIO v2.0.1** (411 commodity, `inputs/data_contract.json`). La matrice A viene da `2026-09-07\svi\outputs\phase2_useeio\A_commodity_411.csv` (SHA-256 `DF82EBD2…FAEDBB`). È un'annata di dati diversa dall'archivio `dati_economici`: questo spiega il 411 contro i 402 prodotti della release BEA attuale |
| Dati della linea 71 | Tavole BEA Summary Make/Use in `inputs/bea_71_sources`: le stesse di `dati_economici\bea\2025-09` (16 impronte su 16 coincidenti, verificato il 22/09/2026) |

## 2. Linea a 411 commodity

Matrice tecnica fissa `A_t = A_2012` in tutte le varianti. Moduli sociale ed ecologico predisposti ma disattivati salvo LP-S.

| Modello | Contenuto | Stato dichiarato | Archivio (SHA-256) |
|---|---|---|---|
| LP statico 2012 | Bilanci materiali, anno singolo | Operativo e validato | in `phase0_lp411_benchmark_complete_2026-09-18.zip` (`0267F7FB…26A53B`) |
| LP-CS0 | 5 periodi; obiettivo = distanza assoluta ponderata dai riferimenti; scorte intertemporali; tetti alle importazioni; lavoro | Operativo e validato; è il benchmark del Capitolo 9 | idem |
| LP-CS1…CS9 | Scenari a un parametro. **CS9** (accelerazione dell'investimento pubblico, +5%) esiste ma è escluso dal report e dal Capitolo 9 | Risolti | risultati in `outputs/scenarios/`, impronte in `outputs/result_manifest.csv` |
| K0-DIAG | Capitale con pieno utilizzo iniziale e 45.671 legami rigidi | **Respinto** come rappresentazione della dinamica reale | `K0_diagnostic_full_utilization_2026-09-18.zip` (`9A3635B0…F532CE`)¹ |
| K1 | Capitale in 6 blocchi (privato/pubblico × E/S/N), stock e investimenti vincolati ai valori osservati, residuo di raccordo misurato; **nessun vincolo di capacità** | Implementato e validato | `K1_empirical_capital_2026-09-18.zip` (`36DA4E6F…1EA690`) |
| K2 | K1 + produttività del lavoro KLEMS + capacità G.17 (21 gruppi) | Implementato e validato; **non causale**: l'investimento non genera capacità | `K2_capital_productivity_capacity_2026-09-18.zip` (`E70A7CC4…EF87B7`) |
| LP-S (+ D0, D1) | Pavimenti sociali di mantenimento storico su 85 commodity; D0 e D1 diagnostiche | Implementato e validato | `LP-S_social_floors_2026-09-18.zip` (`5EFF7DC6…FC66D385`) |

## 3. Linea a 71 industrie

Nomenclatura con suffisso `-71` (checkpoint del 18/09/2026). Matrice industria × industria `A_t = S_t B_t` (quote di mercato); coefficienti negativi conservati. Obiettivo comune alle varianti LP: distanza assoluta normalizzata dai riferimenti, pesi output 2, consumo 4, investimento 1, importazioni 1, esportazioni 1, scorte 0,5, penalità del surplus 10; tetto all'output 125% del riferimento 2012; importazioni ≤ 100% del riferimento 2012. Il lavoro è un proxy monetario (remunerazione dei dipendenti), non ore.

| Modello | Contenuto | Risultato principale dichiarato | Archivio (SHA-256) |
|---|---|---|---|
| csvplan-71 (chiuso e aperto) | Esecuzione di `csvplan.jl` (Julia) su dati a 71 industrie, più correzione diagnostica vettoriale in file separato | Con l'indicizzazione originale le armonie sono positive ma il bilancio non chiude (residuo fino a 1,16 milioni di milioni); con la correzione vettoriale chiude ma 2–6 settori hanno consumo netto negativo. **Risultati di `csvplan.jl`, da tenere separati** | risultati in `outputs/csvplan_71_*` |
| LP-C0-71 | Controllo: flussi e matrice 2012 ripetuti per 5 periodi | Riproduce il 2012 (obiettivo 0, residuo 5,2e-7 milioni) | `LP_C0_71_2026-09-18.zip` (`EDAD1326…E2332D`)¹ |
| LP-A-71 | Matrici annuali a prezzi 2012 (trasformazione di similarità con prezzi KLEMS); riferimenti 2012 | 2016: output −8,4%, consumo −7,6% rispetto ai dati reali | `LP_A_71_2026-09-18.zip` (`79AF281D…0EE5A743`)¹ |
| K2-71 | LP-A-71 + capitale in 6 blocchi (totale investimenti vincolato), produttività KLEMS (63 gruppi), capacità G.17 (20 gruppi, 22 industrie) | Lavoro saturo in tutti gli anni; nessun vincolo G.17 saturo; 2016: output −5,4% rispetto ai dati reali. **Collegamento capitale–capacità aggregato e non causale** | `K2_71_2026-09-18.zip` (`491F43BD…A06968A8`)¹ |
| K2-C1-71 | K2-71 con totale del consumo osservato, composizione 2012 | Copertura del target 95% nel 2016; il target rigido è fattibile | `K2_C1_71_2026-09-18.zip` (`41687E58…E7B5D2`) |
| K2-C2-71 | Vettore dei consumi osservato per anno | Copertura 94% nel 2016; il target rigido è infeasible con tetto all'output 125%, fattibile al 140% | `K2_C2_71_2026-09-18.zip` (`1DADEFE3…8567BC`); diagnostiche in `work/K2-C2-71-hard-*` (non finali) |
| K2-G1-71 | Massimo output 2016 (lessicografico), surplus nullo, consumo ≥ K2-C2-71 | 2016: output +1,2% e consumo +0,6% rispetto ai dati reali, con importazioni −19,5% ed esportazioni −27,7%; 25 industrie al tetto del 125% | `K2_G1_71_2026-09-18.zip` (`B0CC7109…C3F953`) |
| Input fase 0 della linea 71 | Input congelati | — | `LP_71_inputs_phase0_2026-09-18.zip` (`E26934D7…FABBD45`) |

¹ Impronta calcolata da Claude il 22/09/2026 su una copia del file: il progetto LP non ne contiene una propria. Impronte complete in §6.

## 4. Punti rilevanti per il nuovo modello

**Cosa le linee precedenti hanno già stabilito**, da citare e non da ripetere:

- La formulazione LP sparsa riproduce il 2012 a 71 industrie (LP-C0-71).
- Il passaggio ad A annuali a prezzi 2012 è fattibile con la trasformazione di similarità (LP-A-71).
- Con capitale aggregato e produttività osservata, gli investimenti storici sono compatibili con il mantenimento del consumo 2012 (K2-71).

**Cosa resta aperto e il nuovo modello affronta:**

- **Nesso causale investimento → capacità.** K1, K2 e K2-71 lo dichiarano esplicitamente assente per mancanza di una matrice fonte–destinazione per industria e asset. Oggi l'archivio contiene i Fixed Assets dettagliati per 74 industrie × tipo di bene (`bea/2026-09-22`, M3). È l'elemento nuovo della specifica 0.2 (§4.3–4.4, §5.2).
- **Obiettivo.** Tutte le varianti LP usano la distanza dai riferimenti; la specifica 0.2 la riserva alla diagnostica (O4) e introduce O1–O3.
- **Lavoro in ore** invece del proxy monetario.
- **Impostazione prodotti × industrie** (73 × 71) invece della matrice industria × industria.
- **Parametri normativi** (tetto 125%, pesi) che nelle linee precedenti determinano parte dei risultati (K2-C2-71, K2-G1-71). Nel nuovo modello vanno dichiarati e sottoposti a sensibilità fin dall'inizio.

**Confronti previsti** (metodologici, con attribuzione separata):

| Nuovo modello | Termine di confronto | Cosa verifica |
|---|---|---|
| Controllo 2012 | LP-C0-71 | Stessa chiusura del 2012 con un'impostazione diversa |
| Dinamico senza capitale, obiettivo O4 | LP-A-71 | Effetto dell'impostazione prodotti × industrie e del lavoro in ore |
| Dinamico con capitale causale | K2-71 | Effetto del nesso investimento → capacità |
| Scenario CS8 rifatto | LP-CS8 (411) | Compressione dell'investimento con e senza costo futuro |

## 5. Lacune di documentazione del materiale precedente

Da sanare prima di citare questi risultati nel rapporto finale o nel Capitolo 9:

1. Definizione del termine **a** (poste di raccordo) nella linea 411. Per la linea 71 è documentato: residuo di arrotondamento fisso per industria.
2. Valori dei **flussi di riferimento** e dei **fattori di scala** della normalizzazione nella linea 411.
3. Dimensione delle **scorte iniziali** di calibrazione in LP-CS0.
4. Esclusione di **CS9** dal report e dal Capitolo 9: motivazione non documentata.
5. Impronte proprie mancanti per 4 archivi (nota ¹).

## 6. Impronte complete

| Archivio | SHA-256 |
|---|---|
| phase0_lp411_benchmark_complete_2026-09-18.zip | 0267F7FBDEEB63C4DE4BD9985AF135A3DD86E400A2FD56A12C6127268D26A53B |
| K0_diagnostic_full_utilization_2026-09-18.zip ¹ | 9A3635B060CA65A37A542ECCBEAC1C1CF40F39ABC63E07301D4B738CDAF532CE |
| K1_empirical_capital_2026-09-18.zip | 36DA4E6F13B8B9D2DD704D25E3BCAFA9C3897A04ED3B1E1BC8F236A1B31EA690 |
| K2_capital_productivity_capacity_2026-09-18.zip | E70A7CC435ED72C9BDC7EAE52E75BC204ADAAC6674CC3C128C4E66F758EF87B7 |
| LP-S_social_floors_2026-09-18.zip | 5EFF7DC6F902354ADA615A45136B1F9D8590438CBD215C18F3A8F748FC66D385 |
| LP_71_inputs_phase0_2026-09-18.zip | E26934D71A6D701389D648733651C5451D29E67ADE8392CC443FC8836FABBD45 |
| LP_C0_71_2026-09-18.zip ¹ | EDAD132619EB272F5077F6E6639217092ADAC4C3BAB1827D4372E64894E2332D |
| LP_A_71_2026-09-18.zip ¹ | 79AF281D34922853ED0028551780B30F393568185D10F3B78F9C06330EE5A743 |
| K2_71_2026-09-18.zip ¹ | 491F43BD85E1C9303461FE51577B33A6CEA9496C1C0D1FB5715150FCA06968A8 |
| K2_C1_71_2026-09-18.zip | 41687E585B6505DCB48A07121F38196FB9796A7AEDA9A195C6BB7310A2E7B5D2 |
| K2_C2_71_2026-09-18.zip | 1DADEFE3D43394454886674A826F5635CC6DF79E37903369F0778D2F928567BC |
| K2_G1_71_2026-09-18.zip | B0CC7109A7FDB78EAC41A05E2E1B7973CCE0772E010D8CD206F313BEFAC3F953 |
| csvplan.jl (storico) | D9CE22558FCA83F04C5603B19D8AAC5009BA461C0D57529DB17B6B83E243BD54 |
