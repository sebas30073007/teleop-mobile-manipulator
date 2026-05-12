---
title: "Documentación"
nav_order: 2
has_children: true
permalink: /manual-replica/
---

# Documentación

Este repositorio organiza el proyecto de teleoperación robótica como una guía académica de réplica. La documentación sigue el hilo de trazabilidad: de los requisitos al diseño, del diseño a la implementación, y de la implementación a la validación.

## Cómo leer este manual

1. [Introducción]({{ "/docs/02-manual/01-introduccion" | relative_url }}) — problema que aborda y alcance del sistema
2. [Arquitectura del sistema]({{ "/docs/02-manual/02-arquitectura-general" | relative_url }}) — visión general de subsistemas y flujos de datos
3. Subsistemas (cada uno con Requisitos → Diseño → Implementación → Validación):
   - [Robot AGV]({{ "/docs/02-manual/03-robot-agv/" | relative_url }}) — plataforma móvil, manipulador, electrónica, software
   - [Servidor / NUC]({{ "/docs/02-manual/04-servidor/" | relative_url }}) — middleware ZMQ, percepción
   - [XR Meta Quest]({{ "/docs/02-manual/05-xr-metaquest/" | relative_url }}) — Unity, interfaz, controles
4. [Puesta en marcha]({{ "/docs/02-manual/07-puesta-en-marcha" | relative_url }}) — secuencia de arranque
5. [Trabajo a futuro]({{ "/docs/02-manual/11-pendientes" | relative_url }})

## Alcance de la documentación

Este sitio prioriza la **réplica académica**. No es una guía industrial ni un manual comercial de producto final.
