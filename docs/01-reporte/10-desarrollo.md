---
title: "Desarrollo"
nav_order: 10
parent: "Reporte"
---

## Análisis de tareas logísticas

| Tarea | Descripción | Complejidad | Riesgo | Potencial de teleoperación |
|---|---|---:|---:|---:|
| Recepción y traslado interno | Movimiento de contenedores o unidades dentro del almacén | Media | Media | Alta |
| Surtido asistido | Localización y toma de ítems para pedido | Alta | Media | Media |
| Abastecimiento de estación | Reposición de materiales en zonas de trabajo | Media | Baja | Alta |
| Entrega en punto interno | Transporte a nodo de consolidación/despacho | Baja | Baja | Alta |

![Tabla original]({{ "/assets/img/full-tabla-tareas.png" | relative_url }})

## Arquitectura propuesta
La solución se organiza en tres capas: plataforma robótica (movilidad + manipulación), servidor de coordinación (middleware, percepción, telemetría) e interfaz XR para operación remota. El diseño prioriza modularidad, trazabilidad de datos y seguridad operativa.

## Entregables esperados
- Documento de arquitectura y requerimientos.
- Prototipo integrado robot-servidor-XR.
- Protocolo de pruebas y set de métricas.
- Reporte de validación experimental.
