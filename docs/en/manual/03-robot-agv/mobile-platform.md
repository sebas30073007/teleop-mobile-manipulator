---
title: "Mobile Platform"
nav_order: 2
parent: "Robot AGV"
---

# Mobile Platform

## Requirements

The platform had to support the weight of the manipulator and the electronics, move on flat warehouse surfaces, and be compatible with the embedded control modules developed for the project.

## Design

The adopted solution is a **rehabilitated unicycle-type differential platform**. The original mechanical structure was kept, and the motor drivers, wiring, and control electronics were replaced to integrate them with the teleoperation system.

![Base mobile platform]({{ "/assets/img/Hardware base.png" | relative_url }})

Design features:

- **2 DC motors** with encoders for odometry
- **4 caster wheels** (one at each end) for support and stability
- **18-gauge (1.2 mm) steel structure** supporting the manipulator and electronics

## Implementation



### Drivers and I²C configuration

The motors are controlled by the **ESP32-C3 H-Bridge modules** designed for this project (see [Electronics — H-Bridge]({{ "/docs/en/manual/03-robot-agv/h-bridge" | relative_url }})).

Two modules are used in a master–slave architecture over the I²C bus:

| Motor | Module | DIP switch mode |
|---|---|---|
| Right motor | H-Bridge #1 — Master | I²C Master (`SW: 100`) |
| Left motor | H-Bridge #2 — Slave | I²C Slave 1 (`SW: 101`) |

The **master module** receives commands from the NUC and controls the **slave module** in a chain (daisy-chain I²C).

![Driver connections]({{ "/assets/img/PuenteH.png" | relative_url }})

### Rehabilitation

The wiring was replaced and the custom PCB modules were mounted on the existing structure.

![Floor test]({{ "/assets/img/Primer prueba de movilidad.png" | relative_url }})

### Structural integration with the manipulator

The manipulator is mounted on a **metal lift box** that is fixed to the platform using the chassis's existing structural points, including areas near the caster wheel bolts.

![Junction between mobile platform and lift box]({{ "/assets/img/Integración estructural.png" | relative_url }})

## Validation

Platform test results:

| Test | Result |
|---|---|
| Differential motion on flat surface | ✅ Stable |
| Response to direction commands (F/B/L/R) | ✅ Correct |
| MOSFET temperature under 60-minute continuous load | ✅ Within range (effective heatsinks) |
| End-to-end remote control from XR | ✅ Complete |

See full evidence in [Testing and Calibration]({{ "/docs/en/manual/03-robot-agv/testing-calibration" | relative_url }}).
