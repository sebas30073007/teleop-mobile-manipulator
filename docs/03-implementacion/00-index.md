---
title: "Implementación"
nav_order: 3
has_children: true
permalink: /implementacion/
---

# Implementación técnica

## Arquitectura del sistema

El sistema integra un robot móvil-manipulador, un servidor de coordinación y una interfaz XR para teleoperación. La arquitectura prioriza desacoplamiento por módulos y observabilidad de estado.

```
┌──────────────────┐      ┌─────────────────────┐      ┌───────────────────┐
│  Robot AGV       │◄────►│  Servidor / Mid.     │◄────►│  XR Meta Quest    │
│                  │      │                     │      │                   │
│ • Plataforma     │      │ • Middleware ZMQ    │      │ • Unity + OpenXR  │
│   diferencial    │      │ • SLAM 2D           │      │ • Gemelo digital  │
│ • Manipulador    │      │ • Percepción RGB-D  │      │ • Stream video    │
│   2-DOF          │      │ • Telemetría        │      │ • Controles XR    │
│ • PCB Puente H   │      │ • Seguridad básica  │      │ • UI accesible    │
└──────────────────┘      └─────────────────────┘      └───────────────────┘
```
