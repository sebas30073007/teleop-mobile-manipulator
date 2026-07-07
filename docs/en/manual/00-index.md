---
title: "Documentation"
nav_order: 2
parent: "English"
has_children: true
permalink: /en/documentation/
---

# Documentation

This repository organizes the robotic teleoperation project as an academic replication guide. The documentation follows a traceability thread: from requirements to design, from design to implementation, and from implementation to validation.

## How to read this manual

1. [Introduction]({{ "/docs/en/manual/01-introduction" | relative_url }}) — problem addressed and system scope
2. [System Architecture]({{ "/docs/en/manual/02-system-architecture" | relative_url }}) — overview of subsystems and data flows
3. Subsystems (each with Requirements → Design → Implementation → Validation):
   - [Robot AGV]({{ "/docs/en/manual/03-robot-agv/" | relative_url }}) — mobile platform, manipulator, electronics, software
   - [Server / NUC]({{ "/docs/en/manual/04-server/" | relative_url }}) — ZMQ middleware, perception
   - [XR Meta Quest]({{ "/docs/en/manual/05-xr-metaquest/" | relative_url }}) — Unity, interface, controls
4. [Commissioning]({{ "/docs/en/manual/07-commissioning" | relative_url }}) — startup sequence
5. [Future Work]({{ "/docs/en/manual/11-future-work" | relative_url }})

## Documentation scope

This site prioritizes **academic replication**. It is not an industrial guide nor a commercial end-product manual.
