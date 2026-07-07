---
title: "Embedded Software"
nav_order: 4
parent: "Robot AGV"
---

# Embedded Software

The robot's software stack is split into two layers: the **embedded firmware** on the three ESP32-C3 controllers and the **coordination system** running on the onboard NUC.

## Requirements

- Lightweight, stable firmware for real-time motor control
- A coordination system that integrates perception, ZMQ communication, and actuator control
- No ROS dependency (design decision: simplicity and portability)
- Debug interface always available (USB-C)

## ESP32-C3 Firmware (MicroPython)

The robot's three controllers run **MicroPython** firmware. Each has a distinct responsibility and a different communication interface:

| Controller | Firmware | Communication with NUC | Protocol |
|---|---|---|---|
| [H-Bridge master]({{ "/docs/en/manual/03-robot-agv/h-bridge" | relative_url }}) | `main_movil_final.py` | USB-CDC COM4 | ASCII + forwards binary I²C |
| [CL57T (manipulator)]({{ "/docs/en/manual/03-robot-agv/driver-controller-cl57t" | relative_url }}) | `main_manipulador_final.py` | I²C addr `0x0B` via master | ASCII text |
| [Gripper]({{ "/docs/en/manual/03-robot-agv/gripper-controller" | relative_url }}) | `main_gripper_final.py` | USB-CDC COM5 | ASCII text |

[⬇ main_movil_final.py]({{ "/assets/downloads/main_movil_final.py" | relative_url }}){: .btn .btn-outline }
[⬇ main_manipulador_final.py]({{ "/assets/downloads/main_manipulador_final.py" | relative_url }}){: .btn .btn-outline }
[⬇ main_gripper_final.py]({{ "/assets/downloads/main_gripper_final.py" | relative_url }}){: .btn .btn-outline }

## NUC Stack (Python 3.12 + ZMQ)

{: .note }
The project does not use ROS. Coordination between the NUC, sensors, XR interface, and robot control is implemented with Python 3.12 and ZeroMQ.

### Main components

| Component | Function |
|---|---|
| `command_listener` | Receives JSON commands from Meta Quest via ZMQ (port 5002) |
| `motor_bridge` | Translates motion commands into I²C frames for the H-Bridge master (COM4) |
| `manipulator_bridge` | Sends ASCII commands to the CL57T through the H-Bridge master |
| `gripper_bridge` | Sends ASCII commands directly to the gripper (COM5) |
| `camera_worker` | Captures the RealSense D435i stream and publishes it via ZMQ (port 5555) |
| `lidar_worker` | Generates an RPLiDAR occupancy grid and publishes via ZMQ (port 5001 / 5007) |
| `status_worker` | Publishes heartbeat and overall system status |

### Communication topology

```
Operator (Meta Quest)
       │
  [WiFi / ZMQ]
       │
 ┌─────┴──────┐
 │  Onboard NUC│  ← Python 3.12
 └─────┬──────┘
       │
       ├── COM4 (USB-CDC) ──► H-Bridge master (ESP32-C3)
       │                           ├── I²C 0x08 ──► H-Bridge slave (base motor)
       │                           └── I²C 0x0B ──► CL57T Controller
       │                                                └── PUL/DIR ×3 ──► NEMA17 ×3
       │
       ├── COM5 (USB-CDC) ──► Gripper controller (ESP32-C3)
       │                           └── TB6612FNG ──► Gripper motor + encoder
       │
       ├── COM3 (USB)     ──► RPLiDAR C1 (460,800 baud)
       └── USB3           ──► Intel RealSense D435i
```

The NUC's main code is available in the repository:

[⬇ NUC_master_code.py]({{ "/assets/downloads/NUC_master_code.py" | relative_url }}){: .btn .btn-outline }
[View on GitHub](https://github.com/sebas30073007/teleop-mobile-manipulator/blob/main/assets/downloads/NUC_master_code.py){: .btn .btn-outline }

## Current status

| Functionality | Status |
|---|---|
| H-Bridge firmware (all communication modes) | ✅ Functional |
| CL57T firmware — homing, movement, wrist compensation | ✅ Functional |
| Gripper firmware — mm position, stall, JSON calibration | ✅ Functional |
| Individual motor control validated over USB-C | ✅ Verified |
| Control validated over WiFi and BLE | ✅ Verified |
| Base control integration from XR interface | ✅ Functional |
| Full 3DOF manipulator control | ✅ Functional |
| Gripper control from XR interface | ✅ Functional |
