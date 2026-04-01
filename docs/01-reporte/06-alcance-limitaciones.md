---
title: "Alcance y limitaciones"
nav_order: 6
parent: "Reporte"
---

# Alcance y limitaciones

## Alcance del prototipo

El sistema desarrollado cubre la integración completa de tres subsistemas en un entorno controlado de laboratorio, abarcando desde el diseño mecánico y electrónico del robot hasta la interfaz de usuario XR y el middleware de coordinación.

**Plataforma robótica:** Un robot móvil con base de tracción diferencial — dos motores paso a paso NEMA23 con drivers de lazo cerrado CL57T — y un brazo manipulador de dos grados de libertad (articulaciones de hombro y codo), capaz de navegar en superficies planas interiores y realizar operaciones de pick-and-place con objetos de geometría simple y peso moderado.

**Servidor de coordinación:** Un nodo central basado en ROS2 que gestiona la comunicación bidireccional entre la plataforma robótica y la interfaz XR, procesa el stream de cámara para retroalimentación visual al operador, y ejecuta los comandos de movimiento en tiempo real sobre red local (WiFi/LAN).

**Interfaz XR:** Una aplicación desarrollada en Unity para Meta Quest que permite al operador visualizar el entorno del robot en primera persona, emitir comandos de movimiento y manipulación mediante los controladores del headset, y recibir retroalimentación de estado del sistema en tiempo real.

El alcance incluye también: el diseño del protocolo de pruebas, la definición de métricas de evaluación, y la ejecución de sesiones de validación experimental con las métricas cuantificadas. El resultado final es un prototipo integrado funcional, un conjunto de datos de desempeño, y un reporte de validación con conclusiones y recomendaciones.

## Limitaciones del prototipo actual

**Conectividad:** El sistema opera sobre red local (WiFi o Ethernet). No se aborda el rendimiento en redes públicas (4G/5G) ni la operación bajo conectividad limitada o intermitente. Los resultados de latencia y control son específicos a condiciones de red local controlada.

**Entorno físico:** El robot está diseñado para operar en superficies planas, interiores y estructuradas, sin obstáculos dinámicos no controlados. No se contempla navegación en exteriores, escalones, rampas o superficies irregulares.

**Capacidad de manipulación:** El brazo manipulador está diseñado para objetos ligeros de geometría regular (cajas, recipientes). No se aborda manipulación de precisión fina, objetos frágiles, geometrías complejas ni pesos que superen el par máximo de los actuadores seleccionados.

**Usuarios y muestra:** Las sesiones de validación se realizan con un conjunto reducido de usuarios en entorno de laboratorio. Los resultados son indicativos de viabilidad técnica y usabilidad preliminar; no son estadísticamente generalizables a poblaciones más amplias sin estudios adicionales.

**Certificaciones y seguridad:** El prototipo es un sistema experimental de investigación. No sigue procesos de certificación de seguridad funcional (ISO 10218, ISO/TS 15066 para robots colaborativos) ni cumple estándares de producto comercial. Su operación está restringida a entornos controlados con supervisión directa.

---

*Siguiente: [Metodología →]({{ "/docs/01-reporte/07-metodologia" | relative_url }})*
