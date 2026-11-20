# Selección de ETFs con un modelo de clasificación

Quise revisar si un modelo podía ayudarme a seleccionar ETFs y cómo se comparaba esa selección con repartir el capital entre todos por igual. También revisé las caídas y lo que se pierde en comisiones.

## Datos

- Fuente: Yahoo Finance mediante yfinance; precios diarios ajustados.
- Periodo: 2010-01-04 a 2025-12-31. La fecha final solicitada es 2026-01-01, exclusiva.
- Universo: SPY, QQQ, IWM, EFA, EEM, TLT, IEF y GLD.
- 4,024 sesiones por ETF: 32,192 combinaciones fecha-activo antes de ventanas y etiquetas.
- Sin faltantes ni fechas duplicadas en la descarga revisada.
- Los ETF son una selección fija retrospectiva: no se estudia un universo histórico completo ni el sesgo de supervivencia.

| Símbolo | Exposición general usada en el estudio |
|---|---|
| SPY | Acciones estadounidenses de gran capitalización |
| QQQ | Nasdaq-100 |
| IWM | Acciones estadounidenses de pequeña capitalización |
| EFA | Acciones de mercados desarrollados fuera de EE. UU. y Canadá |
| EEM | Acciones de mercados emergentes |
| IEF | Bonos del Tesoro estadounidense de 7 a 10 años |
| TLT | Bonos del Tesoro estadounidense de más de 20 años |
| GLD | Oro |

## Cómo lo trabajé

1. Revisé fechas, disponibilidad y precios.
2. Calculé rendimientos, volatilidad y correlaciones.
3. Generé ocho variables numéricas: rendimientos de 1, 5, 20 y 60 sesiones; volatilidad de 20; y precio relativo a las medias de 10, 20 y 60 sesiones. Agregué indicadores de ticker, mes y día de la semana.
4. Definí una clasificación de rendimiento futuro positivo. Para una señal calculada en t, la entrada se supone al cierre de t+1 y la salida al cierre de t+2. Las variables futuras quedan fuera de los predictores.
5. Comparé DecisionTreeClassifier (profundidad 4) y RandomForestClassifier (100 árboles, profundidad 5). Ambos usan un mínimo de 50 observaciones por hoja y semilla 42.
6. Separé entrenamiento antes de 2020, validación 2020–2022 y test desde 2023. Excluí etiquetas que cruzan los límites. Elegí por accuracy de validación, con precision como desempate, y reentrené con desarrollo anterior a 2023.
7. Usé un umbral fijo de probabilidad 0.55 para la simulación. No hay búsqueda de hiperparámetros ni optimización del umbral en este proyecto.
8. Comparé operaciones vectorizadas independientes y una simulación secuencial con capital limitado.

## Supuestos de la simulación

- Capital inicial normalizado a 1; todas las magnitudes de inversión se expresan en la moneda de cotización, sin conversión a MXN.
- Sin apalancamiento ni ventas en corto. Posiciones fraccionarias permitidas.
- Cada señal positiva ocupa 1/8 del capital; el resto queda en efectivo sin intereses.
- Referencia: los ocho ETFs con pesos iguales y rebalanceo diario.
- Comisión/costo agregado del 0.1 % por lado sobre el cambio absoluto de pesos; es una aproximación y no una tarifa de un bróker específico. No se modela el deslizamiento por separado.
- El capital se reinvierte. Se valora a mercado al final, sin liquidación final forzada.
- Sharpe con tasa libre de riesgo cero y anualización de 252 sesiones; no se incluyen impuestos.
- El modelo permanece fijo después de entrenarse con desarrollo. Las señales del cierre de 2025 son históricas.

## Resultados

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

## Archivos

| Archivo | Contenido |
|---|---|
| etf_portfolio_analysis.ipynb | Notebook ejecutado con explicación de cada etapa |
| etf_project.py | Funciones y ejecución completa del análisis |
| requirements.txt | Versiones del entorno de ejecución |
| RESULTADOS.md | Lectura de resultados y gráficas |
| results/ | Métricas, simulaciones, correlaciones, importancia y gráficas |
| VERIFICACION.md | Comprobaciones realizadas y límites de reproducción |

## Reproducir

El entorno de esta ejecución usó Python 3.12.14. Desde una terminal, dentro de esta carpeta:

```bash
python -m venv .venv
```

En Windows PowerShell, activa con `.venv\Scripts\Activate.ps1`. En Linux/macOS, usa `source .venv/bin/activate`. Después:

```bash
python -m pip install -r requirements.txt
python etf_project.py
```

Para Colab, abre el notebook y ejecuta las celdas en orden. La celda `%%writefile` vuelve a crear el script. No es necesario subir los CSV originales de precios a GitHub: la descarga está incluida.

Los CSV de results son salidas del análisis, no una base original de precios. El proveedor puede revisar los datos ajustados; una descarga posterior y otras versiones de bibliotecas pueden cambiar ligeramente los resultados. Por eso una nueva ejecución puede no dar exactamente las mismas cifras.

## Límites

Ocho ETFs y una sola división temporal no bastan para demostrar una ventaja estable. La accuracy se mide con la clase del modelo y las operaciones con un umbral 0.55. No se hizo calibración de probabilidades, prueba de significancia, comparación de exposición igualada ni evaluación walk-forward. Las correlaciones históricas completas son descriptivas; la correlación de variables con el objetivo se calculó solamente en desarrollo. Las importancias del árbol no demuestran causalidad.

## Relación con el curso

Adaptación de los materiales de [Analytics in Stock Markets Zoomcamp](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp): módulos 1–2 (datos y transformaciones), 3 (modelado), 4 (simulación) y 5 (scripts y automatización). El universo de ETFs, el horizonte y los parámetros corresponden a este proyecto.

La descripción del proyecto del curso está en [projects](https://github.com/DataTalksClub/stock-markets-analytics-zoomcamp/tree/main/projects).
