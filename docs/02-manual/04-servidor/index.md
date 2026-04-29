---
title: "Servidor / NUC"
nav_order: 4
parent: "Documentación"
has_children: true
---

# NUC — Nodo Maestro de Percepción

La **NUC (Intel NUC)** es el computador embarcado del robot. No existe un servidor externo separado: la NUC viaja a bordo y actúa como nodo maestro de percepción, procesamiento y coordinación, ejecutando backend en **Python 3.12**.

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

## Responsabilidades

- Adquisición de sensores (RealSense D435i y RPLiDAR C1)
- Procesamiento selectivo según modo activo (visión por computadora con YOLOv8)
- Publicación de video y datos vía ZeroMQ
- Recepción de comandos desde Unity (Meta Quest 3)
- Coordinación del control del robot y manipulador vía ESP32-C3

## Subsecciones

- [Middleware ZMQ]({{ "/docs/02-manual/04-servidor/middleware" | relative_url }}) — arquitectura de puertos, topics, contrato de datos
- [Percepción]({{ "/docs/02-manual/04-servidor/percepcion" | relative_url }}) — pipeline RealSense y RPLiDAR
- [Pruebas]({{ "/docs/02-manual/04-servidor/pruebas" | relative_url }}) — validaciones de canales y comunicación

## Estado del subsistema

| Funcionalidad | Estado |
|---|---|
| NUC como nodo maestro operativo | ✅ Funcional |
| Streaming ZMQ (video + lidar + estado) | ✅ Verificado |
| Modos de cámara y lidar controlados desde Unity | ✅ Verificado |
| Control base móvil (5002 → ESP32-C3 → motores) | ⏳ Pendiente |
| Control manipulador 3DOF | ⏳ Pendiente |
| Telemetría del robot en `stat` | ⏳ Pendiente |
