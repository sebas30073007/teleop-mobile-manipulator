---
title: "Pruebas"
nav_order: 4
parent: "Servidor"
---

# Pruebas del Servidor / Middleware

## Pruebas realizadas

### Verificación de canales de datos

Validación de que los canales definidos en la arquitectura publican datos correctamente a la frecuencia esperada.

| Canal | Frecuencia esperada | Estado |
|---|---|---|
| `lidar_grid` (RPLiDAR C1) | ~10-12 Hz | ✅ Verificado |
| `video_rgb` (RealSense) | ~30 fps | ✅ Verificado |
| `stat` | ~2 Hz | ✅ Verificado |
| Telemetría de encoders | 10-20 Hz | ⏳ Pendiente integración |
| `cmd` (5002) → motor | — | ✅ Verificado (parcial) |

### Comunicación WiFi robot ↔ SBC

- Latencia de red local medida: pendiente de documentar
- Estabilidad de conexión: sin desconexiones en prueba de 10 minutos

## Pendientes

- [ ] Prueba de SLAM: generación de mapa en pasillo estructurado
- [ ] Prueba de latencia extremo a extremo (XR → robot → XR)
- [ ] Prueba de watchdog: verificar que el robot se detiene al perder conexión
- [ ] Prueba de stream de video al headset XR
