---
title: "Electrónica y control embebido"
nav_order: 6
parent: "Documentación"
---

# Electrónica y control embebido

## Rol de ESP32-C3

Las ESP32-C3 operan como control embebido del sistema físico, ejecutando firmware en **MicroPython**.

## Qué está documentado

- Módulo puente H con pines, modos de operación y comandos funcionales.
- Descripción de control de motores y estados básicos.

## Qué no está disponible aún

El repositorio no incluye todavía el código completo del firmware MicroPython de las ESP32-C3.

## Tabla de disponibilidad de firmware

| Módulo | Función | Firmware disponible | Pines documentados | Estado |
|---|---|---|---|---|
| Puente H ESP32-C3 | Control de motor y comunicación | No | Sí (documentación de pines) | Parcialmente documentado |
| Control de manipulador (ESP32-C3) | Control de actuadores del brazo | No | No | Pendiente por documentar |

> Pendiente por documentar
>
> Actualmente esta información no está disponible en el repositorio.
>
> Para completar esta sección se necesita:
> - Código fuente MicroPython por módulo ESP32-C3.
> - Procedimiento de flasheo y actualización de firmware.
> - Tabla final de pines por módulo y versión de hardware.
>
> Esta información es necesaria porque permite:
> - Replicar el control embebido y validar comportamiento de actuadores de forma trazable.
