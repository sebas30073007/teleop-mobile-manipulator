---
title: "Pruebas"
nav_order: 6
parent: "Robot AGV"
---

# Pruebas del Robot AGV

## Prueba de Puente H

### Ensamble en protoboard 
El puente H se armo primero en protoboard para verificar el funcionamiento primario y capacidad de los componentes. En este caso los más criticos son los mosfets en la etapa de potencia, se midio la temperatura llegnado a registrar hasta 61°C.

![Prototipo armado]({{ "/assets/img/puente_h_prototipo_armado.jpg" | relative_url }})
![Test del prototipo]({{ "/assets/img/puente_h_prototipo_test.jpg" | relative_url }})
![Temperatura en prototipo]({{ "/assets/img/puente_h_temperatura.jpg" | relative_url }})
### Video pruebas
El siguiente video muestra la vista de la salida del puente H desde un osciloscopio. Probando tanto el circuito en protoboard como la PCB.
{% include video_youtube.html id="PR21DzIkdKw" title="Pruebas PWM del Puente H — PCB final" %}

## Pruebas Manipulador

### Prueba estática del manipulador

Validación de rangos de movimiento y torque de cada articulación con el robot detenido.

{% include video_youtube.html id="OUl0yDCDwxs" title="Pruebas del manipulador robótico — Proyecto Terminal 2026" %}

**Resultados:**
- Articulaciones 1 y 2 alcanzan el rango de movimiento de diseño
- No se detectó juego excesivo en las transmisiones HTD3M

---

### Prueba de movimiento rápido

Prueba preliminar de velocidad de movimiento del manipulador...

---

## Prueba robot móvil

### Pruebas

Validación de la plataforma móvil con los módulos Puente H de diseño propio. El siguiente video muestra pruebas escalonadas.

{% include video_youtube.html id="_QijcA0hDec" title="Pruebas de la plataforma robótica — Proyecto Terminal 2026" %}

**Resultados:**
- Movimiento diferencial estable en superficie plana
- Módulos Puente H responden correctamente a comandos de dirección
- Temperatura de MOSFETs dentro del rango aceptable (no se percibe calor excesivo al tacto)

---

### Prueba de robustez prolongada

Prueba térmica del módulo Puente H bajo carga continua durante 60 minutos.

> Pendiente por documentar
>
> Actualmente esta información no está disponible en el repositorio.
>
> Para completar esta sección se necesita:
> - Enlace de video de prueba de robustez prolongada.
> - Parámetros de carga y condiciones ambientales de la prueba.
> - Registro temporal de temperatura durante la sesión.
>
> Esta información es necesaria porque permite:
> - Sustentar con evidencia reproducible el desempeño térmico del módulo.

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
| Pick-and-place con carga | ⏳ Pendiente | Requiere integración completa NUC ↔ ESP32-C3 ↔ XR |
