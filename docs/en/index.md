---
title: "English"
nav_order: 20
has_children: true
permalink: /en/
---

# Development of a remote-operation robotic system for logistics tasks, enabling telework for people with motor disabilities

Welcome to the English section of the documentation site for the terminal project of:

**Sebastián Méndez Villegas** — Mechatronics and Cyber-Physical Systems Engineering

This terminal project was carried out with the support of Santiago Cuesta Machuca (Mechatronics and Production Engineering), the technical guidance of Prof. Joel Arango, a specialist in Mixed, Extended, and Virtual Reality (MR/XR/VR) technologies, and the primary academic advisory of Dr. Huber Girón, project director.

![Full robot with manipulator mounted]({{ "/assets/img/PROYECTO.png" | relative_url }})

## What is this project?

It is a teleoperation platform for a mobile robot with a manipulator, operated through an XR interface on Meta Quest.

## What problem does it try to solve?

Logistics tasks in local distribution centers represent the highest-cost point in the shipment of any merchandise. Teleoperation seeks to enable remote operation, supported by an immersive interface, for people with lower-limb motor disabilities (a population segment with a high unemployment rate).

## Site Index

### Report

1. [Context]({{ "/docs/en/report/01-context" | relative_url }})
2. [Problem Statement]({{ "/docs/en/report/02-problem-statement" | relative_url }})
3. [Research Question]({{ "/docs/en/report/03-research-question" | relative_url }})
4. [Objectives]({{ "/docs/en/report/04-objectives" | relative_url }})
5. [Justification]({{ "/docs/en/report/05-justification" | relative_url }})
6. [Scope and Limitations]({{ "/docs/en/report/06-scope-limitations" | relative_url }})
7. [Methodology]({{ "/docs/en/report/07-methodology" | relative_url }})
8. [Theoretical Framework]({{ "/docs/en/report/08-theoretical-framework" | relative_url }})
9. [Schedule]({{ "/docs/en/report/09-schedule" | relative_url }})
10. [Development]({{ "/docs/en/report/10-development" | relative_url }})
11. [References]({{ "/docs/en/report/11-references" | relative_url }})

### Documentation (replication manual)

1. [Introduction]({{ "/docs/en/manual/01-introduction" | relative_url }})
2. [System Architecture]({{ "/docs/en/manual/02-system-architecture" | relative_url }})
3. [Robot AGV]({{ "/docs/en/manual/03-robot-agv/" | relative_url }})
   - [Embedded Systems]({{ "/docs/en/manual/03-robot-agv/embedded-systems" | relative_url }})
     - [H-Bridge]({{ "/docs/en/manual/03-robot-agv/h-bridge" | relative_url }})
     - [Driver Controller (CL57T)]({{ "/docs/en/manual/03-robot-agv/driver-controller-cl57t" | relative_url }})
     - [Gripper Controller]({{ "/docs/en/manual/03-robot-agv/gripper-controller" | relative_url }})
   - [Mobile Platform]({{ "/docs/en/manual/03-robot-agv/mobile-platform" | relative_url }})
   - [3DOF Manipulator]({{ "/docs/en/manual/03-robot-agv/manipulator" | relative_url }})
   - [Embedded Software]({{ "/docs/en/manual/03-robot-agv/embedded-software" | relative_url }})
   - [Testing and Calibration]({{ "/docs/en/manual/03-robot-agv/testing-calibration" | relative_url }})
4. [Server / NUC]({{ "/docs/en/manual/04-server/" | relative_url }})
   - [ZMQ Middleware]({{ "/docs/en/manual/04-server/middleware" | relative_url }})
   - [Perception]({{ "/docs/en/manual/04-server/perception" | relative_url }})
   - [Server Testing]({{ "/docs/en/manual/04-server/testing" | relative_url }})
5. [XR Meta Quest]({{ "/docs/en/manual/05-xr-metaquest/" | relative_url }})
   - [Unity and ZMQ Communication]({{ "/docs/en/manual/05-xr-metaquest/unity" | relative_url }})
   - [Interface and Controls]({{ "/docs/en/manual/05-xr-metaquest/interface" | relative_url }})
   - [XR Testing]({{ "/docs/en/manual/05-xr-metaquest/testing" | relative_url }})
6. [WF-IoT Protocol: MR-Edge Latency]({{ "/docs/en/manual/wfiot-latency-test-protocol" | relative_url }})
7. [Commissioning]({{ "/docs/en/manual/07-commissioning" | relative_url }})
8. [Safety]({{ "/docs/en/manual/08-safety" | relative_url }})
9. [Troubleshooting]({{ "/docs/en/manual/09-troubleshooting" | relative_url }})
10. [Future Work]({{ "/docs/en/manual/11-future-work" | relative_url }})
11. [Annexes and References]({{ "/docs/en/manual/12-annexes" | relative_url }})

### Español

- [Versión en español de este sitio]({{ "/" | relative_url }}) — el reporte y el manual de réplica completos en español
