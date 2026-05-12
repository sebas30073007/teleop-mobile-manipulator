---
title: "Sistemas embebidos"
nav_order: 1
parent: "Robot AGV"
has_children: true
---

# Sistemas embebidos

Los tres controladores embebidos del robot corren firmware **MicroPython** sobre módulos **ESP32-C3 SuperMini**. Cada uno es responsable de una función de actuación específica y se comunica con la NUC por I²C o USB-CDC.

| Controlador | PCB | Comunicación con NUC | Función principal |
|---|---|---|---|
| [Puente H]({{ "/docs/02-manual/03-robot-agv/electronica" | relative_url }}) | Diseño propio (KiCad) | USB-CDC COM4 (maestro) | Motores DC de tracción |
| [CL57T]({{ "/docs/02-manual/03-robot-agv/controlador-cl57t" | relative_url }}) | Diseño propio (KiCad) | I²C addr `0x0B` vía maestro | 3 ejes del manipulador (PUL/DIR) |
| [Gripper]({{ "/docs/02-manual/03-robot-agv/controlador-gripper" | relative_url }}) | Protoboard (sin PCB) | USB-CDC COM5 | Pinza — posición en mm |

{: .note }
**Costo de fabricación PCBs (JLCPCB, lote de 10 piezas por diseño):** $5.00 USD producción · $17.50 USD envío · $130 MXN derechos de importación.

## Arquitectura I²C

El Puente H configurado como maestro (`DIP = 100`) actúa como concentrador del bus I²C. La NUC solo necesita un canal USB para controlar los 3 nodos embebidos de movimiento:

```
NUC
 └── COM4 (USB) ──► Puente H maestro
                        ├── I²C 0x08 ──► Puente H esclavo (motor base)
                        └── I²C 0x0B ──► Controlador CL57T (3 ejes)
 └── COM5 (USB) ──► Controlador gripper (directo, fuera del bus I²C)
```

## Estado de los firmwares

| Firmware | Líneas | Estado |
|---|---|---|
| `main_movil_final.py` | 1 175 | ✅ Funcional |
| `main_manipulador_final.py` | 933 | ✅ Funcional |
| `main_gripper_final.py` | 703 | ✅ Funcional |
