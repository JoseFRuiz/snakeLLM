# Verificación de especies de *Leptodeira* con un modelo de lenguaje y visión

## 1. ¿Qué es un modelo de lenguaje y de visión?

Un **modelo de lenguaje** es un programa de inteligencia artificial entrenado con grandes cantidades de texto para predecir y generar lenguaje. Por eso puede leer instrucciones escritas en lenguaje natural, como el español, y responder con texto coherente. No consulta una base de datos durante la tarea: responde a partir de los patrones que aprendió durante su entrenamiento y de la información que se le entrega en cada consulta.

Un **modelo de lenguaje y visión** (o modelo multimodal) puede recibir, además de texto, imágenes. El modelo describe lo que observa en una fotografía (colores, manchas, franjas, su forma y su disposición) y relaciona esas observaciones con el texto de las instrucciones. Así puede comparar dos imágenes y una descripción escrita y emitir un juicio razonado.

Estos modelos no "conocen" las especies como lo hace un especialista. Su respuesta depende de la calidad de las imágenes y de las descripciones que se le entregan, y puede contener errores. Además, el modelo puede dar respuestas algo distintas si se le hace la misma pregunta más de una vez.

## 2. Modelo utilizado

Se usó **Claude Haiku 5.5** (identificador `claude-haiku-5-5`), un modelo de lenguaje y visión desarrollado por la empresa Anthropic. Haiku es la versión más pequeña y económica de la familia de modelos Claude. Se accedió a él a través de la interfaz de programación (API) de Anthropic, mediante un programa escrito en Python que envía las consultas y guarda las respuestas. El modelo no se reentrenó ni se ajustó para esta tarea: se usó tal como lo ofrece el proveedor, con los parámetros predeterminados del servicio.

## 3. Información utilizada

En cada consulta el modelo recibió tres elementos:

1. **Una imagen de referencia** de la especie, que muestra la coloración y las manchas de la cabeza de un ejemplar confirmado. Se usó una imagen de referencia por especie para las cuatro especies estudiadas: *L. annulata*, *L. approximans*, *L. ashmeadii* y *L. ornata*.
2. **Las descripciones diagnósticas del patrón de coloración** de la especie, tomadas de la literatura y traducidas al español. Para cada especie se incluyeron todas las descripciones disponibles, cada una identificada con el nombre de su autor:

   | Especie | Autores de las descripciones |
   |---|---|
   | *L. annulata* | Duellman; Costa |
   | *L. approximans* | Gunter; Costa |
   | *L. ashmeadii* | Duellman |
   | *L. ornata* | Duellman; Costa |

   *[Completar con las referencias bibliográficas completas.]*
3. **Una imagen candidata**: una fotografía del ejemplar que se quiere verificar.

Las fotografías candidatas se organizaron en carpetas según su identificación previa por especialistas. Así, cada respuesta del modelo se puede comparar después con la especie real. Se incluyó además un grupo de fotografías **sin identificar**:

| Grupo | Número de fotografías |
|---|---|
| *L. annulata* | 12 |
| *L. approximans* | 32 |
| *L. ashmeadii* | 41 |
| *L. ornata* | 18 |
| Sin identificar | 30 |
| **Total** | **133** |

Antes de enviarlas al modelo, las fotografías se prepararon de la misma manera:

- se corrigió su orientación según la información guardada por la cámara;
- se redujo su tamaño a un máximo de 1568 píxeles en el lado más largo, que es el tamaño recomendado para este modelo;
- se convirtieron al formato JPEG.

## 4. Instrucciones dadas al modelo

Las instrucciones se escribieron en español y le piden al modelo que actúe como un herpetólogo que verifica la especie de un ejemplar. Establecen los siguientes criterios de diagnóstico:

- **Prioridad:** basar el diagnóstico principalmente en la **coloración** y en la **forma de las manchas**. Esto incluye el color de fondo, la presencia y el trazado de franjas, y la forma y disposición de las manchas dorsales.
- **Coloración de la cabeza:** sí se tiene en cuenta (color de la parte superior de la cabeza y manchas, franjas y marcas en la cabeza y la nuca).
- **Rasgos excluidos:** no se tienen en cuenta el tamaño ni la forma de la cabeza, de los ojos ni de las escamas. Las escamas solo sirven como referencia para ubicar manchas o franjas, por ejemplo "franja sobre las parietales". Se excluyeron porque esos rasgos varían con la posición, el ángulo y la distancia de la fotografía.

Con estos criterios, el modelo debe:

1. comparar la imagen candidata con la imagen de referencia y con las descripciones diagnósticas;
2. dar un veredicto: **COINCIDE** o **NO COINCIDE** con la especie;
3. justificar brevemente su veredicto, indicando qué rasgos de coloración y de las manchas coinciden y cuáles no, y en qué descripción se basa cada observación.

El texto completo de las instrucciones está en el Anexo.

## 5. Procedimiento

Cada una de las 133 fotografías se comparó con cada una de las 4 especies, en consultas independientes. En total se hicieron **532 comparaciones**. Cada consulta es independiente: el modelo no recuerda las comparaciones anteriores ni sabe a qué grupo pertenece la fotografía.

De cada consulta se guardó:

- la especie de referencia;
- el grupo de la fotografía;
- el nombre del archivo;
- el veredicto;
- la justificación escrita por el modelo.

Gracias a la justificación, cada veredicto puede revisarse y entender en qué rasgos se basó el modelo.

Como cada fotografía se evalúa frente a las cuatro especies, una misma fotografía puede coincidir con una especie, con varias o con ninguna. Para las fotografías identificadas por especialistas, los veredictos se pueden comparar con la especie real. Así se mide con qué frecuencia el modelo reconoce correctamente la especie y con qué frecuencia la confunde con otra. Las fotografías sin identificar no entran en esa medición: para ellas, el resultado indica con cuál o cuáles especies es compatible su patrón de coloración, según el modelo.

## 6. Aporte a la consistencia del diagnóstico

Identificar una especie por su patrón de coloración implica cierto grado de subjetividad. Dos observadores pueden interpretar de forma distinta la misma fotografía. Por ejemplo, pueden no coincidir en si unas manchas están "fusionadas en zigzag" o "divididas por la línea media". Incluso un mismo observador puede cambiar de criterio según el cansancio, el orden en que revisa las fotografías o lo que espera encontrar. Uno de los propósitos de este análisis es explorar si el modelo puede dar un diagnóstico más consistente y, así, reducir parte de esa subjetividad. El procedimiento contribuye a ello de varias maneras:

- **Criterios explícitos y fijos.** Todas las fotografías se evaluaron con las mismas instrucciones escritas, las mismas imágenes de referencia y las mismas descripciones diagnósticas. Los criterios de diagnóstico, es decir, qué rasgos se priorizan y cuáles se excluyen, quedan definidos por escrito antes del análisis. No dependen del juicio del momento.
- **Evaluación a ciegas.** El modelo no sabe a qué grupo pertenece cada fotografía ni qué especie se espera. Por eso su veredicto no está influido por una identificación previa.
- **Independencia entre consultas.** Cada comparación se hace por separado. El modelo no se cansa ni se ve influido por las fotografías que revisó antes, y el orden de revisión no afecta el resultado.
- **Justificación escrita y verificable.** Cada veredicto va acompañado de los rasgos observados y de la descripción en que se basa. Así, un especialista puede revisar en qué se fundamentó cada decisión, detectar errores de interpretación y discutir los casos de desacuerdo con argumentos concretos.
- **Reproducibilidad.** Las instrucciones, las imágenes y la versión del modelo quedan documentadas. Por eso el análisis puede repetirse y extenderse a nuevas fotografías bajo las mismas condiciones.

Sin embargo, esto no elimina por completo la subjetividad ni garantiza un diagnóstico correcto:

- **Variación entre ejecuciones.** El modelo puede dar respuestas distintas ante la misma consulta repetida, sobre todo en los casos dudosos.
- **Dependencia de la información entregada.** El resultado depende de las instrucciones, de las imágenes de referencia y de las descripciones diagnósticas. Si dos descripciones son muy parecidas, el modelo tendrá dificultad para diferenciar esas especies, igual que una persona (ver sección 7).
- **Sesgos propios del modelo.** Sus sesgos y errores de interpretación de las imágenes no son del todo predecibles.

Por estas razones, el modelo se plantea como una herramienta de apoyo al especialista y no como un reemplazo. Su consistencia puede medirse. Una forma es repetir el análisis varias veces y calcular cuántas veces se mantiene el mismo veredicto. Otra es comparar ese grado de acuerdo con el que se obtiene entre observadores humanos que evalúan las mismas fotografías.

## 7. Evaluación de la claridad de las descripciones diagnósticas

Esta investigación parte de una dificultad conocida: las descripciones de la literatura no siempre son lo bastante claras o determinantes para clasificar una especie. A veces usan términos vagos, como "manchas oscuras" sin especificar su forma. A veces describen rasgos que comparten varias especies. Y a veces dos autores describen la misma especie de forma distinta.

En este análisis, el modelo identifica la especie solo a partir de la imagen de referencia y de las descripciones que se le entregan. Por eso su desempeño depende en gran parte de la claridad de esas descripciones. Si una descripción es ambigua o se superpone con la de otra especie, el modelo también tendrá dificultades para separarlas. Así, el análisis no solo pone a prueba al modelo: también sirve para **evaluar de forma sistemática qué tan útiles son las descripciones** para diferenciar las especies. Para ello se pueden examinar los siguientes indicadores:

- **Fotografías compatibles con varias especies.** Cada fotografía se compara con las cuatro especies. Por eso se puede contar cuántas veces una fotografía de una especie conocida se considera compatible también con otra. Los pares de especies que se confunden con frecuencia indican que sus descripciones no permiten separarlas con claridad. Por ejemplo, las descripciones de Costa para *L. annulata* y *L. approximans* son muy parecidas, y cabe esperar que esas dos especies se confundan más a menudo.
- **Rasgos citados en las justificaciones.** El modelo indica qué rasgos observó y en qué descripción se basa cada observación. Al revisar estas justificaciones, se puede identificar qué rasgos descritos llevan a decisiones correctas, es decir, cuáles son realmente diagnósticos. También se puede ver cuáles aparecen en las decisiones erróneas o se aplican a varias especies.
- **Rasgos difíciles de verificar.** Las justificaciones también muestran los rasgos que el modelo no pudo comprobar en la fotografía, o que interpretó de forma dudosa. Esto ayuda a identificar términos de la descripción que son poco precisos o difíciles de observar en una fotografía.
- **Diferencias entre autores.** Cuando una especie tiene descripciones de varios autores, las justificaciones muestran si estas coinciden o se contradicen frente a una misma fotografía.

Este enfoque puede ampliarse con análisis complementarios en los que solo cambia la información entregada al modelo:

- **Un autor a la vez.** Repetir las comparaciones usando la descripción de un solo autor, para medir cuánto aporta cada una.
- **Sin la imagen de referencia.** Repetir las comparaciones usando solo las descripciones, para medir qué tan determinante es el texto por sí mismo.
- **Sin las descripciones.** Repetir las comparaciones usando solo la imagen de referencia, para medir cuánto aporta el texto frente a la comparación visual.

Si el desempeño mejora o empeora al cambiar las descripciones, eso aporta evidencia objetiva sobre su claridad y su valor diagnóstico. Los resultados pueden servir de base para proponer descripciones más precisas, que indiquen qué rasgos de coloración y de las manchas permiten diferenciar mejor cada especie.

## Anexo. Texto de las instrucciones

En cada consulta, `{especie}` se reemplaza por el nombre de la especie de referencia y `{descripciones}` por sus descripciones diagnósticas, cada una precedida del nombre de su autor. Antes del texto se envían las dos imágenes, con las etiquetas "Imagen de referencia:" e "Imagen candidata:".

> Eres un herpetólogo experto que realiza la verificación de especies.
>
> La especie objetivo es *{especie}*.
>
> --- MATERIALES DE REFERENCIA ---
>
> 1. **Imagen de referencia:** La primera imagen muestra la coloración y las manchas de la cabeza de un ejemplar confirmado de *{especie}*.
> 2. **Descripciones diagnósticas (patrón de coloración), por autor:**
> {descripciones}
>
> --- CRITERIOS DEL DIAGNÓSTICO ---
>
> - **Prioridad:** basa el diagnóstico principalmente en la **coloración** y en la **forma de las manchas**: color de fondo, presencia y trazado de franjas, y forma y disposición de las manchas dorsales (por ejemplo, manchas en media luna, fusionadas en zigzag o divididas por la línea media).
> - **Coloración de la cabeza:** sí tenla en cuenta (color de la parte superior de la cabeza, manchas, franjas y marcas en la cabeza y la nuca).
> - **No tengas en cuenta** el tamaño ni la forma de la cabeza, de los ojos ni de las escamas, aunque se vean diferentes de la imagen de referencia. Las escamas solo sirven como referencia para ubicar manchas o franjas (por ejemplo, "franja sobre las parietales").
>
> --- TAREA ---
>
> La segunda imagen es la **Imagen candidata** que se debe identificar.
>
> 1. **Compara** la imagen candidata con la imagen de referencia y con las descripciones diagnósticas, siguiendo los criterios anteriores.
> 2. **Determina** si la imagen candidata **COINCIDE** o **NO COINCIDE** con *{especie}*.
> 3. **Explica brevemente** los rasgos de coloración y de las manchas que coinciden y los que no coinciden, tanto en la cabeza como en el cuerpo (si es visible), indicando en qué descripción se basa cada observación.
>
> Responde en español. La primera línea de tu respuesta debe ser exactamente "VEREDICTO: COINCIDE" o "VEREDICTO: NO COINCIDE", seguida de una breve justificación.
