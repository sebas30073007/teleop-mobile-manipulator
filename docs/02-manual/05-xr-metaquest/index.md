---
title: "XR Meta Quest"
nav_order: 5
parent: "Documentación"
has_children: true
---

# XR Meta Quest

La interfaz de teleoperación es una **aplicación Unity para Meta Quest 3** que permite al operador visualizar el entorno del robot en realidad mixta (MR), cambiar modos de percepción y, en fases futuras, enviar comandos de control al robot. Se ejecuta en modo passthrough con un canvas world-space flotante frente al operador.

## Arquitectura del sistema

```
┌──────────────────────────────────────────┐
│          Meta Quest 3 (Unity)            │
│                                          │
│  ┌──────────────┐   ┌─────────────────┐  │
│  │  VideoPanel  │   │   LidarPanel    │  │
│  │  RGB anotado │   │  Grid ocupación │  │
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
└──────────────────────────────────────────┘
```

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Motor de juego | Unity (Android ARM64) |
| SDK XR | Meta XR SDK 83.0 (OpenXR) |
| Comunicación NUC ↔ Unity | ZeroMQ (AsyncZMQ / NetMQ en C#) |
| Visión por computadora | YOLOv8 nano (pose y segmentación, en NUC) |
| Gemelo digital | Pendiente (mediano plazo) |

## Subsecciones

- [Unity y comunicación ZMQ]({{ "/docs/02-manual/05-xr-metaquest/unity" | relative_url }}) — setup del proyecto, componentes ZMQ, jerarquía de escena
- [Interfaz y controles]({{ "/docs/02-manual/05-xr-metaquest/interfaz" | relative_url }}) — paneles, modos de percepción, contrato de comandos
- [Pruebas]({{ "/docs/02-manual/05-xr-metaquest/pruebas" | relative_url }}) — validaciones de despliegue, video, lidar, UI

## Estado del subsistema

| Funcionalidad | Estado |
|---|---|
| Proyecto Unity compilado en Meta Quest 3 | ✅ Funcional |
| Stream de video RGB 640×480 @ ~30 fps | ✅ Verificado |
| Panel LiDAR con grid de ocupación | ✅ Verificado |
| StatusPanel y dropdowns de modos | ✅ Verificado |
| Feedback háptico y sonoro | ✅ Implementado |
| Control de base móvil desde headset | ⏳ Pendiente |
| Control de manipulador 3DOF | ⏳ Pendiente |
| Gemelo digital URDF | ⏳ Pendiente |
