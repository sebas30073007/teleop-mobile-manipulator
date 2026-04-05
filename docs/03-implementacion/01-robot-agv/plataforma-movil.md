---
title: "Plataforma móvil"
nav_order: 2
parent: "Robot AGV"
---

# Plataforma móvil

La base del robot es una **plataforma diferencial de tipo uniciclo rehabilitada**. Se conservó la estructura mecánica original y se sustituyeron los drivers de motor, cableado y electrónica de control para integrarlos con el sistema de teleoperación.

## Hardware base

![Plataforma móvil base]({{ "/assets/img/agv_plataforma_base.jpg" | relative_url }})

La plataforma cuenta con:

- **2 motores DC** con encoders
- **4 ruedas locas** (una en cada extremo) para soporte y estabilidad
- **Estructura de acero calibre 18 (1.2 mm)** que soporta el manipulador y la electrónica

## Drivers y conexiones

Los motores son controlados por los **módulos Puente H ESP32-C3** diseñados para este proyecto (ver [Electrónica]({{ "/docs/03-implementacion/01-robot-agv/electronica" | relative_url }})).

![Conexiones del driver]({{ "assets\img\manipulador_manufactura_top.jpg" | relative_url }})

### Configuración de drivers

Se usan dos módulos Puente H. El **módulo maestro** recibe los comandos desde la computadora de a bordo y controla al **módulo esclavo** a través del bus I²C en cadena.

| Motor | Módulo | Modo DIP switch |
|---|---|---|
| Motor derecho | Puente H #1 — Maestro | I²C Maestro (`SW: 100`) |
| Motor izquierdo | Puente H #2 — Esclavo | I²C Slave 1 (`SW: 101`) |

## Re-habilitación

![Prueba en piso]({{ "/assets/img/agv_prueba_piso.jpg" | relative_url }})
