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
| Topics `manip_state` y `gripper_state` en port 5001 | ✅ Verificado |
| Topic `lidar_grid` recibido y renderizado en LidarPanel | ✅ Verificado |
| Topics `walls_snapshot` y `lidar_points_*` en port 5007 | ✅ Verificado |
| Comandos desde Unity confirmados por `mode_ack` en port 5002 | ✅ Verificado |

### Stream de video

| Prueba | Resultado |
|---|---|
| Stream RGB 640×480 @ ~30 fps estable (RealSense D435i) | ✅ Verificado |
| Modo Normal | ✅ |
| Modo Pose (YOLOv8) | ✅ |
| Modo Segment (YOLOv8) | ✅ |
| Modo Off | ✅ |

Nota: resoluciones mayores a 640×480 causaron inestabilidad (frame blanco, drop de FPS).

### Panel LiDAR 2D

| Prueba | Resultado |
|---|---|
| Grid renderizado en modo Detail (200×200) | ✅ Verificado |
| Grid renderizado en modo Medium (400×400) | ✅ Verificado |
| Grid renderizado en modo Panorama (600×600) | ✅ Verificado |
| Cambio dinámico de tamaño de textura al cambiar modo | ✅ Verificado |
| Representación visual correcta (colores de convención) | ✅ Verificado |

### LiDAR 3D inmersivo

| Prueba | Resultado |
|---|---|
| Recepción de walls_snapshot por port 5007 | ✅ Verificado |
| Paredes reconstruidas como cubos 3D en Unity | ✅ Verificado |
| Nube de puntos renderizada con ParticleSystem | ✅ Verificado |
| Modo walls, points y both | ✅ Funcional |

### Drive teleop

| Prueba | Resultado |
|---|---|
| Joystick derecho leído por `QuestMobileDriveTeleop` | ✅ Funcional |
| Comandos `drive_direct` enviados a 15 Hz por ZMQ | ✅ Verificado |
| Deadzone 18 % aplicado correctamente | ✅ Verificado |
| Watchdog NUC (stop en 350 ms sin comando) | ✅ Verificado |
| Modos exclusivos: solo mobile activo al mismo tiempo | ✅ Funcional |

### Control de manipulador y gripper

| Prueba | Resultado |
|---|---|
| Sliders de codo, muñeca y gripper en panel derecho | ✅ Funcional |
| Ghost robot actualiza visualmente antes de enviar | ✅ Funcional |
| Botón Implement envía `POSE base codo muneca` | ✅ Verificado |
| Botón Home ejecuta `HOME_ALL` en CL57T | ✅ Verificado |
| Gripper slider envía `gripper_cmd mm` (0–80 mm) | ✅ Verificado |
| Feedback de posición real (manip_state → slider actualiza) | ✅ Verificado |
| Control de base con `BaseCameraDirectControl` | ✅ Funcional |

### Interfaz UI general

| Prueba | Resultado |
|---|---|
| Dropdowns de cámara y lidar sincronizados con estado NUC | ✅ Verificado |
| StatusPanel actualizado a ~5 Hz | ✅ Verificado |
| Feedback háptico y sonoro (hover + click + vibración) | ✅ Funcional |
| Teclado virtual para cambio de IP | ✅ Funcional |
| Emergency Stop — stop_all + master_disarm | ✅ Verificado |
| IP persistida entre sesiones (PlayerPrefs) | ✅ Verificado |

## Pendientes

| Prueba | Estado |
|---|---|
| Telemetría real del robot en StatusPanel (batería, temperatura) | ⏳ Pendiente |
| Rendimiento con grids grandes bajo carga sostenida prolongada | ⏳ Pendiente |
| Pruebas de usabilidad formales con usuarios objetivo | ⏳ Pendiente |
| Gemelo digital con URDF y sincronización de pose | ⏳ Mediano plazo |
