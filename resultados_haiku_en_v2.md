# Resultados: Claude Haiku 5.5 (instrucciones en inglés, versión en_v2)

Resultados de las 532 comparaciones del archivo `results_claude-haiku-5-5_en_v2.csv`: 133 fotografías, cada una comparada con 4 especies. Las cifras se calcularon con el programa `analisis_resultados.py` y corresponden a **una sola ejecución** del modelo.

Esta prueba usó los mismos criterios de diagnóstico, las mismas imágenes y el mismo modelo que la prueba en español (es_v2). Las instrucciones, las descripciones diagnósticas y las respuestas del modelo están en inglés. Las descripciones se tomaron del documento *Diagnosis Duellaman, Costa & Gunter_English*. Ese documento **no es una traducción** del usado en español:

- sus descripciones son más extensas: incluyen la franja postorbital, los cambios con la edad (ontogenia), el número de manchas dorsales y las manchas laterales;
- incluye una descripción de Costa para *L. ashmeadii*, que no está en la versión en español.

Por eso, las diferencias con la prueba en español pueden deberse tanto al idioma como a la información adicional (sección 6).

## 1. Veredictos por grupo y especie de referencia

La tabla muestra el porcentaje de fotografías de cada grupo (filas) que el modelo consideró compatibles (MATCH) con cada especie de referencia (columnas). La diagonal corresponde a las respuestas correctas, y las demás celdas de las filas identificadas son confusiones.

| Grupo de la fotografía | *L. annulata* | *L. approximans* | *L. ashmeadii* | *L. ornata* |
|---|---|---|---|---|
| *L. annulata* (12) | **67%** | 33% | 8% | 33% |
| *L. approximans* (32) | 75% | **53%** | 19% | 50% |
| *L. ashmeadii* (41) | 39% | 22% | **54%** | 68% |
| *L. ornata* (18) | 72% | 50% | 6% | **67%** |
| Sin identificar (30) | 53% | 50% | 37% | 77% |

## 2. Desempeño por especie

Solo se cuentan las 103 fotografías identificadas por especialistas. La **sensibilidad** es el porcentaje de fotografías de la especie que el modelo reconoció como tal. La **especificidad** es el porcentaje de fotografías de otras especies que el modelo descartó correctamente.

| Especie de referencia | Sensibilidad | Especificidad |
|---|---|---|
| *L. annulata* | 67% | 42% |
| *L. approximans* | 53% | 69% |
| *L. ashmeadii* | 54% | 87% |
| *L. ornata* | 67% | 44% |
| **Global** | **57%** | **58%** |

En conjunto, el desempeño sigue siendo apenas superior al azar, que correspondería a una sensibilidad y una especificidad de 50%. Como en la prueba en español, el resultado varía mucho entre especies.

## 3. Número de especies compatibles por fotografía

| Grupo | 0 especies | 1 especie | 2 especies | 3 especies | 4 especies |
|---|---|---|---|---|---|
| *L. annulata* | 2 | 5 | 3 | 2 | 0 |
| *L. approximans* | 5 | 6 | 9 | 9 | 3 |
| *L. ashmeadii* | 5 | 8 | 18 | 9 | 1 |
| *L. ornata* | 1 | 5 | 7 | 4 | 1 |
| Sin identificar | 3 | 7 | 6 | 10 | 4 |

- En promedio, cada fotografía identificada fue compatible con **1,8 especies**.
- En 59 de las 103 fotografías (57%), la especie correcta estuvo entre las compatibles.
- Solo **10 fotografías (10%)** fueron compatibles únicamente con la especie correcta.

## 4. Fotografías sin identificar

De las 30 fotografías sin identificar, 7 resultaron compatibles con una sola especie:

- 3 con *L. ornata*;
- 3 con *L. approximans*;
- 1 con *L. annulata*.

Estas asignaciones no coinciden con las de la prueba en español, donde 5 fotografías se asignaron a *L. annulata* y 1 a *L. ashmeadii*. Los veredictos sobre estas fotografías cambian de una prueba a otra (sección 6), por lo que ninguna de estas asignaciones debe tomarse como una identificación confiable.

## 5. Qué indican estos resultados sobre las descripciones diagnósticas

**a) La confusión de *L. approximans* con *L. annulata* se mantiene.** El 75% de las fotografías de *L. approximans* se consideró compatible con *L. annulata*. En la prueba en español esa cifra fue del 72%. Es el resultado más estable entre las dos pruebas. Coincide con lo parecidas que son las descripciones de Costa para estas dos especies en ambos idiomas: occipucio claro sin franjas y primera mancha en media luna fusionada en zigzag.

**b) La descripción de *L. annulata* es algo menos permisiva, pero sigue sin descartar a las demás.** Su especificidad subió del 30% al 42%, sobre todo porque aceptó menos fotografías de *L. ashmeadii* (del 63% al 39%). Sin embargo, sigue aceptando el 75% de *L. approximans* y el 72% de *L. ornata*. A cambio, su sensibilidad bajó del 92% al 67%.

**c) *L. ornata* pasó a ser la especie que más fotografías acepta de otras especies.** Aceptó el 68% de las fotografías de *L. ashmeadii* y el 50% de *L. approximans*, y su especificidad bajó del 64% al 44%. Una posible explicación es que la descripción de Costa en inglés incluye rasgos que también pueden verse en *L. ashmeadii*:

- una línea media ancha en el occipucio;
- una mancha oscura en forma de mariposa;
- una primera mancha del cuerpo de forma variable, "de banda a forma de H".

En *L. ashmeadii*, la primera mancha está dividida por la línea media y se prolonga en dos franjas occipitales, lo que podría leerse como una forma de H. Esta explicación es una hipótesis y habría que confirmarla revisando las justificaciones.

**d) La descripción de *L. approximans* mejoró.** Su especificidad subió del 46% al 69% y su sensibilidad del 41% al 53%. La única diferencia en la información para esta especie es que las descripciones en inglés de Gunther y Costa son más completas.

**e) *L. ashmeadii* sigue siendo la especie mejor delimitada.** Su especificidad fue del 87% (90% en español), aunque su sensibilidad se mantuvo cerca del 55%. Es además la especie con veredictos más estables entre las dos pruebas (sección 6).

**f) Los rasgos citados.** Para cada especie de referencia se contó cuántas justificaciones mencionan cada rasgo, separando aciertos y errores. Es una cifra aproximada, porque se basa en buscar palabras en el texto. En esta prueba los términos se buscaron en inglés. Por ejemplo, "media luna" corresponde a *half-moon* o *crescent*, y "moteado" a *mottled* o *speckled*. Por eso las cifras no son directamente comparables con las de la prueba en español.

| Rasgo citado | *L. annulata* | *L. approximans* | *L. ashmeadii* | *L. ornata* |
|---|---|---|---|---|
| media luna | 85% / 95% | 89% / 84% | 14% / 7% | 10% / 2% |
| zigzag | 85% / 95% | 94% / 100% | 51% / 56% | 39% / 41% |
| línea media / dividida | 50% / 53% | 50% / 41% | 84% / 93% | 92% / 85% |
| parietales | 76% / 67% | 85% / 76% | 100% / 100% | 84% / 72% |
| manchas fusionadas | 74% / 95% | 65% / 89% | 51% / 59% | 18% / 37% |
| color uniforme / sin marcas | 98% / 89% | 48% / 62% | 63% / 37% | 78% / 50% |
| moteado | 59% / 23% | 50% / 27% | 28% / 48% | 35% / 50% |

*Porcentaje de justificaciones que mencionan el rasgo: aciertos / errores.*

Como en la prueba en español, la mayoría de los rasgos se citan con una frecuencia parecida en aciertos y errores. Hay algunas diferencias claras:

- **Fusión de manchas.** La mención de manchas fusionadas aparece más en los errores que en los aciertos: con *L. annulata* (95% frente a 74%), con *L. approximans* (89% frente a 65%) y con *L. ornata* (37% frente a 18%). Ver una fusión en zigzag lleva al modelo a aceptar fotografías equivocadas, lo que sugiere que ese rasgo no es diagnóstico entre estas especies.
- **Moteado.** El moteado aparece más en los aciertos con *L. annulata* (59% frente a 23%) y con *L. approximans* (50% frente a 27%). Con *L. annulata* ya se había observado lo mismo en la prueba en español, así que podría ser un rasgo útil.
- **Coloración uniforme o sin marcas.** Aparece más en los aciertos con *L. ashmeadii* (63% frente a 37%) y con *L. ornata* (78% frente a 50%). Con *L. ornata* coincide con la prueba en español.

**g) Las fotografías siguen limitando la verificación de los rasgos.** El 90–93% de las justificaciones menciona algún rasgo que no se puede observar en la fotografía. Cerca de un tercio menciona que el ejemplar parece conservado. Las expresiones de duda (*tentative*, *limited*, *inconclusive*) aparecen en el 71% de los errores y en el 66% de los aciertos. Es una diferencia menor que en la prueba en español.

## 6. Comparación con la prueba en español

| Especie de referencia | Sensibilidad (es / en) | Especificidad (es / en) | Veredictos iguales en ambas pruebas |
|---|---|---|---|
| *L. annulata* | 92% / 67% | 30% / 42% | 74% |
| *L. approximans* | 41% / 53% | 46% / 69% | 49% |
| *L. ashmeadii* | 59% / 54% | 90% / 87% | 91% |
| *L. ornata* | 50% / 67% | 64% / 44% | 71% |
| **Global** | **55% / 57%** | **55% / 58%** | **71%** |

En el desempeño global, las dos pruebas son casi iguales. Pero en el 29% de las comparaciones el veredicto cambió de una prueba a otra. El acuerdo entre ambas, corregido por el azar, es moderado (kappa de Cohen = 0,42). La estabilidad depende de la especie:

- **Estables:** los veredictos frente a *L. ashmeadii*, la especie con la descripción más concreta, coinciden en el 91% de los casos.
- **Inestables:** los veredictos frente a *L. approximans* coinciden solo en el 49%, es decir, prácticamente al azar.

Estos cambios no pueden atribuirse a una sola causa, porque entre las dos pruebas cambiaron a la vez varias cosas:

- el idioma;
- la extensión de las descripciones;
- la descripción adicional de Costa para *L. ashmeadii*;
- la variación propia del modelo entre ejecuciones.

Aun así, el resultado es relevante para el objetivo de consistencia. Cuando la descripción es concreta, el veredicto se mantiene. Cuando la descripción es ambigua, pequeños cambios en la información entregada bastan para cambiarlo.

## 7. Limitaciones

- Los resultados corresponden a una sola ejecución de un solo modelo, el más pequeño de su familia. Para separar el efecto del idioma del de las descripciones habría que hacer dos pruebas más. Una usaría las descripciones en español traducidas literalmente al inglés. La otra repetiría la misma prueba para medir la variación propia del modelo.
- El conteo de rasgos citados se basa en buscar palabras clave en inglés. Es una aproximación y no reemplaza la lectura de las justificaciones.
- Algunos grupos son pequeños. Por ejemplo, *L. annulata* tiene 12 fotografías, así que sus porcentajes cambian mucho con pocas fotografías.
