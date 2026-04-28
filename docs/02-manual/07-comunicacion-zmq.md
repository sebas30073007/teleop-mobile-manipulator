---
title: "Comunicación ZMQ"
nav_order: 7
parent: "Manual de réplica académica"
---

# Comunicación ZMQ

## Para qué se usa

ZMQ es el canal principal de intercambio de datos entre la interfaz XR y la computadora de control.

## Qué conecta

- Interfaz XR (Meta Quest / Unity).
- Computadora de control con Python 3.12.
- Flujo de datos hacia control embebido y subsistemas de robot.

## Datos documentados que viajan por ZMQ

- Stream de video (`video_rgb`).
- Estado y sensores (`stat`, `mode_ack`, `lidar_grid`, `cam_info`, `vision`, `error`).
- Comandos de control en JSON (`cmd`).

## Puertos documentados en el repositorio

| Puerto | Dirección general | Uso documentado |
|---|---|---|
| `:5555` | Computadora de control → XR | Stream de video |
| `:5001` | Computadora de control → XR | Sensores y estado |
| `:5002` | XR → Computadora de control | Comandos JSON |

> Pendiente por documentar
>
> Actualmente esta información no está disponible en el repositorio.
>
> Para completar esta sección se necesita:
> - Contrato formal de mensajes JSON por tipo de comando.
> - Política de reconexión y manejo de pérdida de paquetes.
> - Criterios de verificación de puertos y método de diagnóstico en red.
>
> Esta información es necesaria porque permite:
> - Asegurar interoperabilidad y depuración reproducible durante integración de subsistemas.
