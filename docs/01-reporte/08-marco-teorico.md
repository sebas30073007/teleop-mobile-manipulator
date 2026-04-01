---
title: "Marco teórico"
nav_order: 8
parent: "Reporte"
---

# Marco teórico

## 1. Logística de e-commerce y automatización de almacenes

La logística del comercio electrónico se distingue de la logística tradicional por la granularidad de sus operaciones: en lugar de mover pallets completos entre puntos fijos, gestiona miles de pedidos individuales con ventanas de tiempo reducidas y alta variedad de SKUs. Esta granularidad traslada complejidad operativa hacia el interior del almacén, específicamente hacia las operaciones de surtido (*picking*), clasificación (*sortation*) y empaque (*packing*) [3].

La respuesta de la industria ha sido la automatización progresiva mediante sistemas AGV (*Automated Guided Vehicles*), robots de picking, transportadores automáticos y sistemas AS/RS (*Automated Storage and Retrieval Systems*). Sin embargo, estos sistemas están optimizados para altos volúmenes con baja variabilidad de producto y presentan limitaciones de flexibilidad ante cambios de demanda o de catálogo. La robotización colaborativa — donde el robot amplía las capacidades del operador humano en lugar de reemplazarlo — surge como alternativa complementaria, especialmente relevante en operaciones medianas o con alta variabilidad de SKU [4].

El concepto de *teleoperación logística* extiende el modelo colaborativo al eliminar la restricción de proximidad física: el operador puede supervisar y controlar el robot desde cualquier ubicación con conectividad adecuada. Esto abre la posibilidad de redistribuir la carga de trabajo operativo hacia perfiles de usuarios que no pueden estar presentes físicamente en el almacén, incluyendo personas con discapacidad motriz.

## 2. Discapacidad motriz, teletrabajo e inclusión laboral

La Organización Internacional del Trabajo (OIT) enmarca la discapacidad en el contexto laboral desde un modelo social: la discapacidad no es un atributo de la persona sino el resultado de la interacción entre las condiciones individuales y las barreras del entorno. En consecuencia, la inclusión laboral requiere modificar el entorno — no solo a la persona — para eliminar barreras de acceso al empleo.

En México, los datos del INEGI (Censos Económicos 2024) revelan que la participación laboral formal de personas con discapacidad es estructuralmente baja [7][8]. Las barreras son de tres tipos: físicas (acceso al lugar de trabajo, ergonomía del puesto), tecnológicas (interfaces no adaptadas, software sin accesibilidad) y sociales (prejuicios en procesos de contratación, falta de capacitación específica).

El teletrabajo convencional reduce las barreras físicas para roles de oficina, pero no aplica a tareas operativas que requieren interacción con el entorno físico. La teleoperación robótica extiende el principio del teletrabajo hacia dominios físicos: el operador remoto interactúa con el entorno a través de un sistema que actúa como proxy corporal, habilitando la ejecución de tareas físicas sin presencia en el sitio. Para que este modelo sea genuinamente inclusivo, la interfaz de control debe diseñarse con criterios de accesibilidad desde el inicio — no como adaptación posterior.

## 3. Robótica móvil, manipulación y teleoperación

### Plataformas móviles en interiores

Los robots móviles para interiores operan típicamente sobre bases de tracción diferencial, omnidireccional o de tipo Ackermann. La tracción diferencial — dos ruedas motorizadas independientes con rueda de apoyo pasiva — es la más frecuente en aplicaciones de almacén por su simplicidad mecánica, capacidad de giro en su propio eje y facilidad de control cinemático. El control de velocidad y dirección se reduce a modular de forma independiente la velocidad de cada rueda motriz, lo que lo hace directamente compatible con joysticks analógicos como los que ofrece un controlador XR.

### Manipulación robótica para pick-and-place

Las operaciones de pick-and-place en logística requieren al menos dos grados de libertad activos para operar en el plano vertical (alcance y elevación), complementados por un efector final capaz de asir y soltar objetos de forma controlada. Para el rango de tareas logísticas objetivo — toma de cajas o recipientes ligeros desde estantes o transportadores — un brazo de dos articulaciones (hombro + codo) con garra de dos dedos ofrece suficiente cobertura del espacio de trabajo relevante con la menor complejidad mecánica posible.

El control de motores paso a paso con drivers de lazo cerrado (como el CL57T) combina la simplicidad de control de los steppers con retroalimentación de posición mediante encoder, eliminando el problema de pérdida de pasos bajo carga variable. Para una aplicación de manipulación donde la precisión repetible es más crítica que la velocidad de movimiento, esta solución ofrece una relación costo-desempeño favorable respecto a servomotores de grado industrial.

### Latencia y retroalimentación en teleoperación

La teleoperación efectiva requiere que el operador mantenga *situational awareness* — conciencia del estado del robot y su entorno — a través de retroalimentación sensorial mediada por el sistema. El canal principal es la retroalimentación visual (cámara en primera persona); retroalimentación de profundidad, audio del entorno y, en sistemas más avanzados, retroalimentación háptica, complementan la experiencia.

La latencia de lazo cerrado — el tiempo entre que el operador emite un comando y percibe su efecto a través del video de retroalimentación — es el parámetro de desempeño más crítico. Estudios de teleoperación documentan que latencias superiores a 150–200 ms degradan significativamente la capacidad del operador para realizar ajustes finos, aumentando tanto el tiempo de ejecución como la tasa de error. Para el contexto de este proyecto, operar en red local permite apuntar a latencias menores a 100 ms extremo a extremo.

## 4. Realidad extendida (XR) para interfaces de teleoperación

La realidad extendida engloba realidad virtual (VR), aumentada (AR) y mixta (MR). Para aplicaciones de teleoperación, la VR inmersiva ofrece ventajas sobre las interfaces 2D convencionales: percepción espacial más natural del entorno del robot, control intuitivo mediante movimiento de cabeza y controladores de mano, y reducción de la distancia cognitiva entre la intención del operador y la acción del robot.

Los headsets de consumo actuales — en particular la familia Meta Quest — ofrecen resolución, frecuencia de refresco y capacidades de tracking suficientes para aplicaciones de teleoperación industrial ligera, con la ventaja de un costo significativamente menor que equipos de grado industrial. El SDK de Meta XR para Unity permite integrar renderizado estereoscópico, tracking de controladores y proyección de streams de video externo dentro de la escena virtual, combinando la retroalimentación de la cámara del robot con elementos de UI superpuestos.

Para operadores con discapacidad motriz, la interfaz XR debe diseñarse con criterios de accesibilidad integrados: mínimo número de acciones requeridas por tarea, opciones de control alternativo, retroalimentación redundante (visual y auditiva) y tolerancia a imprecisión de movimiento. La adaptabilidad de la interfaz XR a distintos perfiles de usuario es una de las ventajas clave de este enfoque frente a interfaces físicas especializadas.

## 5. Usabilidad y métricas de evaluación en teleoperación

La usabilidad de un sistema interactivo se define según la norma ISO 9241-11 en tres dimensiones: efectividad (¿el usuario logra el objetivo?), eficiencia (¿a qué costo en tiempo y esfuerzo?) y satisfacción (¿la experiencia resulta aceptable?). Las tres dimensiones son relevantes para un sistema de teleoperación, aunque con pesos distintos según el contexto de uso.

El *System Usability Scale* (SUS) es el instrumento más ampliamente adoptado para evaluación rápida de usabilidad: un cuestionario de 10 ítems en escala Likert que produce una puntuación de 0 a 100. Puntajes superiores a 68 corresponden a sistemas clasificados como aceptables para uso general; puntajes superiores a 80 se consideran buenos. El SUS ha sido validado en sistemas de control remoto y robots, y su brevedad lo hace compatible con sesiones de prueba donde la carga cognitiva del usuario ya es alta.

La carga cognitiva en teleoperación — la cantidad de recursos mentales que el sistema demanda al operador — es un determinante clave tanto de usabilidad como de accesibilidad. Los factores que más la incrementan son: latencia elevada, campo visual limitado en el video de retroalimentación, número de controles activos simultáneos y ausencia de autonomía asistida en el robot. Reducir la carga cognitiva es, en este proyecto, sinónimo de diseñar para inclusión: un sistema más sencillo de operar es simultáneamente un sistema más accesible para personas con discapacidad.

---

*Siguiente: [Cronograma →]({{ "/docs/01-reporte/09-cronograma" | relative_url }})*
