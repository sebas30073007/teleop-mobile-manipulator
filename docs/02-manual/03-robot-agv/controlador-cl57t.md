---
title: "Controlador de drivers (CL57T)"
nav_order: 2
parent: "Robot AGV"
---

# Controlador de drivers (CL57T)

Placa de diseño propio basada en **ESP32-C3** que genera las señales de paso para los tres drivers de motor del manipulador. Cada driver es un **CL57T** (cerrado-lazo, compatible con NEMA17).

## Requisitos

- Controlar 3 ejes del manipulador (articulaciones + hombro) de forma independiente
- Generar señales **PUL / DIR / ENABLE** hacia cada driver CL57T
- Soportar finales de carrera para rutinas de calibración y búsqueda de cero
- Recibir comandos de posición desde la NUC vía I2C (a través del Puente H maestro)

> **Pendiente:** Documentar la tabla de reducción total por eje y los rangos de movimiento en pasos por grado.

## Diseño

### Drivers CL57T

El CL57T es un driver de paso cerrado (servo-stepper) que acepta señales digitales de pulso y dirección. Opera en modo de lazo cerrado usando el encoder del motor para corregir pérdida de pasos.

| Parámetro | Valor |
|---|---|
| Motor compatible | NEMA17 |
| Tipo de lazo | Cerrado (encoder incremental) |
| Señales de control | PUL, DIR, ENABLE (lógica 5V) |
| Corriente máx. | Configurable por DIP en driver |

### Placa controladora

La placa genera las señales para los tres CL57T y gestiona las entradas digitales de los finales de carrera:

| Función | Descripción |
|---|---|
| Salidas PUL/DIR/ENABLE | Una terna por cada eje (×3) |
| Entradas digitales | Finales de carrera para calibración |
| Botón físico | Rutina de búsqueda de cero activable localmente |
| Comunicación | I2C esclavo — recibe comandos del Puente H maestro |

## Implementación

Los comandos de posición viajan desde la NUC por el serial del Puente H maestro (USB → COM4), y el maestro los reenvía a esta placa por el bus I2C. La placa ejecuta la interpolación de pasos localmente, sin que la NUC tenga que gestionar señales en tiempo real.

### Flujo de comando de eje

```
Meta Quest (XR)
    │ ZMQ cmd (manip_cmd)
    ▼
NUC (Python 3.12)
    │ Serial COM4
    ▼
Puente H maestro (ESP32-C3)
    │ I2C
    ▼
Controlador CL57T (ESP32-C3)
    │ PUL / DIR / ENABLE
    ▼
Driver CL57T × 3
    │
    ▼
NEMA17 + reductor planetario × 3 (articulaciones del manipulador)
```

### Estado publicado hacia la NUC

La placa reporta estado periódicamente (`MANIP_STATE`) que incluye:

| Campo | Descripción |
|---|---|
| `busy` | Indica si algún eje está en movimiento |
| `sw2`, `sw3` | Estado de los finales de carrera |
| `calibrated` | Si se completó la rutina de búsqueda de cero |

> **Pendiente:** Documentar el código fuente MicroPython/C de la placa, el procedimiento de flasheo y la tabla de pasos/grado por articulación.

## Validación

| Prueba | Resultado |
|---|---|
| Movimiento de articulaciones (estático) | ✅ Rangos alcanzados, sin pérdida de pasos detectada |
| Rutina de búsqueda de cero | ✅ Funcional con finales de carrera |
| Control remoto desde interfaz XR | ⏳ Pendiente integración completa |

Ver evidencia en [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}).
