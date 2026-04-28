---
title: "Unity y comunicación ZMQ"
nav_order: 2
parent: "XR Meta Quest"
---

# Unity y comunicación ZMQ

## Proyecto Unity

El proyecto está configurado para compilación en **Meta Quest 3** (Android ARM64) usando **Meta XR SDK 83.0** con perfil OpenXR. La escena corre en modo **passthrough MR**: el canvas de UI flota en world-space sobre el entorno real del operador.

### Paquetes Unity principales

| Paquete | Función |
|---|---|
| Meta XR SDK (All-in-One) | SDK principal para Meta Quest, passthrough y controladores |
| AsyncZMQ (NetMQ) | Cliente ZeroMQ para comunicación con la NUC |
| Unity XR Interaction Toolkit | Gestión de ray interaction y EventSystem VR/MR |

## Comunicación con la NUC (ZMQ)

La NUC embarcada en el robot expone tres endpoints ZMQ. Unity actúa como cliente en los tres:

| Puerto | Tipo ZMQ | Dirección | Contenido |
|---|---|---|---|
| `:5555` | PUB/SUB | NUC → Unity | `video_rgb` — frames JPEG del stream principal |
| `:5001` | PUB/SUB | NUC → Unity | `stat`, `mode_ack`, `lidar_grid`, `cam_info`, `vision`, `error` |
| `:5002` | PUB/SUB | Unity → NUC | `cmd` — comandos JSON (modos, y futuramente control del robot) |

### Componentes ZMQ en Unity

#### `ZmqVideoReceiver.cs`
- Se suscribe a `tcp://<NUC_IP>:5555` topic `video_rgb`
- Decodifica JPEG en hilo secundario y actualiza un `RawImage` en `VideoPanel`
- Mantiene métricas locales: FPS, resolución, estado de conexión
- Envía comandos de modo de cámara a port 5002:
  - `SetCameraNormal()`, `SetCameraPose()`, `SetCameraSegment()`, `SetCameraOff()`

#### `ZmqSensorReceiver.cs`
- Se suscribe a `tcp://<NUC_IP>:5001` topics `stat` y `mode_ack`
- Actualiza el estado global: `camera_ok`, `lidar_ok`, modo activo de cámara y lidar
- Alimenta al `RobotStatusPanel`

#### `ZmqLidarGridView.cs`
- Se suscribe a `tcp://<NUC_IP>:5001` topic `lidar_grid`
- Reconstruye el grid como `Texture2D` y lo renderiza en `LidarPanel`
- Adapta el tamaño de textura dinámicamente cuando cambia `grid_size`
- Envía comandos de modo de lidar a port 5002

### Robustez ante slow joiner
Los comandos UI se reenvían más de una vez con pequeña separación temporal para compensar el problema clásico de PUB/SUB late subscription.

## Jerarquía de la escena

```
SampleScene
├── Main_menu
│   └── CanvasRoot
│       ├── UIBackplate
│       │   ├── GradientEffect
│       │   ├── BotonesVideo
│       │   │   └── DropDownIconAnd1LineText   (camera mode)
│       │   ├── BotonesLidar
│       │   │   └── DropDownIconAnd1LineText   (lidar mode)
│       │   ├── StatusPanel
│       │   │   ├── RobotStatusText
│       │   │   ├── TargetIpText
│       │   │   ├── MyIpText
│       │   │   ├── ModeText
│       │   │   ├── FpsText
│       │   │   ├── ResText
│       │   │   ├── CameraOkText
│       │   │   └── LidarOkText
│       │   ├── VideoPanel
│       │   │   ├── VideoReceiver
│       │   │   ├── VideoMask
│       │   │   └── VideoRawImage
│       │   └── LidarPanel
│       │       ├── LidarModeController
│       │       ├── LidarReceiver
│       │       ├── LidarMask
│       │       └── LidarRawImage
│       ├── SensorReceiver
│       └── ISDK_RayCanvasInteraction
├── EventSystem
└── (demás objetos de escena MR)
```

## Gemelo digital (pendiente)

El gemelo digital con modelo URDF del robot y sincronización de pose sigue en el roadmap para mediano plazo. En la arquitectura actual la comprensión espacial del robot se logra a través del video anotado y el grid LiDAR.

## Estado actual

- [x] Proyecto Unity compilado y desplegado en Meta Quest 3
- [x] Comunicación ZMQ establecida (video, sensores, comandos)
- [x] Jerarquía de escena MR estructurada
- [x] Dropdowns y StatusPanel sincronizados con backend
- [ ] Importación de modelo URDF y configuración de articulaciones
- [ ] Suscripción a pose en tiempo real para gemelo digital
