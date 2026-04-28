---
title: "Puesta en marcha"
nav_order: 10
parent: "Manual de réplica académica"
---

# Puesta en marcha

## A) Puesta en marcha actualmente documentada

En el repositorio se documentan componentes, arquitectura de comunicación y pruebas parciales de integración.

## B) Secuencia esperada de arranque (conceptual)

1. Encender robot y verificar alimentación.
2. Verificar estado de módulos embebidos ESP32-C3.
3. Ejecutar sistema de control en Python 3.12.
4. Confirmar comunicación ZMQ.
5. Abrir interfaz XR en Meta Quest.
6. Verificar recepción de datos (video/estado).
7. Probar movimiento a baja velocidad en entorno controlado.

## C) Pendiente por documentar

> Pendiente por documentar
>
> Actualmente esta información no está disponible en el repositorio.
>
> Para completar esta sección se necesita:
> - Comandos exactos de arranque del sistema Python 3.12.
> - Rutas de scripts y orden real de ejecución.
> - Configuración de red (IP, descubrimiento, validación de puertos ZMQ).
> - Checklist operacional previo a pruebas.
>
> Esta información es necesaria porque permite:
> - Ejecutar una secuencia repetible y reducir fallas de integración por configuración incompleta.
