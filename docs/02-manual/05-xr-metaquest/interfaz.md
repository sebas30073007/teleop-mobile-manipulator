---
title: "Interfaz y controles"
nav_order: 2
parent: "XR Meta Quest"
---

# Interfaz de usuario

## Diseño

La UI prioriza **simplicidad y funcionalidad** antes de explotar todo el potencial MR. El operador debe tener siempre una lectura clara del entorno y poder cambiar el modo de percepción sin distraerse.

Principios aplicados:
- El video es la fuente principal de comprensión directa del entorno
- El lidar es un complemento espacial, no compite con el video por el panel principal
- Los streams inactivos no se transmiten (streaming selectivo en la NUC)
- La UI debe ser estable y clara antes de volverse más compleja

## Implementación

### Tipo de canvas

Canvas Unity en **world-space** sobre passthrough MR del Meta Quest 3. El operador interactúa con **ray interaction** usando los controladores del headset.

### VideoPanel — panel principal

Muestra el stream RGB de la RealSense D435i desde la NUC.

| Parámetro | Valor |
|---|---|
| Resolución | 640×480 px |
| Tasa de cuadros objetivo | ~30 fps |
| Transporte | JPEG comprimido sobre ZMQ port 5555 |
| Latencia objetivo | < 150 ms extremo a extremo |

El contenido visual cambia según el `camera_mode` activo, pero siempre es el **stream principal de comprensión del entorno**.

### LidarPanel — panel complementario

Muestra el grid de ocupación 2D generado por el RPLiDAR C1.

Convención visual del grid:
- **Blanco** — espacio libre / transitable
- **Negro** — obstáculo o zona no transitable
- **Verde** — posición del robot
- **Azul** — orientación frontal del robot

Tasa de actualización: ~12 Hz.

### StatusPanel — estado del sistema

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

### Controles de modo

#### Dropdown de cámara (`BotonesVideo`)

| Opción | Comportamiento en NUC |
|---|---|
| Normal | Stream RGB estándar |
| Pose | Stream RGB con detección de pose (YOLOv8 nano) |
| Segment | Stream RGB con segmentación semántica (YOLOv8 nano-seg) |
| Off | Cámara deshabilitada |

#### Dropdown de lidar (`BotonesLidar`)

| Opción | Radio | Grid |
|---|---|---|
| Detail | 1 m | 200×200 |
| Medium | 2 m | 400×400 |
| Panorama | 3 m | 600×600 |
| Off | — | Sin transmisión |

Resolución de celda: 1 cm fijo en todos los modos.

### Contrato de comandos (ZMQ port 5002)

```json
{"type": "set_camera_mode", "mode": "normal|pose|segment|off"}
{"type": "set_lidar_mode",  "mode": "detail|medium|panorama|off"}
```

### Feedback de interacción

El componente `UiInteractionFeedback.cs` añade:
- **Sonido de hover** al apuntar sobre un control
- **Sonido de click** al seleccionar una opción
- **Micro vibración** del controlador Meta Quest

## Validación

| Función | Estado |
|---|---|
| Canvas world-space sobre passthrough MR | ✅ Funcional |
| VideoPanel con stream RGB en tiempo real | ✅ Verificado |
| LidarPanel con grid de ocupación configurable | ✅ Verificado |
| StatusPanel con datos de conexión y sensores | ✅ Verificado |
| Dropdowns de modos operativos | ✅ Verificado |
| Feedback háptico y sonoro | ✅ Implementado |
| Control de base móvil (joystick → port 5002) | ⏳ Pendiente |
| Control de manipulador 3DOF | ⏳ Pendiente |
| Telemetría real del robot (batería, pose) | ⏳ Pendiente |
