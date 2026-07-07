---
title: "Unity and ZMQ Communication"
nav_order: 1
parent: "XR Meta Quest"
---

# Unity and ZMQ Communication

## Technology stack

| Package | Version / Function |
|---|---|
| Meta XR SDK (All-in-One) | 83.0 — main SDK, passthrough and controllers |
| AsyncZMQ (NetMQ) | ZeroMQ client for communication with the NUC |
| Unity XR Interaction Toolkit | Ray interaction and EventSystem for VR/MR |
| TextMesh Pro | All UI text |
| OVRInput | Reads Meta Quest controllers (joystick, buttons, haptics) |

## ZMQ communication architecture

The NUC exposes four ZMQ endpoints. Unity acts as the client on all of them:

| Port | Type | Direction | Topics / Content |
|---|---|---|---|
| `:5555` | PUB/SUB | NUC → Unity | `video_rgb` — JPEG frames 640×480 |
| `:5001` | PUB/SUB | NUC → Unity | `stat`, `mode_ack`, `lidar_grid`, `manip_state`, `gripper_state` |
| `:5002` | PUB/SUB | Unity → NUC | `cmd` — JSON commands (modes, control) |
| `:5007` | PUB/SUB | NUC → Unity | `walls_snapshot`, `walls_delta`, `lidar_points_snapshot`, `lidar_points_frame` |

{: .note }
Commands to `:5002` are re-sent several times with a small time separation to compensate for the ZMQ PUB/SUB *slow joiner* effect.

## IP management — `NucIpManager.cs`

A `DontDestroyOnLoad` singleton that persists the NUC's IP across scenes. Stores it with `PlayerPrefs` (key `"NUC_IP"`) and exposes `CurrentIp` to all scripts. Default IP: `192.168.100.20`.

```csharp
// Use from any script
string ip = NucIpManager.Instance.GetIp();
NucIpManager.Instance.SetIp("192.168.1.50");  // persists across sessions
```

## ZMQ components — reception

### `ZmqVideoReceiver.cs`
- SUB on `:5555`, topic `video_rgb`
- Decodes JPEG on a secondary thread → updates the `RawImage` in `VideoPanel`
- Exposes: `CurrentFps`, `CurrentWidth/Height`, `IsConnected`, `CurrentCameraMode`
- Sends `set_camera_mode` to port `:5002`

### `ZmqSensorReceiver.cs`
- SUB on `:5001`, topics `stat`, `mode_ack`, `manip_state`, `gripper_state`
- Central telemetry hub: feeds `RobotStatusPanel`, `ManipulatorUIController`, and `ZmqGripperStateReceiver`

Key data structures:

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
- SUB on `:5001`, topics `gripper_state` and `stat`
- Exposes properties: `ActualMm`, `TargetMm`, `Busy`, `Calibrated`, `SerialOk`
- Disconnection timeout: 2 s with no data → `StateValid = false`

### `ZmqLidarGridView.cs`
- SUB on `:5001`, topic `lidar_grid`
- Reconstructs the occupancy grid as a `Texture2D` — dynamic resolution per mode
- Sends `set_lidar_mode` to `:5002`

```csharp
// Occupancy grid — payload
class LidarGridPayload {
    public string mode;           // "detail" | "medium" | "panorama"
    public int grid_size;         // 200, 400, or 600
    public float cell_size_m;     // fixed 0.01 m
    public float radius_m;        // 1, 2, or 3 m
    public int[] occupancy;       // grid_size² integers (0=free, ≠0=occupied)
}
```

Visual convention: white=free, black=occupied, green=robot, blue=front.

### `ZmqWallsReceiver.cs`
- SUB on `:5007`, topics `walls_snapshot` and `walls_delta`
- Reconstructs wall segments as Unity objects (scaled cube)
- Binary protocol with magic bytes `WSNP` / `WDEL`

```
Snapshot packet (13 + n×16 bytes):
  [4]  magic "WSNP"
  [1]  version
  [4]  sequence
  [4]  n segments
  [n×16]  x1,y1,x2,y2 (int32 mm each)
```

### `ZmqLidarPointsReceiver.cs`
- SUB on `:5007`, topics `lidar_points_snapshot` and `lidar_points_frame`
- Renders the point cloud with `ParticleSystem` (max. 4,000 particles)
- Binary protocol with magic bytes `LPSN` / `LPFR`

```
Points packet (13 + n×8 bytes):
  [4]  magic "LPSN"
  [1]  version
  [4]  sequence
  [4]  n points
  [n×8]  X, Y (int32 mm each)
```

## ZMQ component — sending: `NucControlCommandSender.cs`

Dedicated thread with a `ConcurrentQueue<string>`. Publishes on `:5002` topic `cmd`. HWM = 20 messages.

### Full JSON message reference

#### General control

```json
{"type": "master_arm"}
{"type": "master_disarm"}
{"type": "stop_all"}
{"type": "set_control_enable", "drive_enabled": true, "manip_enabled": false, "base_enabled": false}
```

#### Mobile base

```json
{"type": "drive_direct", "left": 100, "right": 150}
```
Speeds: −255 to +255. Sent at 15 Hz by the joystick; NUC watchdog: 350 ms with no command → stop.

#### Manipulator

```json
{"type": "manip_cmd", "q": [null, 45.0, -90.0]}
{"type": "base_joint_cmd", "q_base": 30.0}
{"type": "manip_home"}
{"type": "manip_ascii", "line": "POSE 0.0 90.0 -45.0"}
```
`null` in the `q` array means "do not change this axis".

#### Gripper

```json
{"type": "gripper_cmd", "mm": 40.0}
{"type": "gripper_stop"}
{"type": "gripper_ascii", "line": "m 40.0"}
```

#### Perception (modes)

```json
{"type": "set_camera_mode", "mode": "normal|pose|segment|off"}
{"type": "set_lidar_mode",  "mode": "detail|medium|panorama|off"}
{"type": "set_lidar_3d_mode", "mode": "off|walls|points|both"}
{"type": "request_walls_snapshot"}
{"type": "request_points_snapshot"}
```

## Scene hierarchy

```
SampleScene
├── [NucIpManager]              ← persistent singleton
├── [NucControlCommandSender]   ← ZMQ send thread :5002
├── [ZmqSensorReceiver]         ← SUB :5001
├── [ZmqGripperStateReceiver]   ← SUB :5001
│
├── Main_menu
│   └── CanvasRoot  (world-space, ray interaction)
│       ├── UIBackplate
│       │   ├── LeftPanel
│       │   │   ├── StatusPanel
│       │   │   ├── VideoButtons        ← CameraModeDropdownController
│       │   │   ├── EmergencyStop
│       │   │   └── Thumbnails (3)
│       │   ├── CenterPanel
│       │   │   ├── VideoPanel
│       │   │   │   └── VideoRawImage   ← ZmqVideoReceiver
│       │   │   └── LidarPanel
│       │   │       └── LidarRawImage   ← ZmqLidarGridView
│       │   └── RightPanel
│       │       ├── ManipulatorPanel    ← ManipulatorUIController
│       │       │   ├── SliderBase      ← BaseCameraDirectControl
│       │       │   ├── SliderCodo
│       │       │   ├── SliderMuneca
│       │       │   └── SliderGripper
│       │       ├── GhostRobotRoot      ← SimpleArm3DOF (preview)
│       │       └── CameraRotControls
│       └── ISDK_RayCanvasInteraction
│
├── [QuestMobileDriveTeleop]    ← reads the right joystick
├── [ControlModeState]          ← manages exclusive modes
├── EventSystem
└── (other MR scene objects)
```

## Script download

[⬇ Unity Scripts (folder)]({{ "/assets/downloads/Unity scripts" | relative_url }}){: .btn .btn-outline }

| Script | Function |
|---|---|
| `NucControlCommandSender.cs` | Sends all commands to the NUC |
| `NucIpManager.cs` | Persistent IP singleton |
| `NucIpPanelController.cs` | IP configuration panel |
| `IpKeypadController.cs` | Virtual numeric keypad for IP |
| `ZmqVideoReceiver.cs` | Video reception and rendering |
| `ZmqSensorReceiver.cs` | Telemetry and state reception |
| `ZmqGripperStateReceiver.cs` | Real-time gripper state |
| `ZmqLidarGridView.cs` | 2D LiDAR occupancy grid |
| `ZmqWallsReceiver.cs` | Reconstructed 3D walls (LiDAR) |
| `ZmqLidarPointsReceiver.cs` | LiDAR point cloud |
| `ZmqLidar3DCommandSender.cs` | 3D mode commands |
| `QuestMobileDriveTeleop.cs` | Base control with joystick |
| `ManipulatorUIController.cs` | Manipulator + gripper sliders |
| `BaseCameraDirectControl.cs` | Base/camera slider |
| `ControlModeState.cs` | Exclusive control mode manager |
| `RobotStatusPanel.cs` | System status panel |
| `SimpleArm3DOF.cs` (robotControler.cs) | 3D arm model (ghost + real) |
| `LidarModeDropdownController.cs` | 2D LiDAR mode dropdown |
| `CameraModeDropdownController.cs` | Camera mode dropdown |
| `Lidar3DSceneController.cs` | 3D view controller |
| `UiInteractionFeedback.cs` | UI audio and haptics |
| `SceneSwitcher.cs` | Scene switching via buttons |
| `ShowIpKeypadOnClick.cs` | Shows keypad on click |
| `TMPInputFocusHelper.cs` | Focus on text field |
| `cubo.cs` | Visual debug of controller state |

## Validation

| Function | Status |
|---|---|
| Project built and deployed on Meta Quest 3 | ✅ No errors |
| Meta XR SDK initialized, passthrough active | ✅ Verified |
| ZMQ: video + sensors + manipulator telemetry + gripper | ✅ Verified |
| ZMQ: walls and points on port 5007 | ✅ Verified |
| Dropdowns synced with NUC via `mode_ack` | ✅ Verified |
| Joystick drive teleop | ✅ Functional |
| Manipulator + gripper control via sliders | ✅ Functional |
| URDF digital twin | ⏳ Medium term |
