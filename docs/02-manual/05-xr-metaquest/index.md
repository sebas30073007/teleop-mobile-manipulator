---
title: "XR Meta Quest"
nav_order: 5
parent: "Documentación"
has_children: true
---

# XR Meta Quest

La interfaz de teleoperación es una **aplicación Unity para Meta Quest 3** que permite al operador visualizar el entorno del robot en realidad mixta (MR), controlar la base móvil y el manipulador, y cambiar modos de percepción. Se ejecuta en modo passthrough con un canvas world-space flotante frente al operador.

## Arquitectura del sistema

```
┌───────────────────────────────────────────────────────┐
│              Meta Quest 3 (Unity)                     │
│                                                       │
│  [Izq]  StatusPanel + Cámara + EmergStop + IP         │
│  [Centro] VideoPanel (RGB) + LidarPanel (2D grid)     │
│  [Der]  ManipulatorPanel (sliders) + LiDAR 3D         │
│                                                       │
│  [Joystick derecho] → Drive teleop  (15 Hz)           │
└───────────────────────────────────────────────────────┘
     │  ZMQ SUB :5555   video_rgb JPEG
     │  ZMQ SUB :5001   stat, manip_state, gripper_state, lidar_grid
     │  ZMQ SUB :5007   walls, lidar_points (binario)
     │  ZMQ PUB :5002   cmd JSON (control + percepción)
     ▼
┌───────────────────────────────────────────────────────┐
│              NUC — embarcada en el robot              │
└───────────────────────────────────────────────────────┘
```

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Motor de juego | Unity (Android ARM64) |
| SDK XR | Meta XR SDK 83.0 (OpenXR) |
| Comunicación NUC ↔ Unity | ZeroMQ (AsyncZMQ / NetMQ en C#) |
| Input controllers | OVRInput (joystick, botones, hápticos) |
| Visión por computadora | YOLOv8 nano (pose y segmentación, en NUC) |
| Gemelo digital | Pendiente (mediano plazo) |

## Subsecciones

- [Unity y comunicación ZMQ]({{ "/docs/02-manual/05-xr-metaquest/unity" | relative_url }}) — setup del proyecto, todos los componentes ZMQ, referencia completa de comandos JSON
- [Interfaz y controles]({{ "/docs/02-manual/05-xr-metaquest/interfaz" | relative_url }}) — paneles, drive teleop, manipulador, gripper, LiDAR 3D
- [Pruebas]({{ "/docs/02-manual/05-xr-metaquest/pruebas" | relative_url }}) — validaciones de despliegue, video, lidar, control

## Estado del subsistema

| Funcionalidad | Estado |
|---|---|
| Proyecto Unity compilado en Meta Quest 3 | ✅ Funcional |
| Stream de video RGB 640×480 @ ~30 fps | ✅ Verificado |
| Panel LiDAR 2D con grid de ocupación (3 modos) | ✅ Verificado |
| StatusPanel con telemetría de manipulador y gripper | ✅ Verificado |
| Feedback háptico y sonoro | ✅ Implementado |
| Drive teleop desde joystick del headset | ✅ Funcional |
| Control de manipulador 3DOF desde headset | ✅ Funcional |
| Control de gripper (mm) desde headset | ✅ Funcional |
| LiDAR 3D — paredes y nube de puntos | ✅ Funcional |
| Teclado virtual para cambio de IP | ✅ Funcional |
| Gemelo digital URDF | ⏳ Mediano plazo |
