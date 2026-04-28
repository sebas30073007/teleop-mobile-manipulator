---
title: "Metodología"
nav_order: 7
parent: "Reporte"
---

# Metodología

El proyecto sigue una metodología de diseño de ingeniería en cuatro fases secuenciales, con iteraciones dentro de cada fase conforme emerge información nueva. El enfoque está orientado a artefactos: el conocimiento se genera a través del diseño, construcción y evaluación de un sistema real, no de modelos teóricos desconectados de su implementación física.

## Fase 1 — Análisis de contexto y caracterización de tareas

**Objetivo:** Establecer qué problema se resuelve, para quién, y bajo qué condiciones operativas.

**Proceso:** Revisión de literatura sobre logística de e-commerce, automatización de almacenes, discapacidad motriz y sistemas de teleoperación existentes. Identificación de tareas logísticas candidatas para teleoperación y evaluación de cada una según tres criterios: complejidad de ejecución, riesgo operativo y potencial de beneficio de la automatización. Priorización de casos de uso para el prototipo.

**Entregables:** Tabla de análisis de tareas con criterios de priorización. Definición del caso de uso principal: traslado interno y operación de pick-and-place en almacén simulado.

## Fase 2 — Definición de requerimientos y diseño de arquitectura

**Objetivo:** Traducir el problema caracterizado en una especificación de sistema diseñable y evaluable.

**Proceso:** Levantamiento de requerimientos funcionales (qué debe hacer el sistema) y no funcionales (precisión, accesibilidad, costo). Evaluación y selección de tecnologías: Python + ZeroMQ (ZMQ) como middleware de coordinación, ESP32-C3 con MicroPython como controlador embebido de la plataforma robótica, motores paso a paso NEMA con drivers CL57T de lazo cerrado, Unity y Meta Quest para la capa XR. Diseño de la arquitectura modular en tres capas y plan de integración incremental.

**Entregables:** Especificación de requerimientos del sistema. Diagrama de arquitectura y diagrama de comunicación entre subsistemas. Plan de implementación con secuencia de integración.

## Fase 3 — Implementación e integración

**Objetivo:** Construir el prototipo funcional que cumple con la especificación de requerimientos.

**Proceso:** Desarrollo paralelo de los tres subsistemas con puntos de integración definidos. Primero se valida la plataforma robótica de forma independiente: movilidad, control del brazo y retroalimentación de sensores. Luego se integra el servidor Python/ZMQ y se verifica la comunicación robot-servidor en red local. Finalmente se agrega la capa XR y se valida el flujo completo de teleoperación: comando del operador → ZMQ → robot → retroalimentación visual al operador.

**Entregables:** Prototipo integrado funcional. Protocolo de operación documentado. Registro de issues encontrados y mitigaciones aplicadas durante la integración.

## Fase 4 — Validación experimental

**Objetivo:** Generar evidencia cuantitativa sobre el desempeño técnico y la usabilidad del sistema.

**Proceso:** Ejecución de sesiones de prueba con operadores en escenarios de almacén simulado. Recolección sistemática de datos por tarea y por sesión: tiempo de ejecución cronometrado, registro de eventos de error, aplicación del cuestionario SUS al final de cada sesión. Análisis estadístico descriptivo de los resultados y comparación contra los umbrales de referencia definidos en los objetivos.

**Entregables:** Dataset de resultados de pruebas. Análisis de desempeño por subsistema y por tarea. Conclusiones sobre viabilidad técnica y recomendaciones para iteraciones futuras o escalamiento del sistema.

---

*Siguiente: [Marco teórico →]({{ "/docs/01-reporte/08-marco-teorico" | relative_url }})*
