---
title: "Unity y comunicación ZMQ"
nav_order: 1
parent: "XR Meta Quest"
---

# Unity y comunicación ZMQ

## Stack tecnológico

| Paquete | Versión / Función |
|---|---|
| Meta XR SDK (All-in-One) | 83.0 — SDK principal, passthrough y controladores |
| AsyncZMQ (NetMQ) | Cliente ZeroMQ para comunicación con la NUC |
| Unity XR Interaction Toolkit | Ray interaction y EventSystem VR/MR |
| TextMesh Pro | Todos los textos UI |
| OVRInput | Lectura de controladores Meta Quest (joystick, botones, hápticos) |

## Arquitectura de comunicación ZMQ

La NUC expone cuatro endpoints ZMQ. Unity actúa como cliente en todos:

| Puerto | Tipo | Dirección | Tópicos / Contenido |
|---|---|---|---|
| `:5555` | PUB/SUB | NUC → Unity | `video_rgb` — frames JPEG 640×480 |
| `:5001` | PUB/SUB | NUC → Unity | `stat`, `mode_ack`, `lidar_grid`, `manip_state`, `gripper_state` |
| `:5002` | PUB/SUB | Unity → NUC | `cmd` — comandos JSON (modos, control) |
| `:5007` | PUB/SUB | NUC → Unity | `walls_snapshot`, `walls_delta`, `lidar_points_snapshot`, `lidar_points_frame` |

{: .note }
Los comandos a `:5002` se reenvían varias veces con pequeña separación temporal para compensar el *slow joiner* de ZMQ PUB/SUB.

## Gestión de IP — `NucIpManager.cs`

Singleton `DontDestroyOnLoad` que persiste la IP de la NUC entre escenas. Almacena con `PlayerPrefs` (clave `"NUC_IP"`) y expone `CurrentIp` a todos los scripts. IP por defecto: `192.168.100.20`.

```csharp
// Uso desde cualquier script
string ip = NucIpManager.Instance.GetIp();
NucIpManager.Instance.SetIp("192.168.1.50");  // persiste entre sesiones
```

## Componentes ZMQ — recepción

### `ZmqVideoReceiver.cs`
- SUB en `:5555`, tópico `video_rgb`
- Decodifica JPEG en hilo secundario → actualiza `RawImage` en `VideoPanel`
- Expone: `CurrentFps`, `CurrentWidth/Height`, `IsConnected`, `CurrentCameraMode`
- Envía `set_camera_mode` al puerto `:5002`

### `ZmqSensorReceiver.cs`
- SUB en `:5001`, tópicos `stat`, `mode_ack`, `manip_state`, `gripper_state`
- Hub central de telemetría: alimenta `RobotStatusPanel`, `ManipulatorUIController` y `ZmqGripperStateReceiver`

Estructuras de datos clave:

```csharp
class StatPayload {
    public bool camera_ok, lidar_ok, master_serial_ok;
    public bool drive_enabled, manip_enabled, base_enabled;
    public bool manip_busy, gripper_serial_ok;
    public float actual_base_deg, actual_codo_deg, actual_muneca_deg;
    public string active_camera_mode, active_lidar_mode;
}

class ManipStatePayload {
    public float base_deg, codo_deg, muneca_deg;
    public int sw2, sw3;
    public bool busy;
}

class GripperStatePayload {
    public float mm, target_mm;
    public bool busy, calibrated;
}
```

### `ZmqGripperStateReceiver.cs`
- SUB en `:5001`, tópicos `gripper_state` y `stat`
- Expone propiedades: `ActualMm`, `TargetMm`, `Busy`, `Calibrated`, `SerialOk`
- Timeout de desconexión: 2 s sin datos → `StateValid = false`

### `ZmqLidarGridView.cs`
- SUB en `:5001`, tópico `lidar_grid`
- Reconstruye grid de ocupación como `Texture2D` — resolución dinámica por modo
- Envía `set_lidar_mode` al `:5002`

```csharp
// Grid de ocupación — payload
class LidarGridPayload {
    public string mode;           // "detail" | "medium" | "panorama"
    public int grid_size;         // 200, 400 o 600
    public float cell_size_m;     // 0.01 m fijo
    public float radius_m;        // 1, 2 o 3 m
    public int[] occupancy;       // grid_size² enteros (0=libre, ≠0=ocupado)
}
```

Convención visual: blanco=libre, negro=ocupado, verde=robot, azul=frente.

### `ZmqWallsReceiver.cs`
- SUB en `:5007`, tópicos `walls_snapshot` y `walls_delta`
- Reconstruye segmentos de pared como objetos Unity (cubo escalado)
- Protocolo binario con magic bytes `WSNP` / `WDEL`

```
Paquete snapshot (13 + n×16 bytes):
  [4]  magic "WSNP"
  [1]  version
  [4]  sequence
  [4]  n segmentos
  [n×16]  x1,y1,x2,y2 (int32 mm cada uno)
```

### `ZmqLidarPointsReceiver.cs`
- SUB en `:5007`, tópicos `lidar_points_snapshot` y `lidar_points_frame`
- Renderiza nube de puntos con `ParticleSystem` (máx. 4 000 partículas)
- Protocolo binario con magic bytes `LPSN` / `LPFR`

```
Paquete de puntos (13 + n×8 bytes):
  [4]  magic "LPSN"
  [1]  version
  [4]  sequence
  [4]  n puntos
  [n×8]  X, Y (int32 mm cada uno)
```

## Componente ZMQ — envío: `NucControlCommandSender.cs`

Hilo dedicado con `ConcurrentQueue<string>`. Publica en `:5002` tópico `cmd`. HWM = 20 mensajes.

### Referencia completa de mensajes JSON

#### Control general

```json
{"type": "master_arm"}
{"type": "master_disarm"}
{"type": "stop_all"}
{"type": "set_control_enable", "drive_enabled": true, "manip_enabled": false, "base_enabled": false}
```

#### Base móvil

```json
{"type": "drive_direct", "left": 100, "right": 150}
```
Velocidades: −255 a +255. Enviados a 15 Hz por el joystick; watchdog en NUC: 350 ms sin comando → stop.

#### Manipulador

```json
{"type": "manip_cmd", "q": [null, 45.0, -90.0]}
{"type": "base_joint_cmd", "q_base": 30.0}
{"type": "manip_home"}
{"type": "manip_ascii", "line": "POSE 0.0 90.0 -45.0"}
```
`null` en el array `q` significa "no cambiar ese eje".

#### Gripper

```json
{"type": "gripper_cmd", "mm": 40.0}
{"type": "gripper_stop"}
{"type": "gripper_ascii", "line": "m 40.0"}
```

#### Percepción (modos)

```json
{"type": "set_camera_mode", "mode": "normal|pose|segment|off"}
{"type": "set_lidar_mode",  "mode": "detail|medium|panorama|off"}
{"type": "set_lidar_3d_mode", "mode": "off|walls|points|both"}
{"type": "request_walls_snapshot"}
{"type": "request_points_snapshot"}
```

## Jerarquía de escena

```
SampleScene
├── [NucIpManager]              ← singleton persistente
├── [NucControlCommandSender]   ← hilo de envío ZMQ :5002
├── [ZmqSensorReceiver]         ← SUB :5001
├── [ZmqGripperStateReceiver]   ← SUB :5001
│
├── Main_menu
│   └── CanvasRoot  (world-space, ray interaction)
│       ├── UIBackplate
│       │   ├── PanelIzquierdo
│       │   │   ├── StatusPanel
│       │   │   ├── BotonesVideo        ← CameraModeDropdownController
│       │   │   ├── EmergencyStop
│       │   │   └── Thumbnails (3)
│       │   ├── PanelCentral
│       │   │   ├── VideoPanel
│       │   │   │   └── VideoRawImage   ← ZmqVideoReceiver
│       │   │   └── LidarPanel
│       │   │       └── LidarRawImage   ← ZmqLidarGridView
│       │   └── PanelDerecho
│       │       ├── ManipulatorPanel    ← ManipulatorUIController
│       │       │   ├── SliderBase      ← BaseCameraDirectControl
│       │       │   ├── SliderCodo
│       │       │   ├── SliderMuneca
│       │       │   └── SliderGripper
│       │       ├── GhostRobotRoot      ← SimpleArm3DOF (preview)
│       │       └── CameraRotControls
│       └── ISDK_RayCanvasInteraction
│
├── [QuestMobileDriveTeleop]    ← lee joystick derecho
├── [ControlModeState]          ← gestiona modos exclusivos
├── EventSystem
└── (demás objetos de escena MR)
```

## Descarga de scripts

[⬇ Scripts Unity (carpeta)]({{ "/assets/downloads/Unity scripts" | relative_url }}){: .btn .btn-outline }

| Script | Función |
|---|---|
| `NucControlCommandSender.cs` | Envío de todos los comandos a NUC |
| `NucIpManager.cs` | Singleton de IP persistente |
| `NucIpPanelController.cs` | Panel de configuración de IP |
| `IpKeypadController.cs` | Teclado numérico virtual para IP |
| `ZmqVideoReceiver.cs` | Recepción y renderizado del video |
| `ZmqSensorReceiver.cs` | Recepción de telemetría y estado |
| `ZmqGripperStateReceiver.cs` | Estado del gripper en tiempo real |
| `ZmqLidarGridView.cs` | Grid 2D de ocupación LiDAR |
| `ZmqWallsReceiver.cs` | Paredes 3D reconstruidas (LiDAR) |
| `ZmqLidarPointsReceiver.cs` | Nube de puntos LiDAR |
| `ZmqLidar3DCommandSender.cs` | Comandos de modo 3D |
| `QuestMobileDriveTeleop.cs` | Control de base con joystick |
| `ManipulatorUIController.cs` | Sliders del manipulador + gripper |
| `BaseCameraDirectControl.cs` | Slider de base/cámara |
| `ControlModeState.cs` | Gestor de modos de control exclusivos |
| `RobotStatusPanel.cs` | Panel de estado del sistema |
| `SimpleArm3DOF.cs` (robotControler.cs) | Modelo 3D del brazo (ghost + real) |
| `LidarModeDropdownController.cs` | Dropdown modo LiDAR 2D |
| `CameraModeDropdownController.cs` | Dropdown modo cámara |
| `Lidar3DSceneController.cs` | Controlador de vista 3D |
| `UiInteractionFeedback.cs` | Audio y hápticos en UI |
| `SceneSwitcher.cs` | Cambio entre escenas con botones |
| `ShowIpKeypadOnClick.cs` | Muestra teclado al hacer click |
| `TMPInputFocusHelper.cs` | Foco en campo de texto |
| `cubo.cs` | Debug visual de estado de controlador |

## Validación

| Función | Estado |
|---|---|
| Proyecto compilado y desplegado en Meta Quest 3 | ✅ Sin errores |
| SDK Meta XR inicializado, passthrough activo | ✅ Verificado |
| ZMQ: video + sensores + telemetría manipulador + gripper | ✅ Verificado |
| ZMQ: walls y points en puerto 5007 | ✅ Verificado |
| Dropdowns sincronizados con NUC via `mode_ack` | ✅ Verificado |
| Drive teleop por joystick | ✅ Funcional |
| Control de manipulador + gripper por sliders | ✅ Funcional |
| Gemelo digital URDF | ⏳ Mediano plazo |
