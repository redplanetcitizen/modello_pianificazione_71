# M71-E6-predittivo — trasformazione di E6 in modello predittivo: note sui risultati

Aggiornato il 23/09/2026. **Esecuzione ufficiale** sul computer `20260923-072127_M71-E6-predittivo`, commit `4e16359`, nessuna modifica non registrata (Python 3.14.2, numpy 2.5.3, pandas 3.0.6, highspy 1.15.1): 825 risoluzioni LP, 60 minuti di solver, 76 minuti in tutto. I numeri di questo documento vengono da quella esecuzione; la replica in cloud (`20260922-231054`, numpy 2.4.6) è discussa sotto (§ Riproducibilità). Rapporto tecnico completo: `docs/rapporto_M71-E6-predittivo.md` (generato dal comando stesso). Comando unico: `python -m pianificazione71 predittivo`.

## Impostazione

- **Scenario preservato.** E6 "O2 tarato + penalità" resta invariato ed è riprodotto dal test `test_e6_originale_invariato` (obiettivo 4,7869935, scarto < 1e-6). Il predittivo vive in `pianificazione71/predittivo/` con configurazioni proprie.
- **Intervallo.** `SIMULATION_YEAR_MIN = 2008`, `SIMULATION_YEAR_MAX = 2019`; origini τ = 2008…2018, orizzonte H = min(5, 2019 − τ). Lo storico contiene dati 1997–2019 e nessun dato dal 2020 (verificato da `verifica_limiti` e dai test).
- **Pseudo-previsione fuori campione.** L'archivio ha solo dati revisionati (vintage 2025–2026): nessuna previsione real-time è possibile. Dichiarato nel rapporto.
- **Non anticipazione.** A ogni origine τ lo storico è troncato a τ; capacità (κ, θ), pesi w (KLEMS di τ), δ, σ, μ, B, D, Φ vengono da dati ≤ τ; lavoro, domanda pubblica, esportazioni, importazioni, obiettivi di consumo sono previsti con previsori selezionati su origini < τ. Il test di non anticipazione altera tutti i dati successivi a τ e verifica che parametri e soluzione restino identici.
- **Chiusure.** T1: stock finale ≥ stock iniziale × crescita PREVISTA degli FTE (R: produzione prevista di HS). T2: valore dello stock (v = 1, K in miliardi 2012, nessun costo d'uso). T3: T1 + T2.
- **Formulazioni.** P0 (previsioni preliminari senza LP), P1 (O2 con obiettivi previsti; tratti, tetto del consumo, gradualità aggregata/settoriale, chiusura: 60 configurazioni), P2 (tracking L1 con deviazioni assolute; con o senza tracking di investimento, importazioni, scorte: 13 configurazioni), P3 (robusta: lavoro e importazioni al quantile 0,25/0,75 dei residui di validazione), previsione condizionata (esogene future osservate) per la P1 di riferimento.
- **Selezione annidata.** Per l'origine di test τ si sceglie la configurazione con S medio minimo sulle origini < τ (h = 1); il periodo di test non entra nella scelta.

## Risultati principali (indicatore S = Σ α_g WMAE_g / WMAE_g(persistenza); < 1 batte la persistenza)

Protocollo B (obiettivi 2010–2019), un passo avanti:

| Caso | S | Produzione | Consumo | Investimento per tipo | Stock per tipo | Importazioni | Scorte |
|---|---|---|---|---|---|---|---|
| P0 (previsori preliminari) | **0,72** | 0,77 | 0,72 | 0,77 | 0,22 | 1,13 | 0,83 |
| Trend mobile | 0,80 | 0,89 | 0,71 | 0,89 | 0,46 | 1,07 | 0,89 |
| Ultimo tasso | 0,83 | 0,94 | 0,83 | 0,80 | 0,22 | 1,45 | 0,93 |
| P2 con tracking completo (T3) | 0,98 | 0,98 | 1,02 | 1,17 | 0,53 | 1,04 | 0,83 |
| Persistenza | 1,00 | 1 | 1 | 1 | 1 | 1 | 1 |
| Sequenza selezionata (annidata) | 1,25 | 1,26 | 1,08 | 1,17 | 0,41 | 2,16 | 3,37 |
| P1 con tetto 100% e valore terminale (`P1|tetto100|agg|T2`) | 1,27 | 1,45 | 1,08 | 0,65 | 0,20 | 2,84 | 4,43 |
| P1 condizionata (esogene osservate) | 1,70 | 1,31 | 2,33 | 1,09 | 0,29 | 3,46 | 3,79 |
| P1 di riferimento (E6 tradotto) | 2,11 | 1,65 | 2,48 | 2,17 | 0,69 | 3,71 | 3,65 |

Protocollo A (2009–2019, con lo shock) dà la stessa graduatoria (P0 0,76; P2 1,05; P1 2,02): nessuna rottura di regime nella graduatoria; il 2010–2019 è comunque la finestra principale. Caso C (obiettivi 2012–2016, un passo): P0 0,65; P2 0,81; P1 1,93.

Orizzonti pluriennali, protocollo B (media sulle origini):

| Caso | h = 1 | h = 2 | h = 3 | h = 4 | h = 5 |
|---|---|---|---|---|---|
| P0 | **0,72** | **0,80** | **0,85** | 0,92 | 0,99 |
| `P1|tetto100|agg|T2` | 1,27 | 0,97 | 0,92 | 0,92 | 0,99 |
| P2 con tracking completo | 0,98 | 0,97 | 1,00 | 1,04 | 1,10 |
| P1 condizionata (esogene osservate) | 1,70 | 1,04 | 0,87 | **0,77** | **0,76** |
| P1 di riferimento | 2,11 | 1,56 | 1,41 | 1,35 | 1,36 |
| Ultimo tasso | 0,83 | 0,96 | 1,05 | 1,18 | 1,31 |

Esperimento centrale, origine 2011 (una sola soluzione con dati ≤ 2011, obiettivi 2012–2016):

| Caso | h = 1 | h = 2 | h = 3 | h = 4 | h = 5 |
|---|---|---|---|---|---|
| P0 | 0,74 | 0,85 | 0,86 | 0,88 | 0,94 |
| Ultimo tasso | **0,67** | 0,88 | 0,88 | 0,97 | 1,10 |
| `P1|tetto100|agg|T2` | 1,20 | **0,77** | **0,73** | **0,67** | **0,68** |
| P2 con tracking completo | 1,05 | 0,83 | 0,87 | 0,85 | 0,83 |
| P1 condizionata | 1,59 | 0,86 | 0,72 | 0,59 | 0,63 |
| P1 di riferimento | 1,96 | 1,37 | 1,31 | 1,14 | 1,08 |

A un passo nessuna formulazione LP batte P0. Da h = 2 in poi, a partire dal 2011, la P1 con consumo al massimo all'obiettivo e valore terminale fa meglio di P0 (0,67–0,77 contro 0,85–0,88); sulla media delle origini la stessa formulazione è alla pari con P0 solo a h = 3–5. È un'unica origine (5 anni obiettivo): il risultato è compatibile con il fatto che il 2011 precede una fase di crescita regolare, e va verificato su più origini prima di trarne conclusioni.

Aggregati (h = 1, 2010–2019): P2 con tracking ha MAE 152 (miliardi di dollari 2012) e Theil U 0,78 contro 170 e 1,05 di P0, 156 e 0,73 del trend mobile, 254 della persistenza; ma per settore (investimento per industria, consumo per prodotto) P2 e P1 hanno errori 2–10 volte quelli di P0.

## Diagnostica

- **Lavoro e importazioni saturi in P1:** utilizzo del lavoro 1,00 e importazioni sempre al tetto. Le importazioni funzionano come risorsa gratuita fino al tetto: in P2 il tracking delle importazioni previste corregge il livello ma non il meccanismo. Correttivo non implementato: un costo per unità importata o bande calibrate.
- **Residuo materiale:** nullo in P1; circa 100 miliardi l'anno in P2 (deviazioni assorbite dal residuo). Da disciplinare con un limite o una penalità.
- **Saturazione di O2:** nella P1 di riferimento il 25% del consumo è al tetto +20% e il 41% esattamente all'obiettivo; con `tetto100` l'84% è all'obiettivo. Il prezzo ombra del lavoro resta ≈ 10⁻⁶.
- **Stabilità (P1 di riferimento, origine 2013, H = 2):** aggregati invariati sotto perturbazione dei costi (scarto < 3e-13), soluzione primale diversa dello 0,2–0,3% (ottimi multipli con gli stessi aggregati); dati perturbati dell'1% → aggregati 0,03%; pesi ±20% → invariati; tolleranze 1e-6 → 0,06%; punto interno = simplesso; scala in milioni → 0,5% (tolleranze assolute del solver). 33% delle variabili al limite zero.
- **Tempi:** 4,4 s per risoluzione in media, massimo 8,3 s (H = 5).

## Lettura (esclusivamente predittiva)

1. **A un passo il modello interindustriale non aggiunge accuratezza rispetto ai previsori semplici.** P0, cioè la selezione fuori campione tra persistenza, tassi e trend serie per serie, è la migliore in tutte le finestre a h = 1–2 e sulla media delle origini fino a h = 3. A h = 4–5 la P1 con tetto al 100% eguaglia P0; dall'origine 2011 la supera da h = 2 (da confermare su più origini).
2. **L'obiettivo di E6 (massimizzare la soddisfazione del consumo) è un cattivo predittore.** Anche con le esogene future osservate (previsione condizionata) resta peggiore della persistenza a un passo: la soluzione ottima spinge il consumo verso il tetto e l'investimento verso il minimo compatibile con la chiusura.
3. **Il tracking (P2) porta l'LP alla pari con la persistenza sugli aggregati, non sui settori.** La riconciliazione contabile impone struttura ma degrada le previsioni settoriali.
4. **La selezione annidata non salva la famiglia LP a un passo:** la sequenza selezionata resta a 1,18–1,28 (h = 1) e a 1,03–1,08 (h = 2–5).
5. **Criterio di scelta finale.** In base a errore fuori campione a un passo, stabilità tra origini, miglioramento sulla persistenza e semplicità, la configurazione finale è **P0** (previsori preliminari selezionati). Tra le formulazioni LP, `P2|inv1.0|m1.0|S1.0|T3` è la più vicina a un passo e va tenuta come strumento di riconciliazione contabile; `P1|tetto100|agg|T2` è la candidata per gli orizzonti pluriennali.

## Limiti dichiarati

- Dati revisionati, non vintage: pseudo-previsione.
- 11 origini: nessuna divisione stabile stima/selezione/test; usata la validazione annidata a origine mobile (h = 1) e la griglia è discreta e piccola (73 configurazioni). H e ω_h non sono stati esplorati (H = 5 fisso, ω_h = 1).
- P2 è un LP con deviazioni assolute (nessun QP in highspy per questa pipeline).
- Le 71 industrie non sono trattate come osservazioni indipendenti: la selezione usa solo l'indicatore aggregato per origine.
- La calibrazione della capacità nei servizi (inviluppo con tendenza) e la deriva G.17 sono stimate su [1997, τ] e [τ−5, τ]; la storia dal 1997 è mantenuta perché le finestre più corte non sono state confrontate sistematicamente (limite).

## Riproducibilità tra piattaforme

L'esecuzione ufficiale (Windows, Python 3.14, numpy 2.5.3) e la replica in cloud (Linux, Python 3.11, numpy 2.4.6) coincidono esattamente su tutti i casi senza LP (P0, persistenza, ultimo tasso, trend) e sulla P1 condizionata a h = 2–5. Per le formulazioni LP gli indicatori S differiscono in 322 casi su 405: in genere di 0,01–0,02 (1%), al massimo di 0,20 (`P1|tetto100|nessuna|T1`, h = 5, 12%). Graduatorie e conclusioni sono le stesse. Causa probabile, non verificata caso per caso: ottimi multipli. Differenze di arrotondamento tra versioni di numpy nella costruzione dei parametri possono portare il simplesso su vertici diversi con lo stesso valore dell'obiettivo, e le metriche calcolate sulle variabili cambiano. La verifica di stabilità mostra lo stesso fenomeno in piccolo (soluzione primale diversa dello 0,2–0,3% sotto perturbazione dei costi, aggregati invariati). I numeri citati sono quelli dell'esecuzione ufficiale.

## Grafici (modulo `predittivo/grafici_predittivo.py`)

Generati automaticamente dal comando `predittivo` (sezione 10 del rapporto) o a parte con `python -m pianificazione71 predittivo-grafici runs\<cartella>`; copie in `docs/grafici_predittivo/`. Palette categorica validata (dataviz): blu = P0, grigio = benchmark, verde = P2 tracking, arancio = P1/P3, viola = condizionata, giallo = sequenza selezionata; linea tratteggiata = persistenza (S = 1).

- **g1** S a un passo per caso, protocollo B (barre orizzontali, casi principali + 3 migliori P1 e P2).
- **g2** S per orizzonte h = 1…5, protocollo B: sotto la persistenza P0 fino a h = 4, la P1 condizionata solo da h = 3.
- **g3** componenti r_g di S per gruppo (h = 1): la P1 di riferimento è a 2,5–3,7 su consumo, importazioni e scorte; P0 domina ovunque salvo importazioni (1,13).
- **g4** errore % a un passo per anno su consumo e investimento totali (2009–2019, anni 2009–10 evidenziati come shock): la P1 sovrastima il consumo in modo crescente (+4% → +9%) e sottostima l'investimento (−4/−10%); P2 e P0 restano entro ±3% dal 2011.
- **g5** come g1 per il caso C (2012–2016).
- **g6** livelli a un passo 2009–2019 dei sei aggregati (produzione, consumo, investimento, importazioni, scorte, stock) a confronto con l'osservato BEA: P0 e P2 seguono l'osservato entro pochi punti; la P1 si stacca sul consumo (sopra) e su investimento e scorte (sotto), in modo crescente nel tempo.
- **g7** stessi aggregati dall'origine 2011 con h = 1…5 (2012–2016, unica soluzione): l'investimento resta piatto nei casi mostrati (P0, P1 di riferimento, P2) mentre l'osservato sale da 2 530 a 3 100; le importazioni previste crescono più dell'osservato. Il grafico non mostra `P1|tetto100|agg|T2`, che dall'origine 2011 è la formulazione migliore da h = 2.
- **g8** investimento per tipo dall'origine 2011: P0 estrapola la ripresa di E oltre l'osservato; P1 e P2 tengono S ed E piatti al di sotto; R sovrastimato dai due LP (+40% nel 2012), N sottostimato dalla P1.

## Esecuzione ufficiale sul computer

Fatta: commit `4e16359`, esecuzione `20260923-072127_M71-E6-predittivo` (23/09/2026, 76 minuti). I grafici g1–g8 della cartella dell'esecuzione sono stati prodotti alla fine del comando dal modulo `grafici_predittivo.py` nella versione registrata nel commit successivo (solo grafici: nessun numero dipende da quel modulo).
