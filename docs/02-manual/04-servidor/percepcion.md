---
title: "Percepción"
nav_order: 2
parent: "Servidor / NUC"
---

# Percepción

## Sensores

| Sensor | Puerto | Uso principal |
|---|---|---|
| RPLiDAR C1 | COM3 (460800 baud) | Grid de ocupación 2D, pipeline de paredes inmersivo, puntos en frame local |
| Intel RealSense D435i | USB | Stream RGB al XR, profundidad con calibración, nube de puntos |

## Pipeline de percepción

```
RPLiDAR C1 (COM3)          RealSense D435i (USB)
      │                           │
  lidar_async_worker          camera_thread
      │                           │
  ┌───┴────────────┐    ┌─────────┴────────────┐
  │ lidar_grid     │    │ video (JPEG)          │
  │ walls_snapshot │    │ cam_info              │
  │ walls_delta    │    │ depth (calibrado)     │
  │ lidar_points   │    │ visión YOLOv8         │
  └───┬────────────┘    └─────────┬────────────┘
      │                           │
      └──────────┬────────────────┘
                 │
          NUC Python 3.12
                 │
    ┌────────────┼────────────────┐
    │ :5555 video_rgb             │
    │ :5001 JSON topics           │
    │ :5007 binario (walls/pts)   │
    └─────────────────────────────┘
```

## RPLiDAR C1 — Grid de ocupación

- Genera grid de ocupación local en 3 modos: `detail` (1 m), `medium` (2 m), `panorama` (3 m)
- Celda de 1 cm fijo en todos los modos
- Publicado como JSON en topic `lidar_grid` a ~12 Hz
- Puntos con antigüedad > 0.35 s se descartan (`LIDAR_STALE_S`)

## RPLiDAR C1 — Pipeline de paredes inmersivo

Cuando `walls_enabled = true`, el sistema acumula hasta 150 000 puntos en una ventana de 4 segundos y procesa a ~1 Hz:

1. Proyección a grid 2D (resolución 10 cm)
2. Operaciones morfológicas: dilate → close → open
3. Extracción de componentes conectados (mín. 80 px)
4. Simplificación de polilíneas (tolerancia 4 px)
5. Detección y fusión de segmentos ortogonales (tolerancia 15°)

Resultado: segmentos de pared compactos para representación en escena XR inmersiva. Publicado en binario (`WSNP`/`WDEL`) en :5007.

## RPLiDAR C1 — Puntos en frame local

Cuando `points_enabled = true`, publica nube de puntos crudos en frame local del LiDAR a ~8 Hz. Hasta 12 000 puntos por paquete, ventana de 0.35 s. Publicado en binario (`LPSN`/`LPFR`) en :5007.

![RealSense montada — posición frontal sobre base del manipulador]({{ "/assets/raw_assets/20260428_160728.jpg" | relative_url }})

## Intel RealSense D435i — Stream RGB

- Stream de video para el headset XR (vista en primera persona desde el robot)
- Resolución: 640×480 px, hasta 30 fps, compresión JPEG calidad 85
- Publicado en topic `video_rgb` en :5555

## Intel RealSense D435i — Calibración de profundidad

El master aplica una curva de calibración interpolada a las medidas de profundidad antes de publicarlas. La curva corrige la desviación sistemática del sensor entre 160 mm y 1000 mm.

## Intel RealSense D435i — Visión por computadora

Procesado en la NUC (CPU) con YOLOv8 nano:

| Modo | Modelo | Output |
|---|---|---|
| `pose` | `yolov8n-pose.pt` | Keypoints de pose corporal |
| `segment` | `yolov8n-seg.pt` | Máscaras de segmentación semántica |

Resultados publicados en topic `vision` a ~10 Hz.

## Estado actual

| Función | Estado |
|---|---|
| Grid LiDAR (3 modos) | ✅ Verificado |
| Stream RGB 640×480 @ ~30 fps | ✅ Verificado |
| Calibración de profundidad | ✅ Implementada |
| Pipeline de paredes inmersivo | ✅ Implementado |
| Pipeline de puntos LiDAR | ✅ Implementado |
| Transmisión RGB-D completa al Meta Quest | ⏳ Pendiente |
| Mapeo global del entorno (SLAM) | ⏳ Fase futura |
