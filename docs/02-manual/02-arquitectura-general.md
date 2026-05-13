---
title: "Arquitectura del sistema"
nav_order: 2
parent: "Documentación"
---

# Arquitectura del sistema

El proyecto se compone de dos elementos principales: **el robot AGV con manipulador** y **la aplicación XR en Meta Quest**. La aplicación en los lentes permite operar el robot, visualizar información de sensores y decidir qué datos deben enviarse desde el robot para evitar transmitir información innecesaria.

En términos generales, la arquitectura funciona así:

![Arquitectura]({{ "/assets/img/Diagrama general.png" | relative_url }})


La idea central del sistema es que la **NUC (cerebro del robot) actúa como coordinador**, mientras que otros subsistemas ejecutan tareas de bajo nivel, como control de motores, PWM, rampas, señales de drivers y rutinas de calibración. Esto permite que los comandos enviados desde la interfaz XR sean simples y que la complejidad del movimiento se resuelva dentro del robot.

## Diagrama general

![Detalle]({{ "/assets/img/Arquitectura del sistema.png" | relative_url }})


## Interfaz XR en Meta Quest

La interfaz de usuario se ejecuta en los lentes Meta Quest mediante una aplicación desarrollada en Unity. Desde esta interfaz el operador puede ver el estado del robot y enviar comandos de operación.

Los elementos principales de la interfaz son:

| Elemento | Función |
|---|---|
| Cuadro de video | Muestra el streaming de la cámara del robot. |
| Panel de LiDAR | Visualiza información espacial generada por el RPLiDAR. |
| Botones de modo | Permiten solicitar qué tipo de información debe enviar el robot. |
| Controles de movimiento | Envían comandos de velocidad. |
| Controles del manipulador | Envían referencias de ángulo para los ejes del brazo. |

La Meta Quest no recibe todos los datos todo el tiempo. El operador puede solicitar distintos modos de transmisión. Por ejemplo, en el caso del LiDAR, la interfaz puede pedir información en modo **panorama**, **medio** o **detallado**. De esta forma, el robot envía únicamente la resolución necesaria para la tarea actual.

También es posible activar o cancelar el streaming de video desde la interfaz XR. Esto ayuda a reducir carga de red cuando el operador no necesita visualizar la cámara en tiempo real.

## Comunicación ZMQ

La comunicación principal entre la Meta Quest y la NUC se realiza mediante **ZMQ** sobre WiFi. El sistema separa los tipos de información en canales distintos para mantener ordenado el flujo de datos.

| Canal | Dirección | Contenido |
|---|---|---|
| Video | NUC → Meta Quest | Frames de cámara comprimidos para visualización en XR. |
| Sensores / estado | NUC → Meta Quest | Información de LiDAR, estado del sistema, confirmaciones de modo y telemetría. |
| Comandos | Meta Quest → NUC | Órdenes para movimiento, manipulador, video y modos de sensores. |

Esta separación permite que el video, los sensores y los comandos no dependan de un solo flujo. Así, si se reduce o desactiva el video, los comandos de control y la información de estado pueden seguir funcionando.

## NUC embarcada

La NUC Intel i7 es la computadora principal del robot. Su función es recibir comandos desde la Meta Quest, coordinar los sensores y comunicarse con la electrónica embebida.

La NUC está conectada por USB a:

- **RPLiDAR C1**, usado para obtener información del entorno en 2D.
- **Cámara Intel RealSense**, usada para video y percepción RGB-D.
- **Módulo puente H maestro**, encargado de conectar la computadora con la red de placas embebidas.
- **Gripper ESP32-C3**, conectado directamente a la NUC por un canal serie independiente (USB) para el control y lectura de estado del gripper.

La NUC no controla directamente todos los detalles eléctricos del robot. En lugar de eso, envía instrucciones más simples a los módulos ESP32-C3. Por ejemplo, puede indicar una velocidad deseada o un ángulo objetivo, mientras que las placas se encargan de traducir eso a señales eléctricas específicas.

## Red embebida del robot

El robot cuenta con cuatro placas diseñadas para este proyecto:

1. **Puente H maestro**  
   Recibe comandos desde la NUC por USB y controla uno de los motores de tracción. Además, coordina la comunicación I2C con las demás placas.

2. **Puente H esclavo**  
   Se comunica con el maestro por I2C y controla el segundo motor de tracción. Ejecuta tareas locales como PWM y rampas de aceleración.

3. **Controlador de drivers NEMA 17**  
   Controla tres drivers externos del manipulador mediante señales **PUL**, **DIR** y **ENABLE**. También integra entradas digitales pensadas para finales de carrera y rutinas de calibración.

4. **Gripper ESP32-C3**  
   Placa dedicada al gripper, conectada directamente a la NUC por USB (canal serie independiente al del maestro). Reporta estado en tiempo real (posición en mm, ocupado, calibrado) y recibe comandos de posición desde la NUC.

El puente H tiene un selector físico tipo DIP switch que permite configurar distintos modos de operación. Entre ellos se contemplan modos como maestro, esclavo 1, esclavo 2 y esclavo 3. Además, la placa fue pensada para soportar diferentes formas de comunicación, como USB/UART, I2C, Bluetooth, módulo Bluetooth externo y WiFi.

En la configuración actual, el módulo maestro está conectado a la NUC y las demás placas funcionan como esclavas dentro del bus I2C.

## Control del manipulador

El manipulador utiliza tres motores NEMA 17 controlados por drivers externos. La placa dedicada al manipulador genera las señales necesarias para cada eje y permite ejecutar movimientos de forma más estructurada.

El sistema contempla finales de carrera para apoyar procesos de calibración. La placa también incluye un botón físico de prueba que puede ejecutar una rutina de búsqueda de cero. Una vez calibrado el manipulador, los movimientos se realizan dentro de los rangos máximos definidos para cada articulación.

Esto permite que desde la Meta Quest no sea necesario enviar pulsos individuales ni lógica de bajo nivel. La interfaz únicamente envía referencias de movimiento, y la electrónica del robot se encarga de ejecutar la acción de manera controlada.

## Flujo de operación

Un ciclo típico de operación ocurre de la siguiente forma:

1. El operador usa la Meta Quest para activar video, seleccionar resolución de LiDAR o mover el robot.
2. La aplicación XR envía un comando ZMQ hacia la NUC.
3. La NUC interpreta el comando y decide si debe cambiar un modo de sensor, transmitir video o enviar una orden a las placas embebidas.
4. Si el comando involucra movimiento, la NUC lo envía al módulo maestro.
5. El maestro ejecuta su parte del control y, si es necesario, distribuye instrucciones por I2C hacia el puente H esclavo o el controlador del manipulador.
6. Los sensores capturan información del entorno y la NUC envía de regreso a la Meta Quest únicamente los datos solicitados.

## Criterio de diseño

La arquitectura busca dividir responsabilidades de forma clara:

- **Meta Quest:** operación, visualización y selección de modos.
- **NUC:** coordinación general, sensores, streaming y comunicación ZMQ.
- **ESP32-C3:** control embebido de bajo nivel.
- **Placas diseñadas:** adaptación eléctrica, control de motores y señales para drivers.
- **Sensores:** percepción del entorno mediante LiDAR y cámara RGB-D.

Esta división hace que el sistema sea más modular. La interfaz XR puede mantenerse simple, la NUC puede enfocarse en comunicación y percepción, y las placas embebidas pueden resolver el control eléctrico y mecánico de forma local.
