---
title: "Trabajo a futuro"
nav_order: 11
parent: "Documentación"
---

# Trabajo a futuro

Líneas de desarrollo identificadas a partir de los resultados y limitaciones del proyecto terminal.

## Hardware

- **PCB dedicada para el gripper** — diseñar una placa propia para el controlador del gripper que reemplace el montaje en protoboard actual, mejorando la robustez mecánica y reduciendo el cableado suelto.

## Control y modelos matemáticos

- **Modelo matemático para robots móviles uniciclos** — implementar el modelo cinemático diferencial del AGV para calcular odometría y ejecutar trayectorias programadas, en lugar de depender exclusivamente del control manual directo desde la interfaz XR.
- **Cinemática inversa del manipulador** — implementar el modelo de cinemática inversa de los 3 DOF para comandar el end-effector por posición cartesiana, en lugar de ángulos de articulación individuales.
- **Captura de encoders para control en lazo cerrado** — integrar la lectura de los encoders de los motores de tracción en el firmware del Puente H para implementar control de velocidad y posición en lazo cerrado, eliminando la dependencia del control en lazo abierto actual.
