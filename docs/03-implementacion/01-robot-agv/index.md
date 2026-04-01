---
title: "Robot AGV"
nav_order: 1
parent: "Implementación"
has_children: true
---

# Robot AGV

El subsistema robótico integra una **plataforma móvil de tipo diferencial rehabilitada** con un **manipulador de 3 grados de libertad construido desde cero**. Ambas estructuras comparten la electrónica de potencia basada en módulos Puente H de diseño propio con control embebido ESP32-C3.

![Robot completo con manipulador montado]({{ "/assets/img/manipulador_robot_completo.jpg" | relative_url }})

## Componentes principales

| Subsistema | Estado |
|---|---|
| Plataforma móvil (base uniciclo) | Rehabilitada y validada en piso |
| Manipulador 3-DOF | Construido desde cero, validado estáticamente |
| PCB Puente H (x2) | Diseñada, fabricada y probada |
| NUC (computador embarcado) | Operativa — nodo maestro de percepción y ZMQ |
| ESP32-C3 + bus I2C | Bridge USB-I2C hacia PCBs de potencia |

## Arquitectura física

```
┌─────────────────────────────────┐
│         Manipulador 3-DOF       │  ← NEMA17 + reductor 10:1 + HTD3M 2.5:1
│   Gripper rack-and-pinion       │  ← Acero 1.2/0.6mm, corte láser
├─────────────────────────────────┤
│      Plataforma Móvil           │  ← Acero cal. 18, 4 ruedas locas
│   2× motores DC + encoders      │  ← 2× módulos Puente H ESP32-C3
└─────────────────────────────────┘
```

## Páginas de esta sección

- [Plataforma móvil]({{ "/docs/03-implementacion/01-robot-agv/plataforma-movil" | relative_url }}) — Hardware de la base y drivers
- [Manipulador]({{ "/docs/03-implementacion/01-robot-agv/manipulador" | relative_url }}) — Diseño CAD, manufactura y ensamble
- [Electrónica]({{ "/docs/03-implementacion/01-robot-agv/electronica" | relative_url }}) — PCB Puente H: diseño, especificaciones y archivos
- [Software]({{ "/docs/03-implementacion/01-robot-agv/software" | relative_url }}) — Stack ROS y firmware
- [Pruebas]({{ "/docs/03-implementacion/01-robot-agv/pruebas" | relative_url }}) — Resultados y validaciones
