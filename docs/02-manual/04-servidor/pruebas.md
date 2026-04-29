---
title: "Pruebas Servidor"
nav_order: 3
parent: "Servidor / NUC"
---

# Pruebas del Servidor / Middleware

## Verificación de canales de datos

Validación de que los canales de la arquitectura publican datos a la frecuencia esperada.

| Canal | Frecuencia esperada | Estado |
|---|---|---|
| `lidar_grid` (RPLiDAR C1) | ~10-12 Hz | ✅ Verificado |
| `video_rgb` (RealSense) | ~30 fps | ✅ Verificado |
| `stat` | ~2 Hz | ✅ Verificado |
| `cmd` (5002) → motor | — | ✅ Verificado (parcial) |
| Telemetría de encoders | 10-20 Hz | ⏳ Pendiente integración |

## Comunicación WiFi robot ↔ NUC

- Estabilidad de conexión: sin desconexiones en prueba de 10 minutos

> **Pendiente:** Medir y documentar la latencia de red local y la latencia extremo a extremo (XR → robot → XR).

## Pendientes

| Prueba | Estado |
|---|---|
| SLAM: generación de mapa en pasillo estructurado | ⏳ Pendiente |
| Latencia extremo a extremo (XR → robot → XR) | ⏳ Pendiente |
| Watchdog: verificar que el robot se detiene al perder conexión | ⏳ Pendiente |
| Stream de video RGB-D completo al headset XR | ⏳ Pendiente |
