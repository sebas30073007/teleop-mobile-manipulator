---
title: "Pruebas y calibración"
nav_order: 5
parent: "Robot AGV"
---

# Pruebas y calibración del Robot AGV

## Pruebas del Puente H

### Ensamble en protoboard

El puente H se armó primero en protoboard para verificar el funcionamiento primario y la capacidad de los componentes. Los MOSFETs de la etapa de potencia se monitorearon térmicamente, registrando hasta 61 °C.

![Prototipo armado]({{ "/assets/img/puente_h_prototipo_armado.jpg" | relative_url }})
![Test del prototipo]({{ "/assets/img/puente_h_prototipo_test.jpg" | relative_url }})
![Temperatura en prototipo]({{ "/assets/img/puente_h_temperatura.jpg" | relative_url }})

### Video de pruebas PWM

Salida del puente H desde osciloscopio, probando el circuito en protoboard y la PCB final.

{% include video_youtube.html id="PR21DzIkdKw" title="Pruebas PWM del Puente H — PCB final" %}

---

## Pruebas del Manipulador

### Prueba estática

Validación de rangos de movimiento y torque de cada articulación con el robot detenido.

{% include video_youtube.html id="OUl0yDCDwxs" title="Pruebas del manipulador robótico — Proyecto Terminal 2026" %}

**Resultados:**
- Articulaciones 1 y 2 alcanzan el rango de movimiento de diseño
- No se detectó juego excesivo en las transmisiones HTD3M

### Prueba de movimiento rápido

Prueba preliminar de velocidad de movimiento del manipulador. Velocidades funcionales confirmadas.

---

## Pruebas del Gripper

<video controls width="100%">
  <source src="{{ '/assets/vid/Test_gripper_web.mp4' | relative_url }}" type="video/mp4">
  Tu navegador no puede reproducir este video.
</video>

---

## Pruebas de la Plataforma Móvil

### Movimiento diferencial

Validación de la plataforma móvil con los módulos Puente H de diseño propio.

{% include video_youtube.html id="_QijcA0hDec" title="Pruebas de la plataforma robótica — Proyecto Terminal 2026" %}

**Resultados:**
- Movimiento diferencial estable en superficie plana
- Módulos Puente H responden correctamente a comandos de dirección
- Temperatura de MOSFETs dentro del rango aceptable al tacto

### Prueba de robustez prolongada

Prueba térmica del módulo Puente H bajo carga continua durante 60 minutos.

**Resultados:**
- Módulo operó de forma estable durante toda la prueba
- Sin activación del fusible de protección
- Temperatura de MOSFETs estabilizada con disipadores

> **Pendiente:** Agregar el registro temporal de temperatura durante la sesión de 60 minutos con las condiciones exactas de carga.

---

## Resumen de resultados

| Prueba | Resultado | Observaciones |
|---|---|---|
| Movimiento manipulador (estático) | ✅ Aprobada | Rangos de movimiento correctos |
| Movimiento manipulador (rápido) | ✅ Aprobada | Velocidades funcionales |
| Plataforma móvil + PCB Puente H | ✅ Aprobada | Movimiento diferencial estable |
| Sistema integrado en piso | ✅ Aprobada | Operación conjunta validada |
| Robustez Puente H 1 hora | ✅ Aprobada | Sin fallas térmicas |
| Pick-and-place con carga | ⏳ Pendiente | Requiere integración NUC ↔ ESP32-C3 ↔ XR |

---

## Calibración

La calibración consiste en ajustar parámetros para que el comportamiento físico del sistema sea consistente y repetible.

| Elemento | Variable | Estado |
|---|---|---|
| Motores base | Respuesta a rampas de velocidad | ⏳ Pendiente documentar |
| Manipulador | Posición home y repetibilidad por articulación | ⏳ Pendiente documentar |
| Sensores (RealSense D435i) | Alineación y corrección de profundidad | Parcial — curva interpolada implementada |
| Comunicación I²C | Tiempos de respuesta maestro–esclavo | ⏳ Pendiente documentar |

> **Pendiente:** Documentar los procedimientos de calibración paso a paso y los criterios de aceptación por elemento.
