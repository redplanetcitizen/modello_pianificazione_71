# M71-E5 — taratura standard H9c e condizione terminale tarata (H29)

```
orizzonte            terminale   stato                                              fattori                           osservato_su_richiesto  distanza_O4  punteggio_su_massimo  quota_consumo_a_1,2  quota_sotto_obiettivo  eccesso_consumo_cumulato_%  duale_lavoro_medio  anni_disinvestimento_netto                                                                          duale_terminale
2012-2016         mantenimento Optimal                                                   {}  {'E': 1.232, 'S': 1.045, 'N': 1.23, 'R': 1.041}     0.002574                0.9906               0.4896                      0                       10.93           8.222e-07                           2 {'terminale[E]': -0.0, 'terminale[S]': -0.0, 'terminale[N]': -0.0, 'terminale[R]': -0.0}
2012-2016  produzione_per_tipo Optimal {'E': 1.1328, 'S': 1.1328, 'N': 1.1328, 'R': 1.0155} {'E': 1.088, 'S': 0.922, 'N': 1.085, 'R': 1.025}        2.192                0.9871               0.3343                      0                       7.483           1.132e-06                           0 {'terminale[E]': -0.0, 'terminale[S]': -0.0, 'terminale[N]': -0.0, 'terminale[R]': -0.0}
2012-2016 produzione_aggregata Optimal                         {'ESN': 1.1328, 'R': 1.0155}                       {'ESN': 0.987, 'R': 1.025}       0.2445                 0.988               0.3674                      0                       8.335           9.511e-07                           0                                           {'terminale[ESN]': -0.0, 'terminale[R]': -0.0}
2012-2016     lavoro_aggregata Optimal                         {'ESN': 1.1006, 'R': 1.0155}                       {'ESN': 1.016, 'R': 1.025}     0.002574                0.9887               0.3949                      0                       9.032           9.264e-07                           1                                           {'terminale[ESN]': -0.0, 'terminale[R]': -0.0}
2010-2019         mantenimento Optimal                                                   {} {'E': 1.439, 'S': 1.085, 'N': 1.549, 'R': 1.078}      0.01664                0.9907               0.4998                0.01377                       11.13           9.086e-07                           5 {'terminale[E]': -0.0, 'terminale[S]': -0.0, 'terminale[N]': -0.0, 'terminale[R]': -0.0}
2010-2019  produzione_per_tipo Optimal {'E': 1.2931, 'S': 1.2931, 'N': 1.2931, 'R': 1.0529} {'E': 1.113, 'S': 0.839, 'N': 1.198, 'R': 1.024}        4.778                0.9874                0.332                      0                       7.885           1.157e-06                           1 {'terminale[E]': -0.0, 'terminale[S]': -0.0, 'terminale[N]': -0.0, 'terminale[R]': -0.0}
2010-2019 produzione_aggregata Optimal                         {'ESN': 1.2931, 'R': 1.0529}                       {'ESN': 0.953, 'R': 1.024}       0.9038                0.9883               0.3671                      0                       8.679           1.065e-06                           3                                           {'terminale[ESN]': -0.0, 'terminale[R]': -0.0}
2010-2019     lavoro_aggregata Optimal                         {'ESN': 1.1928, 'R': 1.0529}                       {'ESN': 1.033, 'R': 1.024}      0.01664                0.9891                0.397                      0                       9.532           1.044e-06                           3                                           {'terminale[ESN]': -0.0, 'terminale[R]': -0.0}
```

## Scarti dall'osservato, orizzonte 2012-2016

```
variabile                consumo_privato  investimento_E  investimento_N  investimento_R  investimento_S  produzione_lorda  stock_E  stock_N  stock_R  stock_S  media_investimento  media_stock
O2 lavoro_aggregata                  9.0            40.8            55.8            89.4            85.9               2.5      7.2     14.8      3.3      7.4                68.0          8.2
O2 mantenimento                     10.9            39.0            31.1           100.2            26.6               0.9     15.3     18.8      3.0      2.0                49.2          9.8
O2 produzione_aggregata              8.3            47.2            63.9            89.0            86.1               2.8      7.8     15.4      3.3      7.4                71.5          8.5
O2 produzione_per_tipo               7.5            50.2            45.2            79.7            57.3               2.0     14.0     18.8      2.6      4.7                58.1         10.0
```

## Scarti dall'osservato, orizzonte 2010-2019

```
variabile                consumo_privato  investimento_E  investimento_N  investimento_R  investimento_S  produzione_lorda  stock_E  stock_N  stock_R  stock_S  media_investimento  media_stock
O2 lavoro_aggregata                  9.4            57.8            27.1            70.0            78.4               2.3     20.5     11.4      5.2      9.7                58.3         11.7
O2 mantenimento                     11.0            53.7            33.3            70.3            37.3               0.9     28.4     20.1      4.0      3.6                48.6         14.0
O2 produzione_aggregata              8.6            67.2            35.0            68.4            72.8               2.5     20.9     13.3      5.1      8.3                60.9         11.9
O2 produzione_per_tipo               7.8            64.9            41.4            70.9            67.0               2.1     25.6     25.6      5.5      5.4                61.1         15.5
```

