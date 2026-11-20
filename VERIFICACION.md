# Verificación

- Se revisaron el código y las salidas del cuaderno.
- Se ejecutó el script completo con una descarga nueva.
- Se ejecutaron las celdas del notebook de entrega en orden con IPython local, sin un kernel remoto de Colab; se omitió la instalación porque las dependencias ya estaban disponibles.
- Pruebas con datos sintéticos: modificar el último precio no altera las variables anteriores; el objetivo corresponde al retorno de t+1 a t+2; con precios constantes y sin costos el capital no cambia; con una comisión inicial de 0.1 % el capital queda en 0.999 y no vuelve a disminuir si no hay rebalanceo; la caída inicial incluye ese costo.
- Se revisaron los límites temporales del entrenamiento y la validación. No se incluyen objetivos futuros en las variables.
- La accuracy del árbol en test se mantuvo en 54.25 % al repetir la ejecución. Los precios ajustados y el bosque pueden variar ligeramente en nuevas descargas; por eso los archivos finales se generaron juntos en la misma ejecución.
- No se ajustaron modelos ni umbral para mejorar los resultados observados de test.
- No se verificó el rendimiento con otra fuente de precios ni con operaciones reales.

Estas comprobaciones revisan el funcionamiento del código; no prueban que la estrategia vaya a ser rentable en el futuro.
