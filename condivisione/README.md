# Pacchetto per la revisione — modello M71, scenario E6

Questa cartella raccoglie i dati, i parametri e i risultati richiesti per la revisione del modello di programmazione lineare a 71 industrie (repository `pianificazione71`). Tutti i file, tranne questo README, sono generati da

```
python -m pianificazione71 pacchetto
```

a partire dai dati grezzi BEA, BLS e Fed dell'archivio, verificati con SHA-256 prima della lettura. Nessun numero è scritto a mano.

`MANIFEST.json` riporta per ogni file la dimensione e l'impronta SHA-256. Registra anche:

- il commit del codice che ha generato il pacchetto;
- le versioni di Python e dei pacchetti;
- le impronte dei manifest delle release dei dati;
- le esecuzioni copiate in `risultati/`;
- i file esclusi per dimensione, con la loro impronta.

## 1. Riprodurre

Servono Python ≥ 3.11 e git. L'esecuzione di riferimento usa Windows 10, Python 3.14.2, numpy 2.5.3, pandas 3.0.6 e highspy 1.15.1 (versioni esatte in `requisiti-bloccati.txt`).

```
git clone https://github.com/redplanetcitizen/modello_pianificazione_71.git
cd modello_pianificazione_71
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requisiti-bloccati.txt
.venv\Scripts\python.exe -m pip install -e ".[test]"
```

**Dati.** L'archivio dei dati letti dal modello è allegato alla release GitHub del repository come `dati_modello_M71.zip`, con la sua impronta SHA-256 nella descrizione della release. Lo zip contiene:

- i soli file effettivamente letti dal modello, elencati in `config/dati.toml`;
- il `MANIFEST_RELEASE.json` e le `NOTE.md` di ciascuna release.

Estratto lo zip in una cartella `X`, indicare l'archivio con la variabile d'ambiente:

```
$env:DATI_ECONOMICI = "X\dati_economici"                 # PowerShell
.venv\Scripts\python.exe -m pianificazione71 verifica-dati   # impronte dei manifest e dei file usati
.venv\Scripts\python.exe -m pytest                            # tutti i test (circa 8 minuti)
.venv\Scripts\python.exe -m pianificazione71 e6               # scenario E6, 2012-2016 e 2010-2019
.venv\Scripts\python.exe -m pianificazione71 pacchetto        # rigenera questa cartella
```

`verifica-dati --completa` non passa con lo zip, per costruzione: controlla tutti i file delle release, e lo zip contiene solo quelli letti dal modello.

**Controllo indipendente dalle fonti.** Le release sono state scaricate da:

- BEA: tavole Make/Use Summary 1997–2024, release di settembre 2025 (file creati dalla BEA il 3 e il 24/09/2025); file Fixed Assets di dettaglio aggiornati dalla BEA il 26/09/2025 (release dell'archivio `bea/2026-09-22`); tabelle NIPA e GDP by Industry scaricate dall'API BEA il 23/09/2026;
- Fed: G.17, scaricata il 18/09/2026;
- BEA-BLS: account integrato di produzione per industria (KLEMS) 1997–2024, release dell'archivio `bls/2026-09-18`.

In ogni release `NOTE.md` indica provenienza e data. Le serie elementari del capitale riportano i codici di serie BEA (colonne `serie_corrente`, `serie_costo_fisso`), così ogni valore si può confrontare con il foglio `Datasets` dei file `detailnonres_*.xlsx`.

## 2. Contenuto

| File | Contenuto | Unità |
|---|---|---|
| `dati/capitale_industria_tipo_2008_2019.csv` | K, I, D, δ, altre variazioni, per industria I/O (66: 65 private + HS) × tipo × anno | milioni di $ (2012 e correnti) |
| `dati/capitale_serie_elementari_2008_2019.csv` | Serie BEA elementari (industria FA × bene) a costo corrente, a costo fisso (dollari 2017 BEA) e a prezzi 2012, con i codici di serie | milioni di $ |
| `dati/produzione_lavoro_2008_2019.csv` | Produzione lorda corrente (Use e Make), indice di prezzo, produzione a prezzi 2012, FTE | milioni di $; migliaia di FTE |
| `dati/scorte_comparti_2007_2019.csv` | Scorte di fine anno per gli 11 comparti NIPA, correnti e a prezzi del IV trimestre 2012 | milioni di $ |
| `dati/g17_capacita_utilizzo_1997_2019.csv` | Medie annue delle serie mensili G.17: capacità (in % della produzione media 2017, unità dell'indice di produzione), utilizzo (%), produzione approssimata = prodotto delle due medie / 100 | indici |
| `dati/mappatura_71_industrie.csv` | Le 71 industrie I/O con: industrie Fixed Assets, capitale nel modello, vincolo di capacità, serie G.17, gruppo KLEMS, riga FTE, comparto scorte | — |
| `dati/concordanza_fixed_assets_io.csv` | Concordanza 74 industrie Fixed Assets → 65 industrie I/O private (copia di `config/`) | — |
| `modello_E6/capacita_<orizzonte>.csv` | Per industria: fonte della calibrazione, κ, moltiplicatore di utilizzo, deriva θ, K^cap e capacità nell'anno iniziale, utilizzo implicito, κ_t per anno: i coefficienti del vincolo di capacità di E6 | miliardi di $ 2012 |
| `modello_E6/capitale_<orizzonte>.csv` | Per industria e tipo: stock iniziale, δ, peso di capacità w, investimento dell'anno precedente (base della penalità) | miliardi di $ 2012 |
| `modello_E6/inviluppo_H9c_<orizzonte>.csv` | Inviluppo dei massimi 1997–2019 di x/K^cap (H9c) per le industrie senza G.17 e HS | — |
| `modello_E6/configurazione_<orizzonte>.json` | Tutte le opzioni del modello nello scenario E6, fattori terminali, stock iniziale per tipo, minimi terminali, lavoro e importazioni totali | miliardi di $ 2012 |
| `risultati/<esecuzione>/` | Output delle esecuzioni ufficiali (passi C, D, E, predittivo): `esecuzione.json`, `sintesi.md`, tabelle, grafici | miliardi di $ 2012 salvo indicazione (i CSV del passo C sono in milioni) |
| `controlli.md` | Controlli automatici: aggregazione delle serie elementari, anno base, identità di accumulazione | — |
| `esito_test.txt` | Uscita di `pytest` al momento della generazione | — |

La documentazione del progetto è in `../docs/progetto/`:

- `04_specifica_modello.md`: specifica formale e dizionario delle ipotesi H;
- `10_scenario_E6_specifica.md`: il problema LP di E6 vincolo per vincolo;
- `09_registro_modelli_e_test.md`: registro dei modelli, delle opzioni e delle configurazioni;
- `03_registro_decisioni.md`: decisioni, approssimazioni, verifiche aperte;
- note dei passi C, D, E e del predittivo (`06`, `07`, `08`, `11`).

## 3. Definizioni

**Fonte del capitale.** BEA, Fixed Assets, stime dettagliate per industria e tipo di bene (`detailnonres_stk1/2`, `_inv1/2`, `_dep1/2`, `detailresidential`), release del 26/09/2025. La BEA avverte che queste stime di dettaglio hanno qualità inferiore agli aggregati pubblicati. Alcune sono costruite da tendenze dell'aggregato superiore o da fonti meno solide.

**K.** Stock netto di capitale fisso privato, stima di fine anno (*net stock, yearend estimates*). Per ogni serie elementare s (industria FA × bene) la BEA pubblica il valore a costo corrente e a costo fisso in dollari 2017. Il modello lo porta a prezzi 2012 così:

K_s,2012(t) = K_s,costo fisso(t) · K_s,corrente(2012) / K_s,costo fisso(2012)

cioè la quantità della serie valutata al prezzo del suo bene nel 2012. Le serie elementari così ottenute sono additive. Gli aggregati per tipo e industria I/O sono **somme di serie elementari**, mai somme di serie concatenate. Nel 2012 ogni aggregato coincide con il valore corrente (controllo 2 in `controlli.md`).

**I.** Investimento fisso lordo privato della serie elementare, portato a prezzi 2012 con la stessa formula (colonne `I_2012`, `I_corrente`).

**D.** Ammortamento (*depreciation*, consumo di capitale fisso) BEA, stessa formula.

**Base di prezzo.** La BEA valuta lo stock ai prezzi di fine anno, investimento e ammortamento ai prezzi medi dell'anno. K a prezzi 2012 è quindi ai prezzi di fine 2012; I e D ai prezzi medi del 2012. Le due basi differiscono in genere di meno del 2% (mediana 0,2%; 1,7–1,9% per alcune strutture).

**Serie senza valore a costo fisso nel 2012.** Se una serie elementare è nulla a costo fisso nel 2012 ma non negli altri anni, si usa il rapporto corrente/fisso del primo anno disponibile (colonna `prezzo_non_base` delle serie elementari). Riguarda circa lo 0,2% dell'investimento; l'effetto sullo stock è trascurabile. Poiché il primo anno disponibile dipende dalla finestra di anni letta, questi pochi valori possono differire leggermente tra `dati/` e i parametri del modello.

**δ.**

- Nei dati (`delta_annuo`): δ_t = D_t / K_inizio,t, con K_inizio,t = K_fine,t−1, per industria e tipo.
- Nel modello E6: δ_j,a = Σ_t D_j,a,t / Σ_t K_inizio,j,a,t sugli anni dell'orizzonte (2012–2016 o 2010–2019). È costante nell'orizzonte e usa i dati osservati dell'orizzonte stesso.
- Nella pipeline predittiva: ΣD / ΣK_inizio sugli ultimi 5 anni ≤ origine.

**Inizio o fine anno.**

- I dati BEA sono di fine anno.
- Nel modello K_j,a,t è lo stock di **inizio** anno t, pari al dato BEA di fine t−1.
- Accumulazione: K_j,a,t+1 = (1 − δ_j,a) K_j,a,t + I_j,a,t. L'investimento dell'anno t entra in capacità dall'anno t+1 (ipotesi H12).
- Stock iniziale di E6: fine 2011, cioè K al 1/1/2012 (orizzonte 2012–2016; per il 2010–2019: fine 2009).
- Condizione terminale: sullo stock al 1/1/2017, cioè fine 2016 (per il 2010–2019: 1/1/2020).

**Unità e base dei prezzi.**

- Nei file `dati/`: milioni di dollari, correnti o a prezzi 2012.
- Nel modello e nei risultati: miliardi di dollari 2012 (fattore 1000).
- Tutte le righe della Use (usi intermedi, consumo, investimento, domanda pubblica, esportazioni, importazioni) e le colonne della Make sono deflazionate prodotto per prodotto con l'indice di prezzo della produzione lorda dell'industria con lo stesso codice. Fonte: BEA GDP by Industry, tavola 18, ribasata 2012 = 1 (ipotesi H5). `Used` e `Other` usano l'indice delle industrie private (H24).
- La produzione di un'industria a prezzi 2012 è la somma per riga della tavola Make deflazionata per prodotto, non il nominale diviso per un unico indice.
- Le scorte sono a prezzi del IV trimestre 2012 (deflatori NIPA 5.8.9B per comparto).
- Il lavoro è in migliaia di occupati equivalenti a tempo pieno (FTE, NIPA 6.5D).

**Tipi di capitale.**

- E: attrezzature (codici bene E…);
- S: strutture (S…);
- N: prodotti della proprietà intellettuale (software ENS…, R&S RD…, originali artistici AE…);
- R: residenziale privato, tutto attribuito all'industria HS (*Housing*).

Il capitale non residenziale del settore immobiliare (FA 5310) va su ORE, *Other real estate* (ipotesi H18a). Il capitale pubblico non è nel modello.

**Rivalutazioni e altre variazioni dello stock.** Il modello non le rappresenta. Il pacchetto le misura come residui dell'identità di accumulazione, per industria e tipo:

- a prezzi 2012: `altre_variazioni_2012` = K_fine − K_inizio − I + D. Comprende le altre variazioni di volume, gli arrotondamenti delle serie BEA e l'effetto della diversa base di prezzo di K (fine anno) rispetto a I e D (media d'anno). Aggregato per tipo resta sotto lo 0,35% dello stock iniziale in ogni anno del 2008–2019 (`controlli.md`); per singola industria e tipo, sugli stock superiori a 1 miliardo, arriva all'1,1% (costruzioni, strutture, 2008); su stock minimi può essere maggiore (−5,3% per la proprietà intellettuale dell'agricoltura, 53 milioni, 2008). Gli scarti aggregati maggiori cadono nel 2017, 2018 e 2012, soprattutto nel residenziale. La loro origine (per esempio distruzioni da catastrofi naturali, che non rientrano nell'ammortamento) non è stata verificata;
- a costo corrente: `rivalutazioni_e_altre_variazioni_corrente`, stessa identità sui valori correnti. Comprende i guadagni e le perdite in conto capitale (rivalutazioni) più le altre variazioni di volume. Per tipo e anno va da −5,4% a +6,3% dello stock iniziale; per singola industria e tipo da −10,7% a +13,3%.

La BEA non pubblica la scomposizione a questo livello di dettaglio; i due residui sono derivati, non dati pubblicati.

## 4. Industrie

Le 71 industrie I/O della tavola Summary BEA (Use e Make *before redefinitions*, prezzi di produzione) si dividono in:

- 65 industrie private con capitale non residenziale (E, S, N), ottenute da 74 industrie Fixed Assets tramite `concordanza_fixed_assets_io.csv`. Utility, alimentari e bevande, manifatturiere varie, commercio all'ingrosso, credito e assicurazioni aggregano più industrie FA;
- HS, *Housing*, con il solo capitale residenziale R;
- 5 industrie pubbliche (GFGD, GFGN, GFE, GSLG, GSLE): senza capitale né vincolo di capacità nel modello; la domanda pubblica è esogena ai valori osservati.

I prodotti sono 73: i 71 ordinari, che nei bilanci materiali hanno gli stessi codici delle industrie, più `Used` e `Other`, esogeni ai valori osservati (H16).

## 5. Capacità, produzione e utilizzo G.17

Il vincolo di capacità dell'industria j nell'anno t è

x_j,t · κ_j,t ≤ K^cap_j,t = Σ_a∈{E,S,N} w_j,a K_j,a,t      (per HS: K^cap = K_HS,R)

κ_j,t = κ_j · u_j / (1 + θ_j)^(t − a0).

- **w_j,a:** peso di costo d'uso. Il costo d'uso è c_j,a = r_g + δ_j,a,2012, con δ_j,a,2012 il tasso annuo del 2012 (non la media dell'orizzonte) e r_g il rendimento del gruppo KLEMS g calibrato sulla remunerazione del capitale KLEMS del 2012 e troncato a zero. I pesi sono normalizzati così che K^cap_j = Σ_a K_j,a sullo stock al 1/1/2012, e restano gli stessi nei due orizzonti. La remunerazione KLEMS include terreni e scorte (H8b).
- **23 industrie coperte dalla Fed G.17** (estrattivo, utility, manifattura; serie in `dati/g17_…`):
  - κ_j = K^cap_j,a0 · u^G17_j,a0 / x_j,a0;
  - θ_j = (crescita della capacità G.17 / crescita di K^cap)^(1/n) − 1 sull'orizzonte (2012–2016 in E6);
  - u_j = 1 nel vincolo, perché l'utilizzo G.17 è già dentro κ_j.
- **42 industrie senza G.17 e HS** (ipotesi H9c):
  - κ_j = K^cap_j,a0 / x_j,a0;
  - u_j e θ_j vengono dall'inviluppo dei massimi 1997–2019 del rapporto x/K^cap attorno alla sua tendenza log-lineare (`inviluppo_H9c_…`).

La capacità implicita nell'anno iniziale e l'utilizzo che ne risulta sono in `modello_E6/capacita_…` (colonne `capacita_a0`, `utilizzo_implicito_a0`). La colonna `metodo_capacita_fed` distingue le serie G.17 la cui capacità la Fed stima soprattutto da dati fisici (estrattivo, utility, carta, raffinazione, metalli di base, autoveicoli; chimica in parte) da quelle stimate con l'indagine Census sull'utilizzo degli impianti e dati sul capitale. La classificazione è del progetto, ricavata dalle note metodologiche della Fed sulla capacità, che non sono nell'archivio: va considerata indicativa.

**Produzione G.17.** La produzione industriale G.17 non è nell'archivio come serie propria. L'utilizzo G.17 è per definizione il rapporto tra produzione e capacità, mese per mese; nel file la produzione è **approssimata** dal prodotto delle medie annue di capacità e utilizzo, diviso per 100. La capacità è espressa in % della produzione media del 2017 (per l'estrattivo nel 2017: capacità 139,5, utilizzo 71,7%, produzione 100). Nel modello la produzione è quella BEA a prezzi 2012, non la G.17.

## 6. Come E6 aggrega E, S, N e R

- **Accumulazione:** per industria e tipo separatamente, con δ_j,a propri; E, S e N non si scambiano tra loro.
- **Capacità:** aggregato lineare con i pesi w_j,a (sostituibilità perfetta tra tipi, ai prezzi dei servizi del 2012, ipotesi H8). L'alternativa Leontief, un vincolo per tipo, è un'opzione del modello (`capacita_tipo = "leontief"`) non usata in E6. R vincola solo HS.
- **Condizione terminale (H29):**
  - Σ_j Σ_a∈{E,S,N} K_j,a,T+1 ≥ f_ESN · Σ K al 1/1 dell'anno iniziale: somma a **valore** (dollari 2012) su industrie e tipi, senza pesi di capacità;
  - K_HS,R,T+1 ≥ f_R · K_HS,R al 1/1 dell'anno iniziale;
  - f_ESN = (FTE_T / FTE_a0)^((T+1−a0)/(T−a0)), cioè la crescita osservata nell'orizzonte degli FTE totali delle 71 industrie (pubbliche comprese; HS non ha FTE), estesa fino a T+1; f_R è l'analogo sulla produzione di HS. Valori in `configurazione_<orizzonte>.json`.
- **Gradualità (H25b):** sulle somme per tipo (E, S, N, R) su tutte le industrie. Variazioni annue fino al 5% dell'investimento del tipo nell'anno precedente l'orizzonte sono gratuite; oltre, costano 0,1 per unità relativa.
- **Domanda di prodotti per investimento:** per industria e tipo, con la matrice Φ_t,a stimata con GRAS: struttura iniziale dal dettaglio FA per bene (per E tramite il raccordo BEA PEQ) più il 5% della composizione comune, bilanciata sui totali della Use (colonne F02E, F02S, F02N) e sull'investimento FA per industria; φR dalla colonna F02R per il residenziale.

## 7. Informazioni osservate nell'orizzonte usate da E6

E6 è una valutazione **retrospettiva**: usa dati osservati dell'orizzonte che valuta. L'elenco serve a distinguere ciò che il modello riceve da ciò che determina.

- Coefficienti B_t, D_t, Φ_t, φR_t, μ_t delle tavole di ciascun anno dell'orizzonte.
- Coefficienti di lavoro ℓ_j,t = FTE_j,t / x_j,t di ciascun anno.
- Obiettivi di consumo O2 = consumo privato osservato per prodotto e anno.
- Domanda pubblica, esportazioni, voci positive di F050, `Used` e `Other`: osservate.
- Offerta di lavoro L_t (FTE totali) e tetto alle importazioni: osservati per anno.
- δ: rapporto ΣD/ΣK sugli anni dell'orizzonte.
- κ: calibrato su x, K e utilizzo G.17 dell'anno iniziale; w: KLEMS 2012, anno interno a entrambi gli orizzonti.
- Deriva θ delle industrie G.17: crescita osservata nell'orizzonte della capacità G.17 e di K^cap.
- H9c: inviluppo 1997–2019, che comprende anni successivi al 2016.
- Scorte: σ_z calibrato nell'anno iniziale; banda 0,85–1,20 scelta perché contiene tutti i rapporti osservati 2012–2016 (massimo 1,164); composizione ψ dalla somma delle variazioni positive osservate (colonna F030) sugli anni dell'orizzonte.
- Fattori terminali H29: crescita osservata degli FTE e della produzione di HS nell'orizzonte.

La versione non anticipativa, con tutti questi elementi previsti da dati ≤ origine, è la pipeline `M71-E6-predittivo` (`docs/progetto/11_predittivo_note.md`, `docs/rapporto_M71-E6-predittivo.md`).

## 8. Risultati

`risultati/` contiene, per ogni passo, l'ultima esecuzione **ufficiale**: commit registrato, nessuna modifica non registrata, esito completato. Ogni cartella ha un `esecuzione.json` con commit, ambiente, esito della verifica dei dati, parametri e impronte degli output.

I file oltre 10 MB (dettaglio per industria del backtest predittivo) non sono copiati. Sono elencati con impronta in `MANIFEST.json` e si rigenerano con `python -m pianificazione71 predittivo` (circa 75 minuti).

**Riproducibilità tra piattaforme.**

- I parametri e i valori ottimi degli obiettivi si riproducono entro le tolleranze del solver. Un test fissa l'obiettivo di E6 con scarto < 1e-6.
- Le soluzioni primali possono differire tra piattaforme o versioni di numpy, perché l'LP ha ottimi multipli con gli stessi aggregati.
- Nel backtest predittivo, gli indicatori calcolati sulle variabili delle formulazioni LP differiscono in genere dell'1% tra l'esecuzione ufficiale e la replica su Linux, al massimo del 12% in un caso. Le graduatorie non cambiano. I numeri citati nei documenti sono quelli delle esecuzioni ufficiali.
