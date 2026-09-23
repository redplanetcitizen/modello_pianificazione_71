# Specifica formale del modello (v0.2.2)

22/09/2026. Modello di programmazione lineare intertemporale a 71 industrie, anni 2012–2016, prezzi 2012. Scritto da zero: nessun riferimento a `csvplan.jl`.

Specifica di ricerca verificabile. Ogni ipotesi è numerata (**H1, H2, …**) e ripresa nella mappa dei parametri (§10). Le verifiche empiriche ancora da completare sono segnate **[VERIFICA]**. Il registro delle decisioni (`03_registro_decisioni.md`) distingue scelte adottate, approssimazioni del primo test e verifiche aperte.

**v0.2.1:** O2 riformulato come programmazione per obiettivi generica, senza riferimento a autori specifici.

**Modifiche rispetto alla v0.1:** trattamento esplicito dei valori negativi; capacità legata a un aggregato del capitale per industria invece che a vincoli per tipo; RAS come stima condizionata alla struttura iniziale, con verifica preventiva dei margini; surplus ridefinito (lordo/netto, scomposizione, due raccordi); non additività delle serie concatenate; identità di controllo come misura degli scarti; condizione terminale di non depauperamento; `Used` e `Other` esogeni; test G.17 come controllo esterno parziale; nuovo ordine di implementazione.

---

## 1. Insiemi e indici

| Simbolo | Contenuto | Dimensione |
|---|---|---|
| J | Industrie I/O Summary (111CA … GSLE), comprese 5 industrie pubbliche | 71 |
| C | Prodotti: 71 prodotti I/O + `Used` (rottami e usato) + `Other` (importazioni non comparabili e rettifica verso il resto del mondo) | 73 |
| C₇₁ | Prodotti ordinari (esclusi Used e Other) | 71 |
| A | Tipi di capitale non residenziale: E attrezzature, S strutture, N proprietà intellettuale | 3 |
| R | Capitale residenziale, solo per l'industria Housing, trattato a parte (§4.3) | 1 |
| Z | Comparti delle scorte NIPA 5.8.5B (righe 2, 3, 5, 6, 8, 9, 11–15) | 11 |
| t | Anni 2012 … 2016; t₀ = 2012, T = 2016 | 5 |

## 2. Impostazione contabile

- **Tavole di base:** Make (V, industrie × prodotti) e Use (U, prodotti × industrie), Summary, prima delle ridefinizioni, prezzi alla produzione, una coppia per anno (**H1**).
- **Modello prodotti × industrie, senza tavola simmetrica.** Due vettori di attività, q (prodotti) e x (industrie), legati dalle quote di mercato:
  - coefficienti d'uso B_t = U_t · diag(x_t^obs)⁻¹ (prodotti × industrie);
  - quote di mercato D_t = V_t · diag(q_t^obs)⁻¹ (industrie × prodotti);
  - x_t = D_t q_t (**H2**: tecnologia dell'industria nella ripartizione dei prodotti secondari).
  Questa scelta evita i coefficienti negativi che nascerebbero dalla trasformazione in tavola simmetrica. **Non** elimina i valori negativi e le poste speciali già presenti nelle tavole originali.
- **Valori negativi e poste speciali** nelle tavole originali, trattati uno per uno e registrati:
  - importazioni (F050, negative per convenzione): diventano la variabile m ≥ 0 con segno invertito;
  - variazione delle scorte (F030): può essere negativa; è una variabile libera (§4.5);
  - imposte meno sussidi (V002): può essere negativa; non entra nei bilanci materiali;
  - righe `Used` e `Other` e loro celle negative: esogene (§4.8);
  - eventuali altri negativi nelle celle intermedie: elencati dalla pipeline e trattati caso per caso, senza azzeramenti silenziosi (**H3**).
- **Celle soppresse "..."** della Use: poste a 0, elencate, e il residuo rispetto ai totali pubblicati è misurato nelle identità di controllo (§6) (**H4**).
- **Prezzi 2012 e additività.**
  - Le tavole 2013–2016 sono deflazionate componente per componente (doppia deflazione). Il prodotto c prende l'indice di prezzo della produzione lorda dell'industria che lo produce in prevalenza (GDP by Industry) (**H5**).
  - Le serie in dollari concatenati **non si sommano** tra componenti. Ogni aggregato (per tipo di capitale, per industria, per comparto di scorte) si costruisce da valori correnti deflazionati componente per componente con i rispettivi indici ribasati al 2012, oppure da indici di quantità. Mai sommando serie concatenate (**H6**).

## 3. Variabili (per ogni t)

| Variabile | Significato | Dim. |
|---|---|---|
| q_t ≥ 0 | produzione interna per prodotto | 73 |
| x_t ≥ 0 | produzione lorda per industria | 71 |
| m_t ≥ 0 | importazioni per prodotto (ordinari) | 71 |
| γ_t ≥ 0 | livello del consumo privato (paniere a composizione fissa) | 1, oppure 71 nella variante per obiettivi (O2) |
| I_{j,a,t} ≥ 0 | investimento lordo privato dell'industria j nel tipo a | 71×3 |
| K_{j,a,t} ≥ 0 | stock netto di capitale a inizio anno | 71×3 |
| I^R_t, K^R_t ≥ 0 | investimento e stock residenziale | 1 + 1 |
| S_{z,t} ≥ 0 | stock di scorte a fine anno per comparto | 11 |
| ΔS_{z,t} libera | variazione delle scorte | 11 |
| r_t ≥ 0 | residuo materiale del bilancio | 73 |

Grandezze esogene: consumi e investimenti pubblici g_t (F06–F10), esportazioni e_t (F040), offerta di lavoro L̄_t, righe `Used` e `Other` (§4.8).

Dimensione indicativa: circa 3.500 variabili in tutto. È un LP piccolo.

## 4. Vincoli

### 4.1 Bilancio materiale per prodotto

q_t + m_t = B_t x_t + ĉ_t γ_t + g_t + Σ_a Φ_{a,t} I_{·,a,t} + φ^R_t I^R_t + Ψ_t ΔS_t + e_t + r_t

- ĉ_t: composizione del consumo privato, colonna F010 normalizzata a somma 1 (**H7**).
- Φ_{a,t}: composizione per prodotto dell'investimento di tipo a di ciascuna industria. Colonne a somma 1. È la tavola stimata dei flussi di capitale (§5.2).
- φ^R_t: composizione della colonna F02R.
- Ψ_t: composizione per prodotto delle scorte di ciascun comparto (§5.4).
- r_t: residuo materiale del bilancio LP (§7).

### 4.2 Quote di mercato
x_t = D_t q_t.

### 4.3 Capacità

**Ipotesi di base (approssimazione del primo test):** un aggregato lineare del capitale per industria.

K^cap_{j,t} = Σ_a w_{j,a} K_{j,a,t},  x_{j,t} ≤ K^cap_{j,t} / κ_j

- I pesi w_{j,a} sono calibrati sul 2012, proporzionali ai prezzi impliciti di noleggio (costi d'uso) per unità di stock di ciascun tipo, dove KLEMS li fornisce per industria e tipo di asset (**H8**).
- È un'**approssimazione locale dichiarata**. I costi d'uso servono normalmente ad aggregare le *variazioni* dei servizi del capitale (indice di Törnqvist, come nel metodo Fed), non come pesi fissi sui livelli degli stock. Qui si usano come coefficienti fissi al 2012, sottoposti a sensibilità.
- κ_j = K^cap_{j,2012} · u_{j,2012} / x^obs_{j,2012}, con u l'utilizzo della capacità dalla Fed G.17 dove esiste, altrimenti u = 1 (**H9**).
- **Stock netto come proxy della capacità (H10).** BEA usa l'ammortamento geometrico per la maggior parte degli asset, quindi si parte dallo stock netto. Valore dello stock, servizi del capitale e massimo prodotto sostenibile restano grandezze diverse: il proxy va verificato (§6.3). **[VERIFICA]**
- **Varianti di sensibilità** che delimitano la tecnologia:
  - *complementarità perfetta:* un vincolo per tipo, x_j ≤ K_{j,a} / κ_{j,a};
  - *sostituibilità perfetta:* l'aggregato lineare.
  La tecnologia effettiva non è identificata dai dati di stock e ammortamento: le due varianti ne danno i limiti.
- **Residenziale:** x_{Housing,t} ≤ K^R_t / κ^R. È il rapporto tra servizi abitativi e stock di abitazioni, con κ^R calibrato sul 2012.
- **[VERIFICA]** Quali variabili per asset contenga il file KLEMS archiviato e come i suoi tipi corrispondano a E, S, N. BEA-BLS pubblicano anche tavole a dettaglio ampliato: se il file archiviato non basta, vanno scaricate.

### 4.4 Accumulazione

K_{j,a,t+1} = (1 − δ_{j,a}) K_{j,a,t} + I_{j,a,t}  e analogo per K^R.

- δ_{j,a}: tassi impliciti di ammortamento (DetailNonres_rate), aggregati per tipo con pesi degli stock a prezzi correnti (**H11**).
- L'investimento dell'anno t diventa operativo in t+1 (**H12**). Variante: operativo in parte già in t.
- K_{2012} osservato.

### 4.5 Scorte
- S_{z,t} = S_{z,t−1} + ΔS_{z,t}, con S_{2011} osservato (5.8.5B, 2011Q4).
- S_{z,t} ≥ σ_z · Σ_{j∈z} x_{j,t}, con σ_z il rapporto osservato nel 2012 (**H13**).

### 4.6 Lavoro
Σ_j ℓ_{j,t} x_{j,t} ≤ L̄_t, con ℓ dalle ore KLEMS e L̄_t le ore osservate come limite superiore (**H14**). Variante: L̄ più alto.

### 4.7 Conti con l'estero
- Saldo: Σ e_{c,t} − Σ m_{c,t} ≥ −F̄_t, con F̄_t il disavanzo osservato (**H15**).
- Bande sulle importazioni: m_{c,t} ≤ (1+ε) μ_{c,t} · (uso interno)_c, con μ dalla Import matrix ed ε parametro di test.

### 4.8 `Used` e `Other`
Esogeni ai valori osservati di ciascun anno e contabilizzati separatamente (**H16**).
- `Used` non è assimilato a nuova formazione di capitale.
- `Other` comprende importazioni non comparabili e rettifica verso il resto del mondo.
- Nel test storico fissarli ai valori osservati è un **condizionamento ex post**, non un comportamento generato dal modello; negli scenari va dichiarato come tale.

### 4.9 Condizione terminale (non depauperamento)
Σ_j K_{j,a,T+1} ≥ Σ_j K_{j,a,2012} per ciascun tipo a, e K^R_{T+1} ≥ K^R_{2012} (**H17**).

- È una regola esplicita di non depauperamento, aggregata per tipo: consente di riallocare il capitale tra industrie.
- Lo stock osservato nel 2017 **non** è un vincolo. È un confronto esterno: imporlo incorporerebbe nel risultato la traiettoria storica da valutare.
- **Sensibilità:** crescita minima prefissata dello stock per tipo.
- **Controllo obbligatorio della distribuzione annuale dell'investimento.** Il solo vincolo di mantenimento può spingere il modello a rinviare l'investimento all'ultimo anno, perché investire prima comporta ammortamento e il modello può attendere. L'esito dipende dalla funzione obiettivo e da quando l'investimento aumenta la capacità (H12). Ogni soluzione riporta il profilo temporale di I per tipo.

### 4.10 Pavimento del consumo
γ_t ≥ γ_min, comune a O3 e alle varianti che lo richiedono.

## 5. Costruzione dei parametri

### 5.1 Matrici tecniche
B_t e D_t come al §2, per ogni anno, a prezzi 2012.

### 5.2 Composizione dell'investimento Φ (stima condizionata)

Il RAS ripartisce un totale coerente tra righe e colonne. **Non** ricava dai soli margini una struttura di celle identificata univocamente: il risultato dipende dalla matrice iniziale, che è quindi un'ipotesi del modello, dichiarata e sottoposta a sensibilità.

**Verifiche preliminari dei margini, per anno e tipo** (prima di ogni bilanciamento):
- **Perimetro:** investimento privato non residenziale per tipo nei Fixed Assets contro le colonne F02E, F02S, F02N della Use.
- **Valutazione:** la Use a prezzi alla produzione registra i margini di commercio e trasporto come righe di prodotto a sé; i Fixed Assets sono a prezzi d'acquisto. I totali devono coincidere; lo scarto si misura e si spiega.
- **Totali:** coerenza con la release (settembre 2025 per tutte le fonti).
- Se i margini non coincidono, lo scarto si documenta e si decide come ripartirlo **prima** del RAS.

**Margini:**
- colonne: investimento dell'industria j nel tipo a, dai Fixed Assets dettagliati, con concordanza 74 → 71 (**H18**);
- righe: investimento per prodotto dalle colonne F02 della Use.

**Struttura iniziale (H19), dichiarata:**
- E: raccordo PEQ Summary (prodotti per tipo di attrezzatura) combinato con la composizione per tipo di bene delle attrezzature di ciascuna industria nei Fixed Assets;
- S e N: righe della Use per tipo, uguali per tutte le industrie.
- Sensibilità: strutture iniziali alternative, misurando quanto cambia Φ.

**Tavola 1997:** stima di ricerca BEA. Serve come confronto diagnostico **solo per E e S**, aggregata a livelli comparabili. Per N non è utilizzabile, perché precede la capitalizzazione di R&S e originali artistici (revisione 2013). Se in una variante la si usa come struttura iniziale, diventa un'ipotesi che influenza il risultato e va dichiarata come tale.

### 5.3 Capitale e ammortamenti
K^obs e δ dai file M3 (stk1, rate) per industria e tipo di bene. L'aggregazione per tipo usa valori correnti deflazionati componente per componente (H6). Gli indici a costo fisso (base 2017) sono ribasati al 2012 (**H20**).

### 5.4 Scorte
- Stock per comparto da 5.8.5B (IV trimestre), deflazionati con 5.8.9B ribasato al 2012.
- Composizione Ψ_z: colonna F030 ripartita sui prodotti del comparto (**H21**).
- Corrispondenza comparti → industrie: tabella fissa (**H22**).

### 5.5 Lavoro
ℓ_{j,t} = ore_{j,t} / x^obs_{j,t}, dalle ore KLEMS, con concordanza dove le classificazioni differiscono.

### 5.6 Settore pubblico
Le 5 industrie pubbliche producono servizi assorbiti da g_t. Investimenti e capitale pubblici esogeni nella versione 0 (**H23**); variante endogena dalla Sezione 7.

## 6. Identità di controllo

Con i valori osservati inseriti (x^obs, q^obs, m^obs, γ = 1, I^obs, ΔS^obs) si misurano gli scarti di ciascun vincolo, per anno. **Uno scarto va identificato e spiegato, non attribuito in anticipo alla pipeline.**

Prima di confrontare, si verifica che le due parti di ogni identità abbiano **stesso perimetro e stessa base di prezzo**.

### 6.1 Bilancio materiale e quote di mercato
Residuo per prodotto; x = Dq esatto per costruzione. Cause attese di scarto: celle soppresse (H4), arrotondamenti, deflazione (H5).

### 6.2 Accumulazione
Scarto K^obs_{t+1} − [(1−δ)K^obs_t + I^obs_t]. Cause possibili:
- rivalutazioni (valori correnti);
- altre variazioni di volume degli asset (distruzioni, riclassificazioni);
- non additività delle serie concatenate (se violata H6);
- differenze tra tassi medi e ammortamento effettivo.

### 6.3 Capitale e capacità (controllo esterno parziale)
Nelle industrie coperte dalla G.17 si confronta la capacità implicita K^cap/κ con la capacità Fed. Il controllo **non è pienamente indipendente**: per molte industrie manifatturiere la Fed stima la capacità anche con servizi del capitale e anzianità degli impianti. Si separano due gruppi:
- industrie in cui la capacità G.17 deriva soprattutto da misure fisiche o indagini sull'utilizzo: controllo esterno più informativo;
- industrie in cui il capitale entra nella stima della capacità: il confronto è in parte circolare, da leggere come tale.
**[VERIFICA]** classificazione dei gruppi dalla metodologia G.17.

## 7. Surplus: definizioni

1. **Residuo materiale del bilancio LP (r_t).** Produzione disponibile che nessun uso assorbe. Positivo solo dove un prodotto non è scarso; segnala capacità in eccesso o composizioni rigide.

2. **Prodotto finale lordo e netto.**
   - Prodotto finale lordo: q + m − Bx (a prezzi 2012, al netto di `Used`/`Other` esogeni).
   - Prodotto netto: prodotto finale lordo meno l'ammortamento Σ δ K.

3. **Surplus economico** = prodotto netto − consumo privato, scomposto in:

   consumo pubblico + investimento netto (I − δK) + variazione delle scorte + saldo con l'estero (e − m) + residuo materiale.

   **Solo l'investimento netto è capitale aggiuntivo.** Il resto del surplus ha altre destinazioni e non equivale a beni disponibili per costruire capitale.

La catena **surplus → investimento → capitale → capacità → produzione** richiede due raccordi, verificati separatamente:
- **materiale:** prodotti d'investimento (Φ) → tipi di asset → industrie utilizzatrici → capacità (§4.3). È il cuore del modello;
- **contabile:** reddito (V003 e altre voci) → risparmio → investimento. Serve al confronto con l'economia osservata ed è tenuto distinto.

Il reddito lordo di gestione (V003) è una categoria di reddito, non un bilancio materiale: si riporta, non si confonde con le grandezze sopra.

## 8. Obiettivi alternativi

Tutti condividono i vincoli del §4. Per ciascuno si dichiarano **scala, normalizzazione e vincoli aggiuntivi**.

| Codice | Obiettivo | Scala e normalizzazione | Uso |
|---|---|---|---|
| O1 | max Σ_t β^t γ_t | γ = 1 al paniere osservato 2012; β dichiarato | Riferimento |
| O2 | Programmazione per obiettivi: massimizzazione di una funzione concava e separabile del grado di soddisfazione per prodotto rispetto a obiettivi γ*_{c,t}, con rendimenti decrescenti oltre l'obiettivo; approssimata a tratti lineari senza uscire dall'LP | rapporti di soddisfazione adimensionali; numero e posizione dei tratti dichiarati | Pianificazione con obiettivi espliciti |
| O3 | max Σ K_{T+1}, capitale terminale a valore dello stock (dollari 2012), con γ ≥ γ_min (decisione 22/09; la versione a pesi di costo d'uso w resta come variante, `pesi_o3 = "costo_uso"`) | stock netto a prezzi 2012 | Accumulazione |
| O4 | min distanza L1 dalle traiettorie osservate | scarti relativi, normalizzati per industria | **Solo diagnostica retrospettiva** |

La **scelta** di pesi, obiettivi γ* e β è una decisione sociale e istituzionale. Il loro **effetto numerico** e la sensibilità dei risultati fanno invece parte delle verifiche tecniche.

## 9. Ordine di implementazione

1. **Sistema prodotti–industrie:** B, D per anno, trattamento dei negativi e delle celle soppresse, deflazione, identità §6.1.
2. **Margini dell'investimento:** verifiche di perimetro, valutazione e totali (§5.2).
3. **Stima di Φ** per anno e tipo, con strutture iniziali alternative; confronto con la tavola 1997 per E e S.
4. **Capitale:** stock, ammortamento, identità di accumulazione (§6.2).
5. **Rapporto tra capitale e capacità:** κ, pesi w, confronto G.17 (§6.3). È il passaggio che decide se la dinamica del capitale sarà economicamente interpretabile, oltre che contabilmente coerente.
6. **Modello statico 2012**, poi dinamico 2012–2016, con blocchi attivabili da configurazione.
7. **Obiettivi O1–O4 e sensibilità.**

## 10. Mappa dei parametri

| Parametro | Dim. | Fonte (release / file) | Ipotesi |
|---|---|---|---|
| U_t, V_t | 73×71, 71×73 | bea/2025-09 M1: IOUse/IOMake_Before_Redefinitions_PRO_Summary | H1–H4 |
| Deflatori di prodotto | 73×5 | bea/2026-09-23 api GDPbyIndustry | H5, H6 |
| ĉ_t | 73 | Use F010 | H7 |
| g_t, e_t | 73 | Use F06C…F10N, F040 | H23 |
| μ_t | 71 | bea/2026-09-22 M1: ImportMatrices_Before_Redefinitions_Summary | H15 |
| `Used`, `Other` | 2×(71+fd) | Use, righe Used e Other | H16 |
| Φ_{a,t}, φ^R_t | 73×71 per tipo | bea/2026-09-22 M3 (inv1), M4 (PEQBridge_Summary); Use F02E/S/N/R; RAS | H18, H19 |
| Confronto Φ (E, S) | 180×123 | bea/2025-09 M5: flow1997 + rettifiche | solo diagnostica |
| K^obs, δ | 71×3 + R | bea/2026-09-22 M3: stk1, stk2, DetailNonres_rate, detailresidential | H6, H10, H11, H20 |
| w_{j,a} | 71×3 | bls/2026-09-18 KLEMS (costi d'uso per asset) **[VERIFICA]** | H8 |
| κ_j, κ^R | 71 + 1 | K^obs, x^obs, Fed G.17 | H9, H10 |
| S^obs, Ψ | 11, 73×11 | bea/2026-09-23 api NIPA T50805B, T50809B; Use F030 | H13, H21, H22 |
| ℓ_t, L̄_t | 71×5 | bls/2026-09-18 KLEMS | H14 |
| F̄_t | 5 | Use F040, F050 | H15 |
| Concordanza FA 74 → I/O 71 | — | da costruire; controllo con bea/2025-09 concordanze | H18 |
| Capacità G.17 | industrie coperte | fed_g17/2026-09-18 | §6.3 |

## 11. Dizionario delle ipotesi

| Codice | Ipotesi | Tipo |
|---|---|---|
| H1 | Matrici Make/Use annuali | scelta |
| H2 | Tecnologia dell'industria nelle quote di mercato | scelta |
| H3 | Negativi originali trattati caso per caso | scelta |
| H4 | Celle soppresse a 0, residuo misurato | approssimazione |
| H5 | Prezzo del prodotto = prezzo dell'industria produttrice prevalente | approssimazione |
| H6 | Nessuna somma di serie concatenate | scelta |
| H7 | Composizione del consumo osservata e fissa per anno | approssimazione |
| H8 | Aggregato lineare del capitale con pesi da costi d'uso 2012 | approssimazione (primo test) |
| H9 | u = 1 fuori dalla copertura G.17 | approssimazione; **sostituita da H9b** (D0: incompatibile con i dati) |
| H9b | u_2012 = 0,772 (utilizzo G.17 dell'industria totale) fuori dalla copertura G.17, escluso HS | approssimazione adottata (22/09) |
| H10 | Stock netto come proxy della capacità | approssimazione da verificare |
| H11 | δ per tipo come media ponderata | approssimazione |
| H12 | Investimento operativo dall'anno successivo | scelta, con variante |
| H13 | Rapporto scorte/produzione minimo al livello 2012 | approssimazione; **sostituita da H13b** |
| H13b | Minimo scorte/produzione = 0,85·σ_2012 | approssimazione adottata (22/09) |
| H13c | Massimo scorte/produzione = 1,20·σ_2012; scorte finali ≥ scorte 2011 | approssimazione adottata (22/09) |
| H14 | Ore osservate come massimo disponibile | approssimazione |
| H15 | Disavanzo estero massimo = osservato | scelta, con sensibilità |
| H16 | `Used` e `Other` esogeni (condizionamento ex post) | scelta (primo test) |
| H17 | Non depauperamento per tipo; 2017 solo come confronto | scelta, con sensibilità |
| H18 | Concordanza FA 74 → I/O 71 | da costruire |
| H19 | Struttura iniziale del RAS | approssimazione dichiarata, con sensibilità |
| H20 | Ribasamento 2017 → 2012 | scelta |
| H21 | Composizione delle scorte da F030 | approssimazione |
| H22 | Corrispondenza comparti scorte → industrie | approssimazione |
| H23 | Settore pubblico esogeno | scelta (versione 0) |
