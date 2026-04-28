---
title: "Software"
nav_order: 5
parent: "Robot AGV"
---

# Software del Robot AGV

El stack de software del robot se divide en dos capas: el **firmware embebido** en los módulos Puente H (ESP32-C3) y el **sistema de coordinación** corriendo en la NUC a bordo.

## Firmware ESP32-C3 (MicroPython)

Cada módulo Puente H corre firmware en **MicroPython** que implementa:

- Máquina de estados (`DISARMED` → `ARMED` → ejecución)
- Lectura del DIP switch al arranque para selección de modo de comunicación
- Parser de comandos discretos (`F/B/L/R/S/T`) y numéricos (`[-255, 255]`)
- Generación de rampas de aceleración/frenado (ningún cambio es instantáneo)
- Control PWM sobre `GPIO6` (PWM_0) y `GPIO7` (PWM_1)
- Canal USB-C siempre activo como interfaz de debug prioritaria

## Stack NUC (Python 3.12 + ZMQ)

{: .note }
La coordinación actual entre NUC, sensores, interfaz XR y control del robot se implementa con Python 3.12 y ZeroMQ.

### Componentes principales previstos

| Componente | Función |
|---|---|
| `command_listener` | Recibe comandos JSON desde Meta Quest vía ZMQ (port 5002) |
| `motor_bridge` | Traduce comandos de movimiento a instrucciones para ESP32-C3 |
| `manipulator_bridge` | Coordina comandos del manipulador 3DOF |
| `camera_worker` | Captura/transforma stream de cámara y lo publica por ZMQ |
| `lidar_worker` | Publica grid de ocupación y estado por ZMQ |
| `status_worker` | Publica heartbeat y estado general del sistema |

### Topología de comunicación

```
Operador (Meta Quest / PC)
       │
   [WiFi / ZMQ]
       │
 ┌─────┴──────┐
 │  NUC a bordo│  ← Python 3.12
 └─────┬──────┘
       ├── I²C → Puente H #1 (motor derecho)
       ├── I²C → Puente H #2 (motor izquierdo)
       ├── USB → RPLiDAR C1
       └── USB → Intel RealSense D435i
```

## Estado actual

- [x] Firmware ESP32-C3 funcional (todos los modos de comunicación)
- [x] Control de motores individual validado por USB-C
- [x] Control validado por WiFi y BLE
- [ ] Integración de control completo de base desde interfaz XR
- [ ] Integración de control completo de manipulador 3DOF
- [ ] Documentación de scripts finales de despliegue en NUC
