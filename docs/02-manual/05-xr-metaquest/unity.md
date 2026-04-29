---
title: "Unity y comunicación ZMQ"
nav_order: 1
parent: "XR Meta Quest"
---

# Unity y comunicación ZMQ

## Requisitos

La aplicación Unity debía:

- Ejecutarse en Meta Quest 3 con modo passthrough MR
- Recibir video RGB y datos de sensores desde la NUC en tiempo real
- Enviar comandos de modo de percepción a la NUC
- Ser extensible para agregar control del robot y gemelo digital en etapas futuras

## Diseño

### Stack tecnológico

| Paquete | Función |
|---|---|
| Meta XR SDK (All-in-One) 83.0 | SDK principal para Meta Quest, passthrough y controladores |
| AsyncZMQ (NetMQ) | Cliente ZeroMQ para comunicación con la NUC |
| Unity XR Interaction Toolkit | Gestión de ray interaction y EventSystem VR/MR |

### Arquitectura de comunicación

La NUC embarcada expone tres endpoints ZMQ. Unity actúa como cliente en los tres:

| Puerto | Tipo ZMQ | Dirección | Contenido |
|---|---|---|---|
| `:5555` | PUB/SUB | NUC → Unity | `video_rgb` — frames JPEG del stream principal |
| `:5001` | PUB/SUB | NUC → Unity | `stat`, `mode_ack`, `lidar_grid`, `cam_info`, `vision`, `error` |
| `:5002` | PUB/SUB | Unity → NUC | `cmd` — comandos JSON (modos, y en el futuro control del robot) |

## Implementación

### Componentes ZMQ en Unity

#### `ZmqVideoReceiver.cs`
- Se suscribe a `tcp://<NUC_IP>:5555` topic `video_rgb`
- Decodifica JPEG en hilo secundario y actualiza un `RawImage` en `VideoPanel`
- Mantiene métricas locales: FPS, resolución, estado de conexión
- Envía comandos de modo de cámara a port 5002

#### `ZmqSensorReceiver.cs`
- Se suscribe a `tcp://<NUC_IP>:5001` topics `stat` y `mode_ack`
- Actualiza el estado global: `camera_ok`, `lidar_ok`, modo activo
- Alimenta al `RobotStatusPanel`

#### `ZmqLidarGridView.cs`
- Se suscribe a `tcp://<NUC_IP>:5001` topic `lidar_grid`
- Reconstruye el grid como `Texture2D` y lo renderiza en `LidarPanel`
- Adapta el tamaño de textura dinámicamente al cambiar modo
- Envía comandos de modo de lidar a port 5002

{: .note }
Los comandos UI se reenvían varias veces con pequeña separación temporal para compensar el problema de *slow joiner* de ZMQ PUB/SUB.

### Jerarquía de la escena

```
SampleScene
├── Main_menu
│   └── CanvasRoot
│       ├── UIBackplate
│       │   ├── BotonesVideo     (dropdown camera mode)
│       │   ├── BotonesLidar     (dropdown lidar mode)
│       │   ├── StatusPanel
│       │   ├── VideoPanel
│       │   │   └── VideoRawImage
│       │   └── LidarPanel
│       │       └── LidarRawImage
│       ├── SensorReceiver
│       └── ISDK_RayCanvasInteraction
├── EventSystem
└── (demás objetos de escena MR)
```

## Validación

| Función | Estado |
|---|---|
| Proyecto compilado y desplegado en Meta Quest 3 | ✅ Sin errores |
| SDK Meta XR inicializado, passthrough activo | ✅ Verificado |
| Comunicación ZMQ establecida (video + sensores + comandos) | ✅ Verificado |
| Dropdowns sincronizados con backend via `mode_ack` | ✅ Verificado |
| Importación de modelo URDF (gemelo digital) | ⏳ Mediano plazo |

> **Pendiente:** Documentar el procedimiento completo de build e instalación APK en Meta Quest 3.
