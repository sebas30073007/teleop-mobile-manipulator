---
title: "Justificación"
nav_order: 5
parent: "Reporte"
---

# Justificación

La propuesta se justifica desde tres ejes complementarios: económico, social y técnico. La convergencia de los tres argumentos establece que el proyecto no solo es pertinente como ejercicio académico, sino que responde a una necesidad real con soluciones realizables dentro del estado actual de la tecnología.

## Eje económico: la presión del e-commerce sobre la logística

El mercado de automatización de almacenes proyecta doblar su tamaño entre 2019 y 2026, pasando de $15,000 a $30,000 millones de dólares [4]. Esta expansión está impulsada, en gran medida, por la misma presión que el e-commerce ejerce sobre los ciclos de surtido y los costos de fulfillment. Las empresas que no automatizan parte de sus operaciones enfrentan costos crecientes de personal temporal, mayores tasas de error en surtido y pérdida de competitividad en velocidad de entrega.

Sin embargo, la automatización total —robots industriales, sistemas AS/RS de gran escala— implica inversiones de capital que están al alcance solo de grandes operadores. Las medianas y pequeñas operaciones logísticas, que representan la mayoría del ecosistema en mercados como el mexicano, necesitan soluciones de menor costo inicial y mayor flexibilidad operativa. Una plataforma de teleoperación robótica de propósito específico ofrece exactamente eso: capacidad automatizada para tareas concretas, operada por personal remoto, con un perfil de inversión significativamente menor que una solución de automatización completa.

## Eje social: inclusión laboral como imperativo de diseño

En México, 7.7 millones de personas viven con alguna forma de discapacidad motriz [7][8]. De este universo, el 96% se encuentra en situación de informalidad laboral — no por falta de capacidades cognitivas, sino por ausencia de herramientas de trabajo adaptadas a sus condiciones de movilidad [7]. El diseño de interfaces de teleoperación accesibles no es una consideración secundaria de este proyecto: es uno de sus ejes de justificación principales.

El teletrabajo operativo — donde un operador remoto controla un robot que actúa como proxy físico en el almacén — elimina las barreras de desplazamiento y acceso físico al lugar de trabajo. Si la interfaz es suficientemente accesible e intuitiva, personas con discapacidad motriz pueden ejecutar tareas logísticas desde cualquier ubicación con conectividad básica, incorporándose a cadenas de valor formales sin depender de adaptaciones costosas del entorno físico de trabajo. Esta es la contribución de mayor impacto potencial del proyecto: demostrar que la teleoperación robótica puede ser un mecanismo real de inclusión laboral, no solo una tecnología de mejora productiva.

## Eje técnico: madurez tecnológica y viabilidad del prototipo

La convergencia de tres tecnologías con curvas de madurez favorables — robótica móvil, middleware de comunicación en tiempo real (Python + ZeroMQ) y realidad extendida (XR) — hace viable la construcción de un prototipo funcional dentro del marco de un proyecto terminal universitario. Los costos de los componentes clave han bajado considerablemente en la última década: microcontroladores WiFi de alto rendimiento (ESP32), motores paso a paso con drivers de lazo cerrado (CL57T), y headsets XR de consumo (Meta Quest) hoy ofrecen capacidades que hace cinco años solo estaban disponibles en equipos industriales de costo prohibitivo [6].

El ecosistema de software abierto complementa esta accesibilidad de hardware: MicroPython para ESP32-C3, Python 3.12 en la NUC, Unity, el SDK de Meta XR y las bibliotecas de visión por computadora de código abierto permiten implementaciones robustas sin licencias propietarias. Esto hace que el prototipo desarrollado sea, por diseño, reproducible y extensible — condición indispensable para que un proyecto de investigación académica genere valor más allá de su contexto de desarrollo inmediato.

---

*Siguiente: [Alcance y limitaciones →]({{ "/docs/01-reporte/06-alcance-limitaciones" | relative_url }})*
