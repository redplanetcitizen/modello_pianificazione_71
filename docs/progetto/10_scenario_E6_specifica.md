# Scenario E6 "O2 tarato + penalità" (2012–2016): specifica completa del problema LP

Aggiornato il 22/09/2026. Esecuzione `M71-E6-taratura-gradualita`, caso `2012-2016_penalita`.

Nella configurazione nominata del registro (`09_registro_modelli_e_test.md`) questo scenario è "O2 tarato + penalità". Rieseguibile con:

```
costruisci(cfg, range(2012, 2017), inviluppo=True)
Opzioni(obiettivo="O2", capacita_non_g17="inviluppo_tendenza", sigma_fattore=0.85,
        terminale_fattori={"ESN": 1.1006, "R": 1.0155}, penalita_var_inv=0.10)
```

## Particolarità dello scenario

- **Dimensioni:** 71 industrie × 71 prodotti ordinari; `Used` e `Other` esogeni. Anni 2012–2016; prezzi 2012; miliardi di dollari. LP di 4.870 variabili e 2.898 vincoli, risolto con HiGHS 1.15.1.
- **Obiettivo O2:** gli obiettivi per prodotto sono il consumo privato osservato di ogni prodotto in ogni anno. Il piano non fissa un paniere, ma può ricomporre il consumo entro 0–120% di ciascun obiettivo.
- **Domanda finale esogena:** spesa e investimento pubblici, esportazioni e voci positive delle importazioni restano ai valori osservati. Il piano sceglie produzione, consumo privato, investimento privato per industria e tipo, scorte e importazioni.
- **Taratura:**
  - **capacità:**
    - industrie con dati G.17: κ con l'utilizzo G.17 e la deriva θ;
    - altre industrie e HS: inviluppo con tendenza 1997–2019 (H9c);
  - **scorte:** banda 0,85–1,20 del rapporto 2012 (H13b, H13c);
  - **stock finale:** legato alla crescita del lavoro (H29);
  - **investimento:** gradualità tramite penalità (H25b).
- **Tipi di capitale:** E attrezzature, S strutture, N proprietà intellettuale per 65 industrie private; R residenziale per HS. Le 5 industrie pubbliche non hanno vincolo di capacità.

## Indici e parametri

- t ∈ {2012,…,2016}; c prodotti; j industrie; a ∈ {E, S, N} (per HS: R); z comparti di scorte (11).
- **Tecnologia:** B_t (usi intermedi per unità di produzione), D_t (quote di mercato), x^spec_t (produzione di Used/Other).
- **Investimento:** Φ_{t,a} (prodotti per unità di investimento FA), φR_t.
- **Capitale e capacità:** K0 (stock 2012), δ_{j,a}, w_{j,a} (pesi di capacità), κ_j, u_j, θ_j.
- **Lavoro:** ℓ_{j,t} (FTE per unità di produzione), L_t (FTE osservati).
- **Scorte:** σ_z, S_{z,2011}, ψ_c.
- **Estero:** μ_{c,t} (quote d'importazione), M̄_t (importazioni totali osservate), ε = 0,10.
- **Consumo:** ĉ_{c,t} = obiettivo O2 (consumo osservato, ≥ 0); peso p_{c,t} = ĉ_{c,t} / Σ ĉ_t.
- **Domanda esogena:** G_{c,t} + X_{c,t} + F^+_{c,t} (pubblica, esportazioni, voci positive di F050).

## Variabili (tutte ≥ 0 salvo ΔS)

- x_{j,t} produzione; q_{c,t} offerta interna; m_{c,t} importazioni; r_{c,t} residuo materiale;
- c_{c,t} consumo; ρ^k_{c,t} tratti di soddisfazione;
- I_{j,a,t} investimento; K_{j,a,t} stock di inizio anno (2013–2017);
- S_{z,t} scorte; ΔS_{z,t} variazione delle scorte (libera);
- su/giù di variazione dell'investimento per tipo (tratti liberi e penalizzati).

## Funzione obiettivo

max Σ_t Σ_c p_{c,t} · (1,0·ρ¹ + 0,5·ρ² + 0,1·ρ³) − Σ_{a,t} 0,1 · (su²_{a,t} + giù²_{a,t}) / I_{a,2011}

con 0 ≤ ρ¹ ≤ 0,9; 0 ≤ ρ² ≤ 0,1; 0 ≤ ρ³ ≤ 0,2. Nessuno sconto tra anni (β = 1).

## Vincoli

1. **Soddisfazione O2:** c_{c,t} = ĉ_{c,t}·(ρ¹ + ρ² + ρ³), da cui 0 ≤ c ≤ 1,2·ĉ; c = 0 se ĉ ≤ 0.
2. **Bilancio materiale per prodotto:**
   q + m − r − Σ_j B_{cj} x_j − c − Σ_{j,a} Φ_{c,j,a} I_{j,a} − φR_c I_{HS,R} − ψ_c Σ_z ΔS_z = G + X + F^+
3. **Quote di mercato:** x_{j,t} = Σ_c D_{jc,t} q_{c,t} + x^spec_{j,t}.
4. **Capacità**, 65 industrie private con capitale:
   x_{j,t} · κ_j · u_j / (1+θ_j)^{t−2012} ≤ Σ_a w_{j,a} K_{j,a,t}
   - G.17 (23 industrie): u = 1, θ dalla deriva G.17;
   - altre (42): u, θ dall'inviluppo con tendenza 1997–2019.
5. **Capacità abitativa:** x_{HS,t} · κ_HS · u_HS / (1+θ_HS)^{t−2012} ≤ K_{HS,R,t}, con u e θ dall'inviluppo.
6. **Accumulazione:** K_{j,a,t+1} = (1 − δ_{j,a}) K_{j,a,t} + I_{j,a,t}, con K_{j,a,2012} = K0.
7. **Condizione terminale H29:**
   - Σ_{j, a∈{E,S,N}} K_{j,a,2017} ≥ 1,1006 · Σ K0 (crescita degli FTE 2012–16, estesa a 5 anni);
   - K_{HS,R,2017} ≥ 1,0155 · K0_{HS,R} (crescita della produzione di HS).
8. **Gradualità H25b:** per tipo a e anno t, Σ_j I_{j,a,t} − Σ_j I_{j,a,t−1} = su¹ + su² − giù¹ − giù².
   - Livelli 2011 osservati: E 889, S 411, N 626, R 382.
   - su¹, giù¹ ≤ 0,05·I_{a,2011} (gratuiti); su², giù² penalizzati.
9. **Lavoro:** Σ_j ℓ_{j,t} x_{j,t} ≤ L_t (124.498 → 134.423 migliaia di FTE).
10. **Importazioni:** Σ_c m_{c,t} ≤ M̄_t (2.360 → 2.422).
11. **Bande delle importazioni per prodotto:**
    m_{c,t} ≤ 1,10 · μ_{c,t} · (Σ_j B_{cj} x_j + c + Σ Φ I + G)_{c,t}
12. **Scorte:** S_{z,t} = S_{z,t−1} + ΔS_{z,t}, con S_{z,2011} osservato.
13. **Banda delle scorte:** 0,85·σ_z·Σ_{j∈z} x_{j,t} ≤ S_{z,t} ≤ 1,20·σ_z·Σ_{j∈z} x_{j,t}.
14. **Scorte finali:** S_{z,2016} ≥ S_{z,2011}.
15. **Non negatività** di tutte le variabili salvo ΔS.

## Risultati (scarto medio dall'osservato)

- Produzione 2,7%; consumo +7,4%.
- Investimento 10,0% (E −4…−9%, S −10…+3%, N −9…−15%, R −7…−23%).
- Stock 1,3%; nessun anno con disinvestimento netto.
- Punteggio O2 al 98,7% del massimo; consumo al tetto +20%: 34%.
