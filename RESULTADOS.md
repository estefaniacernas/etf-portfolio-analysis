# Resultados del proyecto

## Lo que encontré

El árbol fue el modelo elegido en validación. En test tuvo una accuracy de 54.25%, frente a 53.90% al predecir siempre una subida. La diferencia fue de 0.35 puntos porcentuales. Es una diferencia pequeña. No hice una prueba estadística para saber si se sostiene más allá de esta muestra. Además, las observaciones de varios ETFs en una misma fecha no son independientes.

| Indicador | Modelo | Pesos iguales diarios |
|---|---:|---:|
| Rendimiento acumulado | 2.09% | 58.95% |
| Rendimiento anual compuesto | 0.70% | 16.85% |
| Volatilidad anualizada | 1.56% | 10.98% |
| Caída máxima | -2.38% | -10.93% |
| Sharpe (tasa 0 %) | 0.453 | 1.473 |

En esta simulación, seleccionar ETFs con el modelo no mejoró el rendimiento frente a repartir el capital por igual. La estrategia ganó 2.09%, mientras que la referencia ganó 58.95%. El Sharpe también fue menor.

La estrategia presentó una caída máxima menor, pero también invirtió menos capital porque dejaba posiciones en efectivo cuando no había señal. Por eso no puedo atribuir esa diferencia solamente a una mejor selección de activos. Para separar esos efectos habría que comparar portafolios con una proporción invertida similar.

Lo que más me llamó la atención es que acertar un poco más no se tradujo en ganar más. También importan cuánto se gana o pierde en cada operación, los costos y cuánto capital permanece invertido.

Dejé los parámetros como estaban antes de revisar test. Si continúo con otras variables o con una frecuencia distinta de rebalanceo, necesitaré otro periodo de evaluación para no elegir las reglas que mejor se acomoden a estos resultados.

![Capital](results/equity_comparison.png)

![Caídas](results/drawdown_comparison.png)
