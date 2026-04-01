---
title: "Software"
nav_order: 5
parent: "Robot AGV"
---

# Software del Robot AGV

El stack de software del robot se divide en dos capas: el **firmware embebido** en los módulos Puente H (ESP32-C3) y el **sistema de navegación y control** basado en ROS corriendo en la computadora de a bordo.

## Firmware ESP32-C3 (Módulos Puente H)

Cada módulo Puente H corre un firmware independiente que implementa:

- Máquina de estados (`DISARMED` → `ARMED` → ejecución)
- Lectura del DIP switch al arranque para selección de modo de comunicación
- Parser de comandos discretos (`F/B/L/R/S/T`) y numéricos (`[-255, 255]`)
- Generación de rampas de aceleración/frenado (ningún cambio es instantáneo)
- Control PWM sobre `GPIO6` (PWM_0) y `GPIO7` (PWM_1)
- Canal USB-C siempre activo como interfaz de debug prioritaria

## Stack ROS

{: .note }
La integración ROS está en progreso. La arquitectura de nodos está definida; los detalles de implementación se actualizarán conforme avance la integración.

### Nodos principales previstos

| Nodo | Función |
|---|---|
| `motor_driver_node` | Publica comandos al bus I²C hacia los módulos Puente H |
| `odometry_node` | Lee encoders y publica `/odom` |
| `cmd_vel_bridge` | Traduce `geometry_msgs/Twist` a comandos de velocidad por motor |
| `manipulator_node` | Controla los motores del manipulador |
| `lidar_node` | Driver del RPLiDAR C1 → `/scan` |
| `realsense_node` | Driver del Intel RealSense D435i → `/depth/image`, `/color/image` |

### Topología de comunicación

```
Operador (XR / PC)
       │
   [WiFi / ROS]
       │
 ┌─────┴──────┐
 │  SBC a bordo│  ← computadora de abordo
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
- [ ] Nodo ROS `motor_driver_node` — en desarrollo
- [ ] Integración de odometría con encoders
- [ ] Nodo del manipulador con cinemática
