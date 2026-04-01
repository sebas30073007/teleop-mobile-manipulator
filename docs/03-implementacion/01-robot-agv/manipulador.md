---
title: "Manipulador"
nav_order: 3
parent: "Robot AGV"
---

# Manipulador

El manipulador es un **brazo de 3 grados de libertad construido desde cero**, diseñado específicamente para tareas de pick-and-place en entornos de logística de e-commerce. Incluye un gripper de accionamiento lineal por cremallera y piñón.

## Diseño y materiales

![Materiales del manipulador]({{ "/assets/img/manipulador_materiales.jpg" | relative_url }})

El diseño prioriza:
- **Rigidez estructural** mediante piezas de acero de 1.2 mm y 0.6 mm cortadas a láser
- **Transmisión por bandas HTD3M** (relación 2.5:1) para reducir el juego angular en las articulaciones
- **NEMA17 con reductor planetario 10:1** en cada articulación para obtener el torque necesario

### Componentes clave

| Componente | Descripción |
|---|---|
| Eslabón 1 | Acero 1.2 mm cortado a láser, transmisión HTD3M 50T (2.5:1) |
| Eslabón 2 | Acero 1.2 mm, transmisión HTD3M 20T con offset |
| Eslabón 3 / muñeca | Acero, transmisión HTD3M |
| Torre base | Acero mecanizado (APOLO) |
| Gripper | Cremallera + piñón, accionado con NEMA17 |
| Actuadores | NEMA17 + reductor planetario 10:1 en cada articulación |
| Rodamientos | Baleros planos de precisión en articulaciones |
| Sensores | Intel RealSense D435i + RPLiDAR C1 (en torre) |

## Manufactura

### Corte láser

Las piezas estructurales principales fueron cortadas en láser a partir de lámina de acero de 1.2 mm (calibre 18) y 0.6 mm. Los archivos DXF de corte están almacenados en `assets/raw_assets/CADs manipulador/DXF/`.

![Manufactura corte láser]({{ "/assets/img/manipulador_corte_laser.jpg" | relative_url }})

{% include video_youtube.html id="HL85R2YZLBA" title="Construcción del manipulador 3DOF — Proyecto Terminal 2026" %}

### Primeras piezas

![Primeras piezas ensambladas]({{ "/assets/img/manipulador_primeras_piezas.jpg" | relative_url }})

## Ensamble

![Ensamble completo del manipulador]({{ "/assets/img/manipulador_ensamble.jpg" | relative_url }})

<!-- Video prueba estática del robot con manipulador — reemplazar YOUTUBE_ID -->
<!-- {% include video_youtube.html id="YOUTUBE_ID" title="Prueba estática — robot móvil con manipulador" %} -->

## Visor 3D

{: .note }
El modelo 3D estará disponible una vez exportado el ensamble desde Autodesk Inventor a formato GLB. Colocar el archivo en `assets/models/manipulador_ensamble.glb` y descomentar la línea siguiente.

<!-- {% include model_viewer.html src="/assets/models/manipulador_ensamble.glb" alt="Ensamble manipulador 3-DOF" %} -->

## CAD y archivos fuente

El proyecto CAD completo (Autodesk Inventor 2024) se encuentra en `assets/raw_assets/CADs manipulador/`. Contiene:
- `Ensamble final.iam` — ensamble completo del manipulador
- `Gripper_0.iam` — subconjunto del gripper
- Archivos `.ipt` individuales para cada pieza
- Archivos DXF de corte láser en `DXF/`
- Archivos STEP de motores y reductores de referencia

## Estado actual

- [x] Diseño CAD completo (Inventor)
- [x] Manufactura de piezas por corte láser
- [x] Ensamble mecánico
- [x] Prueba estática de movimiento (control Arduino)
- [ ] Integración con firmware ROS definitivo
- [ ] Calibración de cinemática inversa
- [ ] Prueba de pick-and-place con carga
