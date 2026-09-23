# M71-C6 — capacità legata al capitale

## Tassi di rendimento per gruppo KLEMS (2012)

- gruppi: 61; mediana r = 0.124; min -0.087 (523); max 1.298 (5411)
- gruppi con r negativo, troncato a 0: 2

## Pesi w per tipo (mediana tra industrie)

```
       min   50%   max
tipo                  
E    0.737 1.243 2.471
N    1.061 1.960 9.572
R    1.000 1.000 1.000
S    0.172 0.720 0.971
```

## κ (capitale per la capacità / produzione a piena capacità, 2012)

- industrie: 66; con utilizzo G.17: 23; κ mediano 0.68

## Controllo esterno parziale G.17 (2013–2016)

Utilizzo implicito u* = x·κ/K^cap contro utilizzo G.17; crescita di K^cap contro crescita della capacità G.17.

| Metodo G.17 | Industrie | Scarto medio assoluto u* − u (punti) | Correlazione u*, u | Crescita K^cap 2012–16 | Crescita capacità G.17 |
|---|---:|---:|---:|---:|---:|
| fisico | 8 | 6.6 | 0.60 | 12.7% | 11.5% |
| indagine+capitale | 14 | 3.4 | 0.84 | 3.8% | -3.3% |
| misto | 1 | 6.3 | -0.99 | 14.2% | -10.0% |

## Deriva tra capacità G.17 e capitale (opzione di calibrazione a)

Deriva annua θ = (crescita capacità G.17 / crescita K^cap)^(1/4) − 1, 2012–2016:

```
                    count    mean     min     50%     max
metodo_g17                                               
fisico             8.0000 -0.0032 -0.0277 -0.0075  0.0378
indagine+capitale 14.0000 -0.0181 -0.0429 -0.0234  0.0339
misto              1.0000 -0.0576 -0.0576 -0.0576 -0.0576
```

Verifica fuori campione (θ stimata 2012–2014): errore medio assoluto sull'utilizzo, punti percentuali:

| Anno | Gruppo | Senza deriva | Con deriva |
|---:|---|---:|---:|
| 2015 | fisico | 6.7 | 4.0 |
| 2015 | indagine+capitale | 3.8 | 2.2 |
| 2015 | misto | 7.9 | 3.3 |
| 2015 | tutti | 5.0 | 2.9 |
| 2016 | fisico | 10.3 | 7.9 |
| 2016 | indagine+capitale | 5.4 | 3.5 |
| 2016 | misto | 11.9 | 2.9 |
| 2016 | tutti | 7.4 | 5.0 |
