---
title: "Implementación"
nav_order: 3
has_children: true
permalink: /implementacion/
---

# Implementación técnica

## Arquitectura del sistema

### Visión general
El sistema integra un robot móvil-manipulador, un servidor de coordinación y una interfaz XR para teleoperación. La arquitectura prioriza desacoplamiento por módulos y observabilidad de estado.

![Arquitectura del sistema]({{ "/assets/img/full-arquitectura-sistema.png" | relative_url }})

### Flujos de datos
- Telemetría del robot hacia servidor.
- Comandos de control desde XR al servidor y de servidor al robot.
- Datos de percepción para asistencia de operación y registro.

### Comunicación
- Mensajería de control en red local.
- Sincronización de estado para interfaz XR.
- Registro de eventos para análisis posterior.

### Seguridad
- Segmentación básica de red para componentes críticos.
- Control de acceso por sesión de operación.
- Registro de trazas para auditoría técnica.

### Roadmap
1. Integración base de comunicaciones.
2. Estabilización de operación teleasistida.
3. Validación de desempeño y usabilidad.

## Módulos
- [Robot AGV + manipulador]({{ "/docs/03-implementacion/01-robot-agv/" | relative_url }})
- [Servidor]({{ "/docs/03-implementacion/02-servidor/" | relative_url }})
- [XR Meta Quest]({{ "/docs/03-implementacion/03-xr-metaquest/" | relative_url }})
