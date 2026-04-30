---
title: "Interfaz y controles"
nav_order: 2
parent: "XR Meta Quest"
---

# Interfaz y controles

La aplicación Unity se ejecuta en modo passthrough MR sobre el Meta Quest 3. Un **canvas world-space flotante** frente al operador agrupa todos los controles en tres paneles. El operador interactúa con **ray interaction** usando los controladores del headset.

![Vista de la interfaz de teleoperación en realidad mixta]({{ "/assets/img/UI MixReality.png" | relative_url }})

---

## Diseño general — tres paneles

| Panel | Posición | Función |
|---|---|---|
| **Panel izquierdo** | Izq. | Estado de conexión, controles de cámara, stop de emergencia |
| **Panel central** | Centro | Stream de video principal + grid LiDAR 2D |
| **Panel derecho** | Der. | Sliders de manipulador y gripper, rotación de cámara |

Los streams inactivos **no se transmiten** desde la NUC — la UI pide selectivamente lo que necesita.

---

## Panel izquierdo

### StatusPanel — estado del sistema

El `RobotStatusPanel` se refresca a ~5 Hz desde el tópico `stat` de ZMQ `:5001`.

| Campo | Contenido |
|---|---|
| Robot | `Connected` / `Disconnected` |
| Target IP | IP de la NUC (configurable con el teclado) |
| My IP | IP del headset en la red local |
| Mode | Modo de cámara y LiDAR activos |
| FPS | Cuadros por segundo del video |
| Res | Resolución del frame recibido |
| Camera OK | Estado del sensor RealSense D435i |
| Lidar OK | Estado del RPLiDAR C1 |

### Controles de cámara

Dropdown (`CameraModeDropdownController`) para seleccionar el procesamiento de imagen en NUC:

| Opción | Comportamiento en NUC |
|---|---|
| Normal | Stream RGB estándar |
| Pose | RGB con detección de pose (YOLOv8 nano) |
| Segment | RGB con segmentación semántica (YOLOv8 nano-seg) |
| Off | Cámara deshabilitada |

### Emergency Stop

Botón rojo que envía `stop_all` + `master_disarm` a la NUC. Detiene toda la locomoción y pone los motores en `DISARMED` de inmediato.

### Configuración de IP

Teclado numérico virtual (`IpKeypadController`) que aparece al hacer click sobre el campo de IP en el StatusPanel. Permite cambiar la IP de la NUC sin quitar el headset:

1. Apuntar al campo IP con el ray y hacer click
2. El teclado flota frente al operador
3. Introducir la nueva IP y confirmar con **Apply**
4. `NucIpPanelController` llama `Reconnect()` en todos los sockets ZMQ

La IP se persiste entre sesiones en `PlayerPrefs` (clave `"NUC_IP"`).

---

## Panel central

### VideoPanel — stream principal

| Parámetro | Valor |
|---|---|
| Resolución | 640×480 px |
| Tasa de cuadros | ~30 fps |
| Transporte | JPEG comprimido, ZMQ `:5555` tópico `video_rgb` |
| Latencia objetivo | < 150 ms extremo a extremo |

{: .warning }
Resoluciones mayores a 640×480 causan inestabilidad (frames en blanco, drops de FPS). No subir por encima de este límite.

### LiDAR 2D — grid de ocupación

El `ZmqLidarGridView` suscribe al tópico `lidar_grid` en `:5001` y renderiza el grid como `Texture2D` en el `LidarPanel`.

Convención de colores:
- **Blanco** — espacio libre / transitable
- **Negro** — obstáculo o zona no transitable
- **Verde** — posición del robot en el grid
- **Azul** — dirección frontal del robot

Dropdown de modo (`LidarModeDropdownController`):

| Modo | Radio | Grid | Tamaño de punto |
|---|---|---|---|
| Detail | 1 m | 200×200 | 3×3 px |
| Medium | 2 m | 400×400 | 5×5 px |
| Panorama | 3 m | 600×600 | 7×7 px |
| Off | — | Sin transmisión | — |

Resolución de celda: 1 cm fijo. Tasa de actualización: ~12 Hz.

---

## Panel derecho

### Control de manipulador y gripper

El `ManipulatorUIController` gestiona 4 sliders independientes. Cuando el modo manipulador está activo, cada slider mueve su articulación al soltar (**Implement** envía todos al mismo tiempo) o individualmente según la configuración.

| Control | Articulación | Rango |
|---|---|---|
| Base | Rotación de la base | −80° a +80° |
| Joint Elbow 1 (Codo) | Articulación del codo | 0° a 136.5° |
| Joint Wrist 1 (Muñeca) | Orientación de la muñeca | −220° a 0° |
| Gripper | Apertura de la pinza | 0 mm (cerrado) a 80 mm (abierto) |

**Ghost robot**: un modelo 3D visual (`SimpleArm3DOF`) muestra la pose deseada en tiempo real mientras se ajustan los sliders, antes de enviar el comando.

**Botón Home**: envía `manip_home` → `HOME_ALL` en el controlador CL57T (ejecuta rutina de homing desde el headset).

**Botón Implement**: envía la pose completa en un solo mensaje `POSE base codo muneca` + `gripper_cmd mm`.

### Control de base — `BaseCameraDirectControl.cs`

Slider en modo "base/cámara" que envía `base_joint_cmd` continuamente a la NUC para rotar la base del manipulador de forma independiente.

---

## Drive teleop — joystick derecho

El `QuestMobileDriveTeleop` lee el `Primary2DAxis` del controlador derecho y lo convierte en velocidades diferenciales:

```
joystick.y (±1) → v (avance/retroceso)
joystick.x (±1) → w (giro)

left  = clamp(v - w, -255, 255)
right = clamp(v + w, -255, 255)
```

| Parámetro | Valor |
|---|---|
| Frecuencia de envío | 15 Hz |
| Deadzone | 0.18 (18 % del rango total) |
| Velocidad máxima | ±255 (raw) → ±70 % duty cycle en hardware |
| Watchdog en NUC | 350 ms sin comando → stop automático |

El joystick solo es activo cuando el modo "Mobile" está habilitado en `ControlModeState`.

---

## Gestión de modos de control — `ControlModeState.cs`

Los tres modos de control son **exclusivos** (solo uno activo a la vez). El `ControlModeState` gestiona los toggles y arma/desarma el robot según el modo activo:

| Toggle | Activa | Arma/Desarma |
|---|---|---|
| Mobile | Drive teleop (joystick) | Arm → habilita motores de tracción |
| Manip | Sliders de manipulador + gripper | Arm → habilita CL57T |
| Base | Slider de base (rotación del brazo) | — |

Al desactivar todos los modos: envía `stop_all` + `master_disarm`.

---

## LiDAR 3D inmersivo

El `Lidar3DSceneController` activa visualizaciones en espacio 3D usando los datos de `:5007`:

| Modo | Qué muestra |
|---|---|
| Walls | Segmentos de pared como cubos 3D (altura 1.2 m, grosor 5 cm) |
| Points | Nube de puntos del LiDAR (partículas cyan, máx. 4 000) |
| Both | Ambos simultáneamente |
| Off | Sin visualización 3D |

Los datos viajan en protocolos binarios con magic bytes (`WSNP`, `WDEL`, `LPSN`, `LPFR`) para máxima eficiencia en la red WiFi local.

---

## Feedback de interacción

El componente `UiInteractionFeedback` añade retroalimentación multisensorial en todos los controles UI:

| Evento | Audio | Háptico (controlador derecho) |
|---|---|---|
| Hover (apuntar sobre control) | Sonido suave (vol. 0.6) | Vibración 0.08 amp / 0.08 Hz / 30 ms |
| Click (seleccionar opción) | Sonido click (vol. 0.8) | Vibración 0.18 amp / 0.18 Hz / 50 ms |

---

## Validación

| Función | Estado |
|---|---|
| Canvas world-space sobre passthrough MR | ✅ Funcional |
| VideoPanel con stream RGB en tiempo real | ✅ Verificado |
| LidarPanel 2D con grid de ocupación configurable | ✅ Verificado |
| StatusPanel con conexión, sensores y telemetría | ✅ Verificado |
| Dropdowns de modos de cámara y LiDAR | ✅ Verificado |
| Feedback háptico y sonoro | ✅ Implementado |
| Control de base móvil desde headset (joystick) | ✅ Funcional |
| Control de manipulador 3DOF y gripper (sliders) | ✅ Funcional |
| Ghost robot con preview de pose | ✅ Funcional |
| Teclado virtual para IP | ✅ Funcional |
| LiDAR 3D (paredes + nube de puntos) | ✅ Funcional |
| Gemelo digital URDF | ⏳ Mediano plazo |
