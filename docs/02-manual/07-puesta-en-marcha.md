---
title: "Puesta en marcha"
nav_order: 7
parent: "Documentación"
---

# Puesta en marcha

## Secuencia de arranque (conceptual)

1. Encender robot y verificar alimentación de potencia
2. Verificar estado de módulos embebidos ESP32-C3 (LEDs de estado)
3. Ejecutar sistema de control en Python 3.12 en la NUC
4. Confirmar comunicación ZMQ (canales :5555, :5001, :5002)
5. Abrir interfaz XR en Meta Quest 3
6. Verificar recepción de datos (video / estado / lidar)
7. Probar movimiento a baja velocidad en entorno controlado

## Documentado actualmente

- Componentes, arquitectura de comunicación y pruebas parciales de integración de subsistemas

> **Pendiente:** Documentar comandos exactos de arranque del sistema Python 3.12, rutas de scripts, configuración de red reproducible (IPs, descubrimiento ZMQ) y checklist operacional pre-prueba.
