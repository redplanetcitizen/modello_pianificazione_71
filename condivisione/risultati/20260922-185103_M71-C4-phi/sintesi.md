# M71-C4 — stima di Φ (composizione dell'investimento per industria)

Struttura iniziale dal dettaglio dei Fixed Assets, quota comune λ = 0.05; bilanciamento GRAS.

| Anno | Tipo | Iter. | Converge | Scala Use/FA | Spostamento dalla struttura iniziale | Celle negative |
|---:|---|---:|---|---:|---:|---:|
| 2012 | E | 18 | True | 1.1076 | 11.1% | 0 |
| 2012 | S | 69 | True | 1.0420 | 6.0% | 0 |
| 2012 | N | 26 | True | 0.9915 | 25.2% | 0 |
| 2013 | E | 18 | True | 1.1013 | 11.7% | 0 |
| 2013 | S | 59 | True | 1.0411 | 6.6% | 0 |
| 2013 | N | 26 | True | 0.9925 | 25.7% | 0 |
| 2014 | E | 18 | True | 1.0992 | 11.9% | 0 |
| 2014 | S | 55 | True | 1.0387 | 7.1% | 0 |
| 2014 | N | 25 | True | 0.9931 | 25.7% | 0 |
| 2015 | E | 19 | True | 1.1026 | 12.5% | 0 |
| 2015 | S | 48 | True | 1.0513 | 8.8% | 0 |
| 2015 | N | 25 | True | 0.9939 | 26.5% | 0 |
| 2016 | E | 18 | True | 1.1157 | 14.3% | 0 |
| 2016 | S | 46 | True | 1.0640 | 10.6% | 0 |
| 2016 | N | 25 | True | 0.9929 | 26.8% | 0 |

## Sensibilità alla struttura iniziale

Differenza relativa Σ|X_λ − X_base| / ΣX_base (media sui 5 anni):

```
lambda   0.2   1.0
tipo              
E      12.2% 72.4%
N      10.3% 64.8%
S      10.2% 66.8%
```

λ = 1 corrisponde a una composizione comune a tutte le industrie: misura quanta informazione apporta il dettaglio dei Fixed Assets.
