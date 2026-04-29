---
title: "Servidor / NUC"
nav_order: 4
parent: "Documentación"
has_children: true
---

# NUC — Nodo Maestro de Percepción

La **NUC (Intel NUC i7)** es el computador embarcado del robot. No existe un servidor externo separado: la NUC viaja a bordo y actúa como nodo central de percepción, procesamiento y coordinación, ejecutando backend en **Python 3.12**.

[Ver código fuente NUC](https://github.com/sebas30073007/teleop-mobile-manipulator/blob/main/assets/downloads/NUC_master_code.py){: .btn .btn-outline }

## Conexiones físicas

```
┌──────────────────────────────────────────┐
│             NUC (embarcada)              │
│                                          │
│  COM3 — RPLiDAR C1         (USB)         │
│  COM4 — Puente H maestro   (USB)         │
│           └─ I2C → Puente H esclavo      │
│           └─ I2C → Controlador CL57T     │
│  COM5 — Gripper ESP32-C3   (USB)         │
│  USB  — Intel RealSense D435i            │
│                                          │
│  Python master server (ZMQ)             │
│    PUB :5555  → video_rgb               │
│    PUB :5001  → JSON topics             │
│    SUB :5002  ← comandos Unity          │
│    PUB :5007  → paredes/puntos binarios │
└──────────────────────────────────────────┘
            │ WiFi
            ▼
┌──────────────────────────────────────────┐
│          Meta Quest 3 (Unity)            │
└──────────────────────────────────────────┘
```

## Responsabilidades

- Adquisición de sensores (RealSense D435i y RPLiDAR C1)
- Procesamiento selectivo según modo activo (visión YOLOv8, grid LiDAR, pipeline de paredes)
- Publicación de video, sensores y datos binarios vía ZeroMQ
- Recepción de comandos desde Unity (modos, drive, manipulador, gripper)
- Control de base móvil y manipulador vía serial → master bridge → I2C
- Control de gripper vía serial directo (COM5)

## Subsecciones

- [Middleware ZMQ]({{ "/docs/02-manual/04-servidor/middleware" | relative_url }}) — arquitectura completa de puertos, topics, comandos y protocolos seriales
- [Percepción]({{ "/docs/02-manual/04-servidor/percepcion" | relative_url }}) — pipeline RealSense, RPLiDAR, paredes y puntos
- [Pruebas]({{ "/docs/02-manual/04-servidor/pruebas" | relative_url }}) — validaciones de canales y comunicación

## Estado del subsistema

| Funcionalidad | Estado |
|---|---|
| Streaming ZMQ (video + lidar + estado) | ✅ Verificado |
| Control base móvil y manipulador | ✅ Implementado |
| Telemetría manipulador y gripper | ✅ Implementado |
| Modos inmersivos (paredes, puntos LiDAR) | ✅ Implementado |
| Watchdog ZMQ con paro seguro completo | ⏳ Parcial |
