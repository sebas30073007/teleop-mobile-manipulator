---
title: "Plataforma móvil"
nav_order: 3
parent: "Robot AGV"
---

# Plataforma móvil

## Requisitos

La plataforma debía soportar el peso del manipulador y la electrónica, moverse en superficies planas de almacén y ser compatible con los módulos de control embebido desarrollados para el proyecto.

## Diseño

La solución adoptada es una **plataforma diferencial de tipo uniciclo rehabilitada**. Se conservó la estructura mecánica original y se sustituyeron los drivers de motor, cableado y electrónica de control para integrarlos con el sistema de teleoperación.

Características de diseño:

- **2 motores DC** con encoders para odometría
- **4 ruedas locas** (una en cada extremo) para soporte y estabilidad
- **Estructura de acero calibre 18 (1.2 mm)** que soporta el manipulador y la electrónica

## Implementación

![Plataforma móvil base]({{ "/assets/img/agv_plataforma_base.jpg" | relative_url }})

### Drivers y configuración I²C

Los motores son controlados por los **módulos Puente H ESP32-C3** diseñados para este proyecto (ver [Electrónica — Puente H]({{ "/docs/02-manual/03-robot-agv/electronica" | relative_url }})).

Se usan dos módulos en arquitectura maestro–esclavo sobre bus I²C:

| Motor | Módulo | Modo DIP switch |
|---|---|---|
| Motor derecho | Puente H #1 — Maestro | I²C Maestro (`SW: 100`) |
| Motor izquierdo | Puente H #2 — Esclavo | I²C Slave 1 (`SW: 101`) |

El **módulo maestro** recibe los comandos desde la NUC y controla al **módulo esclavo** en cadena (daisy chain I²C).

![Conexiones del driver]({{ "/assets/img/manipulador_manufactura_top.jpg" | relative_url }})

### Re-habilitación

Se sustituyó el cableado y se montaron los módulos PCB de diseño propio sobre la estructura existente.

![Prueba en piso]({{ "/assets/img/agv_prueba_piso.jpg" | relative_url }})

## Validación

Resultados de pruebas de la plataforma:

| Prueba | Resultado |
|---|---|
| Movimiento diferencial en superficie plana | ✅ Estable |
| Respuesta a comandos de dirección (F/B/L/R) | ✅ Correcta |
| Temperatura MOSFETs bajo carga continua 60 min | ✅ Dentro del rango (disipadores efectivos) |
| Control remoto extremo a extremo desde XR | ⏳ Pendiente integración completa |

Ver evidencia completa en [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}).
