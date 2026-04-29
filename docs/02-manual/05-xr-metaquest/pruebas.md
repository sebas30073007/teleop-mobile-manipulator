---
title: "Pruebas XR"
nav_order: 3
parent: "XR Meta Quest"
---

# Pruebas XR Meta Quest

## Demo de la interfaz

{% include video_youtube.html id="G229ZIQ-Y1g" title="Pruebas UI con Meta Quest 3 — Proyecto Terminal 2026" %}

---

## Pruebas realizadas

### Setup y despliegue Unity

| Prueba | Resultado |
|---|---|
| Proyecto compilado y desplegado en Meta Quest 3 | ✅ Sin errores |
| SDK Meta XR inicializado correctamente | ✅ Verificado |
| Passthrough MR activo, canvas world-space visible | ✅ Verificado |
| Ray interaction con controladores en todos los controles UI | ✅ Funcional |

### Comunicación ZMQ

| Prueba | Resultado |
|---|---|
| Conexión ZMQ Meta Quest 3 ↔ NUC sobre WiFi local | ✅ Establecida |
| Topic `video_rgb` recibido en port 5555 | ✅ Verificado |
| Topics `stat` y `mode_ack` recibidos en port 5001 | ✅ Verificado |
| Topic `lidar_grid` recibido y renderizado en LidarPanel | ✅ Verificado |
| Comandos desde Unity confirmados por `mode_ack` en port 5002 | ✅ Verificado |

### Stream de video

| Prueba | Resultado |
|---|---|
| Stream RGB 640×480 @ ~30 fps estable (RealSense D435i) | ✅ Verificado |
| Modo Normal verificado | ✅ |
| Modo Pose (YOLOv8) verificado | ✅ |
| Modo Segment (YOLOv8) verificado | ✅ |
| Modo Off verificado | ✅ |

Nota: resoluciones mayores a 640×480 causaron inestabilidad (frame blanco, drop de FPS).

### Panel de LiDAR

| Prueba | Resultado |
|---|---|
| Grid renderizado en modo Detail (200×200) | ✅ Verificado |
| Grid renderizado en modo Medium (400×400) | ✅ Verificado |
| Grid renderizado en modo Panorama (600×600) | ✅ Verificado |
| Cambio dinámico de tamaño de textura al cambiar modo | ✅ Verificado |
| Representación visual correcta (colores de convención) | ✅ Verificado |

### Interfaz UI

| Prueba | Resultado |
|---|---|
| Dropdowns de cámara y lidar sincronizados con estado NUC | ✅ Verificado |
| StatusPanel actualizado a ~2 Hz | ✅ Verificado |
| Feedback háptico y sonoro (hover + click + vibración) | ✅ Funcional |

## Pendientes

| Prueba | Estado |
|---|---|
| Control de base móvil desde headset (joystick → ZMQ port 5002) | ⏳ Pendiente |
| Control de manipulador 3DOF desde headset | ⏳ Pendiente |
| Telemetría real del robot en StatusPanel (batería, pose, temperatura) | ⏳ Pendiente |
| Rendimiento con grids grandes (400×400, 600×600) bajo carga sostenida | ⏳ Pendiente |
| Pruebas de usabilidad formales con usuarios objetivo | ⏳ Pendiente |
| Gemelo digital con URDF y sincronización de pose | ⏳ Mediano plazo |
