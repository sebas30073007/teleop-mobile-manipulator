---
title: "Arquitectura del sistema"
nav_order: 3
parent: "Documentación"
---

# Arquitectura del sistema

La arquitectura vigente conecta operación XR, comunicación ZMQ, control en Python 3.12 y control embebido en ESP32-C3 con MicroPython.

```text
Usuario / operador
→ Meta Quest / interfaz XR
→ Comunicación ZMQ
→ Computadora de control (Python 3.12)
→ ESP32-C3 (MicroPython)
→ Actuadores y sensores del robot móvil con manipulador
```

## Componentes lógicos

| Componente | Rol en el sistema | Estado |
|---|---|---|
| Interfaz XR (Meta Quest) | Visualización y operación remota | Implementado parcialmente |
| Comunicación ZMQ | Canal de mensajes entre XR y computadora de control | Implementado |
| Computadora de control (Python 3.12) | Coordinación de sensores, video y comandos | Implementado parcialmente |
| Control embebido (ESP32-C3 + MicroPython) | Ejecución de control sobre actuadores | Implementado parcialmente |
| Actuadores | Movimiento de base móvil y manipulador | Implementado parcialmente |
| Sensores | Captura de entorno y estado del robot | Implementado parcialmente |
| Robot físico | Plataforma AGV + manipulador | Implementado |

> Pendiente por documentar
>
> Actualmente esta información no está disponible en el repositorio.
>
> Para completar esta sección se necesita:
> - Diagrama de arquitectura de alto nivel en imagen editable.
> - Diagrama de conexiones entre computadora de control y módulos embebidos.
> - Diagrama de flujo de datos con formato de mensajes.
>
> Esta información es necesaria porque permite:
> - Comprender rápidamente el sistema y evitar interpretaciones ambiguas durante la réplica.
