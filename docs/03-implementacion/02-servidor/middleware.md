---
title: "Middleware"
nav_order: 2
parent: "Servidor"
---

# Middleware ZMQ

## Arquitectura de comunicación

El master Python corre en la NUC y gestiona toda la comunicación con Unity vía **ZeroMQ (ZMQ)**. El diseño es pub-sub con tres puertos diferenciados por responsabilidad:

| Puerto | Rol NUC | Rol Unity | Protocolo |
|---|---|---|---|
| `:5555` | PUB | SUB | Video — frames JPEG del stream principal |
| `:5001` | PUB | SUB | Sensores y estado — JSON por topic |
| `:5002` | SUB | PUB | Comandos desde Unity hacia NUC |

## Hilos internos del master Python

El master está organizado en workers concurrentes:

| Hilo / Worker | Responsabilidad |
|---|---|
| `camera_thread` | Pipeline RealSense: captura, procesa según `camera_mode`, publica |
| `video_pub_thread` | Publica frames JPEG en port 5555 |
| `lidar_async_worker` | Captura RPLiDAR, genera grid de ocupación, publica según `lidar_mode` |
| `sensor_pub_thread` | Publica `stat`, `cam_info`, `mode_ack`, `lidar_grid`, `error` en port 5001 |
| `command_listener_thread` | Escucha comandos en port 5002, actualiza modos activos |
| `status_thread` | Publica heartbeat periódico del sistema |

## Topics ZMQ (port 5001)

| Topic | Tipo | Contenido |
|---|---|---|
| `stat` | JSON | Estado del sistema (ver estructura abajo) |
| `mode_ack` | JSON | Confirmación de cambio de modo |
| `lidar_grid` | JSON | Grid de ocupación activo (ver estructura abajo) |
| `cam_info` | JSON | Intrínsecos de la cámara y escala de profundidad |
| `vision` | JSON | Resultados de YOLOv8 (keypoints / máscaras) |
| `error` | JSON | Mensajes de error del sistema |

### Estructura típica de `stat`

```json
{
  "camera_ok": true,
  "lidar_ok": true,
  "cmd_link_ok": true,
  "active_camera_mode": "normal",
  "active_lidar_mode": "detail",
  "uptime": 123.4,
  "ts": 1712000000.0,
  "dropped_frames": 0
}
```

### Estructura de `lidar_grid`

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

## Modos de operación

### Modos de cámara

| Modo | Comportamiento |
|---|---|
| `normal` | Stream RGB estándar sin anotaciones ML |
| `pose` | RGB anotado con detección de pose (YOLOv8 nano-pose) |
| `segment` | RGB anotado con segmentación semántica (YOLOv8 nano-seg) |
| `off` | Cámara deshabilitada; sin publicación de video |

### Modos de lidar

| Modo | Celda | Radio | Grid |
|---|---|---|---|
| `detail` | 1 cm | 1 m | 200×200 |
| `medium` | 1 cm | 2 m | 400×400 |
| `panorama` | 1 cm | 3 m | 600×600 |
| `off` | — | — | Sin publicación |

## Comandos entrantes (port 5002)

```json
{"type": "set_camera_mode", "mode": "normal|pose|segment|off"}
{"type": "set_lidar_mode",  "mode": "detail|medium|panorama|off"}
```

Futuros comandos de control del robot y manipulador usarán el mismo puerto.

## Decisiones de diseño

- **Streaming selectivo** — la NUC solo publica el modo activo; los modos inactivos no consumen CPU ni ancho de banda
- **Separación de puertos** — video en un puerto dedicado permite alta frecuencia sin bloquear el canal de sensores
- **Cola con high watermark** — manejo asíncrono de frames para absorber picos sin acumular latencia
- **Herramienta de corrección de profundidad** — curva de calibración interpolada para la RealSense D435i que ajusta la estimación de distancia real

## Estado actual

- [x] Arquitectura ZMQ de 3 puertos operativa
- [x] Streaming de video y lidar funcional
- [x] Cambio de modos desde Unity confirmado por `mode_ack`
- [ ] Control de robot y manipulador via port 5002
- [ ] Telemetría completa del robot en `stat` (batería, pose, temperatura)
- [ ] Watchdog de conexión con detención segura del robot
