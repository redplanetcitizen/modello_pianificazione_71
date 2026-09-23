# M71-E6-predittivo — sintesi del backtest

Tempo totale 4538 s; risoluzioni LP 825, tempo medio 4.4 s.

## A_2008_2019

Indicatore S (< 1: meglio della persistenza) per caso e orizzonte h — primi 12 per h = 1:

```
                  caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
                    P0  1 0.757         1.000         0.817      0.760                0.766         0.294           1.142     0.883
          ultimo_tasso  1 0.852         1.000         0.932      0.887                0.804         0.294           1.364     0.956
          trend_mobile  1 0.863         1.000         0.934      0.774                0.943         0.598           1.106     0.950
           persistenza  1 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
P2|inv1.0|m1.0|S1.0|T3  1 1.048         1.000         1.035      1.049                1.259         0.717           1.092     0.891
P2|inv1.0|m1.0|S1.0|T1  1 1.051         1.000         1.033      1.049                1.277         0.719           1.092     0.891
    P1|tetto100|agg|T2  1 1.236         1.000         1.367      1.079                0.683         0.253           2.629     4.187
P2|inv1.0|m0.0|S0.0|T3  1 1.239         1.000         1.037      1.039                1.255         0.715           2.109     3.756
P2|inv1.0|m0.0|S0.0|T1  1 1.244         1.000         1.037      1.041                1.266         0.716           2.106     3.814
     P2|lx2.0|li0.5|T3  1 1.250         1.000         1.017      1.080                1.438         0.740           1.852     3.336
     P2|lx0.5|li0.5|T3  1 1.258         1.000         1.060      1.069                1.434         0.738           1.679     3.502
     P2|lx0.5|li0.5|T1  1 1.270         1.000         1.058      1.068                1.434         0.739           1.943     3.480
```

Per h > 1 (primi 8 per ogni h):

```
h = 2
                  caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
                    P0  2 0.796         1.000         0.850      0.780                0.823         0.379           1.208     0.885
          trend_mobile  2 0.894         1.000         0.983      0.745                0.990         0.669           1.198     1.013
          ultimo_tasso  2 0.956         1.000         1.082      0.914                0.898         0.379           1.790     0.997
P1|tetto100|agg+ind|T2  2 0.972         1.000         0.970      0.965                0.801         0.357           1.676     2.235
    P1|tetto100|agg|T2  2 0.972         1.000         1.109      0.948                0.590         0.289           1.866     2.294
P2|inv1.0|m1.0|S1.0|T3  2 0.973         1.000         0.900      1.000                1.090         0.840           1.126     0.899
P2|inv1.0|m1.0|S1.0|T1  2 0.974         1.000         0.894      1.000                1.103         0.842           1.126     0.899
           persistenza  2 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
h = 3
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
                       P0  3 0.849         1.000         0.870      0.837                0.925         0.425           1.266     0.911
condizionata|P1|E6|agg|T1  3 0.871         1.000         0.788      0.758                0.796         0.502           2.445     1.512
       P1|tetto100|agg|T2  3 0.922         1.000         1.043      0.937                0.654         0.321           1.594     1.713
   P1|tetto100|agg+ind|T2  3 0.935         1.000         0.933      0.971                0.843         0.414           1.501     1.580
             trend_mobile  3 0.954         1.000         1.043      0.797                1.074         0.716           1.267     1.040
   P1|tetto110|agg+ind|T2  3 0.966         1.000         0.970      1.029                0.894         0.425           1.290     1.616
    P1|stretto|agg+ind|T2  3 0.967         1.000         0.968      1.015                0.912         0.426           1.298     1.630
       P1|tetto100|ind|T2  3 0.995         1.000         0.984      0.908                1.060         0.645           1.425     1.601
h = 4
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
condizionata|P1|E6|agg|T1  4 0.774         1.000         0.701      0.671                0.711         0.533           2.015     1.321
                       P0  4 0.921         1.000         0.920      0.905                1.035         0.486           1.418     0.937
       P1|tetto100|agg|T2  4 0.923         1.000         1.068      0.952                0.674         0.364           1.534     1.391
   P1|tetto100|agg+ind|T2  4 0.942         1.000         0.986      0.986                0.883         0.502           1.176     1.288
   P1|tetto110|agg+ind|T2  4 0.971         1.000         1.011      1.005                0.905         0.516           1.216     1.458
    P1|stretto|agg+ind|T2  4 0.975         1.000         1.013      0.999                0.918         0.515           1.239     1.478
       P1|tetto100|ind|T2  4 0.991         1.000         1.021      0.935                1.049         0.724           1.107     1.337
       P1|tetto110|agg|T2  4 0.991         1.000         1.196      0.982                0.756         0.343           1.713     1.337
h = 5
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
condizionata|P1|E6|agg|T1  5 0.755         1.000         0.711      0.756                0.625         0.529           1.902     0.840
    P1|stretto|agg+ind|T2  5 0.976         1.000         1.063      0.981                0.965         0.604           1.183     1.000
   P1|tetto110|agg+ind|T2  5 0.977         1.000         1.068      0.993                0.944         0.607           1.177     1.000
       P1|tetto100|agg|T2  5 0.990         1.000         1.223      1.010                0.678         0.381           1.944     0.997
   P1|tetto100|agg+ind|T2  5 0.992         1.000         1.096      1.049                0.937         0.596           1.037     1.000
                       P0  5 0.995         1.000         0.966      0.968                1.148         0.549           1.678     0.920
              persistenza  5 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
         P1|E6|agg+ind|T2  5 1.013         1.000         1.102      1.068                0.966         0.615           1.165     0.980
```

## B_2010_2019

Indicatore S (< 1: meglio della persistenza) per caso e orizzonte h — primi 12 per h = 1:

```
                  caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
                    P0  1 0.722         1.000         0.773      0.718                0.773         0.222           1.133     0.829
          trend_mobile  1 0.804         1.000         0.894      0.710                0.890         0.463           1.073     0.889
          ultimo_tasso  1 0.832         1.000         0.937      0.829                0.802         0.222           1.453     0.932
P2|inv1.0|m1.0|S1.0|T3  1 0.982         1.000         0.981      1.022                1.169         0.533           1.041     0.834
P2|inv1.0|m1.0|S1.0|T1  1 0.986         1.000         0.979      1.022                1.191         0.536           1.041     0.834
           persistenza  1 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
P2|inv1.0|m0.0|S0.0|T3  1 1.201         1.000         0.987      1.012                1.165         0.532           2.277     4.024
P2|inv1.0|m0.0|S0.0|T1  1 1.205         1.000         0.987      1.014                1.177         0.533           2.271     4.056
     P2|lx2.0|li0.5|T3  1 1.207         1.000         0.953      1.047                1.372         0.554           1.942     3.607
     P2|lx0.5|li0.5|T3  1 1.228         1.000         1.017      1.046                1.366         0.552           1.758     3.860
     P2|lx2.0|li0.5|T1  1 1.229         1.000         0.953      1.049                1.372         0.554           2.107     3.873
     P2|lx0.5|li0.5|T1  1 1.239         1.000         1.015      1.046                1.367         0.553           2.076     3.774
```

Per h > 1 (primi 8 per ogni h):

```
h = 2
                  caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
                    P0  2 0.796         1.000         0.850      0.780                0.823         0.379           1.208     0.885
          trend_mobile  2 0.894         1.000         0.983      0.745                0.990         0.669           1.198     1.013
          ultimo_tasso  2 0.956         1.000         1.082      0.914                0.898         0.379           1.790     0.997
P1|tetto100|agg+ind|T2  2 0.972         1.000         0.970      0.965                0.801         0.357           1.676     2.235
    P1|tetto100|agg|T2  2 0.972         1.000         1.109      0.948                0.590         0.289           1.866     2.294
P2|inv1.0|m1.0|S1.0|T3  2 0.973         1.000         0.900      1.000                1.090         0.840           1.126     0.899
P2|inv1.0|m1.0|S1.0|T1  2 0.974         1.000         0.894      1.000                1.103         0.842           1.126     0.899
           persistenza  2 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
h = 3
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
                       P0  3 0.849         1.000         0.870      0.837                0.925         0.425           1.266     0.911
condizionata|P1|E6|agg|T1  3 0.871         1.000         0.788      0.758                0.796         0.502           2.445     1.512
       P1|tetto100|agg|T2  3 0.922         1.000         1.043      0.937                0.654         0.321           1.594     1.713
   P1|tetto100|agg+ind|T2  3 0.935         1.000         0.933      0.971                0.843         0.414           1.501     1.580
             trend_mobile  3 0.954         1.000         1.043      0.797                1.074         0.716           1.267     1.040
   P1|tetto110|agg+ind|T2  3 0.966         1.000         0.970      1.029                0.894         0.425           1.290     1.616
    P1|stretto|agg+ind|T2  3 0.967         1.000         0.968      1.015                0.912         0.426           1.298     1.630
       P1|tetto100|ind|T2  3 0.995         1.000         0.984      0.908                1.060         0.645           1.425     1.601
h = 4
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
condizionata|P1|E6|agg|T1  4 0.774         1.000         0.701      0.671                0.711         0.533           2.015     1.321
                       P0  4 0.921         1.000         0.920      0.905                1.035         0.486           1.418     0.937
       P1|tetto100|agg|T2  4 0.923         1.000         1.068      0.952                0.674         0.364           1.534     1.391
   P1|tetto100|agg+ind|T2  4 0.942         1.000         0.986      0.986                0.883         0.502           1.176     1.288
   P1|tetto110|agg+ind|T2  4 0.971         1.000         1.011      1.005                0.905         0.516           1.216     1.458
    P1|stretto|agg+ind|T2  4 0.975         1.000         1.013      0.999                0.918         0.515           1.239     1.478
       P1|tetto100|ind|T2  4 0.991         1.000         1.021      0.935                1.049         0.724           1.107     1.337
       P1|tetto110|agg|T2  4 0.991         1.000         1.196      0.982                0.756         0.343           1.713     1.337
h = 5
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
condizionata|P1|E6|agg|T1  5 0.755         1.000         0.711      0.756                0.625         0.529           1.902     0.840
    P1|stretto|agg+ind|T2  5 0.976         1.000         1.063      0.981                0.965         0.604           1.183     1.000
   P1|tetto110|agg+ind|T2  5 0.977         1.000         1.068      0.993                0.944         0.607           1.177     1.000
       P1|tetto100|agg|T2  5 0.990         1.000         1.223      1.010                0.678         0.381           1.944     0.997
   P1|tetto100|agg+ind|T2  5 0.992         1.000         1.096      1.049                0.937         0.596           1.037     1.000
                       P0  5 0.995         1.000         0.966      0.968                1.148         0.549           1.678     0.920
              persistenza  5 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
         P1|E6|agg+ind|T2  5 1.013         1.000         1.102      1.068                0.966         0.615           1.165     0.980
```

## C_2012_2016_origine_2011

Indicatore S (< 1: meglio della persistenza) per caso e orizzonte h — primi 12 per h = 1:

```
                  caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
          ultimo_tasso  1 0.672         1.000         0.857      0.740                0.436         0.418           0.680     0.597
                    P0  1 0.742         1.000         0.732      1.070                0.479         0.418           0.633     0.656
           persistenza  1 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
P2|inv1.0|m1.0|S1.0|T3  1 1.047         1.000         0.829      0.937                1.355         1.672           0.763     0.810
P2|inv1.0|m1.0|S1.0|T1  1 1.047         1.000         0.830      0.937                1.355         1.672           0.763     0.810
          trend_mobile  1 1.081         1.000         1.208      1.156                1.205         0.379           0.808     1.061
     P2|lx0.5|li0.5|T3  1 1.182         1.000         0.874      0.939                1.427         1.626           1.041     2.762
    P1|tetto100|agg|T2  1 1.204         1.000         1.740      0.888                0.475         0.235           1.503     4.428
     P2|lx0.5|li0.1|T3  1 1.210         1.000         0.837      0.937                1.421         1.612           1.162     3.491
     P2|lx0.5|li0.1|T1  1 1.212         1.000         0.833      0.937                1.498         1.752           1.067     3.052
     P2|lx0.5|li0.5|T1  1 1.234         1.000         0.853      0.941                1.430         1.631           1.415     3.521
     P2|lx2.0|li0.5|T3  1 1.239         1.000         0.792      0.953                1.443         1.659           1.961     3.266
```

Per h > 1 (primi 8 per ogni h):

```
h = 2
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
       P1|tetto100|agg|T2  2 0.775         1.000         0.945      0.792                0.379         0.292           0.627     2.347
       P1|tetto100|ind|T1  2 0.810         1.000         0.814      0.613                0.652         1.040           0.790     2.159
   P2|inv1.0|m1.0|S1.0|T1  2 0.827         1.000         0.808      0.591                0.948         1.187           1.197     0.787
   P2|inv1.0|m1.0|S1.0|T3  2 0.832         1.000         0.829      0.585                0.948         1.188           1.197     0.787
       P1|tetto100|ind|T2  2 0.835         1.000         0.759      0.792                0.553         0.594           1.844     2.148
   P1|tetto100|agg+ind|T1  2 0.852         1.000         0.764      0.590                0.743         1.029           1.447     2.436
                       P0  2 0.853         1.000         0.864      1.086                0.638         0.544           1.102     0.619
condizionata|P1|E6|agg|T1  2 0.863         1.000         0.946      0.615                0.476         0.292           3.764     1.632
h = 3
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
condizionata|P1|E6|agg|T1  3 0.719         1.000         0.761      0.712                0.454         0.328           1.754     1.305
       P1|tetto100|agg|T2  3 0.733         1.000         0.853      0.747                0.390         0.325           1.107     1.740
       P1|tetto100|ind|T2  3 0.792         1.000         0.833      0.770                0.648         0.588           1.058     1.397
   P1|tetto100|agg+ind|T2  3 0.810         1.000         0.844      0.771                0.719         0.617           1.056     1.353
   P1|tetto100|agg+ind|T3  3 0.810         1.000         0.725      0.774                0.740         0.914           0.625     1.807
       P1|tetto100|ind|T3  3 0.819         1.000         0.787      0.776                0.660         0.874           0.905     1.715
       P1|tetto100|agg|T3  3 0.828         1.000         0.906      0.785                0.473         0.741           1.324     1.724
       P1|tetto100|ind|T1  3 0.830         1.000         0.784      0.779                0.697         0.858           0.923     1.789
h = 4
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
condizionata|P1|E6|agg|T1  4 0.589         1.000         0.541      0.605                0.382         0.349           1.470     1.217
       P1|tetto100|agg|T2  4 0.666         1.000         0.804      0.678                0.330         0.337           0.953     1.483
       P1|tetto100|agg|T3  4 0.763         1.000         0.914      0.807                0.338         0.620           0.884     1.452
       P1|tetto110|agg|T2  4 0.768         1.000         1.049      0.739                0.330         0.384           1.214     1.330
        P1|stretto|agg|T2  4 0.768         1.000         1.050      0.739                0.330         0.383           1.213     1.331
       P1|tetto100|ind|T2  4 0.789         1.000         0.927      0.718                0.710         0.632           0.793     1.016
       P1|tetto110|ind|T2  4 0.792         1.000         0.912      0.797                0.684         0.618           0.535     1.085
       P1|tetto100|ind|T3  4 0.793         1.000         0.816      0.812                0.627         0.715           0.781     1.374
h = 5
                     caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
condizionata|P1|E6|agg|T1  5 0.627         1.000         0.621      0.656                0.347         0.365           1.927     0.839
       P1|tetto100|agg|T2  5 0.677         1.000         0.884      0.669                0.278         0.323           1.486     0.984
        P1|stretto|ind|T2  5 0.719         1.000         0.835      0.538                0.717         0.660           0.953     1.000
       P1|tetto110|ind|T2  5 0.719         1.000         0.835      0.538                0.717         0.660           0.953     1.000
   P1|tetto110|agg+ind|T2  5 0.757         1.000         0.845      0.581                0.797         0.717           0.953     1.000
    P1|stretto|agg+ind|T2  5 0.758         1.000         0.847      0.584                0.797         0.717           0.954     1.000
       P1|tetto100|ind|T3  5 0.762         1.000         0.818      0.798                0.603         0.629           0.879     1.000
       P1|tetto100|ind|T1  5 0.769         1.000         0.818      0.797                0.631         0.652           0.872     1.000
```

## C_2012_2016

Indicatore S (< 1: meglio della persistenza) per caso e orizzonte h — primi 12 per h = 1:

```
                  caso  h     S  alfa_coperto  r_produzione  r_consumo  r_investimento_tipo  r_stock_tipo  r_importazioni  r_scorte
                    P0  1 0.646         1.000         0.653      0.726                0.584         0.231           1.115     0.729
          ultimo_tasso  1 0.696         1.000         0.721      0.744                0.642         0.231           1.353     0.748
          trend_mobile  1 0.805         1.000         0.878      0.730                0.921         0.442           1.068     0.809
P2|inv1.0|m1.0|S1.0|T3  1 0.809         1.000         0.845      0.910                0.808         0.311           1.013     0.788
P2|inv1.0|m1.0|S1.0|T1  1 0.810         1.000         0.846      0.912                0.808         0.311           1.013     0.788
           persistenza  1 1.000         1.000         1.000      1.000                1.000         1.000           1.000     1.000
P2|inv1.0|m0.0|S0.0|T3  1 1.036         1.000         0.849      0.909                0.804         0.307           2.405     3.934
P2|inv1.0|m0.0|S0.0|T1  1 1.045         1.000         0.852      0.908                0.804         0.307           2.542     3.975
     P2|lx0.5|li0.5|T3  1 1.066         1.000         0.871      0.899                1.157         0.374           1.666     3.653
     P2|lx0.5|li0.5|T1  1 1.079         1.000         0.864      0.899                1.159         0.375           1.984     3.635
     P2|lx2.0|li0.5|T3  1 1.083         1.000         0.831      0.928                1.184         0.384           2.045     3.553
     P2|lx0.5|li0.1|T3  1 1.088         1.000         0.860      0.896                1.249         0.389           1.786     3.657
```

## Selezione annidata (h = 1)

```
 origine                 scelta  S_validazione  n_validazione                                                          motivo
    2008           P1|E6|agg|T1            NaN              0 storia di validazione insufficiente: configurazione predefinita
    2009           P1|E6|agg|T1            NaN              1 storia di validazione insufficiente: configurazione predefinita
    2010      P1|stretto|agg|T2       1.556954              2                                                                
    2011     P1|tetto100|agg|T2       1.445443              3                                                                
    2012     P1|tetto100|agg|T2       1.384969              4                                                                
    2013     P1|tetto100|agg|T2       1.291419              5                                                                
    2014     P1|tetto100|agg|T2       1.267981              6                                                                
    2015     P1|tetto100|agg|T2       1.260517              7                                                                
    2016 P2|inv1.0|m1.0|S1.0|T3       1.277883              8                                                                
    2017 P2|inv1.0|m1.0|S1.0|T3       1.230697              9                                                                
    2018 P2|inv1.0|m1.0|S1.0|T3       1.163366             10                                                                
```

