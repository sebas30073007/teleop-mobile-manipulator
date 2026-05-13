---
title: "Software embebido"
nav_order: 4
parent: "Robot AGV"
---

# Software embebido

El stack de software del robot se divide en dos capas: el **firmware embebido** en los tres controladores ESP32-C3 y el **sistema de coordinación** corriendo en la NUC a bordo.

## Requisitos

- Firmware ligero y estable para control de motores en tiempo real
- Sistema de coordinación que integre percepción, comunicación ZMQ y control de actuadores
- Sin dependencia de ROS (decisión de diseño: simplicidad y portabilidad)
- Interfaz de debug siempre disponible (USB-C)

## Firmwares ESP32-C3 (MicroPython)

Los tres controladores del robot corren firmware **MicroPython**. Cada uno tiene una responsabilidad distinta y una interfaz de comunicación diferente:

| Controlador | Firmware | Comunicación con NUC | Protocolo |
|---|---|---|---|
| [Puente H maestro]({{ "/docs/02-manual/03-robot-agv/electronica" | relative_url }}) | `main_movil_final.py` | USB-CDC COM4 | ASCII + reenvía binario I²C |
| [CL57T (manipulador)]({{ "/docs/02-manual/03-robot-agv/controlador-cl57t" | relative_url }}) | `main_manipulador_final.py` | I²C addr `0x0B` vía maestro | ASCII texto |
| [Gripper]({{ "/docs/02-manual/03-robot-agv/controlador-gripper" | relative_url }}) | `main_gripper_final.py` | USB-CDC COM5 | ASCII texto |

[⬇ main_movil_final.py]({{ "/assets/downloads/main_movil_final.py" | relative_url }}){: .btn .btn-outline }
[⬇ main_manipulador_final.py]({{ "/assets/downloads/main_manipulador_final.py" | relative_url }}){: .btn .btn-outline }
[⬇ main_gripper_final.py]({{ "/assets/downloads/main_gripper_final.py" | relative_url }}){: .btn .btn-outline }

## Stack NUC (Python 3.12 + ZMQ)

{: .note }
El proyecto no usa ROS. La coordinación entre NUC, sensores, interfaz XR y control del robot se implementa con Python 3.12 y ZeroMQ.

### Componentes principales

| Componente | Función |
|---|---|
| `command_listener` | Recibe comandos JSON desde Meta Quest vía ZMQ (port 5002) |
| `motor_bridge` | Traduce comandos de movimiento a tramas I²C para el Puente H maestro (COM4) |
| `manipulator_bridge` | Envía comandos ASCII al CL57T a través del Puente H maestro |
| `gripper_bridge` | Envía comandos ASCII al gripper directamente (COM5) |
| `camera_worker` | Captura stream RealSense D435i y lo publica por ZMQ (port 5555) |
| `lidar_worker` | Genera grid de ocupación RPLiDAR y publica por ZMQ (port 5001 / 5007) |
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
       │
       ├── COM4 (USB-CDC) ──► Puente H maestro (ESP32-C3)
       │                           ├── I²C 0x08 ──► Puente H esclavo (motor base)
       │                           └── I²C 0x0B ──► Controlador CL57T
       │                                                └── PUL/DIR ×3 ──► NEMA17 ×3
       │
       ├── COM5 (USB-CDC) ──► Controlador gripper (ESP32-C3)
       │                           └── TB6612FNG ──► Motor gripper + encoder
       │
       ├── COM3 (USB)     ──► RPLiDAR C1 (460 800 baud)
       └── USB3           ──► Intel RealSense D435i
```

El código principal de la NUC está disponible en el repositorio:

[⬇ NUC_master_code.py]({{ "/assets/downloads/NUC_master_code.py" | relative_url }}){: .btn .btn-outline }
[Ver en GitHub](https://github.com/sebas30073007/teleop-mobile-manipulator/blob/main/assets/downloads/NUC_master_code.py){: .btn .btn-outline }

## Estado actual

| Funcionalidad | Estado |
|---|---|
| Firmware Puente H (todos los modos de comunicación) | ✅ Funcional |
| Firmware CL57T — homing, movimiento, compensación muñeca | ✅ Funcional |
| Firmware gripper — posición mm, stall, calibración JSON | ✅ Funcional |
| Control de motores individual validado por USB-C | ✅ Verificado |
| Control validado por WiFi y BLE | ✅ Verificado |
| Integración control base desde interfaz XR | ✅ Funcional |
| Control completo manipulador 3DOF | ✅ Funcional |
| Control gripper desde interfaz XR | ✅ Funcional |
