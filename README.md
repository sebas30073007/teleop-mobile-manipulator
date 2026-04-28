# Teleoperación móvil-manipulador para logística inclusiva

Repositorio de documentación académica para un proyecto universitario de robótica teleoperada con realidad mixta.

## Objetivo académico

Documentar la arquitectura, implementación y validación de una plataforma de teleoperación para réplica académica, diferenciando claramente lo implementado, lo parcial y lo pendiente por documentar.

## Estado actual del proyecto

- **Implementado actualmente:** estructura documental, arquitectura base, integración parcial de robot + control + XR y comunicación ZMQ.
- **Parcialmente implementado:** control completo extremo a extremo y validación consolidada con protocolo formal.
- **Pendiente por documentar:** BOM, esquema eléctrico completo, ensamblaje completo, calibración formal, seguridad formal y medición formal de latencia.

## Arquitectura resumida

```text
Operador
→ Meta Quest / interfaz XR (Unity + Meta XR SDK 83.0)
→ Comunicación ZMQ
→ Computadora de control (Python 3.12)
→ ESP32-C3 (MicroPython)
→ Robot móvil + manipulador + sensores
```

## Tecnologías principales

- Python 3.12
- ZeroMQ (ZMQ)
- ESP32-C3 con MicroPython
- Meta XR SDK 83.0
- Unity
- Jekyll + Just the Docs

## Cómo levantar el sitio de documentación localmente

```bash
bundle install
bundle exec jekyll serve
```

Sitio local esperado: `http://localhost:4000`

## Ruta recomendada de lectura

1. Inicio del sitio.
2. Manual de réplica académica.
3. Arquitectura general.
4. Subsistemas (robot, manipulador, electrónica, ZMQ, control Python, XR).
5. Puesta en marcha, pruebas, calibración, seguridad y troubleshooting.
6. Estado actual y pendientes para réplica completa.

## Advertencia importante

Este repositorio prioriza **réplica académica**. Varias secciones están marcadas como **Pendiente por documentar** para evitar inventar información técnica no disponible.
