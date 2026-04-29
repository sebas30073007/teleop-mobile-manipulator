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

**Sistemas embebidos**
- [Puente H]({{ "/docs/02-manual/03-robot-agv/electronica" | relative_url }}) — driver de motor DC de diseño propio (ESP32-C3), PCB, firmware, modos I2C
- [Controlador de drivers (CL57T)]({{ "/docs/02-manual/03-robot-agv/controlador-cl57t" | relative_url }}) — placa ESP32-C3 que genera señales PUL/DIR/ENABLE para los 3 ejes del manipulador

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
| Firmware ESP32-C3 (motores) | ✅ Funcional en todos los modos |
| Control NUC ↔ ESP32-C3 ↔ XR | ⏳ Integración en proceso |
