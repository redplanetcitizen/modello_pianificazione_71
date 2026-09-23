# M71-E3 — funzione d'investimento stimata, O2 2010-2019

## Stima (1998-2009) e verifica fuori campione

```
tipo      c0     c1  R2_stima  tasso_2005_09  MAPE_acc_2010_19  MAPE_acc_2012_16  MAPE_tasso_2010_19  MAPE_tasso_2012_16
   E -0.0577 0.0426    0.6914         0.1634           23.7263           24.9673              9.1848             10.6882
   S  0.0349 0.0048    0.0055         0.0436           16.6494           13.6446             11.4473              8.5940
   N  0.2057 0.0057    0.4744         0.2838           11.1933            9.4802              6.6418              4.1310
   R -0.1513 1.8933    0.1123         0.0414           54.9225           55.9961             36.0567             33.4048
```

## Casi

```
                            stato  consumo_cumulato_2010_19  consumo_cumulato_2012_16  anni_disinv_netto_2010_19  produzione_lorda_10_19  consumo_privato_10_19  media_investimento_10_19  media_stock_10_19  produzione_lorda_12_16  consumo_privato_12_16  media_investimento_12_16  media_stock_12_16
caso                                                                                                                                                                                                                                                                                                    
O2                        Optimal                132,243.87                 65,241.85                          6                    0.57                  12.24                     62.99              20.00                    0.43                  12.73                     49.71              23.78
acceleratore_banda_10%    Optimal                126,696.98                 62,133.19                          0                    1.85                   7.48                     23.51               9.76                    2.33                   7.39                     20.88              10.10
tasso_costante_banda_10%  Optimal                127,137.48                 62,409.00                          0                    2.17                   7.84                     23.17              10.70                    2.45                   7.86                     22.73              10.58
tasso_costante_penalita   Optimal                125,527.89                 61,568.16                          0                    2.41                   6.44                     23.85              10.17                    2.71                   6.38                     23.13              10.21
investimento_osservato    Optimal                125,094.73                 61,249.01                          0                    2.90                   6.23                      0.00               1.38                    2.99                   5.87                      0.00               1.79
```

## Scarti 2010-2019 per variabile

```
variabile                 consumo_privato  investimento_E  investimento_N  investimento_R  investimento_S  produzione_lorda  stock_E  stock_N  stock_R  stock_S  media_investimento  media_stock
O2                                   12.2            60.7            47.9           108.0            35.3               0.6     31.5     37.1      6.4      5.0                63.0         20.0
acceleratore_banda_10%                7.5            26.1            31.5            29.1             7.2               1.9     12.7     21.2      4.2      0.9                23.5          9.8
investimento_osservato                6.2             0.0             0.0             0.0             0.0               2.9      0.4      3.9      0.2      1.1                 0.0          1.4
tasso_costante_banda_10%              7.8            26.7            31.0            27.3             7.8               2.2     14.0     23.1      4.5      1.2                23.2         10.7
tasso_costante_penalita               6.4            19.8            27.8            39.2             8.6               2.4     10.8     22.8      6.1      1.0                23.9         10.2
```
