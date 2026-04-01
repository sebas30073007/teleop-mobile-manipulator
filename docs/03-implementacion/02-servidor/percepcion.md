---
title: "Percepción y SLAM"
nav_order: 3
parent: "Servidor"
---

# Percepción y SLAM

El sistema de percepción combina dos sensores complementarios para cubrir las necesidades de navegación y teleoperación: el **RPLiDAR C1** para mapeo 2D y el **Intel RealSense D435i** para percepción 3D y streaming al operador XR.

## Sensores

| Sensor | Uso principal | Interface |
|---|---|---|
| RPLiDAR C1 | Navegación 2D, SLAM, detección de obstáculos | USB → `/scan` |
| Intel RealSense D435i | Percepción 3D, visual odometry, streaming RGB-D al XR | USB → `/camera/*` |

## Pipeline de percepción

```
RPLiDAR C1             RealSense D435i
     │                       │
  /scan             /camera/depth/image
     │               /camera/color/image
     │                       │
     └──────────┬────────────┘
                │
         Servidor ROS
                │
    ┌───────────┼───────────┐
    │           │           │
  SLAM       Nube de     Streaming
  2D         puntos      RGB-D → XR
```

## SLAM 2D

El sistema de navegación autónoma utiliza el láser 2D para:

- Construir un mapa 2D del entorno de almacén mediante **SLAM** (paquete `slam_toolbox` o `gmapping`)
- Localizar el robot dentro del mapa construido
- Detectar obstáculos en tiempo real para evitarlos

El mapa generado se comparte al headset XR para visualizarlo como minimap en la interfaz de teleoperación.

## Percepción 3D (RealSense D435i)

El Intel RealSense D435i provee:

- **Imagen RGB** — stream de video para el headset XR (vista del robot)
- **Imagen de profundidad** — distancias por pixel para apoyo en manipulación
- **Nube de puntos** — representación 3D del entorno cercano

En la interfaz XR, el stream de video del RealSense es la **vista principal del operador** (primera persona desde el robot).

## Estado actual

- [x] Sensores integrados al SBC a bordo (RPLiDAR C1 + RealSense D435i)
- [x] Topics publicados y verificados individualmente
- [ ] Pipeline SLAM activo con mapa generado
- [ ] Transmisión de mapa al headset XR
- [ ] Stream RGB-D estable al Meta Quest
