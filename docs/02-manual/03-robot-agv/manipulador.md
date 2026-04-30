---
title: "Manipulador 3DOF"
nav_order: 3
parent: "Robot AGV"
---

# Manipulador 3DOF

## Requisitos

El manipulador debía ejecutar tareas de pick-and-place en entornos de logística de e-commerce. Elementos base:

- Materiales disponibles: lámina de acero calibre 18 (1.2 mm) y calibre 24 (0.6 mm)
- Herramientas disponibles: cortadora láser
- Motores disponibles: NEMA17 (stock en laboratorio)
- Ligero y compacto para montarse sobre la plataforma AGV
- Capacidad de agarre (gripper) para objetos de tamaño mediano


## Diseño

![Manipulador completo — vista lateral]({{ "/assets/img/render.png" | relative_url }})

El brazo cuenta con **3 articulaciones rotacionales** más un **gripper lineal**:

| Componente | Descripción |
|---|---|
| Eslabón 1 | Acero 0.6 mm, transmisión HTD3M 50T (2.5:1) |
| Eslabón 2 | Acero 0.6 mm, transmisión HTD3M 50T (2.5:1) |
| Base / hombro | Acero 1.2 mm, transmisión HTD3M 50T (1:1) |
| Gripper | Cremallera + piñón, motor Pololu con reductor (100:1) |
| Actuadores | NEMA17 + reductor planetario 10:1 + polea HTD3M (2.5:1) |
| Chumaceras | Baleros en cada articulación |
| Sensores montados | Intel RealSense D435i + RPLiDAR C1 |

Principios de diseño:
- **Rigidez estructural** mediante acero cortado a láser
- **Transmisión por bandas HTD3M** para aumentar la capacidad de cargar del robot
- **Reducción compuesta (10:1 × 2.5:1 = 25:1)** para torque suficiente con NEMA17



## Manufactura

### Corte láser

Las piezas estructurales fueron cortadas en láser a partir de lámina de acero. Los archivos DXF están en [`assets/raw_assets/CADs manipulador/DXF/`](https://github.com/sebas30073007/teleop-mobile-manipulator/tree/main/assets/raw_assets/CADs%20manipulador/DXF) del repositorio.

![Manufactura corte láser]({{ "/assets/img/manipulador_corte_laser.jpg" | relative_url }})

{% include video_youtube.html id="HL85R2YZLBA" title="Construcción del manipulador 3DOF — Proyecto Terminal 2026" %}

### Primeras piezas

![Primeras piezas ensambladas]({{ "/assets/img/manipulador_primeras_piezas.jpg" | relative_url }})

## Ensamble

![Ensamble completo del manipulador]({{ "/assets/img/AGV_manipulador completo.png" | relative_url }})


### Gripper


El gripper del manipulador está compuesto por dos pinzas impresas en 3D de color rojo, diseñadas para abrir y cerrar de forma simétrica mediante un mecanismo de piñón-cremallera. En el collage se observan diferentes vistas del sistema: una vista montada sobre el manipulador, una vista superior y una vista frontal del mecanismo.

El accionamiento del gripper se realiza mediante un motor Pololu con reducción mecánica, el cual transmite el movimiento hacia un piñón central. Este piñón engrana con las cremalleras internas de ambas pinzas, permitiendo que se desplacen en sentidos opuestos. La geometría de las pinzas incluye refuerzos internos tipo costilla, lo que permite mantener una estructura ligera sin perder rigidez.

Este diseño fue pensado para tareas de manipulación básica, donde el robot pueda sujetar objetos sin requerir un mecanismo demasiado pesado o complejo. Al estar ubicado en el extremo del segundo eslabón, el gripper representa la herramienta final del manipulador y define directamente la capacidad de interacción física del robot con su entorno.
![Gripper]({{ "/assets/img/Manipulador gripper.png" | relative_url }})

El gripper está controlado por un ESP32-C3 dedicado, conectado directamente a la NUC por USB independiente (COM5). Ver [Controlador de drivers]({{ "/docs/02-manual/03-robot-agv/controlador-cl57t" | relative_url }}) y [Software embebido]({{ "/docs/02-manual/03-robot-agv/software" | relative_url }}).



### Mecanismos de transmisión y soporte


Este collage muestra detalles del sistema de transmisión mecánica del manipulador, principalmente en las zonas donde las poleas, correas y chumaceras permiten transmitir el movimiento de los motores hacia los eslabones. La transmisión por banda dentada permite mover las articulaciones sin colocar todos los motores directamente sobre los ejes finales, ayudando a distribuir mejor el peso del sistema.

En la imagen izquierda se aprecia una de las articulaciones principales del manipulador, donde una polea roja transmite el movimiento hacia el eje de rotación. La chumacera sostiene el eje y evita que este roce directamente con la lámina estructural. Esto permite que el movimiento sea más limpio, estable y con menor fricción.

En la imagen derecha se observa un acercamiento al sistema de polea, banda y rodamiento tensor. El rodamiento funciona como apoyo adicional para mejorar la tensión de la banda y reducir holguras durante el movimiento. Este tipo de solución fue importante para que el manipulador pudiera moverse de forma más controlada, especialmente considerando que la estructura trabaja con varios ejes, bandas y elementos atornillados.

![transmisión lateral y eje rotacional de eslabones]({{ "/assets/img/Mecanismos.png" | relative_url }})



### Eje rotacional de la base del manipulador

El eje rotacional de la base permite que todo el manipulador gire respecto a la plataforma móvil. En la imagen se muestra el conjunto mecánico encargado de generar esta rotación, así como la estructura metálica que soporta el peso del brazo.

La rotación se transmite mediante un motor colocado en la parte posterior del manipulador, usando una reducción por polea y banda. A diferencia de los eslabones, que utilizan una reducción mayor, la base emplea una reducción menor, suficiente para generar el giro del conjunto completo. Esta configuración permite separar el movimiento de orientación del manipulador del movimiento de los eslabones superiores.

También se observa la estructura en forma de “C” que eleva el manipulador sobre la base móvil. Esta pieza fue fabricada con lámina doblada y reforzada, ya que durante las pruebas se identificó que la rigidez era crítica para soportar el peso del manipulador. La doble capa de material ayuda a reducir deformaciones y mejora la estabilidad del sistema durante los movimientos.

El volumen interno de esta estructura también se aprovecha para alojar componentes electrónicos, como drivers CL57T y cableado, reduciendo el ruido visual del robot y optimizando el uso del espacio disponible.


![Base rotatoria — motor y Soporte de base rotatoria]({{ "/assets/img/Eje rotacional.png" | relative_url }})



### Sistema de poleas, correas y sensores de límite

Este collage muestra el sistema principal de poleas y correas encargado de transmitir el movimiento desde los motores hacia los eslabones del manipulador. La arquitectura mecánica utiliza dos motores colocados de forma paralela y simétrica: uno controla el primer eslabón y el otro controla el segundo eslabón mediante una transmisión adicional.

El primer motor transmite el movimiento directamente al primer eslabón. El segundo motor parte desde la misma zona de eje, pero su polea no está unida rígidamente al primer eslabón; esto permite que el movimiento pueda transmitirse de forma independiente hacia el segundo eslabón mediante otra banda que sube hasta la articulación superior. De esta manera, cada grado de libertad conserva su propia transmisión, aunque compartan zonas físicas cercanas dentro de la estructura.

Las imágenes también muestran los sistemas de tensión implementados con rodamientos. Estos tensores ayudan a mantener las bandas con la tensión adecuada y reducen problemas como deslizamiento, holgura o vibraciones. En la zona inferior se observa una barra transversal con rodamientos que sirve como tensor común para los sistemas de transmisión de los eslabones.

En la vista derecha se aprecia uno de los sensores finales de carrera montado cerca del recorrido físico del manipulador. Estos sensores se colocaron en puntos estratégicos para funcionar como referencia de calibración y límite mecánico. Su ubicación permite definir una posición cercana al cero del sistema sin interferir con el movimiento normal del brazo.


![Poleas y correas — vista diagonal]({{ "/assets/img/Poleas.png" | relative_url }})



## CAD y archivos fuente

El proyecto CAD completo (Autodesk Inventor 2026) está en [`assets/raw_assets/CADs manipulador/`](https://github.com/sebas30073007/teleop-mobile-manipulator/tree/main/assets/raw_assets/CADs%20manipulador) del repositorio:

- `Ensamble final.iam` — ensamble completo del manipulador
- `Gripper_0.iam` — subconjunto del gripper
- Archivos `.ipt` individuales por pieza
- Archivos DXF de corte láser en `DXF/`
- Archivos STEP de motores y reductores de referencia

## Validación

| Prueba | Resultado |
|---|---|
| Rangos de movimiento por articulación | ✅ Alcanzados |
| Juego en transmisiones HTD3M | ✅ Sin juego excesivo |
| Velocidad de movimiento rápido | ✅ Funcional |
| Control remoto integrado XR → NUC → manipulador | ⏳ Pendiente |

Ver evidencia completa en [Pruebas y calibración]({{ "/docs/02-manual/03-robot-agv/pruebas" | relative_url }}).
