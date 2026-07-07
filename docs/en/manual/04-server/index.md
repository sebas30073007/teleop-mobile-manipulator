---
title: "Server / NUC"
nav_order: 4
parent: "Documentation"
has_children: true
---

# NUC — Perception Master Node

The **NUC (Intel NUC i7)** is the robot's onboard computer. There is no separate external server: the NUC travels onboard and acts as the central node for perception, processing, and coordination, running a **Python 3.12** backend.

[View NUC source code](https://github.com/sebas30073007/teleop-mobile-manipulator/blob/main/assets/downloads/NUC_master_code.py){: .btn .btn-outline }

## Physical connections

```
┌──────────────────────────────────────────┐
│             NUC (onboard)                │
│                                          │
│  COM3 — RPLiDAR C1         (USB)         │
│  COM4 — Master H-bridge    (USB)         │
│           └─ I2C → Slave H-bridge        │
│           └─ I2C → CL57T controller      │
│  COM5 — Gripper ESP32-C3   (USB)         │
│  USB  — Intel RealSense D435i            │
│                                          │
│  Python master server (ZMQ)             │
│    PUB :5555  → video_rgb               │
│    PUB :5001  → JSON topics             │
│    SUB :5002  ← Unity commands          │
│    PUB :5007  → walls/binary points     │
└──────────────────────────────────────────┘
            │ WiFi
            ▼
┌──────────────────────────────────────────┐
│          Meta Quest 3 (Unity)            │
└──────────────────────────────────────────┘
```

## Responsibilities

- Sensor acquisition (RealSense D435i and RPLiDAR C1)
- Selective processing depending on the active mode (YOLOv8 vision, LiDAR grid, walls pipeline)
- Publishing video, sensor, and binary data via ZeroMQ
- Receiving commands from Unity (modes, drive, manipulator, gripper)
- Mobile base and manipulator control via serial → master bridge → I2C
- Gripper control via direct serial (COM5)

## Subsections

- [ZMQ Middleware]({{ "/docs/en/manual/04-server/middleware" | relative_url }}) — full architecture of ports, topics, commands, and serial protocols
- [Perception]({{ "/docs/en/manual/04-server/perception" | relative_url }}) — RealSense, RPLiDAR, walls, and points pipeline
- [Testing]({{ "/docs/en/manual/04-server/testing" | relative_url }}) — channel and communication validations

## Subsystem status

| Feature | Status |
|---|---|
| ZMQ streaming (video + lidar + state) | ✅ Verified |
| Mobile base and manipulator control | ✅ Implemented |
| Manipulator and gripper telemetry | ✅ Implemented |
| Immersive modes (walls, LiDAR points) | ✅ Implemented |
| ZMQ watchdog with full safe stop | ⏳ Partial |
