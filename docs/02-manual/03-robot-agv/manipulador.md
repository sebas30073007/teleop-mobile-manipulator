---
title: "Manipulador 3DOF"
nav_order: 4
parent: "Robot AGV"
---

# Manipulador 3DOF

## Requisitos

El manipulador debía ejecutar tareas de pick-and-place en entornos de logística de e-commerce. Restricciones principales:

- Materiales accesibles: lámina de acero calibre 18 (1.2 mm) y calibre 24 (0.6 mm)
- Herramientas disponibles: cortadora láser
- Motores: NEMA17 (stock en laboratorio)
- Ligero y compacto para montarse sobre la plataforma AGV
- Capacidad de agarre (gripper) para objetos de tamaño mediano

> **Pendiente:** Documentar la carga útil de diseño (gramos) y el alcance máximo en cada articulación.

## Diseño

El brazo cuenta con **3 articulaciones rotacionales** más un **gripper lineal**:

| Componente | Descripción |
|---|---|
| Eslabón 1 | Acero 0.6 mm, transmisión HTD3M 50T (2.5:1) |
| Eslabón 2 | Acero 0.6 mm, transmisión HTD3M 50T (2.5:1) |
| Base / hombro | Acero 1.2 mm, transmisión HTD3M 50T (1:1) |
| Gripper | Cremallera + piñón, motor Pololu con reductor (100:1) |
| Actuadores | NEMA17 + reductor planetario 10:1 + polea HTD3M (2.5:1) |
| Chumaceras | Baleros en cada articulación |
| Sensores montados | Intel RealSense D435i + RPLiDAR C1 (en torre sobre efector) |

Principios de diseño:
- **Rigidez estructural** mediante acero cortado a láser
- **Transmisión por bandas HTD3M** para reducir el juego angular
- **Reducción compuesta (10:1 × 2.5:1 = 25:1)** para torque suficiente con NEMA17

![Materiales del manipulador]({{ "/assets/img/manipulador_materiales.jpg" | relative_url }})

## Manufactura

### Corte láser

Las piezas estructurales fueron cortadas en láser a partir de lámina de acero. Los archivos DXF están en `assets/raw_assets/CADs manipulador/DXF/`.

![Manufactura corte láser]({{ "/assets/img/manipulador_corte_laser.jpg" | relative_url }})

{% include video_youtube.html id="HL85R2YZLBA" title="Construcción del manipulador 3DOF — Proyecto Terminal 2026" %}

### Primeras piezas

![Primeras piezas ensambladas]({{ "/assets/img/manipulador_primeras_piezas.jpg" | relative_url }})

## Ensamble

![Ensamble completo del manipulador]({{ "/assets/img/manipulador_ensamble.jpg" | relative_url }})

> **Pendiente:** Documentar la secuencia de ensamble paso a paso con orden de montaje de baleros, poleas y bandas.

## CAD y archivos fuente

El proyecto CAD completo (Autodesk Inventor 2026) está en `assets/raw_assets/CADs manipulador/`:

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
