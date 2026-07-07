---
title: "Inicio"
nav_order: 1
---

# Desarrollo de un sistema robótico de operación remota orientado a tareas logísticas, para el teletrabajo de personas con discapacidad motriz

Bienvenido al sitio de documentación del proyecto terminal de:

**Sebastián Méndez Villegas** — Ingeniería en Mecatrónica y Sistemas Ciberfísicos

Este proyecto terminal se desarrolló con el apoyo de Santiago Cuesta Machuca (Ingeniería en Mecatrónica y Producción), el acompañamiento técnico del Mtro. Joel Arango, especialista en tecnologías de Realidad Mixta, Extendida y Virtual (MR/XR/VR), y la asesoría principal del Dr. Huber Girón, director de este proyecto.

![Robot completo con manipulador montado]({{ "/assets/img/PROYECTO.png" | relative_url }})

## ¿Qué es este proyecto?

Es una plataforma de teleoperación para robot móvil con manipulador, operada desde interfaz XR en Meta Quest.

## ¿Qué problema busca resolver?

Las tareas logísticas en centros de distribución local son el punto que más costo representa dentro del envio de cualquier mercancia. La teleoperación busca habilitar operación remota con apoyo de interfaz inmersiva para personas con discapacidad motriz en miembros inferiores (sector poblacional con gran tasa de desempleo).

## Índice del sitio

### Reporte

1. [Contexto]({{ "/docs/01-reporte/01-contexto" | relative_url }})
2. [Problemática]({{ "/docs/01-reporte/02-problematica" | relative_url }})
3. [Pregunta de investigación]({{ "/docs/01-reporte/03-pregunta-investigacion" | relative_url }})
4. [Objetivos]({{ "/docs/01-reporte/04-objetivos" | relative_url }})
5. [Justificación]({{ "/docs/01-reporte/05-justificacion" | relative_url }})
6. [Alcance y limitaciones]({{ "/docs/01-reporte/06-alcance-limitaciones" | relative_url }})
7. [Metodología]({{ "/docs/01-reporte/07-metodologia" | relative_url }})
8. [Marco teórico]({{ "/docs/01-reporte/08-marco-teorico" | relative_url }})
9. [Cronograma]({{ "/docs/01-reporte/09-cronograma" | relative_url }})
10. [Desarrollo]({{ "/docs/01-reporte/10-desarrollo" | relative_url }})
11. [Referencias]({{ "/docs/01-reporte/11-referencias" | relative_url }})

### Documentación (manual de réplica)

1. [Introducción]({{ "/docs/02-manual/01-introduccion" | relative_url }})
2. [Arquitectura del sistema]({{ "/docs/02-manual/02-arquitectura-general" | relative_url }})
3. [Robot AGV]({{ "/docs/02-manual/03-robot-agv/" | relative_url }})
   - [Sistemas embebidos]({{ "/docs/02-manual/03-robot-agv/sistemas-embebidos" | relative_url }})
     - [Puente H]({{ "/docs/02-manual/03-robot-agv/electronica" | relative_url }})
     - [Controlador de drivers (CL57T)]({{ "/docs/02-manual/03-robot-agv/controlador-cl57t" | relative_url }})
     - [Controlador del gripper]({{ "/docs/02-manual/03-robot-agv/controlador-gripper" | relative_url }})
   - [Plataforma móvil]({{ "/docs/02-manual/03-robot-agv/plataforma-movil" | relative_url }})
   - [Manipulador 3DOF]({{ "/docs/02-manual/03-robot-agv/manipulador" | relative_url }})
   - [Software embebido]({{ "/docs/02-manual/03-robot-agv/software" | relative_url }})
   - [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }})
4. [Servidor / NUC]({{ "/docs/02-manual/04-servidor/" | relative_url }})
   - [Middleware ZMQ]({{ "/docs/02-manual/04-servidor/middleware" | relative_url }})
   - [Percepción]({{ "/docs/02-manual/04-servidor/percepcion" | relative_url }})
   - [Pruebas Servidor]({{ "/docs/02-manual/04-servidor/pruebas" | relative_url }})
5. [XR Meta Quest]({{ "/docs/02-manual/05-xr-metaquest/" | relative_url }})
   - [Unity y comunicación ZMQ]({{ "/docs/02-manual/05-xr-metaquest/unity" | relative_url }})
   - [Interfaz y controles]({{ "/docs/02-manual/05-xr-metaquest/interfaz" | relative_url }})
   - [Pruebas XR]({{ "/docs/02-manual/05-xr-metaquest/pruebas" | relative_url }})
6. [Protocolo WF-IoT: Latencia MR–Edge]({{ "/docs/wfiot_latency_test_protocol" | relative_url }})
7. [Puesta en marcha]({{ "/docs/02-manual/07-puesta-en-marcha" | relative_url }})
8. [Seguridad]({{ "/docs/02-manual/08-seguridad" | relative_url }})
9. [Troubleshooting]({{ "/docs/02-manual/09-troubleshooting" | relative_url }})
10. [Trabajo a futuro]({{ "/docs/02-manual/11-pendientes" | relative_url }})
11. [Anexos y referencias]({{ "/docs/02-manual/12-anexos" | relative_url }})

### English

- [English version of this site]({{ "/en/" | relative_url }}) — full translation of the report and the replication manual
