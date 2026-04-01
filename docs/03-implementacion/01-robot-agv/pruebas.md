---
title: "Pruebas"
nav_order: 6
parent: "Robot AGV"
---

# Pruebas del Robot AGV

## Pruebas realizadas

### Prueba estática del manipulador

Validación de rangos de movimiento y torque de cada articulación con el robot detenido.

{% include video_youtube.html id="OUl0yDCDwxs" title="Pruebas del manipulador robótico — Proyecto Terminal 2026" %}

**Resultados:**
- Articulaciones 1 y 2 alcanzan el rango de movimiento de diseño
- No se detectó juego excesivo en las transmisiones HTD3M
- El gripper rack-and-pinion opera correctamente en apertura/cierre

---

### Prueba de movimiento rápido — manipulador (Arduino)

Prueba preliminar de velocidad de movimiento del manipulador controlado directamente desde Arduino, antes de integración ROS.

<!-- {% include video_youtube.html id="YOUTUBE_ID" title="Movimiento manipulador — prueba rápida Arduino" %} -->

---

### Prueba en piso — robot móvil + PCB Puente H

Validación de la plataforma móvil con los módulos Puente H de diseño propio (PCB final).

{% include video_youtube.html id="_QijcA0hDec" title="Pruebas de la plataforma robótica — Proyecto Terminal 2026" %}

**Resultados:**
- Movimiento diferencial estable en superficie plana
- Módulos Puente H responden correctamente a comandos de dirección y velocidad
- Temperatura de MOSFETs dentro del rango aceptable en prueba prolongada

---

### Prueba en piso — robot móvil + manipulador

Prueba del sistema integrado (plataforma + manipulador) en movimiento sobre piso.

<!-- {% include video_youtube.html id="YOUTUBE_ID" title="Robot móvil + manipulador en piso" %} -->

---

### Prueba de robustez prolongada — Puente H (1 hora)

Prueba térmica del módulo Puente H bajo carga continua durante 60 minutos.

<!-- {% include video_youtube.html id="YOUTUBE_ID" title="Prueba robustez Puente H — 1 hora" %} -->

**Resultados:**
- El módulo operó de forma estable durante toda la prueba
- Sin activación del fusible de protección
- Temperatura de MOSFETs estabilizada con disipadores

---

## Resumen de resultados

| Prueba | Resultado | Observaciones |
|---|---|---|
| Movimiento manipulador (estático) | ✅ Aprobada | Rangos de movimiento correctos |
| Movimiento manipulador (rápido) | ✅ Aprobada | Velocidades funcionales |
| Plataforma móvil + PCB Puente H | ✅ Aprobada | Movimiento diferencial estable |
| Sistema integrado en piso | ✅ Aprobada | Operación conjunta validada |
| Robustez Puente H 1 hora | ✅ Aprobada | Sin fallas térmicas |
| Pick-and-place con carga | ⏳ Pendiente | Requiere integración ROS completa |

## Pendientes

- [ ] Prueba de pick-and-place con objetos reales
- [ ] Validación de odometría vs. ground truth
- [ ] Prueba de navegación autónoma en zona estructurada
