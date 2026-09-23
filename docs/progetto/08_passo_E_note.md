# Passo E — note sui test

Aggiornato il 22/09/2026. Calibrazione adottata: H9b e H13b (vedi `07_passo_D_note.md`).

## E1 — gradualità dell'investimento applicata a O2

Esecuzione `M71-E1-gradualita-O2`, comando `python -m pianificazione71 e1`.

**O2 resta invariato.** Le nuove opzioni del modello sono disattivate per default. Il caso `O2` di E1 coincide con O2 del passo D2 (differenza massima 0 sugli aggregati; obiettivo 4,809292). O2 si recupera così com'è con le opzioni predefinite.

### Meccanismi introdotti

| Codice | Meccanismo | Formulazione LP | Approssima |
|---|---|---|---|
| H25a | Limite alla variazione annua dell'investimento per tipo | (1−g)·I_{a,t−1} ≤ I_{a,t} ≤ (1+g)·I_{a,t−1}, somma sulle industrie; I_2011 osservato come base | Costi di aggiustamento convessi (vincolo rigido) |
| H25b | Penalità sulle variazioni annue per tipo | Variazione relativa rispetto a I_{a,2011}: libera fino al 5%, poi penalità p per unità, nella scala dei punteggi di O2 | Costo di aggiustamento convesso (lineare a tratti) |
| H26 | Tempi di costruzione per S e R | Spesa_t = ½·avvii_t + ½·avvii_{t−1} per industria; avvii 2011 = spesa 2011 (ipotesi di regime). Accumulazione e capacità invariate (convenzione BEA: lo stock cresce con la spesa effettuata) | Tempi di costruzione (Kydland–Prescott) |

### Risultati: scarto percentuale medio assoluto dall'osservato

Anni 2012–2016; per gli stock 2012–2017.

| Caso | Produzione | Consumo | Investimento (media 4 tipi) | Stock (media 4 tipi) | Consumo cumulato | Anni con inv. netto < 0 |
|---|---|---|---|---|---|---|
| O2 (passo D) | 0,8 | 11,9 | 64,0 | 12,9 | 64.728 | 4 |
| Limite ±10% | 1,4 | 10,6 | 27,6 | 5,7 | 64.022 | 2 |
| Limite ±15% | 1,3 | 10,8 | 28,4 | 6,4 | 64.116 | 3 |
| Limite ±25% | 1,2 | 11,1 | 31,8 | 7,6 | 64.267 | 3 |
| Penalità p = 0,01 | 1,4 | 10,4 | 25,9 | 4,9 | 63.884 | 2 |
| Penalità p = 0,1 | 1,4 | 10,4 | 25,7 | 4,8 | 63.872 | 2 |
| Tempi di costruzione S, R | 0,9 | 11,8 | 58,9 | 12,8 | 64.667 | 4 |
| Combinato (±15% + tempi S, R) | 1,4 | 10,8 | 28,2 | 6,4 | 64.098 | 3 |

### Lettura

1. **Effetto sugli scarti.** La gradualità dimezza lo scarto sull'investimento, da 64% a 26–32%, e riduce quello sugli stock da 13% a 5–8%. Il costo in consumo è piccolo: −0,7…−1,3% del consumo cumulato, cioè 460–860 miliardi su cinque anni.
2. **Tempi di costruzione.** Da soli agiscono solo sulle strutture (scarto S da 41% a 23%). Impediscono i crolli ma non i picchi: il residenziale resta a +106%.
3. **Livello della penalità.** Con p = 0,01 e p = 0,1 le soluzioni sono quasi identiche. Il modello sfrutta la variazione libera del 5% e quasi non paga la penalità: il risultato dipende dalla soglia, non da p.
4. **La direzione resta sbagliata.**
   - Con la penalità l'investimento scende regolarmente del 5% l'anno (E da 845 a 702, N da 588 a 463), mentre nell'economia osservata cresce del 3–5% l'anno.
   - Con il limite del 15% ha un profilo a U.
   - Lo scarto sul consumo resta intorno al 10–11%.

   La gradualità corregge la forma della traiettoria, non il livello. Il livello dipende dalla capacità libera iniziale (H9b) e dalla condizione terminale di solo mantenimento dello stock: il modello consuma di più investendo meno, perché la capacità non manca.
5. **Prossima verifica.** Occorre agire sulle cause del livello:
   - sensibilità dell'utilizzo iniziale nei servizi (u fuori G.17 tra 0,772 e 1);
   - condizione terminale di crescita (es. +5–10% per tipo, coerente con la crescita osservata dello stock);
   - non depauperamento per industria.

## E2 — orizzonte esteso 2010–2019, confronto sul 2012–2016 (variante b)

Esecuzione `M71-E2-orizzonte-2010-2019`, comando `python -m pianificazione71 e2`.

**Parametrizzazione.** L'orizzonte è ora un parametro di `costruisci(cfg, anni)`. Con il default 2012–2016 tutti i parametri coincidono con quelli del passo D (differenza massima 0 su B, D, Φ, K0, δ, w, κ, θ, ℓ, σ, μ).

**Calibrazione 2010–2019.** Tutte le grandezze di calibrazione sono riferite all'anno di avvio 2010:

- stock iniziale 2010, κ con l'utilizzo G.17 del 2010, σ delle scorte del 2010;
- deriva θ stimata sul 2010–2019 e δ medio sul 2010–2019;
- pesi w invariati (2012);
- H9b applicata al 2010: u fuori dalla copertura G.17 = 0,734 (industria totale G.17 nel 2010, anno di ripresa dopo la recessione);
- H13b invariata;
- lavoro = FTE osservati;
- condizione terminale: stock 2020 ≥ stock 2010 per tipo.

**Controllo al punto osservato 2010–2019.**

- Capacità: 0–3 industrie oltre il limite per anno (441, 5415, 485; HS di poco).
- Scorte: 1–2 comparti sotto il minimo nel 2016–2019 (il rapporto osservato scende a 0,69·σ_2010).

La traiettoria osservata è quindi quasi, ma non del tutto, ammissibile.

### Scarto percentuale medio assoluto dall'osservato, anni 2012–2016

| Caso | Produzione | Consumo | Investimento | Stock | Consumo cumulato 2012–16 | Anni con inv. netto < 0 (2012–16) |
|---|---|---|---|---|---|---|
| O2, 2012–16 | 0,8 | 11,9 | 64,0 | 12,9 | 64.728 | 4 |
| Limite ±15%, 2012–16 | 1,3 | 10,8 | 28,4 | 6,4 | 64.116 | 3 |
| Penalità, 2012–16 | 1,4 | 10,4 | 25,7 | 4,8 | 63.872 | 2 |
| O2, 2010–19 | 0,4 | 12,7 | 49,7 | 23,8 | 65.242 | 3 |
| Limite ±15%, 2010–19 | 0,5 | 11,3 | 42,5 | 13,3 | 64.365 | 4 |
| Penalità, 2010–19 | 0,8 | 10,3 | 30,9 | 8,1 | 63.829 | 1 |

### Lettura

1. **L'orizzonte esteso non avvicina il modello all'economia osservata.**
   - La produzione migliora: 0,4–0,8%.
   - Lo scarto su investimento e stock resta o peggiora: con O2 e il limite gli stock si allontanano (24% e 13%).
2. **Con la penalità la traiettoria 2010–2019 è regolare ma stazionaria.**
   - L'investimento netto resta vicino a zero per tutto il decennio (tra −31 e +77 miliardi l'anno); nell'economia osservata cresce.
   - Il consumo parte già +7% nel 2010 e cresce con la produzione.
3. **Causa: il modello non ha bisogno di accumulare.**
   - Nel 2010 H9b concede il 36% di capacità libera fuori dalla copertura G.17 (1/0,734 − 1). La produzione osservata cresce del 23% nel 2010–2019 e il lavoro disponibile del 17%.
   - La capacità iniziale basta a coprire quasi tutta la crescita del decennio senza investimento netto.
   - La condizione terminale chiede solo di mantenere lo stock del 2010.

   Il turnpike del modello è dunque un sentiero di semplice mantenimento del capitale, non quello di accumulazione osservato. Allungare l'orizzonte rende questo comportamento più evidente, anziché correggerlo.
4. **Implicazione.**
   - Gli scarti su investimento e stock non sono effetti di bordo: derivano dal fatto che nel modello il capitale ha valore solo come capacità, e la capacità calibrata non è scarsa.
   - Le verifiche decisive riguardano la calibrazione della capacità nei servizi (H9b, soprattutto se applicata a un anno di crisi) e una condizione terminale coerente con la crescita (stock finale ≥ stock iniziale × crescita della produzione o del lavoro).

## E3 — funzione d'investimento stimata fuori campione, inserita in O2 (2010–2019)

Esecuzione `M71-E3-funzione-investimento`, comando `python -m pianificazione71 e3`.

**Dati e stima.** Per tipo di capitale, sullo stesso perimetro del modello:

- investimento e stock di inizio anno Fixed Assets a prezzi 2012;
- produzione a prezzi 2012 delle industrie private (per R: HS).

La stima usa il 1998–2009, cioè solo anni precedenti l'orizzonte del modello, quindi senza circolarità. Le regole stimate sono due:

- **acceleratore:** I/K = c0 + c1·X/K;
- **tasso costante:** I/K pari alla media 2005–2009.

| Tipo | c0 | c1 | R² stima | Tasso 2005–09 | Scarto fuori campione acceleratore 2010–19 | Scarto fuori campione tasso costante 2010–19 |
|---|---|---|---|---|---|---|
| E | −0,058 | 0,043 | 0,69 | 0,163 | 23,7% | 9,2% |
| S | 0,035 | 0,005 | 0,01 | 0,044 | 16,6% | 11,4% |
| N | 0,206 | 0,006 | 0,47 | 0,284 | 11,2% | 6,6% |
| R | −0,151 | 1,893 | 0,11 | 0,041 | 54,9% | 36,1% |

L'acceleratore stimato prevede l'investimento 2010–2019 peggio della regola a tasso costante. Il periodo di stima comprende la bolla tecnologica e quella immobiliare: la relazione investimento–produzione non è stabile. Per il residenziale entrambe le regole falliscono.

**Inserimento in O2 (H28).** Le regole sono applicate in forma endogena: K e X sono le variabili del modello. Due modalità:

- banda ±10% attorno alla regola;
- penalità a gradini sullo scarto: libera fino al 5% di I_2009, poi 0,1 fino al 15%, poi 0,5 per unità relativa.

Caso diagnostico aggiuntivo: investimento per tipo fissato ai valori osservati.

| Caso | Consumo cumulato 2010–19 | Anni inv. netto < 0 | Produzione | Consumo | Investimento | Stock |
|---|---|---|---|---|---|---|
| O2 | 132.244 | 6 | 0,6 | 12,2 | 63,0 | 20,0 |
| Acceleratore, banda ±10% | 126.697 | 0 | 1,9 | 7,5 | 23,5 | 9,8 |
| Tasso costante, banda ±10% | 127.137 | 0 | 2,2 | 7,8 | 23,2 | 10,7 |
| Tasso costante, penalità | 125.528 | 0 | 2,4 | 6,4 | 23,9 | 10,2 |
| Investimento osservato | 125.095 | 0 | 2,9 | 6,2 | 0,0 | 1,4 |

Le ultime quattro colonne sono lo scarto percentuale medio assoluto dall'osservato, 2010–2019.

### Lettura

1. **Scomposizione del vantaggio di consumo.** Anche con l'investimento per tipo uguale a quello osservato, il consumo resta +6,2% sopra l'osservato e la produzione +2,9%. Circa metà dello scarto di O2 (12,2%) viene dalla minore accumulazione. L'altra metà viene da:
   - la riallocazione della produzione corrente;
   - soprattutto, la capacità libera ipotizzata (H9b: 36% nel 2010 fuori dalla copertura G.17), che il modello usa e l'economia osservata no.
2. **Con le regole il disinvestimento netto sparisce e gli scarti su investimento e stock si dimezzano** (23% e 10%). L'investimento però si colloca sistematicamente sul bordo inferiore della banda: il piano investe il minimo consentito.
   - Con la regola a tasso costante, E resta piatto intorno a 780 mentre nell'economia osservata cresce da 790 a 1.290.
   - La regola è autoreferenziale (I = i·K con K endogeno): se il modello accumula poco, la regola chiede poco.
3. **Conclusione.** Il livello dell'accumulazione nel modello non è determinato dai dati ma da ciò che il piano valuta:
   - il consumo entro l'orizzonte;
   - una condizione terminale di solo mantenimento;
   - una capacità calibrata abbondante.

   Una regola comportamentale impone la forma della traiettoria, non la motivazione ad accumulare. Le verifiche successive riguardano la capacità nei servizi e il valore del capitale a fine orizzonte.

## E4 — taratura della capacità fuori G.17 sull'inviluppo dei massimi 1997–2019 (H9c)

Esecuzione `M71-E4-taratura-capacita`, comando `python -m pianificazione71 e4`. È una verifica di taratura, non uno stress test: gli obiettivi di O2 restano uguali al consumo osservato.

**Metodo.** Per le 42 industrie senza dati G.17 e per HS si calcola il rapporto r = x / K^cap sul 1997–2019 (produzione e capitale a prezzi 2012, pesi w del 2012). Due varianti:

- **inviluppo:** capacità = K^cap × max r;
- **inviluppo con tendenza (peak-to-peak):** log r = α + g·t + e; capacità = K^cap × exp(α + g·t + max e), con deriva θ_j = e^g − 1.

Il massimo di r cade quasi sempre nel 1997–2000 (26 industrie su 43), perché il rapporto produzione/capitale scende nel tempo per l'aumento dell'intensità di capitale. Per questo l'inviluppo senza tendenza dà un margine simile a quello di H9b. Utilizzo implicito medio, pesato sulla produzione:

| Anno di avvio | Uniforme (H9b) | Inviluppo | Inviluppo con tendenza |
|---|---|---|---|
| 2012 | 0,772 | 0,786 | 0,881 |
| 2010 | 0,734 | 0,759 | 0,845 |

**Risultati.**

| Orizzonte | Metodo | Violazioni al punto osservato | O4 | Punteggio O2 / massimo | Consumo a +20% | Eccesso di consumo cumulato | Anni inv. netto < 0 |
|---|---|---|---|---|---|---|---|
| 2012–16 | uniforme | 4 | 0,0129 | 99,2% | 55% | +11,9% | 4 |
| 2012–16 | inviluppo | 3 (≤ 0,5%) | 0,0024 | 99,2% | 54% | +12,0% | 4 |
| 2012–16 | inviluppo con tendenza | 2 (≤ 0,4%) | 0,0026 | 99,1% | 49% | +10,9% | 2 |
| 2010–19 | uniforme | 18 (fino a 1,37) | 0,0905 | 99,2% | 55% | +12,4% | 6 |
| 2010–19 | inviluppo | 8 (≤ 2%, più 213 G.17) | 0,0148 | 99,2% | 55% | +12,5% | 7 |
| 2010–19 | inviluppo con tendenza | 10 (≤ 1%, più 213 G.17) | 0,0166 | 99,1% | 50% | +11,1% | 5 |

Il prezzo ombra medio del lavoro resta intorno a 10⁻⁶ in tutti i casi.

### Lettura

1. **La taratura sull'inviluppo migliora la coerenza con i dati.** La traiettoria osservata diventa quasi esattamente ammissibile: O4 scende da 0,013 a 0,002 sul 2012–16 e da 0,091 a 0,015 sul 2010–19. Le violazioni residue sono ≤ 1–2%, salvo l'industria 213 (G.17). La variante con tendenza è la più coerente con il metodo peak-to-peak e dimezza il margine di capacità rispetto a H9b.
2. **O2 però cambia poco.** Resta saturo (punteggio 99%, metà del consumo al tetto +20%), con un eccesso di consumo di +11%. La variante con tendenza riduce lo scarto sull'investimento da 64% a 49% e gli anni di disinvestimento.
3. **Conclusione di taratura.**
   - La capacità libera fuori G.17 non è la fonte principale dell'eccesso di consumo di O2.
   - L'eccesso corrisponde in buona parte alla minore accumulazione: l'investimento del modello è inferiore all'osservato di 500–1.500 miliardi l'anno, lo stesso ordine di grandezza dell'eccesso di consumo (1.000–1.800 miliardi l'anno).
   - Il resto (circa 6%, vedi E3) viene dalla riallocazione.
   - Il parametro che governa l'accumulazione è la condizione terminale, che oggi chiede solo di mantenere lo stock iniziale.

## E5 — taratura standard H9c e condizione terminale tarata (H29)

Esecuzione `M71-E5-taratura-terminale`, comando `python -m pianificazione71 e5`.

H9c (inviluppo con tendenza) è ora la taratura standard dei nuovi test (decisione del 22/09). La condizione terminale tarata impone:

stock finale del gruppo ≥ fattore × stock iniziale

Il fattore è la crescita osservata di una grandezza di flusso nell'orizzonte, estesa all'intervallo dello stock. Non si usa lo stock osservato, per non incorporare la traiettoria storica. Varianti:

- **produzione per tipo:** E, S, N ≥ crescita della produzione privata; R ≥ crescita di HS;
- **produzione aggregata:** E+S+N insieme ≥ crescita della produzione; R ≥ crescita di HS;
- **lavoro aggregata:** E+S+N ≥ crescita degli FTE; R ≥ crescita di HS.

| Orizzonte | Terminale | Fattori | Osservato / richiesto | O4 | Consumo a +20% | Eccesso di consumo | Anni inv. netto < 0 |
|---|---|---|---|---|---|---|---|
| 2012–16 | mantenimento | 1 | E 1,23; S 1,05; N 1,23; R 1,04 | 0,003 | 49% | +10,9% | 2 |
| 2012–16 | produzione per tipo | 1,133 (R 1,016) | **S 0,92** | 2,19 | 33% | +7,5% | 0 |
| 2012–16 | produzione aggregata | 1,133 (R 1,016) | **ESN 0,99** | 0,24 | 37% | +8,3% | 0 |
| 2012–16 | lavoro aggregata | 1,101 (R 1,016) | ESN 1,02; R 1,03 | 0,003 | 39% | +9,0% | 1 |
| 2010–19 | mantenimento | 1 | E 1,44; S 1,09; N 1,55; R 1,08 | 0,017 | 50% | +11,1% | 5 |
| 2010–19 | produzione per tipo | 1,293 (R 1,053) | **S 0,84** | 4,78 | 33% | +7,9% | 1 |
| 2010–19 | produzione aggregata | 1,293 (R 1,053) | **ESN 0,95** | 0,90 | 37% | +8,7% | 3 |
| 2010–19 | lavoro aggregata | 1,193 (R 1,053) | ESN 1,03; R 1,02 | 0,017 | 40% | +9,5% | 3 |

### Lettura

1. **Criterio di taratura.** L'unica variante che lascia ammissibile la traiettoria osservata è quella aggregata legata al lavoro: O4 resta invariato.
   - Legata alla produzione, chiede più capitale di quanto l'economia osservata ne abbia accumulato: nel 2010–19 il rapporto capitale/prodotto è sceso.
   - Per tipo, chiede alle strutture una crescita che non c'è stata (osservato +8,5% in dieci anni).

   Proposta: H29 = E+S+N ≥ crescita degli FTE, R ≥ crescita della produzione di HS.
2. **Effetto su O2 (lavoro aggregata).**
   - L'eccesso di consumo scende da +11% a +9–9,5%.
   - La quota di consumo al tetto del +20% scende dal 50% al 40%.
   - Gli stock finali di E e N raggiungono o superano l'osservato.
3. **Restano due distorsioni.**
   - **Tempi:** l'accumulazione si concentra alla fine (E +278% nel 2019; +99% nel 2016 sull'orizzonte breve).
   - **Composizione:** l'investimento in strutture cessa dal 2015 e lo stock S scende del 16–25%. Il vincolo aggregato si soddisfa con i beni che costano meno da produrre a fine orizzonte.

   I prezzi ombra del vincolo terminale sono ≈ 0: con O2 quasi saturo il vincolo costa poco in termini di obiettivo, e la scelta di tempi e composizione resta quasi indifferente.
4. **Conclusione di taratura.**
   - La condizione terminale tarata sul lavoro fissa correttamente il livello dell'accumulazione, compatibile con i dati.
   - I tempi e la composizione dipendono da vincoli tecnici che il modello non ha: costi di aggiustamento (H25) e, per la composizione, un legame tra tipo di capitale e capacità delle singole industrie.

## E6 — taratura standard (H9c + H29) con gradualità dell'investimento

Esecuzione `M71-E6-taratura-gradualita`, comando `python -m pianificazione71 e6`.

Casi: taratura (H9c + H29 legata agli FTE); + penalità a gradini (H25b); + limite ±15% (H25a); + penalità e tempi di costruzione S, R (H26). Scarti in percentuale media assoluta dall'osservato.

| Orizzonte | Caso | Consumo a +20% | Eccesso di consumo | Anni inv. netto < 0 | Investimento | Stock |
|---|---|---|---|---|---|---|
| 2012–16 | taratura | 39% | +9,0% | 1 | 68,0 | 8,2 |
| 2012–16 | + penalità | 34% | +7,4% | 0 | **10,0** | **1,3** |
| 2012–16 | + limite ±15% | 37% | +8,1% | 0 | 27,5 | 4,9 |
| 2012–16 | + penalità + tempi di costruzione | 34% | +7,4% | 0 | 9,9 | 1,3 |
| 2010–19 | taratura | 40% | +9,5% | 3 | 58,3 | 11,7 |
| 2010–19 | + penalità | 34% | +7,4% | 0 | **21,0** | **5,2** |
| 2010–19 | + limite ±15% | 39% | +8,7% | 1 | 30,4 | 8,1 |
| 2010–19 | + penalità + tempi di costruzione | 34% | +7,3% | 0 | 21,0 | 5,3 |

**Ammissibilità dell'osservato.**

- Con la penalità l'osservato resta ammissibile: la penalità è morbida. Il valore di O4 (0,07 e 0,17) include il costo delle variazioni osservate oltre il 5% e non è una distanza.
- Con il limite ±15% l'osservato viola il limite in alcuni anni del 2010–19 (O4 = 0,078).

### Lettura

1. **La combinazione H9c + H29 + penalità dà il modello più aderente finora.**
   - **2012–16:** scarto medio sull'investimento 10% (da 64% di O2 in D), sugli stock 1,3%, produzione +2–3%, consumo +5…+9%.
   - **2010–19:** investimento 21%, stock 5%.
   - L'investimento cresce in modo regolare e l'investimento netto è positivo e crescente (da 121 a 667 miliardi).
   - I tempi di costruzione non aggiungono nulla alla penalità.
2. **Eccesso di consumo residuo: +7,3–7,4%, vicino al +6,2% ottenuto in E3 fissando l'investimento ai valori osservati.** Il residuo viene quasi tutto dalla riallocazione della produzione corrente e non più dalle scelte di accumulazione.
3. **Distorsione residua di composizione (2010–19).**
   - Strutture sopra l'osservato del 12–29%.
   - Attrezzature e proprietà intellettuale sotto del 20–35%.

   Il vincolo terminale aggregato in dollari premia i beni che si ammortizzano lentamente: costa meno mantenere il valore dello stock con le strutture. Nel 2012–16 la distorsione è piccola (entro ±15%).
4. **Correttivo di taratura possibile.** Aggregare lo stock finale con i pesi di capacità w (costi d'uso), cioè in termini di servizi produttivi invece che di valore. Il vincolo diventa neutrale rispetto alla durata dei beni.

## E7 — condizione terminale in servizi produttivi (H29b, H29c)

Esecuzione `M71-E7-terminale-servizi`, comando `python -m pianificazione71 e7`. Tutti i casi usano H9c e la penalità H25b.

Varianti:

- **H29b:** Σ w·K finale (E+S+N, pesi di capacità w dei costi d'uso) ≥ crescita degli FTE;
- **H29c:** la stessa aggregazione, ≥ crescita della produzione privata.

In tutti i casi R resta a valore, legato alla crescita di HS.

| Orizzonte | Terminale | Osservato / richiesto (E+S+N) | O4 senza penalità | Eccesso di consumo | Anni inv. netto < 0 | Investimento | Stock |
|---|---|---|---|---|---|---|---|
| 2012–16 | H29 valore, FTE | 1,016 | 0,003 | +7,4% | 0 | 10,0 | 1,3 |
| 2012–16 | H29b capacità, FTE | 1,051 | 0,003 | +10,2% | 3 | 25,5 | 6,4 |
| 2012–16 | H29c capacità, produzione | 1,021 | 0,003 | +10,2% | 3 | 25,6 | 6,4 |
| 2010–19 | H29 valore, FTE | 1,033 | 0,017 | +7,4% | 0 | 21,0 | 5,2 |
| 2010–19 | H29b capacità, FTE | 1,102 | 0,017 | +10,2% | 6 | 29,3 | 10,5 |
| 2010–19 | H29c capacità, produzione | 1,017 | 0,017 | +10,1% | 4 | 28,4 | 10,0 |

### Lettura

1. **H29b è più lasco di H29.** In servizi produttivi il capitale osservato è cresciuto più degli FTE, perché E e N (con pesi alti) crescono più in fretta di S. Il modello accumula meno e l'eccesso di consumo torna al 10%. La distorsione a favore di S sparisce, ma tutti i tipi finiscono sotto l'osservato.
2. **H29c ha un livello corretto in unità di servizio (osservato/richiesto 1,02), ma il modello aggira il vincolo tra industrie.**
   - I pesi w sono normalizzati all'interno di ciascuna industria e non sono confrontabili tra industrie.
   - Il modello accumula N nelle industrie con w più alto: sul 2012–16 la somma w·K di N supera l'osservato del 40%, mentre lo stock N in dollari è −32%.
   - Gli stock reali di E e N finiscono il 20–40% sotto l'osservato.
3. **Conclusione.** L'aggregazione in servizi produttivi non è una taratura valida della condizione terminale.
   - H29 (valore, FTE) resta la migliore: l'osservato è ammissibile e gli scarti sono i più bassi.
   - La sua distorsione di composizione nel 2010–19 (S sopra, E e N sotto) resta aperta. Il correttivo coerente è un pavimento per industria e tipo (non depauperamento per industria, già indicato in D4), da affiancare a H29 aggregato.
