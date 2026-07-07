---
title: "Robot AGV"
nav_order: 3
parent: "Documentation"
has_children: true
---

# Robot AGV

The robotic subsystem integrates a **rehabilitated differential-drive mobile platform** with a **3-degree-of-freedom manipulator built from scratch**. Both structures use embedded modules to perform the low-level operation of the mobile base and of the manipulator.

![Full robot with manipulator mounted]({{ "/assets/img/AGV.png" | relative_url }})

## Subsections

**Electronics**
- [Embedded systems]({{ "/docs/en/manual/03-robot-agv/embedded-systems" | relative_url }}) — H-Bridge, CL57T and gripper: MicroPython ESP32-C3, firmware, I²C and USB protocols

**Mechanics**
- [Mobile platform]({{ "/docs/en/manual/03-robot-agv/mobile-platform" | relative_url }}) — rehabilitated differential base
- [3DOF Manipulator]({{ "/docs/en/manual/03-robot-agv/manipulator" | relative_url }}) — design, laser manufacturing, CAD, assembly

**Software and validation**
- [Embedded software]({{ "/docs/en/manual/03-robot-agv/embedded-software" | relative_url }}) — MicroPython ESP32-C3, NUC Python 3.12 stack
- [Testing and calibration]({{ "/docs/en/manual/03-robot-agv/testing-calibration" | relative_url }}) — validations performed, results

## Subsystem status

| Component | Status |
|---|---|
| Differential mobile platform | ✅ Built and tested |
| 3DOF manipulator | ✅ Built and tested |
| H-Bridge PCB modules (×2) | ✅ Designed, assembled, and tested |
| H-Bridge firmware (ESP32-C3) | ✅ Functional in all modes |
| CL57T firmware (ESP32-C3) | ✅ Functional — homing, wrist compensation |
| Gripper firmware (ESP32-C3) | ✅ Functional — mm control, stall detect |
| NUC ↔ ESP32-C3 ↔ XR control | ⏳ Integration in progress |
