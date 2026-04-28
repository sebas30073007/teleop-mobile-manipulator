---
title: "Sistema de control en Python 3.12"
nav_order: 8
parent: "Documentación"
---

# Sistema de control en Python 3.12

## Rol de la computadora de control

La computadora de control coordina percepción, estado, publicación de datos y recepción de comandos para el robot teleoperado.

## Implementado actualmente

- Backend documentado en Python 3.12.
- Flujo de publicación/suscripción de datos vía ZMQ para XR.

## Parcialmente implementado

- Integración de telemetría completa del robot y de control total del manipulador en ciclo operacional único.

> Pendiente por documentar
>
> Actualmente esta información no está disponible en el repositorio.
>
> Para completar esta sección se necesita:
> - Scripts reales de arranque del backend Python.
> - Lista de dependencias (`requirements.txt` o equivalente).
> - Estructura de carpetas del código de control.
>
> Esta información es necesaria porque permite:
> - Ejecutar, depurar y mantener la réplica académica del sistema de control.
