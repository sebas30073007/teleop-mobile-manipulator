---
title: "Servidor"
nav_order: 2
parent: "Implementación"
has_children: true
---

# NUC — Nodo Maestro de Percepción

La **NUC (Intel NUC)** es el computador embarcado del robot. No existe un servidor externo separado: la NUC viaja a bordo del robot y actúa como nodo maestro de percepción, procesamiento y coordinación.

## Responsabilidades principales

- Adquisición de sensores (RealSense D435i y RPLiDAR C1)
- Procesamiento selectivo según el modo activo (visión por computadora con YOLO)
- Publicación de video y datos via **ZeroMQ**
- Recepción de comandos desde Unity (Meta Quest 3)
- Coordinación futura del control del robot y del manipulador vía ESP32-C3

## Arquitectura física

```
┌──────────────────────────────────────────┐
│             NUC (embarcada)              │
│                                          │
│  RealSense D435i (USB)                   │
│  RPLiDAR C1     (USB)                    │
│  ESP32-C3       (USB) → bus I2C → PCBs  │
│                                          │
│  Python master server (ZMQ)             │
│    PUB :5555  → video_rgb               │
│    PUB :5001  → stat, lidar_grid, ...   │
│    SUB :5002  ← cmd (desde Unity)       │
└──────────────────────────────────────────┘
            │ WiFi
            ▼
┌──────────────────────────────────────────┐
│          Meta Quest 3 (Unity)            │
└──────────────────────────────────────────┘
```

## Flujos de datos

| Canal | Dirección | Contenido |
|---|---|---|
| Video stream | NUC → Quest | Frames JPEG (640×480 @ ~30 fps) via ZMQ :5555 |
| Estado y sensores | NUC → Quest | `stat`, `lidar_grid`, `mode_ack`, `cam_info` via ZMQ :5001 |
| Comandos de modo | Quest → NUC | JSON `set_camera_mode`, `set_lidar_mode` via ZMQ :5002 |
| Control del robot | Quest → NUC (futuro) | Comandos de velocidad y articulación via ZMQ :5002 |

## Módulos del servidor

- [Middleware ZMQ]({{ "/docs/03-implementacion/02-servidor/middleware" | relative_url }}) — Arquitectura de puertos, topics y contrato de datos
- [Percepción]({{ "/docs/03-implementacion/02-servidor/percepcion" | relative_url }}) — Pipeline de visión y lidar
- [Pruebas]({{ "/docs/03-implementacion/02-servidor/pruebas" | relative_url }}) — Validaciones de integración

## Estado actual

- [x] NUC como nodo maestro operativo a bordo del robot
- [x] Streaming selectivo ZMQ funcional (video + lidar + estado)
- [x] Modos de cámara y lidar controlados desde Unity
- [ ] Control de base móvil (port 5002 → ESP32-C3 → motores)
- [ ] Control de manipulador 3DOF
- [ ] Telemetría del robot (batería, pose, temperatura) en pipeline de `stat`
