---
title: "Interfaz y controles"
nav_order: 3
parent: "XR Meta Quest"
---

# Interfaz de usuario

## Filosofía de diseño

La UI prioriza **simplicidad y funcionalidad** antes de explotar todo el potencial MR. El objetivo es que el operador tenga siempre una lectura clara del entorno y pueda cambiar el modo de percepción sin distraerse.

Principios aplicados:
- El video es la fuente principal de comprensión directa del entorno
- El lidar es un complemento espacial, no compite con el video por el panel principal
- Los streams inactivos no se transmiten (streaming selectivo)
- La UI debe ser estable y clara antes de volverse más compleja

## Tipo de canvas

La interfaz corre como un **canvas Unity en world-space**, visible sobre el passthrough MR del Meta Quest 3. El operador interactúa con los controles mediante **ray interaction** con los controladores del headset.

## Paneles de la UI

### VideoPanel — panel principal

Muestra el stream RGB de la RealSense D435i transmitido desde la NUC. El contenido visual del video cambia según el `camera_mode` activo, pero siempre es el **stream principal de comprensión del entorno**.

Configuración de transmisión:
- **Resolución:** 640×480 px
- **Tasa de cuadros objetivo:** ~30 fps
- **Transporte:** JPEG comprimido sobre ZMQ port 5555
- **Latencia objetivo:** < 150 ms extremo a extremo

### LidarPanel — panel complementario

Muestra el grid de ocupación 2D generado por el RPLiDAR C1. Se usa como ayuda espacial para detección de obstáculos y lectura de zonas transitables.

Convención visual del grid:
- **Blanco** — espacio libre / transitable
- **Negro** — obstáculo o zona no transitable
- **Verde** — posición del robot
- **Azul** — orientación frontal del robot

Tasas de actualización: ~12 Hz.

### StatusPanel — estado del sistema

Muestra información en tiempo real del estado de la comunicación y los sensores:

| Campo | Contenido |
|---|---|
| Robot | Connected / Disconnected |
| Target IP | IP de la NUC |
| My IP | IP del headset |
| Mode | Modo de cámara y lidar activos |
| FPS | Cuadros por segundo del video |
| Res | Resolución del frame recibido |
| Camera OK | Estado del sensor RealSense |
| Lidar OK | Estado del RPLiDAR C1 |

Tasa de refresco: ~2 Hz (heartbeat desde topic `stat`).

## Controles de modo

La UI expone dos dropdowns para cambiar el modo de operación de los sensores. Al seleccionar una opción, Unity envía un comando JSON a la NUC vía ZMQ port 5002.

### Dropdown de cámara (`BotonesVideo`)

| Opción | Comportamiento en NUC |
|---|---|
| Normal | Stream RGB estándar, sin anotaciones ML |
| Pose | Stream RGB con detección de pose (YOLOv8 nano) |
| Segment | Stream RGB con segmentación semántica (YOLOv8 nano-seg) |
| Off | Cámara deshabilitada, sin transmisión de video |

### Dropdown de lidar (`BotonesLidar`)

| Opción | Radio | Grid | Uso |
|---|---|---|---|
| Detail | 1 m | 200×200 | Precisión máxima local |
| Medium | 2 m | 400×400 | Compromiso precisión/contexto |
| Panorama | 3 m | 600×600 | Mayor contexto espacial |
| Off | — | — | Sin transmisión de grid |

Resolución de celda: 1 cm fijo en todos los modos.

## Contrato de comandos (ZMQ port 5002)

Los comandos se envían como JSON. Para mejorar la robustez ante el problema de *slow joiner* de ZMQ, cada comando se reenvía varias veces con pequeña separación temporal.

```json
// Cambio de modo de cámara
{"type": "set_camera_mode", "mode": "normal"}
{"type": "set_camera_mode", "mode": "pose"}
{"type": "set_camera_mode", "mode": "segment"}
{"type": "set_camera_mode", "mode": "off"}

// Cambio de modo de lidar
{"type": "set_lidar_mode", "mode": "detail"}
{"type": "set_lidar_mode", "mode": "medium"}
{"type": "set_lidar_mode", "mode": "panorama"}
{"type": "set_lidar_mode", "mode": "off"}
```

Comandos de control de robot y manipulador se integrarán en etapas futuras por el mismo puerto.

## Feedback de interacción

El componente `UiInteractionFeedback.cs` añade retroalimentación sensorial al interactuar con la UI:

- **Sonido de hover** al apuntar sobre un control
- **Sonido de click** al seleccionar una opción
- **Micro vibración** del controlador Meta Quest

Esto mejora la legibilidad táctil de la interfaz y la confianza del operador al cambiar modos.

## Estado actual

- [x] Canvas world-space sobre passthrough MR funcional
- [x] VideoPanel con stream RGB en tiempo real
- [x] LidarPanel con grid de ocupación configurable
- [x] StatusPanel con datos de conexión y sensores
- [x] Dropdown de modos de cámara operativo
- [x] Dropdown de modos de lidar operativo
- [x] Feedback háptico y sonoro implementado
- [ ] Control de base móvil (joystick → port 5002)
- [ ] Control de manipulador 3DOF
- [ ] Integración de telemetría real del robot (batería, pose)
- [ ] Pruebas de usabilidad formales con usuarios objetivo
