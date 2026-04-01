---
title: "Pruebas"
nav_order: 4
parent: "XR Meta Quest"
---

# Pruebas XR Meta Quest

## Demo de la interfaz

{% include video_youtube.html id="G229ZIQ-Y1g" title="Pruebas UI con Meta Quest 3 — Proyecto Terminal 2026" %}

---

## Pruebas realizadas

### Setup y despliegue Unity

- Proyecto compilado y desplegado en Meta Quest 3 sin errores
- SDK Meta XR inicializado correctamente
- Passthrough MR activo, canvas world-space visible sobre el entorno real
- Ray interaction con controladores funcional en todos los controles UI

### Comunicación ZMQ

- Conexión ZMQ establecida entre Meta Quest 3 y NUC sobre red WiFi local
- Topic `video_rgb` recibido en port 5555 correctamente
- Topics `stat` y `mode_ack` recibidos en port 5001
- Topic `lidar_grid` recibido y renderizado en LidarPanel
- Comandos enviados desde Unity a NUC via port 5002 confirmados por `mode_ack`

### Stream de video

- Stream RGB 640×480 @ ~30 fps estable desde RealSense D435i
- Resoluciones mayores causaron inestabilidad (frame blanco, drop de FPS); se fijó en 640×480
- Todos los modos de cámara verificados: Normal, Pose (YOLOv8), Segment (YOLOv8), Off

### Panel de LiDAR

- Grid de ocupación recibido y renderizado para los tres modos: Detail, Medium, Panorama
- Cambio dinámico de tamaño de textura al cambiar modo verificado
- Representación visual correcta: blanco=libre, negro=obstáculo, verde=robot, azul=frente
- Corrección de centrado en grids de tamaño par verificada

### Interfaz UI

- Dropdowns de cámara y lidar sincronizados con estado de la NUC
- StatusPanel actualizado a ~2 Hz (Camera OK, Lidar OK, FPS, modos activos)
- Feedback háptico y sonoro funcional (hover click y micro vibración)

## Pendientes

- [ ] Control de base móvil desde headset (joystick → cmd via ZMQ port 5002)
- [ ] Control de manipulador 3DOF desde headset
- [ ] Integración de telemetría real del robot en StatusPanel (batería, pose, temperatura)
- [ ] Prueba de rendimiento con grids grandes (400×400, 600×600) en Quest bajo carga
- [ ] Pruebas de usabilidad formales con usuarios objetivo (diseño inclusivo)
- [ ] Gemelo digital con URDF y sincronización de pose
