---
title: "Percepción"
nav_order: 2
parent: "Servidor / NUC"
---

# Percepción

## Requisitos

El sistema de percepción debía cubrir dos necesidades complementarias:

- **Navegación 2D** — detección de obstáculos y asistencia visual al operador XR
- **Comprensión del entorno cercano** — imagen RGB en primera persona desde el robot para el headset

## Sensores seleccionados

| Sensor | Uso principal | Interfaz |
|---|---|---|
| RPLiDAR C1 | Navegación 2D, grid de ocupación local, detección de obstáculos | USB → worker de LiDAR en NUC |
| Intel RealSense D435i | Stream RGB al XR, profundidad, nube de puntos 3D | USB → worker de cámara en NUC |

## Implementación

### Pipeline de percepción

```
RPLiDAR C1             RealSense D435i
     │                       │
  LiDAR worker         Camera worker
     │                       │
     └──────────┬────────────┘
                │
           NUC Python 3.12
                │
        Publicación ZMQ
                │
    ┌───────────┴───────────┐
    │ :5555 video_rgb JPEG  │
    │ :5001 lidar_grid JSON │
    └───────────────────────┘
                │
              XR UI
```

### RPLiDAR C1 — Navegación 2D

- Genera un **grid de ocupación local** del entorno
- Detecta obstáculos en tiempo real
- Provee asistencia visual de contexto al operador XR
- Tres modos de resolución/alcance: `detail`, `medium`, `panorama`

El enfoque actual es **teleoperación con percepción asistida**. El mapeo global queda como expansión futura.

### Intel RealSense D435i — Percepción 3D

- **Imagen RGB** — stream de video para el headset XR (vista en primera persona desde el robot)
- **Imagen de profundidad** — apoyo en tareas de manipulación
- **Nube de puntos** — representación 3D del entorno cercano
- **Corrección de profundidad** — curva de calibración interpolada implementada en el worker

## Validación

| Función | Estado |
|---|---|
| RealSense D435i integrada y publicando video | ✅ Verificado |
| RPLiDAR C1 integrado y publicando grid | ✅ Verificado |
| Stream RGB recibido en Meta Quest | ✅ Verificado |
| Grid LiDAR recibido y renderizado en XR | ✅ Verificado |
| Mapeo global del entorno | ⏳ Fase futura |
| Transmisión minimapa global al headset | ⏳ Fase futura |
| Stream RGB-D completo al Meta Quest | ⏳ Pendiente |
