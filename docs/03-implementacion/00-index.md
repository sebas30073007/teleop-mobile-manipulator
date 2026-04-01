---
title: "Implementación"
nav_order: 3
has_children: true
permalink: /implementacion/
---

# Implementación técnica

## Arquitectura del sistema

### Visión general
El sistema integra un robot móvil-manipulador, un servidor de coordinación y una interfaz XR para teleoperación. La arquitectura prioriza desacoplamiento por módulos y observabilidad de estado.

```
┌──────────────────┐      ┌─────────────────────┐      ┌───────────────────┐
│  Robot AGV       │◄────►│  Servidor / Mid.     │◄────►│  XR Meta Quest    │
│                  │      │                     │      │                   │
│ • Plataforma     │      │ • ROS bus de mens.  │      │ • Unity + OpenXR  │
│   diferencial    │      │ • SLAM 2D           │      │ • Gemelo digital  │
│ • Manipulador    │      │ • Percepción RGB-D  │      │ • Stream video    │
│   2-DOF          │      │ • Telemetría        │      │ • Controles XR    │
│ • PCB Puente H   │      │ • Seguridad básica  │      │ • UI accesible    │
└──────────────────┘      └─────────────────────┘      └───────────────────┘
```

### Flujos de datos

| Canal | Origen → Destino | Contenido |
|---|---|---|
| Telemetría | Robot → Servidor → XR | Pose, velocidad, estado, alertas |
| Comandos | XR → Servidor → Robot | `cmd_vel`, comandos manipulador |
| Percepción | Robot → Servidor → XR | Scan LiDAR, imagen RGB-D, mapa |
| Sincronización | Bidireccional | Estado del sistema, modo activo |

### Estado de integración

| Módulo | Estado |
|---|---|
| Robot AGV — hardware | ✅ Construido y validado |
| Robot AGV — software (ROS) | 🔄 En integración |
| Servidor middleware | 🔄 En integración |
| XR Meta Quest | 🔄 En integración |
| Sistema completo end-to-end | ⏳ Pendiente |

## Módulos
- [Robot AGV + manipulador]({{ "/docs/03-implementacion/01-robot-agv/" | relative_url }})
- [Servidor]({{ "/docs/03-implementacion/02-servidor/" | relative_url }})
- [XR Meta Quest]({{ "/docs/03-implementacion/03-xr-metaquest/" | relative_url }})
