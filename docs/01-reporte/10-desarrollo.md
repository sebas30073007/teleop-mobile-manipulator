---
title: "Desarrollo"
nav_order: 10
parent: "Reporte"
---

# Desarrollo

## Análisis de tareas logísticas

El punto de partida del diseño fue determinar qué tareas dentro de un almacén de e-commerce son candidatas viables para teleoperación con un robot móvil-manipulador. El análisis consideró cuatro tareas representativas del flujo interno de almacén, evaluadas según tres criterios: complejidad de ejecución (nivel de destreza y decisión requerido), riesgo operativo (consecuencias de un error) y potencial de teleoperación (beneficio marginal de operar el robot de forma remota versus presencial).

| Tarea | Descripción | Complejidad | Riesgo | Potencial teleop. |
|---|---|:---:|:---:|:---:|
| Traslado interno | Movimiento de unidades entre zonas del almacén | Media | Media | **Alta** |
| Surtido asistido | Localización y toma de ítems para pedido | Alta | Media | Media |
| Abastecimiento de estación | Reposición de materiales en zonas de trabajo | Media | Baja | **Alta** |
| Entrega en punto interno | Transporte a nodo de consolidación o despacho | Baja | Baja | **Alta** |

![Tabla de análisis de tareas]({{ "/assets/img/full-tabla-tareas.png" | relative_url }})

Las tareas de traslado interno y abastecimiento de estación fueron seleccionadas como casos de uso primarios del prototipo, por la combinación de alto potencial de teleoperación y nivel de riesgo manejable para un sistema en fase de validación experimental.

## Arquitectura del sistema

El sistema se organiza en tres capas funcionales diseñadas para ser independientes a nivel de desarrollo pero integradas en tiempo real durante la operación. La comunicación fluye de forma bidireccional entre capas: los comandos del operador bajan de XR al robot, y la telemetría y el video suben del robot a la interfaz XR.

```
[ Interfaz XR — Meta Quest + Unity ]
           ↕  WebSocket / ROSbridge
[ Servidor ROS2 — Middleware + Percepción ]
           ↕  WiFi / Serial
[ Plataforma Robótica — Base móvil + Brazo ]
```

### Capa 1: Plataforma robótica

**Base móvil:** Tracción diferencial con dos motores paso a paso NEMA23 controlados por drivers CL57T de lazo cerrado. Los encoders integrados en los drivers permiten control de posición preciso sin acumulación de error por pérdida de pasos. La electrónica de control está centralizada en un microcontrolador ESP32-C3, que recibe comandos de velocidad desde el servidor ROS2 y los traduce en señales de paso y dirección para los drivers.

**Brazo manipulador:** Dos grados de libertad — articulación de hombro (rotación en plano vertical) y articulación de codo (flexión) — accionados por motores paso a paso NEMA17 en el hombro y NEMA34 en el codo (mayor par requerido por el mayor momento de carga). El efector final es una garra de dos dedos accionada por servomotor, controlada directamente desde el nodo ROS2 del brazo.

**Sensores:** Cámara RGB montada en el extremo del brazo para retroalimentación visual al operador. La posición de montaje en el efector permite al operador ver el objeto objetivo desde el punto de vista del robot durante la operación de agarre.

### Capa 2: Servidor de coordinación (middleware ROS2)

El servidor corre sobre una PC con Ubuntu y ROS2. Su función es actuar como hub de coordinación entre la plataforma robótica y la interfaz XR, gestionando todos los flujos de datos del sistema:

- **Recepción de comandos:** Nodo ROSbridge que expone un WebSocket hacia la interfaz XR, recibe comandos de movimiento en formato JSON y los publica como mensajes ROS2 estándar (`cmd_vel` para la base, ángulos para el brazo).
- **Control de la base móvil:** Nodo que suscribe a `cmd_vel` y transmite las señales correspondientes al ESP32-C3 vía WiFi o serial.
- **Control del brazo:** Nodo que recibe ángulos objetivo por articulación y coordina el movimiento secuencial del hombro y el codo.
- **Procesamiento de video:** El stream de la cámara del robot se recibe en el servidor, se comprime y se retransmite hacia la interfaz XR.
- **Telemetría:** Estado del sistema (velocidad actual, ángulos del brazo, estado de la garra, indicadores de batería) publicado hacia la interfaz XR para su visualización en el HUD del operador.

### Capa 3: Interfaz XR (Unity + Meta Quest)

La interfaz XR es una aplicación Unity desplegada en Meta Quest en modo standalone. El operador ve el entorno del robot en primera persona — el video de la cámara proyectado en el visor estereoscópico — y controla el sistema mediante los controladores del headset:

| Control | Acción |
|---|---|
| Joystick izquierdo | Velocidad de traslación de la base móvil |
| Joystick derecho | Velocidad de rotación de la base móvil |
| Gatillo derecho | Apertura / cierre de garra |
| Botones A / B | Elevación del brazo (subir / bajar codo) |
| Botones X / Y | Rotación del hombro |

La interfaz incluye un HUD superpuesto con indicadores de estado: nivel de batería, latencia de red, estado de conexión con el servidor y alertas de sistema. El diseño del HUD sigue el principio de carga cognitiva mínima: información visible solo cuando es relevante para la tarea activa.

## Decisiones de diseño clave

**¿Por qué ROS2?** ROS2 ofrece comunicación DDS confiable entre nodos, un ecosistema maduro de drivers de hardware para robots (motores, cámaras, sensores), y facilidad de integración con herramientas externas (Unity, Python, C++). Construir el middleware desde cero habría duplicado el esfuerzo de desarrollo sin añadir valor al sistema.

**¿Por qué ESP32-C3?** Integra WiFi y Bluetooth en un solo chip, tiene capacidad de cómputo suficiente para control de motores en tiempo real, y su ecosistema de desarrollo (Arduino/ESP-IDF) permite prototipado rápido. El bajo costo por unidad facilita reemplazos durante fases de prueba sin impacto significativo en presupuesto.

**¿Por qué Meta Quest?** Es el headset de consumo con mejor relación rendimiento/precio disponible en el mercado actual, con SDK activamente mantenido para Unity. Su modo standalone — sin conexión a PC — simplifica la arquitectura de la capa XR y elimina una fuente de latencia adicional.

**¿Por qué drivers CL57T (lazo cerrado) para los motores paso a paso?** Los steppers en lazo abierto pierden pasos bajo carga variable, generando error acumulado de posición no detectable por el controlador. Los drivers CL57T añaden un encoder al motor y corrigen el error en tiempo real: el resultado es la predictibilidad de un stepper con la confiabilidad de un servomotor, a un costo sustancialmente menor que una solución de servo industrial.

---

*Siguiente: [Referencias →]({{ "/docs/01-reporte/11-referencias" | relative_url }})*
