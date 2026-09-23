# Passo C — dati a 71 industrie: note di lavoro

Aggiornato il 22/09/2026. Codice: repository `modello_pianificazione_71`, comandi `c1`, `c2`, `c4`–`c7` (o `passo-c` per tutti). Tutte le cifre sono confermate dall'esecuzione ufficiale sul computer (commit `e1e5845`, §3).

## C1 — Sistema prodotti–industrie 2012–2016 (`M71-C1-sistema`)

**Fonti:** Use e Make Summary prima delle ridefinizioni, prezzi alla produzione (`bea/2025-09`); indici di prezzo della produzione lorda per industria, GDP by Industry tavola 18 (`bea/2026-09-23`).

**Identità contabili (dollari correnti).** Tutte chiudono entro l'arrotondamento: scarto massimo 14 milioni (colonna delle costruzioni, 2016) su tavole di circa 30.000 miliardi. Produzione per industria Use e Make coincidono entro 12 milioni; per prodotto coincidono esattamente.

**Celle "...".** Circa 2.420 nella Use e 4.255 nella Make per anno. **Sono zeri**: la nota BEA dice che i valori nulli non sono mostrati, e i totali pubblicati tornano ponendo "..." = 0. La nota della release `bea/2025-09`, che le definiva dati soppressi per riservatezza, va corretta. L'ipotesi H4 cade: non c'è nulla da stimare.

**Valori negativi (5 anni, 346 celle).**

| Categoria | Celle | Trattamento |
|---|---:|---|
| Importazioni F050 (segno negativo per convenzione) | 237 | variabile m ≥ 0 |
| Riga o colonna `Used`/`Other` | 69 | esogene (H16) |
| Riduzione delle scorte F030 | 19 | variazione libera |
| Sussidi superiori alle imposte V002 | 13 | fuori dai bilanci materiali |
| Da esaminare | 8 | vedi sotto |

Le 8 celle da esaminare: prodotti agricoli (111CA) usati dall'amministrazione federale non militare (GFGN), negativi in tutti gli anni (−200/−432 milioni), verosimilmente operazioni della Commodity Credit Corporation; risultato lordo di gestione negativo di GFE (2013) e del settore titoli 523 (2014–2015). Le prime generano 7 coefficienti B negativi all'anno, piccoli (fino a −0,002); le seconde non entrano nei bilanci materiali.

**Importazioni positive in F050** per commercio all'ingrosso (42), trasporti ferroviario, marittimo, su gomma e altri (482, 483, 484, 487OS): 45–55 miliardi l'anno. Da trattare come usi esterni fissi, non come importazioni negative.

**Prezzo del prodotto = prezzo dell'industria con lo stesso codice (H5).** Verificata: per tutti i 71 prodotti e tutti gli anni l'industria principale ha lo stesso codice; quota minima 60% (713, 2012).

**Nuova ipotesi H24:** `Used` e `Other` non hanno un indice di prezzo proprio; si usa quello della produzione lorda delle industrie private (PVT).

**Sistema a prezzi 2012.** Deflazione per prodotto; x e q reali come somme dei componenti deflazionati (H6). Bilanci per prodotto chiusi (scarto ≤ 7,4 milioni, lo stesso del nominale); x = Dq esatto; colonne di D a somma 1. Produzione reale: 29.232 miliardi (2012) → 32.016 miliardi (2016). Indici di prezzo 2016 tra 0,49 (prodotti petroliferi) e 1,24 (credito).

## C2 — Margini dell'investimento (`M71-C2-margini`)

**Fonti:** Fixed Assets dettagliati per 74 industrie × tipo di bene (`detailnonres_inv1`, `detailresidential`); colonne F02 della Use; NIPA 5.3.5.

La Use coincide con la NIPA 5.3.5 in tutti gli anni e tipi. Il confronto rilevante è Fixed Assets contro Use:

| Tipo | Scarto FA − Use | Spiegazione documentata da BEA |
|---|---|---|
| N (proprietà intellettuale) | ≤ 0,02% | margini coincidenti |
| R (residenziale) | ≤ 0,13% | margini coincidenti |
| E (attrezzature) | da −0,06% a −1,66% (fino a −18,6 miliardi nel 2016) | vendite di rottami, margini dei rivenditori sull'usato, valutazione intersettoriale delle auto usate, revisioni statistiche non ancora recepite nei FA |
| S (strutture) | da −3,4% a −5,6% (fino a −31,8 miliardi nel 2016) | i FA registrano sostanzialmente le **strutture nuove** (scarto con la riga NIPA delle strutture nuove tra −0,1% e −1,0%); la differenza riguarda strutture usate, commissioni dei mediatori, momento di registrazione degli impianti elettrici |

**Riga `Used` nella colonna F02E:** circa −102/−109 miliardi l'anno, il 10% dell'investimento in attrezzature. Il totale FA delle attrezzature corrisponde al totale Use **inclusa** questa riga, non ai soli prodotti ordinari.

**Conseguenza per Φ.** I margini di riga (prodotti ordinari della Use) e di colonna (FA per industria) non hanno lo stesso totale: per le attrezzature differiscono per la riga `Used` più lo scarto di riconciliazione, per le strutture per lo scarto usato/nuovo. Serve una regola di raccordo **prima** del bilanciamento (decisione aperta).

**Concordanza FA 74 → I/O.** Costruita (`config/concordanza_fa_io.csv`): 74 industrie FA su 65 industrie I/O. Aggregazioni: utility (3→1), alimentari e bevande (2→1), apparecchi medicali in 339, commercio all'ingrosso (2→1), credito (4→1), assicurazioni (2→1). Ipotesi H18a: il capitale non residenziale del settore immobiliare (5310) va a Other real estate; le abitazioni (HS) ricevono il capitale residenziale. Restano senza investimento privato FA: HS (residenziale) e le 5 industrie pubbliche (esogene, H23).

## C3 — Verifiche e concordanze KLEMS

- **Capitale per tipo:** il file KLEMS distingue arte e intrattenimento, R&S, IT, software e "altro". Attrezzature e strutture **non sono separate**. I pesi per tipo si costruiscono quindi con il costo d'uso (C6, decisione D2).
- **Lavoro:** le ore sono solo un indice (2017 = 100); la tavola NIPA 6.9 non è più nell'API. Unità del lavoro: FTE (C7, decisione D3).
- **Classificazione KLEMS:** 63 industrie; aggregati rispetto alle 71 I/O: commercio al dettaglio (44RT), immobiliare (531 = HS + ORE), ospedali e case di cura (622HO), governo federale (GF) e locale (GSL).

## Decisioni applicate (22/09/2026)

- **D1 — raccordo dei margini:** totali per prodotto dalla Use (prodotti ordinari); totali per industria dei Fixed Assets riscalati in proporzione per tipo; riga `Used` esogena.
- **D2 — pesi E/S/N:** costi d'uso con tasso di rendimento per gruppo KLEMS calibrato sulla remunerazione del capitale 2012.
- **D3 — lavoro:** FTE NIPA 6.5D, controllo con l'indice delle ore KLEMS.

## C4 — Matrice Φ (`M71-C4-phi`)

- **Struttura iniziale** dal dettaglio FA (94 tipi di bene): attrezzature → categorie del raccordo PEQ → prodotti, margini compresi; strutture: esplorazione mineraria → 213, il resto → 23; proprietà intellettuale: R&S → 5412OP, software → 511/5415, opere artistiche → 512/511/711AS. Quota comune λ = 0,05.
- **GRAS:** converge in 15 casi su 15 (5 anni × 3 tipi), in 18–69 iterazioni; nessuna cella negativa; 65 industrie.
- **Fattori di raccordo Use/FA:** attrezzature 1,10–1,12 (riga `Used` esogena); strutture 1,04–1,06; proprietà intellettuale 0,99.
- **Spostamento dalla struttura iniziale:** E 11–14%, S 6–11%, N 25–27%.
- **Informatività del dettaglio FA:** rispetto a una composizione comune a tutte le industrie (λ = 1) le celle cambiano del 65–72%. **Sensibilità** a λ = 0,2: 10–12%.
- **Esempi:** trasporto aereo 64% aeromobili; trasporto su gomma 75% autoveicoli; ferrovie 73% altri mezzi di trasporto.
- **Uso nel modello:** Φ dà il fabbisogno di prodotti per unità di investimento FA; l'accumulazione resta in unità FA.

## C4b — Confronto di Φ con la tavola dei flussi di capitale 1997 (`M71-C4b-confronto-1997`)

- Perimetro comparabile: attrezzature e strutture non residenziali, senza software; tavola 1997 con le rettifiche BEA del 2018 per 5 industrie; commercio al dettaglio aggregato. Indice di dissomiglianza ½Σ|a − b|.
- **Φ 2012 è più vicina alla tavola 1997 di una composizione comune in 56 industrie su 62.** Dissomiglianza media ponderata: 0,27 contro 0,46.
- Eccezioni: altri mezzi di trasporto (3364OT), editoria (511), credito (521CI), rifiuti (562), case di cura (623), alloggio (721).
- Lettura: controllo di plausibilità della struttura iniziale con una fonte indipendente di 15 anni prima; non valida le singole celle (tecnologie e prezzi relativi sono cambiati).

## C5 — Capitale a prezzi 2012 (`M71-C5-capitale`)

- Serie elementari FA (industria × bene) valutate ai prezzi 2012 del bene: quantità a costo fisso × rapporto corrente/costo fisso del 2012. Aggregati per somma delle serie elementari (H6).
- **Identità di accumulazione** K_fine − K_inizio − I + D: scarto ≤ 0,09% dello stock per E, N, S (≤ 0,05% dal 2013); residenziale 0,15% nel 2012, ≤ 0,02% dopo. Nessuna "altra variazione di volume" rilevante in questo periodo.
- **δ aggregati:** E 0,139–0,141; N 0,247–0,261; S 0,031; residenziale 0,023. Per industria: E 0,07–0,28; N 0,12–0,71; S 0,02–0,07.
- **Stock netto fine 2016 (miliardi 2012):** E 6.754; S 12.574; N 2.838; residenziale 16.989.

## C6 — Capacità legata al capitale (`M71-C6-capacita`)

- **Tassi di rendimento 2012** per 61 gruppi KLEMS: mediana 0,124; due negativi troncati a 0 (titoli 523, abbigliamento 315AL); massimi elevati (servizi legali 1,30, raffinazione 0,60, ingrosso 0,55) dove la remunerazione KLEMS comprende rendimenti di attivi non presenti in K (terreni, scorte, intangibili non capitalizzati): ipotesi H8b.
- **Pesi w** (mediana): E 1,24; S 0,72; N 1,96; per costruzione K^cap_2012 = ΣK.
- **κ** per 66 industrie; utilizzo G.17 per 23 industrie (21 serie; l'estrattivo usa una serie per 211, 212, 213; le utility usano elettricità e gas anche per l'acqua: H9a).
- **Controllo esterno parziale G.17, 2013–2016:**

| Metodo G.17 | Industrie | Scarto medio assoluto u* − u | Correlazione | Crescita K^cap 2012–16 | Crescita capacità G.17 |
|---|---:|---:|---:|---:|---:|
| fisico | 8 | 6,6 punti | 0,60 | +12,7% | +11,5% |
| indagine + capitale | 14 | 3,4 punti | 0,84 | +3,8% | −3,3% |
| misto (chimica) | 1 | 6,3 punti | −0,99 | +14,2% | −10,0% |

  **Lettura:** nei gruppi a capacità misurata fisicamente la crescita del capitale segue quella della capacità (in media); nella manifattura stimata da indagine la capacità G.17 **cala** mentre lo stock di capitale cresce: il proxy stock-capacità (H10) sovrastima la crescita della capacità di circa 1,8 punti l'anno. Casi estremi: supporto all'estrazione (213) con utilizzo implicito 0,40 contro 0,67 nel 2016 (capitale accumulato durante il boom petrolifero); chimica e manifattura varia (339) con capitale +11/+14% contro capacità −7/−10%. **H10 è sostenuta solo in parte**: nel modello il vincolo di capacità rischia di essere più lasco del reale nella manifattura. Opzioni per il passo D: κ variabile nel tempo, oppure capacità G.17 diretta per le industrie coperte, con il capitale per le altre.

- **Deriva tra capacità G.17 e capitale:** θ = (crescita capacità / crescita K^cap)^(1/4) − 1. Media annua: gruppi fisici −0,3%; manifattura da indagine −1,8%; chimica −5,8%.
- **Verifica fuori campione:** stimando θ sul 2012–2014 e applicandolo al 2015–2016, l'errore medio assoluto sull'utilizzo scende da 5,0 a 2,9 punti (2015) e da 7,4 a 5,0 punti (2016); il miglioramento c'è in tutti i gruppi. Una deriva stimata e dichiarata migliora la capacità implicita anche fuori dal periodo di stima.

## C7 — Lavoro, scorte, estero (`M71-C7-lavoro-scorte-estero`)

- **Lavoro:** FTE per 70 industrie (HS senza addetti, H14a; federale generale: civili → GFGN, militari → GFGD): 124,5 milioni (2012) → 134,4 milioni (2016). Controllo con le ore KLEMS: correlazione delle crescite 2012–16 per gruppo 0,99, scarto medio 3,0 punti.
- **Scorte:** 11 comparti, stock IV trimestre a prezzi IV trim. 2012. σ = stock / produzione del comparto: da 0,011 (altre industrie) a 0,72 (concessionari auto). La colonna F030 della Use coincide con la variazione delle scorte NIPA 5.7.5; la differenza con la variazione degli stock di fine anno (fino a 160 miliardi nel 2015) è l'aggiustamento di valutazione (caduta dei prezzi del petrolio).
- **Estero (miliardi 2012):** esportazioni 1.982 → 2.007; importazioni 2.586 → 2.673; saldo tra −471 e −630. Voci positive di F050 (margini su importazioni) 53–57 miliardi, usi esterni fissi.

## Nuove ipotesi

- **H8b:** la remunerazione del capitale KLEMS include attivi non compresi in K; r è sovrastimato dove questi pesano.
- **H9a:** utilizzo di elettricità e gas applicato all'intera industria delle utility (acqua compresa).
- **H14a:** nessun FTE per HS; immobiliare su ORE; federale generale diviso tra civili (GFGN) e militari (GFGD).
- **H18a:** capitale non residenziale del settore immobiliare su ORE.
- **H24:** prezzo di `Used` e `Other` = indice della produzione lorda delle industrie private.

## 3. Replicabilità

**Esecuzione ufficiale di riferimento del passo C:** commit `e1e5845`, nessuna modifica non registrata, comando `passo-c` (Windows, Python 3.14.2, numpy 2.5.3, pandas 3.0.6, highspy 1.15.1, xlrd 2.0.2), cartelle `runs/20260922-1850*` e `runs/20260922-1851*`–`1852*`.

Confronto con le esecuzioni di prova in ambiente Linux (Python 3.11, numpy 2.4.6):

| Sotto-passo | File identici byte per byte | Differenze |
|---|---:|---|
| C1 sistema | 37/39 | `controlli_reali.csv`, `sintesi.md`: controllo x = Dq, 1,7e-10 contro 2,3e-10 milioni |
| C2 margini | 4/4 | — |
| C4 Φ | 42/43 | `diagnostica.csv`: residui del GRAS dell'ordine di 1e-4 milioni |
| C4b confronto 1997 | 2/2 | — |
| C5 capitale | 5/5 | — |
| C6 capacità | 8/8 | — |
| C7 lavoro, scorte, estero | 8/8 | — |

Tutti i dati prodotti sono identici su due sistemi operativi e due versioni delle librerie; le sole differenze sono rumore di calcolo in file diagnostici. Le cifre di questa nota sono quindi quelle ufficiali.
