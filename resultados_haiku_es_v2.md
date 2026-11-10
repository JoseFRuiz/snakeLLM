# Resultados: Claude Haiku 5.5 (instrucciones versión es_v2)

Resultados de las 532 comparaciones del archivo `results_claude-haiku-5-5_es_v2.csv`: 133 fotografías, cada una comparada con 4 especies. Las cifras se calcularon con el programa `analisis_resultados.py`. Corresponden a **una sola ejecución** del modelo.

## 1. Veredictos por grupo y especie de referencia

La tabla muestra el porcentaje de fotografías de cada grupo (filas) que el modelo consideró compatibles (COINCIDE) con cada especie de referencia (columnas). La diagonal corresponde a las respuestas correctas. Las demás celdas de las filas identificadas son confusiones.

| Grupo de la fotografía | *L. annulata* | *L. approximans* | *L. ashmeadii* | *L. ornata* |
|---|---|---|---|---|
| *L. annulata* (12) | **92%** | 25% | 8% | 25% |
| *L. approximans* (32) | 72% | **41%** | 12% | 19% |
| *L. ashmeadii* (41) | 63% | 63% | **59%** | 54% |
| *L. ornata* (18) | 83% | 50% | 6% | **50%** |
| Sin identificar (30) | 80% | 37% | 23% | 53% |

## 2. Desempeño por especie

Solo se cuentan las 103 fotografías identificadas por especialistas.

- La **sensibilidad** es el porcentaje de fotografías de la especie que el modelo reconoció como tal.
- La **especificidad** es el porcentaje de fotografías de otras especies que el modelo descartó correctamente.

| Especie de referencia | Sensibilidad | Especificidad |
|---|---|---|
| *L. annulata* | 92% | 30% |
| *L. approximans* | 41% | 46% |
| *L. ashmeadii* | 59% | 90% |
| *L. ornata* | 50% | 64% |
| **Global** | **55%** | **55%** |

En conjunto, el desempeño es apenas superior al azar. Con una sensibilidad y una especificidad de 50% el modelo no estaría diferenciando nada. Sin embargo, el resultado varía mucho entre especies. Esa variación es lo más informativo sobre las descripciones (sección 5).

## 3. Número de especies compatibles por fotografía

| Grupo | 0 especies | 1 especie | 2 especies | 3 especies | 4 especies |
|---|---|---|---|---|---|
| *L. annulata* | 1 | 7 | 2 | 1 | 1 |
| *L. approximans* | 5 | 14 | 10 | 0 | 3 |
| *L. ashmeadii* | 2 | 8 | 11 | 12 | 8 |
| *L. ornata* | 1 | 5 | 7 | 5 | 0 |
| Sin identificar | 3 | 6 | 13 | 6 | 2 |

- En promedio, cada fotografía identificada fue compatible con **1,9 especies**.
- En 57 de las 103 fotografías (55%), la especie correcta estuvo entre las compatibles.
- Solo **9 fotografías (9%)** fueron compatibles únicamente con la especie correcta.

## 4. Fotografías sin identificar

De las 30 fotografías sin identificar, solo 6 resultaron compatibles con una sola especie: 5 con *L. annulata* y 1 con *L. ashmeadii*. Como se explica abajo, la descripción de *L. annulata* acepta la mayoría de las fotografías de otras especies. Por eso esas asignaciones a *L. annulata* no deben tomarse como una identificación confiable.

## 5. Qué indican estos resultados sobre las descripciones diagnósticas

**a) La descripción de *L. annulata* no permite descartar otras especies.** El modelo la consideró compatible con el 92% de las fotografías de *L. annulata*. Pero también la consideró compatible con el 72% de *L. approximans*, el 83% de *L. ornata* y el 63% de *L. ashmeadii*, así que su especificidad es solo del 30%. Las justificaciones muestran por qué. Duellman describe la cabeza de *L. annulata* como "por lo general carece de marcas". Ese rasgo describe la *ausencia* de algo, y el modelo lo aplica a casi cualquier fotografía en la que no distingue marcas con claridad. Así, la descripción describe la especie, pero no la diferencia de las demás.

**b) *L. annulata* y *L. approximans* se confunden, sobre todo en una dirección.** El 72% de las fotografías de *L. approximans* se consideró compatible con *L. annulata*. En cambio, solo el 25% de las de *L. annulata* se consideró compatible con *L. approximans*. Esto es coherente con lo parecidas que son las descripciones de Costa para estas dos especies. En ambas, el modelo cita casi siempre los mismos rasgos: "media luna" en el 86–96% de las justificaciones y "zigzag" en el 100%.

**c) La descripción de *L. ashmeadii* es la más diagnóstica.** Como especie de referencia, *L. ashmeadii* tuvo la especificidad más alta (90%): el modelo descartó casi todas las fotografías de otras especies. Sus justificaciones se basan en rasgos concretos y localizados, como las manchas en las escamas parietales (citadas en el 100% de los casos) y la primera mancha dividida por la línea media.

**d) Las otras descripciones no contienen un rasgo que excluya a *L. ashmeadii*.** Las fotografías de *L. ashmeadii* se consideraron compatibles con las otras tres especies en el 54–63% de los casos. El 49% de esas fotografías fue compatible con 3 o 4 especies. Las descripciones de *L. annulata*, *L. approximans* y *L. ornata* indican qué rasgos deben estar presentes, pero no cuáles deberían estar ausentes. Por eso no permiten descartar a *L. ashmeadii*.

**e) Los rasgos citados reflejan el vocabulario de la descripción más que lo observado.** Para cada especie de referencia se contó con qué frecuencia las justificaciones mencionan ciertos rasgos, comparando los aciertos con los errores. Esta cifra es aproximada, porque se basa en la búsqueda de palabras en el texto.

| Rasgo citado | *L. annulata* | *L. approximans* | *L. ashmeadii* | *L. ornata* |
|---|---|---|---|---|
| media luna | 92% / 92% | 96% / 86% | 36% / 26% | 40% / 40% |
| zigzag | 100% / 100% | 100% / 100% | 28% / 30% | 43% / 32% |
| línea media / dividida | 13% / 28% | 17% / 26% | 100% / 100% | 95% / 95% |
| parietales | 76% / 65% | 30% / 23% | 100% / 100% | 98% / 100% |
| color uniforme / sin marcas | 84% / 77% | 61% / 60% | 70% / 57% | 68% / 32% |
| moteado | 39% / 17% | 24% / 28% | 14% / 9% | 32% / 25% |

*Porcentaje de justificaciones que mencionan el rasgo: aciertos / errores.*

Los rasgos se citan con casi la misma frecuencia en los aciertos y en los errores. Esto indica que el modelo revisa la fotografía buscando los términos de la descripción que se le entrega, y que esos términos, por sí solos, no separan las especies. Hay dos excepciones. Con *L. ornata*, la referencia a coloración uniforme o sin marcas aparece en el 68% de los aciertos y en el 32% de los errores. Con *L. annulata*, el moteado aparece en el 39% de los aciertos y en el 17% de los errores. Estos podrían ser rasgos útiles para el diagnóstico.

**f) Las fotografías limitan la verificación de los rasgos.** El 92–93% de las justificaciones menciona algún rasgo que no se puede observar en la fotografía, tanto en los aciertos como en los errores. Las expresiones de duda ("no es concluyente", "confianza moderada", "limitada") aparecen con más frecuencia en los errores (74%) que en los aciertos (58%). Por lo tanto, cuando el modelo expresa dudas, su veredicto es menos confiable. Además, el 31–39% de las justificaciones menciona que el ejemplar parece conservado, lo que puede alterar la coloración.

## 6. Limitaciones

- Los resultados corresponden a una sola ejecución de un solo modelo, el más pequeño de su familia. Repetir el análisis permitiría estimar cuánto varían los veredictos.
- Una ejecución anterior con un modelo más grande (Claude Opus 5.5) y una versión anterior de las instrucciones tuvo una exactitud global del 63%. No es directamente comparable, porque cambiaron dos cosas a la vez: el modelo y las instrucciones.
- El conteo de rasgos citados se basa en la búsqueda de palabras clave. Es una aproximación y no reemplaza la lectura de las justificaciones.
- Algunos grupos son pequeños, como *L. annulata*, con 12 fotografías. Por eso sus porcentajes cambian mucho con pocas fotografías.
