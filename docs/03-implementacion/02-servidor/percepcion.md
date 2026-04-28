---
title: "Percepción"
nav_order: 3
parent: "Servidor"
---

# Percepción

El sistema de percepción combina dos sensores complementarios para cubrir las necesidades de navegación y teleoperación: el **RPLiDAR C1** para mapeo 2D y el **Intel RealSense D435i** para percepción 3D y streaming al operador XR.

## Sensores

| Sensor | Uso principal | Interfaz |
|---|---|---|
| RPLiDAR C1 | Navegación 2D, detección de obstáculos, grid de ocupación | USB → worker de LiDAR en NUC |
| Intel RealSense D435i | Percepción 3D y streaming RGB-D al XR | USB → worker de cámara en NUC |

## Pipeline de percepción

```
RPLiDAR C1             RealSense D435i
     │                       │
  LiDAR worker         Camera worker
     │                       │
     └──────────┬────────────┘
                │
           NUC Python
                │
        Publicación ZMQ
                │
              XR UI
```

## Navegación 2D basada en grid

El sistema de navegación actual utiliza el láser 2D para:

- Generar un grid de ocupación local del entorno
- Detectar obstáculos en tiempo real
- Proveer asistencia visual de contexto al operador XR

Actualmente el enfoque es teleoperación con percepción asistida. El mapeo global queda como expansión futura.

## Percepción 3D (RealSense D435i)

El Intel RealSense D435i provee:

- **Imagen RGB** — stream de video para el headset XR (vista del robot)
- **Imagen de profundidad** — distancias por pixel para apoyo en manipulación
- **Nube de puntos** — representación 3D del entorno cercano

En la interfaz XR, el stream de video del RealSense es la **vista principal del operador** (primera persona desde el robot).

## Estado actual

- [x] Sensores integrados al SBC a bordo (RPLiDAR C1 + RealSense D435i)
- [x] Canales ZMQ publicados y verificados individualmente
- [ ] Integración de mapeo global del entorno (fase futura)
- [ ] Transmisión de minimapa global al headset XR
- [ ] Stream RGB-D estable al Meta Quest
