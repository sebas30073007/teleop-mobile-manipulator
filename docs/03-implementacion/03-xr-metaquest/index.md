---
title: "XR Meta Quest"
nav_order: 3
parent: "Implementación"
has_children: true
---

# XR Meta Quest

La interfaz de teleoperación es una **aplicación Unity para Meta Quest 3** que permite al operador visualizar el entorno del robot en realidad mixta (MR), cambiar modos de percepción y, en fases futuras, enviar comandos de control al robot. Se ejecuta en modo passthrough con un canvas world-space flotante frente al operador.

## Arquitectura del sistema

La NUC (Intel NUC) es el **computador embarcado del propio robot**. No existe un servidor externo separado: la NUC publica sensores y recibe comandos directamente vía **ZeroMQ (ZMQ)** sobre WiFi.

```
┌──────────────────────────────────────────┐
│          Meta Quest 3 (Unity)            │
│                                          │
│  ┌──────────────┐   ┌─────────────────┐  │
│  │  VideoPanel  │   │   LidarPanel    │  │
│  │  RGB anotado │   │  Grid ocupación │  │
│  │  (camera_mode│   │  (lidar_mode)   │  │
│  └──────────────┘   └─────────────────┘  │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │  StatusPanel  + Dropdowns UI     │    │
│  └──────────────────────────────────┘    │
└──────────────────────────────────────────┘
     │  ZMQ SUB :5555   (video_rgb JPEG)
     │  ZMQ SUB :5001   (stat, lidar_grid, mode_ack, …)
     │  ZMQ PUB :5002   (cmd JSON)
     ▼
┌──────────────────────────────────────────┐
│          NUC — embarcada en el robot     │
│                                          │
│  RealSense D435i  →  camera_mode         │
│  RPLiDAR C1       →  lidar_mode          │
│  ESP32-C3 (USB)   →  bus I2C → PCBs     │
└──────────────────────────────────────────┘
```

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Motor de juego | Unity (Android ARM64) |
| SDK XR | Meta XR SDK (OpenXR) |
| Comunicación NUC ↔ Unity | ZeroMQ (AsyncZMQ en C#) |
| Stream de video | JPEG sobre ZMQ port 5555 |
| Datos de sensores | JSON sobre ZMQ port 5001 |
| Comandos desde UI | JSON sobre ZMQ port 5002 |
| Visión por computadora | YOLOv8 nano (pose y segmentación) |
| Gemelo digital | Pendiente (mediano plazo) |

## Módulos de esta sección

- [Unity y comunicación ZMQ]({{ "/docs/03-implementacion/03-xr-metaquest/unity" | relative_url }}) — Setup del proyecto y componentes ZMQ
- [Interfaz y controles]({{ "/docs/03-implementacion/03-xr-metaquest/interfaz" | relative_url }}) — UI, paneles, modos y streaming
- [Pruebas]({{ "/docs/03-implementacion/03-xr-metaquest/pruebas" | relative_url }}) — Validaciones de componentes individuales

## Estado actual

- [x] Arquitectura ZMQ definida y funcional
- [x] Proyecto Unity compilado y desplegado en Meta Quest 3
- [x] Stream de video RGB 640×480 @ ~30 fps funcional
- [x] Panel de LiDAR con grid de ocupación funcional
- [x] Panel de estado (StatusPanel) funcional
- [x] Dropdowns de modo de cámara y lidar operativos
- [x] Feedback háptico y sonoro en UI
- [ ] Control de base móvil desde port 5002
- [ ] Control de manipulador 3DOF desde port 5002
- [ ] Telemetría de robot real en StatusPanel
- [ ] Gemelo digital con URDF
- [ ] Pruebas de usabilidad formales
