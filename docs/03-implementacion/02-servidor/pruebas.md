---
title: "Pruebas"
nav_order: 4
parent: "Servidor"
---

# Pruebas del Servidor / Middleware

## Pruebas realizadas

### Verificación de topics ROS

Validación de que los topics definidos en la arquitectura publican datos correctamente a la frecuencia esperada.

| Topic | Frecuencia esperada | Estado |
|---|---|---|
| `/scan` (RPLiDAR) | ~10 Hz | ✅ Verificado |
| `/camera/color/image` | 30 fps | ✅ Verificado |
| `/camera/depth/image` | 30 fps | ✅ Verificado |
| `/odom` | 10-20 Hz | ⏳ Pendiente integración encoder |
| `/cmd_vel` → motor | — | ✅ Verificado (parcial) |

### Comunicación WiFi robot ↔ SBC

- Latencia de red local medida: pendiente de documentar
- Estabilidad de conexión: sin desconexiones en prueba de 10 minutos

## Pendientes

- [ ] Prueba de SLAM: generación de mapa en pasillo estructurado
- [ ] Prueba de latencia extremo a extremo (XR → robot → XR)
- [ ] Prueba de watchdog: verificar que el robot se detiene al perder conexión
- [ ] Prueba de stream de video al headset XR
