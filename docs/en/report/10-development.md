---
title: "Development"
nav_order: 10
parent: "Report"
---

# Development

## Logistics task analysis

The starting point of the design was determining which tasks within an e-commerce warehouse are viable candidates for teleoperation with a mobile-manipulator robot. The analysis considered four representative tasks from the internal warehouse flow, evaluated according to three criteria: execution complexity (level of skill and decision-making required), operational risk (consequences of an error), and teleoperation potential (marginal benefit of operating the robot remotely versus on-site).

| Task | Description | Complexity | Risk | Teleop. potential |
|---|---|:---:|:---:|:---:|
| Internal transfer | Movement of units between warehouse zones | Medium | Medium | **High** |
| Assisted picking | Locating and retrieving items for an order | High | Medium | Medium |
| Station restocking | Replenishing materials in work zones | Medium | Low | **High** |
| Delivery to internal point | Transport to a consolidation or dispatch node | Low | Low | **High** |

![Task analysis table]({{ "/assets/img/full-tabla-tareas.png" | relative_url }})

The internal transfer and station restocking tasks were selected as the prototype's primary use cases, due to the combination of high teleoperation potential and a manageable risk level for a system in the experimental validation phase.

## System architecture

The system is organized into three functional layers designed to be independent at the development level but integrated in real time during operation. Communication flows bidirectionally between layers: operator commands flow down from XR to the robot, and telemetry and video flow up from the robot to the XR interface.

```
[ XR Interface — Meta Quest + Unity ]
           ↕  ZeroMQ (ZMQ)
[ Onboard NUC — Middleware + Perception ]
           ↕  WiFi / Serial
[ Robotic Platform — Mobile base + Arm ]
```

### Layer 1: Robotic platform

**Mobile base:** Differential drive with two NEMA23 stepper motors controlled by closed-loop CL57T drivers. The encoders integrated in the drivers enable precise position control without accumulated error from step loss. The control electronics are centralized in an ESP32-C3 microcontroller with MicroPython firmware, which receives velocity commands from the NUC and translates them into step and direction signals for the drivers.

**Manipulator arm:** Three degrees of freedom with shoulder and elbow joints, plus a gripper end effector for pick-and-place tasks. Motion control is coordinated from the NUC and executed through embedded ESP32-C3 controllers.

**Sensors:** RGB camera mounted at the end of the arm for visual feedback to the operator. The mounting position on the end effector allows the operator to see the target object from the robot's point of view during the grasping operation.

### Layer 2: Coordination server (Python + ZMQ middleware)

The server runs on the Intel NUC onboard the robot, with Python 3.12 and ZeroMQ. Its function is to act as a coordination hub between the robotic platform and the XR interface, managing all data flows in the system:

- **Command reception:** ZMQ listener that receives movement commands in JSON format from the XR interface.
- **Mobile base control:** Service that translates movement commands and transmits the corresponding signals to the ESP32-C3 via WiFi or serial.
- **Arm control:** Service that receives per-joint targets and coordinates the arm's sequential movement.
- **Video processing:** The robot's camera stream is received at the server, compressed, and retransmitted to the XR interface.
- **Telemetry:** System status (current speed, arm angles, gripper state, battery indicators) published to the XR interface for display on the operator's HUD.

### Layer 3: XR Interface (Unity + Meta Quest)

The XR interface is a Unity application deployed on Meta Quest in standalone mode. The operator sees the robot's environment in first person — the camera video projected on the stereoscopic display — and controls the system using the headset's controllers:

| Control | Action |
|---|---|
| Left joystick | Mobile base translation speed |
| Right joystick | Mobile base rotation speed |
| Right trigger | Gripper open / close |
| A / B buttons | Arm elevation (elbow up / down) |
| X / Y buttons | Shoulder rotation |

The interface includes an overlaid HUD with status indicators: battery level, network latency, server connection status, and system alerts. The HUD design follows the principle of minimal cognitive load: information visible only when relevant to the active task.

## Key design decisions

**Why Python + ZMQ?** The project uses a lightweight middleware with ZeroMQ to simplify local-network integration between the NUC and Unity (Meta Quest), using JSON messages and dedicated ports per data type. This architecture reduces deployment complexity for the prototype's current context.

**Why ESP32-C3?** It integrates WiFi and Bluetooth on a single chip, has sufficient compute capacity for real-time motor control, and its development ecosystem (Arduino/ESP-IDF) enables rapid prototyping. The low per-unit cost facilitates replacements during test phases without significant budget impact.

**Why Meta Quest?** It is the consumer headset with the best performance-to-price ratio currently available on the market, with an actively maintained SDK for Unity. Its standalone mode — without a PC connection — simplifies the XR layer architecture and eliminates an additional source of latency.

**Why closed-loop CL57T drivers for the stepper motors?** Open-loop steppers lose steps under variable load, generating accumulated position error that is not detectable by the controller. CL57T drivers add an encoder to the motor and correct the error in real time: the result is the predictability of a stepper with the reliability of a servomotor, at a substantially lower cost than an industrial servo solution.

---

*Next: [References →]({{ "/docs/en/report/11-references" | relative_url }})*
