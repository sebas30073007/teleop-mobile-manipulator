# James Dyson Award 2026 — Entry Draft (English)

> Borrador para el formulario en línea de jamesdysonaward.org.
> Deadline: **15 de julio de 2026** — meta segura: enviar el 14 de julio.
> Los límites de palabras exactos aparecen en el formulario al registrarte; cada
> sección aquí está escrita en ~120–180 palabras para que recortar sea fácil.
> Registro: https://www.jamesdysonaward.org/es-ES/register/ (México, con
> comprobante de inscripción de la Ibero).

---

## Project name

**TELMA — a mixed-reality avatar robot for accessible remote work**

> Alternativas si TELMA no te convence: "ReachOut", "Presence". El nombre debe
> ser corto y citable en medios (tip oficial del JDA). "TELMA" =
> TELeoperated Mobile mAnipulator, y suena a nombre de persona — fácil de
> recordar.

---

## What it does

TELMA is a teleoperated mobile manipulator that lets a person do physical
warehouse work from anywhere — including people with lower-limb motor
disabilities, who face some of the highest unemployment rates. Wearing a Meta
Quest headset, the operator sees through the robot's camera in mixed reality,
drives its wheeled base with a joystick, and controls a 3-axis steel arm and
gripper to pick and place real objects. Everything runs over standard WiFi
with a communication design that keeps control commands responsive even while
streaming video and 3D LiDAR maps: measured round-trip latency stays below
72 ms in the 95th percentile with zero lost commands, well inside the 100 ms
threshold where teleoperation starts to degrade.

---

## Your inspiration

Local distribution and micro-fulfillment warehouses are the most
labor-intensive and costly link in e-commerce logistics, yet they are
precisely the environments where full robot autonomy keeps failing: layouts
change daily and humans share every aisle. At the same time, in Mexico,
people with lower-limb motor disabilities face enormous barriers to
employment — most physical jobs are simply closed to them, and warehouse
work is the clearest example. Teleoperation connects both problems: if the
physically demanding part of the job can be done through a robot, the job
becomes a seated, remote job that anyone with full use of their hands and
head can do. We set out to build that bridge with accessible hardware: a
rehabilitated mobile platform, laser-cut steel, catalog motors, and our own
open motor-driver electronics — proving the concept does not need a
six-figure robot.

---

## How it works

The operator wears a Meta Quest 3 running our Unity app in mixed-reality
passthrough. Three floating panels show live 640×480 video, a 2D LiDAR
occupancy map, robot telemetry, and sliders for the arm; the right joystick
drives the base. A "ghost robot" 3D preview shows the commanded arm pose
before it is sent. The headset talks over WiFi to an edge PC on the robot
using ZeroMQ messaging, with commands, telemetry, video, and 3D spatial data
separated on four independent channels so heavy sensor streams never delay a
command. The edge PC runs the perception services (RGB-D camera with optional
YOLOv8 pose/segmentation modes, 360° LiDAR) and forwards motion commands to
embedded ESP32-C3 modules: our custom-designed H-bridge boards drive the
differential base over an I²C master–slave bus, closed-loop stepper drivers
move the three arm joints, and a dedicated microcontroller runs the
rack-and-pinion gripper. Firmware boots disarmed, requires an explicit arm
command, and a 350 ms watchdog plus an emergency stop button halt everything
instantly.

---

## Design process

We designed simulation-first to avoid wasting material and time. Every
circuit was simulated in Falstad, then validated on a protoboard, and only
then committed to a PCB: the motor-driver board went through
schematic → two-layer layout in KiCad → fabrication → hand soldering, and
carries design decisions born from earlier failures, like optocoupler
isolation between logic and power and a firmware state machine that boots
disarmed. The mechanical arm followed the same loop in Autodesk Inventor:
parts were designed, laser-cut from sheet steel, assembled, and redesigned —
the L-brackets joining base, first link, and motor took several versions, and
when tight bends exceeded what our manual bender could do safely, we split
parts in two and bolted them. Testing revealed sheet-metal flexibility
perpendicular to the load axis, which we countered with doubled material in
the critical C-shaped riser. The mixed-reality interface went through two
full iterations before the final three-panel design, and we validated the
communication layer with a 7,350-probe latency study across seven sensor-load
conditions.

---

## How is it different

Immersive teleoperation systems exist in research labs, but they typically
treat the wireless link as a given — and they run on robots costing tens of
thousands of dollars. TELMA is different in three ways. First, the
communication layer is engineered, not assumed: traffic is isolated per
function on independent channels, and the operator can select camera and
LiDAR modes at runtime so bandwidth is spent only on what the task needs; we
measured that command latency stays interactive even under maximum sensor
load. Second, it is radically affordable and reproducible: a rehabilitated
differential platform, laser-cut steel links, stock NEMA17 motors, and our
own open-hardware motor drivers, with all CAD, PCB files, and firmware
documented publicly. Third, it is designed around the operator: everything is
controlled seated, using only head and hands, which makes physically
demanding warehouse work accessible to people with lower-limb motor
disabilities rather than replacing workers with full autonomy.

---

## Future plans

The immediate step is completing end-to-end validation of the integrated arm
under real pick-and-place tasks, followed by user trials with seated
operators, including people with lower-limb motor disabilities, measuring
task performance and comfort. On the technical side we will deploy the
compact spatial encoding we already prototyped (which compresses LiDAR maps
up to 460×, freeing bandwidth for multiple robots on one network), instrument
the radio layer to harden the system against WiFi interference, and explore
one-operator/multiple-robot supervision. The long-term goal is a pilot in a
local micro-fulfillment warehouse in Mexico City, operated remotely by
workers who today are excluded from these jobs. The latency evaluation is
being prepared for submission to an IEEE conference.

---

## Awards (optional field)

None yet. (Si el paper es aceptado antes de que anuncien resultados
nacionales, se puede mencionar en actualizaciones de prensa, no aquí.)

---
---

# Material de apoyo — checklist

## Imágenes (máx. 5, 3 MB c/u)

| # | Imagen sugerida | Fuente en el repo |
|---|---|---|
| 1 | Foto héroe: robot completo (AGV + brazo + gripper) | `assets/img/AGV_manipulador completo.png` |
| 2 | Collage proceso CAD: Inventor render + piezas cortadas + ensamble | `assets/img/render.png` + `manipulador_corte_laser.jpg` + `manipulador_primeras_piezas.jpg` |
| 3 | Collage electrónica: Falstad/esquemático → protoboard → PCB KiCad → placa ensamblada instalada | `assets/img/Esquematico PuenteH.png` + `PCB 2 layers PuenteH.png` + `Manofactura JLCPCB PuenteH.png` + `Puente H e instalación.png` |
| 4 | Interfaz MR en el Quest (tres paneles + video + LiDAR) | `assets/img/UI MixReality.png` |
| 5 | Operador usando el sistema / robot en acción (pick-and-place o navegación) | foto nueva o frame del video |

> Tip JDA: los collages cuentan más historia por imagen. Verificar peso <3 MB
> (exportar JPEG ~85%).

## Video (<3 min, YouTube/Vimeo, opcional pero muy recomendado)

Guion sugerido (estructura problema → proceso → demo):

1. **0:00–0:20** El problema: trabajo de almacén inaccesible para personas
   con discapacidad motriz; autonomía total falla en espacios compartidos.
2. **0:20–1:20** Proceso iterativo (la parte que el jurado pondera):
   simulaciones Falstad → protoboard → PCB KiCad; Inventor → corte láser →
   rediseños (piezas L); iteraciones de la interfaz MR. Usar clips ya
   existentes (video de construcción del manipulador, ID YouTube `HL85R2YZLBA`).
3. **1:20–2:30** Demo: operador sentado con el Quest manejando el robot —
   conducción, brazo, gripper, e-stop. Mostrar la vista desde dentro del
   headset (grabación de pantalla del Quest).
4. **2:30–3:00** Cierre: costo accesible, hardware abierto, visión del
   trabajo remoto inclusivo.

## Registro — pasos

1. Crear cuenta en jamesdysonaward.org (país: México).
2. Subir comprobante de estudiante (constancia de inscripción o credencial
   vigente de la Ibero).
3. Llenar el formulario con las secciones de este borrador (ajustar a los
   límites de palabras que marque el formulario).
4. Subir imágenes (1 mínimo, 5 máximo) y enlazar el video de YouTube.
5. Enviar **a más tardar el 14 de julio** (la zona horaria del cierre del 15
   no es consistente entre fuentes: la ficha Ibero dice 17:00 CDMX, la prensa
   dice 23:59 PST).

## Nota legal

Al enviar, la entrada se hace **pública** en el sitio del JDA (sin
confidencialidad). Conservas el 100% de la propiedad intelectual, pero la
publicación cuenta como divulgación previa para patentes (MX/US: 12 meses de
gracia; UE/Japón: sin gracia). El proyecto ya es público en GitHub Pages, así
que el riesgo incremental es bajo.

## Referencias — ganadores de años anteriores

Cada página de proyecto en jamesdysonaward.org muestra la entrada real tal
como se llenó el formulario (descripción, inspiración, cómo funciona, proceso
de diseño, diferenciación, planes) + sus imágenes y video. Es la mejor guía
de tono y extensión.

- Archivo completo de ganadores por año (globales + nacionales + finalistas):
  https://www.jamesdysonaward.org/past-winners/

**México:**
- Signal Glove (nacional MX 2024, Héctor Hernández, IPN — guante traductor LSM):
  https://www.jamesdysonaward.org/en-US/2024/project/signal-glove
  Comunicado IPN: https://www.ipn.mx/CCS/comunicados/ver-comunicado.html?y=2024&n=41&t=6
- OpticalApp (nacional MX 2025, Alejandro Aguilar, SABES Celaya — diagnóstico ocular con IA):
  https://mexiconewsdaily.com/news/mexican-student-wins-james-dyson-national-award-for-eye-disease-detection-app/
  (página JDA: buscar "OpticalApp" en past-winners)

**Comparables directos (robótica / accesibilidad / hardware iterativo):**
- Sole (nacional EE.UU. 2025 — dispositivo robótico vestible para foot drop)
- Polyformer (Sustentabilidad 2022 — botellas PET a filamento 3D; historia maker iterativa)
- The Life Chariot (Humanitario 2023 — remolque-ambulancia todoterreno)
- SmartHEAL (Internacional 2022): https://www.jamesdysonaward.org/2022/project/smartheal/

**Ganadores globales recientes:**
- OnCue (Médico 2025 — teclado para Parkinson) y WaterSense (Sustentabilidad
  2025): https://www.jamesdysonaward.org/2025/project/watersense
- Athena y airXeed Radiosonde (2024)
- The Golden Capsule (Internacional 2023):
  https://www.jamesdysonaward.org/2023/project/the-golden-capsule
- Nacionales 2025 (los 28 países): https://www.dyson.co.uk/discover/sustainability/james-dyson-award/james-dyson-award-2025-national-winners
- Nacionales 2024: https://www.dyson.co.uk/discover/sustainability/james-dyson-award/james-dyson-award-2024-national-winners

**Videos (YouTube):**
- Ganadores globales 2025: https://www.youtube.com/watch?v=V2u3pxY9lZ0
- Anuncio Top 20 2025: https://www.youtube.com/watch?v=trx32XdJvOU
- Playlist oficial JDA: https://www.youtube.com/playlist?list=PLpBQHVUlKs3rm5kBoO22ufn2yWJiiQkuP
- Playlist James Dyson Foundation: https://www.youtube.com/playlist?list=PLGDt1rpYvtbnafUgb8c-dxUdU7TDtcSHp
- Ejemplo de video de ganador nacional (Revr, Australia 2023):
  https://www.youtube.com/watch?v=92FjMMXXLGs
