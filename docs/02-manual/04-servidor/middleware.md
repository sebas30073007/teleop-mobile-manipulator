---
title: "Middleware ZMQ"
nav_order: 1
parent: "Servidor / NUC"
---

# Middleware ZMQ

[Ver código fuente NUC](https://github.com/sebas30073007/teleop-mobile-manipulator/blob/main/assets/downloads/NUC_master_code.py){: .btn .btn-outline }

## Diseño

El master Python usa **ZeroMQ** con cuatro puertos diferenciados por tipo de dato:

| Puerto | Rol NUC | Rol Unity | Tipo |
|---|---|---|---|
| `:5555` | PUB | SUB | Video — frames JPEG comprimidos |
| `:5001` | PUB | SUB | Sensores y estado — JSON por topic |
| `:5002` | SUB | PUB | Comandos desde Unity hacia NUC |
| `:5007` | PUB | SUB | Paredes y puntos LiDAR — datos binarios |

**Decisiones de diseño:**
- **Separación de puertos** — video y datos binarios en puertos dedicados para no bloquear el canal JSON
- **Streaming selectivo** — cada modo publica solo si está activo; los modos inactivos no consumen CPU ni red
- **High watermark** — manejo asíncrono de colas para absorber picos sin acumular latencia

---

## Puertos y topics

### Puerto :5555 — Video

Topic único `video_rgb`. Frames JPEG a 640×480 px, hasta 30 fps, calidad 85.

### Puerto :5001 — Sensores y estado (JSON)

| Topic | Frecuencia | Contenido |
|---|---|---|
| `stat` | ~2 Hz | Estado global del sistema (ver estructura abajo) |
| `mode_ack` | Al cambiar modo | Confirmación de cambio de modo |
| `lidar_grid` | ~12 Hz | Grid de ocupación activo (ver estructura abajo) |
| `cam_info` | Continuo | Intrínsecos RealSense y escala de profundidad |
| `vision` | ~10 Hz | Resultados YOLOv8 (keypoints o máscaras) |
| `error` | Por evento | Mensajes de error del sistema |
| `manip_state` | ~4 Hz | Ángulos actuales del manipulador y estado de finales de carrera |
| `gripper_state` | ~4 Hz | Posición del gripper en mm, busy, calibrado |
| `walls_status` | Continuo | Estado del pipeline de paredes inmersivo |
| `points_status` | Continuo | Estado del pipeline de puntos LiDAR |

#### Estructura de `stat`

```json
{
  "camera_ok": true,
  "lidar_ok": true,
  "cmd_link_ok": true,
  "master_serial_ok": true,
  "gripper_serial_ok": true,
  "active_camera_mode": "normal",
  "active_lidar_mode": "detail",
  "walls_enabled": false,
  "points_enabled": false,
  "drive_enabled": false,
  "manip_enabled": false,
  "actual_base_deg": 0.0,
  "actual_codo_deg": 0.0,
  "actual_muneca_deg": 0.0,
  "gripper_mm": 0.0,
  "gripper_calibrated": false,
  "uptime_s": 123.4,
  "ts": 1712000000.0
}
```

#### Estructura de `lidar_grid`

```json
{
  "ts": 1712000000.0,
  "mode": "detail",
  "grid_size": 200,
  "cell_size_m": 0.01,
  "radius_m": 1.0,
  "hits": 1420,
  "occupancy": [0, 0, 1, 0, ...]
}
```

`occupancy[]` es el grid linealizado (row-major). `1` = obstáculo, `0` = libre.

#### Estructura de `manip_state`

```json
{
  "base_deg": 0.0,
  "codo_deg": 45.0,
  "muneca_deg": -30.0,
  "sw2": 0,
  "sw3": 1,
  "busy": false,
  "ts": 1712000000.0
}
```

#### Estructura de `gripper_state`

```json
{
  "mm": 25.0,
  "target_mm": 30.0,
  "count": 1200,
  "busy": false,
  "calibrated": true,
  "ts": 1712000000.0
}
```

### Puerto :5007 — Paredes y puntos binarios

Canal binario para modos inmersivos (opcionales). Publica cuatro tipos de paquetes:

| Paquete | Magic bytes | Contenido |
|---|---|---|
| `walls_snapshot` | `WSNP` | Snapshot completo de segmentos de pared derivados del LiDAR |
| `walls_delta` | `WDEL` | Añadidos y eliminados desde el último snapshot |
| `lidar_points_snapshot` | `LPSN` | Nube completa de puntos LiDAR en frame local |
| `lidar_points_frame` | `LPFR` | Frame incremental de puntos LiDAR |

---

## Modos de operación

### Modos de cámara

| Modo | Comportamiento |
|---|---|
| `normal` | Stream RGB sin procesamiento |
| `pose` | RGB anotado con detección de pose (YOLOv8 nano-pose) |
| `segment` | RGB anotado con segmentación semántica (YOLOv8 nano-seg) |
| `off` | Cámara deshabilitada; sin publicación de video |

### Modos de LiDAR

| Modo | Celda | Radio | Grid |
|---|---|---|---|
| `detail` | 1 cm | 1 m | 200×200 |
| `medium` | 1 cm | 2 m | 400×400 |
| `panorama` | 1 cm | 3 m | 600×600 |
| `off` | — | — | Sin publicación |

### Modo paredes (`walls_enabled`)

Cuando activo, el pipeline de paredes procesa el buffer acumulado del RPLiDAR (ventana de 4 s, hasta 150 000 puntos), aplica operaciones morfológicas y extrae segmentos de pared simplificados para el modo inmersivo XR. Frecuencia de procesamiento: ~1 Hz.

### Modo puntos (`points_enabled`)

Publica los puntos LiDAR crudos en frame local para representación volumétrica en XR. Hasta 12 000 puntos por paquete a ~8 Hz.

---

## Comandos (puerto :5002)

Todos los comandos son JSON. Algunos son comandos de control continuo; otros son eventos puntuales.

### Modos de percepción

```json
{"type": "set_camera_mode", "mode": "normal|pose|segment|off"}
{"type": "set_lidar_mode",  "mode": "detail|medium|panorama|off"}
{"type": "set_walls_mode",  "enabled": true}
{"type": "set_points_mode", "enabled": true}
```

### Habilitación de control

```json
{"type": "set_control_enable", "drive_enabled": true, "manip_enabled": true, "base_enabled": true}
{"type": "master_arm"}
{"type": "master_disarm"}
{"type": "stop_all"}
```

### Control de base móvil

```json
{"type": "drive_cmd", "v": 0.5, "w": -0.3, "enabled": true}
{"type": "drive_direct", "left": 150, "right": 120}
```

`drive_cmd` usa modelo uniciclo (v = velocidad lineal, w = velocidad angular, rango [-1, 1]). La NUC mezcla y envía al master bridge a 15 Hz.

### Control del manipulador

```json
{"type": "manip_cmd",     "q": [base_deg, codo_deg, muneca_deg]}
{"type": "base_joint_cmd","q_base": 45.0}
{"type": "manip_home"}
{"type": "manip_ascii",   "line": "HOME_ALL"}
```

### Control del gripper

```json
{"type": "gripper_cmd",   "opening_mm": 30.0}
{"type": "gripper_stop"}
{"type": "gripper_ascii", "line": "m 25.0"}
```

---

## Puentes seriales

### Master bridge (COM4) — base y manipulador

El thread `serial_master_thread` gestiona COM4 a 115200 baud. Protocolo de salida:

| Comando | Formato | Descripción |
|---|---|---|
| Drive | `{left},{right}\n` | Tokens de motor, e.g. `150,120` o `S,S` para parar |
| Pose manipulador | `POSE {base} {codo} {muneca}\n` | Ángulos en grados |
| Base individual | `BASE_GOTO {deg}\n` | Solo eje base |
| Home | `HOME_ALL\n` | Búsqueda de cero en todos los ejes |
| Armar | `ARM\n` / `DISARM\n` | Habilita o deshabilita salidas |
| Parar todo | `STOPALL\n` | Detiene base y manipulador |
| Query estado | `M STATE?\n` | Solicita estado del manipulador a ~4 Hz |

La NUC lee respuestas de estado con regex:
```
BASE={deg}deg(...) | CODO={deg}deg(...) | MUNECA={deg}deg(...) SW2={0|1} SW3={0|1}
```

### Gripper bridge (COM5) — gripper

El thread `serial_gripper_thread` gestiona COM5 a 115200 baud. Protocolo:

| Comando | Formato | Descripción |
|---|---|---|
| Mover a posición | `m {mm}\n` | Posición objetivo en mm |
| Detener | `s\n` | Detiene el gripper |
| Query estado | `p\n` | Solicita estado a ~4 Hz |

La NUC lee respuestas con regex:
```
GRIPPER_STATE mm={mm} count={count} target_mm={mm} target_count={count} busy={0|1} calibrated={0|1}
```

---

## Calibración de profundidad

El master aplica una **curva de calibración interpolada** a las medidas de la RealSense D435i. Los pares `(intel_mm, real_mm)` cubren de 160 mm a 1000 mm y compensan la desviación sistemática del sensor a distintas distancias. La corrección se aplica antes de publicar `cam_info`.

---

## Hilos internos

| Hilo | Responsabilidad |
|---|---|
| `camera_thread` | Pipeline RealSense: captura, procesa según `camera_mode` |
| `video_pub_thread` | Publica frames JPEG en :5555 |
| `lidar_async_worker` | Captura RPLiDAR, genera grid y ejecuta pipeline de paredes/puntos |
| `sensor_pub_thread` | Publica todos los topics JSON en :5001 |
| `walls_pub_thread` | Publica datos binarios en :5007 |
| `command_listener_thread` | Escucha :5002 y actualiza modos/estado |
| `serial_master_thread` | Gestiona COM4: drive + manipulador |
| `serial_gripper_thread` | Gestiona COM5: gripper |

## Estado actual

| Funcionalidad | Estado |
|---|---|
| Streaming video, lidar grid, stat | ✅ Verificado |
| Cambio de modos cámara y lidar desde Unity | ✅ Verificado via `mode_ack` |
| Control base móvil (`drive_cmd`) | ✅ Implementado |
| Control manipulador 3DOF (`manip_cmd`) | ✅ Implementado |
| Control gripper (`gripper_cmd`) | ✅ Implementado |
| Telemetría manipulador (`manip_state`) | ✅ Implementado |
| Telemetría gripper (`gripper_state`) | ✅ Implementado |
| Pipeline de paredes inmersivo | ✅ Implementado |
| Pipeline de puntos LiDAR | ✅ Implementado |
| Watchdog de desconexión con paro seguro | ⏳ Parcial — timeout de drive cmd implementado (`DRIVE_CMD_TIMEOUT_S = 0.35 s`), watchdog de conexión ZMQ pendiente |
