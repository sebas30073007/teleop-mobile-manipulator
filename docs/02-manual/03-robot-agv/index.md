---
title: "Robot AGV"
nav_order: 3
parent: "Documentación"
has_children: true
---

# Robot AGV

El subsistema robótico integra una **plataforma móvil de tipo diferencial rehabilitada** con un **manipulador de 3 grados de libertad construido desde cero**. Ambas estructuras usan módulos embebidos para realizar la operación de bajo nivel de la parte movil como del manipulador.

![Robot completo con manipulador montado]({{ "/assets/img/AGV.png" | relative_url }})

## Subsecciones

**Electrónica**
- [Sistemas embebidos]({{ "/docs/02-manual/03-robot-agv/sistemas-embebidos" | relative_url }}) — Puente H, CL57T y gripper: MicroPython ESP32-C3, firmwares, protocolos I²C y USB

**Mecánica**
- [Plataforma móvil]({{ "/docs/02-manual/03-robot-agv/plataforma-movil" | relative_url }}) — base diferencial rehabilitada
- [Manipulador 3DOF]({{ "/docs/02-manual/03-robot-agv/manipulador" | relative_url }}) — diseño, manufactura láser, CAD, ensamble

**Software y validación**
- [Software embebido]({{ "/docs/02-manual/03-robot-agv/software" | relative_url }}) — MicroPython ESP32-C3, stack NUC Python 3.12
- [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}) — validaciones ejecutadas, resultados

## Estado del subsistema

| Componente | Estado |
|---|---|
| Plataforma móvil diferencial | ✅ Construida y probada |
| Manipulador 3DOF | ✅ Construido y probado |
| Módulos Puente H PCB (×2) | ✅ Diseñados, ensamblados y probados |
| Firmware Puente H (ESP32-C3) | ✅ Funcional en todos los modos |
| Firmware CL57T (ESP32-C3) | ✅ Funcional — homing, compensación muñeca |
| Firmware gripper (ESP32-C3) | ✅ Funcional — control mm, stall detect |
| Control NUC ↔ ESP32-C3 ↔ XR | ⏳ Integración en proceso |
