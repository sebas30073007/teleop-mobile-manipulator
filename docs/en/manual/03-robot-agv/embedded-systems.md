---
title: "Embedded Systems"
nav_order: 1
parent: "Robot AGV"
has_children: true
---

# Embedded Systems

The robot's three embedded controllers run **MicroPython** firmware on **ESP32-C3 SuperMini** modules. Each one is responsible for a specific actuation function and communicates with the NUC over I²C or USB-CDC.

| Controller | PCB | Communication with NUC | Main function |
|---|---|---|---|
| [H-Bridge]({{ "/docs/en/manual/03-robot-agv/h-bridge" | relative_url }}) | Custom design (KiCad) | USB-CDC COM4 (master) | Traction DC motors |
| [CL57T]({{ "/docs/en/manual/03-robot-agv/driver-controller-cl57t" | relative_url }}) | Custom design (KiCad) | I²C addr `0x0B` via master | 3 manipulator axes (PUL/DIR) |
| [Gripper]({{ "/docs/en/manual/03-robot-agv/gripper-controller" | relative_url }}) | Protoboard (no PCB) | USB-CDC COM5 | Gripper — position in mm |

{: .note }
**PCB manufacturing cost (JLCPCB, batch of 10 units per design):** $5.00 USD production · $17.50 USD shipping · $130 MXN import duties.

## I²C Architecture

The H-Bridge configured as master (`DIP = 100`) acts as the I²C bus hub. The NUC only needs one USB channel to control the 3 embedded motion nodes:

```
NUC
 └── COM4 (USB) ──► H-Bridge master
                        ├── I²C 0x08 ──► H-Bridge slave (base motor)
                        └── I²C 0x0B ──► CL57T controller (3 axes)
 └── COM5 (USB) ──► Gripper controller (direct, outside the I²C bus)
```

## Firmware status

| Firmware | Lines | Status |
|---|---|---|
| `main_movil_final.py` | 1,175 | ✅ Functional |
| `main_manipulador_final.py` | 933 | ✅ Functional |
| `main_gripper_final.py` | 703 | ✅ Functional |
