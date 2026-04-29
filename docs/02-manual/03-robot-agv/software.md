---
title: "Software embebido"
nav_order: 5
parent: "Robot AGV"
---

# Software embebido

El stack de software del robot se divide en dos capas: el **firmware embebido** en los módulos Puente H (ESP32-C3) y el **sistema de coordinación** corriendo en la NUC a bordo.

## Requisitos

- Firmware ligero y estable para control de motores en tiempo real
- Sistema de coordinación que integre percepción, comunicación ZMQ y control de actuadores
- Sin dependencia de ROS (decisión de diseño: simplicidad y portabilidad)
- Interfaz de debug siempre disponible (USB-C)

## Firmware ESP32-C3 (MicroPython)

Cada módulo Puente H corre firmware en **MicroPython** que implementa:

- Máquina de estados (`DISARMED` → `ARMED` → ejecución)
- Lectura del DIP switch al arranque para selección de modo de comunicación
- Parser de comandos discretos (`F/B/L/R/S/T`) y numéricos (`[-255, 255]`)
- Generación de rampas de aceleración/frenado
- Control PWM sobre `GPIO6` (PWM_0) y `GPIO7` (PWM_1)
- Canal USB-C siempre activo como interfaz de debug prioritaria

Ver la descripción completa del hardware en [Puente H]({{ "/docs/02-manual/03-robot-agv/electronica" | relative_url }}).

> **Pendiente:** Publicar el código fuente MicroPython y el procedimiento de flasheo.

## Stack NUC (Python 3.12 + ZMQ)

{: .note }
El proyecto no usa ROS. La coordinación entre NUC, sensores, interfaz XR y control del robot se implementa con Python 3.12 y ZeroMQ.

### Componentes principales

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
Operador (Meta Quest)
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

El código principal de la NUC está disponible en el repositorio:

[⬇ NUC_master_code.py]({{ "/assets/downloads/NUC_master_code.py" | relative_url }}){: .btn .btn-outline }
[Ver en GitHub](https://github.com/sebas30073007/teleop-mobile-manipulator/blob/main/assets/downloads/NUC_master_code.py){: .btn .btn-outline }

> **Pendiente:** Publicar el archivo de dependencias (`requirements.txt`) y los scripts de arranque del sistema completo.

## Estado actual

| Funcionalidad | Estado |
|---|---|
| Firmware ESP32-C3 (todos los modos de comunicación) | ✅ Funcional |
| Control de motores individual validado por USB-C | ✅ Verificado |
| Control validado por WiFi y BLE | ✅ Verificado |
| Integración control base desde interfaz XR | ✅ Funcional |
| Control completo manipulador 3DOF | ✅ Funcional |
| Scripts finales de despliegue NUC documentados | ⏳ Pendiente |
