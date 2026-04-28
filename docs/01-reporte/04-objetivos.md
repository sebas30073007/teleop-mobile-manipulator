---
title: "Objetivos"
nav_order: 4
parent: "Reporte"
---

# Objetivos

## Objetivo general

Diseñar, integrar y validar experimentalmente una plataforma de teleoperación robótica orientada a tareas logísticas, compuesta por un robot móvil-manipulador, un servidor de coordinación basado en Python y ZeroMQ (ZMQ), y una interfaz de operación en realidad extendida (XR) sobre Meta Quest, evaluando su desempeño técnico y usabilidad en escenarios controlados de almacén simulado.

## Objetivos específicos

**OE1 — Análisis de tareas:** Identificar y caracterizar las tareas logísticas con mayor potencial de teleoperación en función de su complejidad de ejecución, riesgo operativo y beneficio marginal de automatización, definiendo el caso de uso primario del prototipo.

**OE2 — Requerimientos de sistema:** Definir los requerimientos funcionales, no funcionales y de interfaz del sistema, incluyendo latencia máxima aceptable, precisión de manipulación, resolución y frecuencia del video de retroalimentación, y criterios mínimos de usabilidad.

**OE3 — Integración técnica:** Construir e integrar los tres subsistemas —plataforma robótica, servidor middleware y capa XR— garantizando comunicación en tiempo real, control de movimiento confiable y retroalimentación visual al operador durante la teleoperación.

**OE4 — Validación experimental:** Ejecutar un protocolo de pruebas estructurado que permita comparar el desempeño del sistema teleoperado contra una línea base de referencia, cuantificando tiempo de ejecución por tarea, tasa de error operativo y usabilidad percibida mediante métricas estandarizadas.

## Métricas de evaluación

| Métrica | Instrumento de medición | Umbral de referencia |
|---|---|---|
| Tiempo de ejecución por tarea | Cronometraje por sesión de prueba | Comparable a ejecución manual (±20%) |
| Tasa de error operativo | Registro de eventos de falla o desviación | < 15% de intentos |
| Latencia de control extremo a extremo | Medición en red local (ms) | < 100 ms |
| Usabilidad percibida | Cuestionario SUS (escala 0–100) | Puntaje ≥ 68 (rango aceptable) |

Las métricas fueron seleccionadas por su relevancia operativa directa y por disponer de instrumentos de medición validados en la literatura de teleoperación y usabilidad. El umbral del SUS (≥ 68) corresponde al punto de corte empírico establecido por Bangor et al. para clasificar un sistema como aceptable para uso general.

---

*Siguiente: [Justificación →]({{ "/docs/01-reporte/05-justificacion" | relative_url }})*
