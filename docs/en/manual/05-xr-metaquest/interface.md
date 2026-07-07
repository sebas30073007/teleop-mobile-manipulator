---
title: "Interface and Controls"
nav_order: 2
parent: "XR Meta Quest"
---

# Interface and Controls

The Unity application runs in MR passthrough mode on the Meta Quest 3. A **floating world-space canvas** in front of the operator groups all controls into three panels. The operator interacts using **ray interaction** with the headset controllers.

![View of the teleoperation interface in mixed reality]({{ "/assets/img/UI MixReality.png" | relative_url }})

---

## General layout — three panels

| Panel | Position | Function |
|---|---|---|
| **Left panel** | Left | Connection status, camera controls, emergency stop |
| **Center panel** | Center | Main video stream + 2D LiDAR grid |
| **Right panel** | Right | Manipulator and gripper sliders, camera rotation |

Inactive streams **are not transmitted** from the NUC — the UI selectively requests what it needs.

---

## Left panel

### StatusPanel — system status

`RobotStatusPanel` refreshes at ~5 Hz from the ZMQ `stat` topic on `:5001`.

| Field | Content |
|---|---|
| Robot | `Connected` / `Disconnected` |
| Target IP | NUC's IP (configurable via keypad) |
| My IP | Headset's IP on the local network |
| Mode | Active camera and LiDAR modes |
| FPS | Video frames per second |
| Res | Resolution of the received frame |
| Camera OK | RealSense D435i sensor status |
| Lidar OK | RPLiDAR C1 status |

### Camera controls

Dropdown (`CameraModeDropdownController`) to select image processing on the NUC:

| Option | Behavior on NUC |
|---|---|
| Normal | Standard RGB stream |
| Pose | RGB with pose detection (YOLOv8 nano) |
| Segment | RGB with semantic segmentation (YOLOv8 nano-seg) |
| Off | Camera disabled |

### Emergency Stop

Red button that sends `stop_all` + `master_disarm` to the NUC. Immediately stops all locomotion and sets the motors to `DISARMED`.

### IP configuration

Virtual numeric keypad (`IpKeypadController`) that appears when clicking the IP field in the StatusPanel. Allows changing the NUC's IP without removing the headset:

1. Point the ray at the IP field and click
2. The keypad floats in front of the operator
3. Enter the new IP and confirm with **Apply**
4. `NucIpPanelController` calls `Reconnect()` on all ZMQ sockets

The IP is persisted across sessions in `PlayerPrefs` (key `"NUC_IP"`).

---

## Center panel

### VideoPanel — main stream

| Parameter | Value |
|---|---|
| Resolution | 640×480 px |
| Frame rate | ~30 fps |
| Transport | Compressed JPEG, ZMQ `:5555` topic `video_rgb` |
| Target latency | < 150 ms end-to-end |

{: .warning }
Resolutions above 640×480 cause instability (blank frames, FPS drops). Do not exceed this limit.

### 2D LiDAR — occupancy grid

`ZmqLidarGridView` subscribes to the `lidar_grid` topic on `:5001` and renders the grid as a `Texture2D` in the `LidarPanel`.

Color convention:
- **White** — free / traversable space
- **Black** — obstacle or non-traversable zone
- **Green** — robot position on the grid
- **Blue** — robot's forward direction

Mode dropdown (`LidarModeDropdownController`):

| Mode | Radius | Grid | Point size |
|---|---|---|---|
| Detail | 1 m | 200×200 | 3×3 px |
| Medium | 2 m | 400×400 | 5×5 px |
| Panorama | 3 m | 600×600 | 7×7 px |
| Off | — | No transmission | — |

Cell resolution: fixed 1 cm. Update rate: ~12 Hz.

---

## Right panel

### Manipulator and gripper control

`ManipulatorUIController` manages 4 independent sliders. When manipulator mode is active, each slider moves its joint on release (**Implement** sends all at the same time) or individually depending on the configuration.

| Control | Joint | Range |
|---|---|---|
| Base | Base rotation | −80° to +80° |
| Joint Elbow 1 (Codo) | Elbow joint | 0° to 136.5° |
| Joint Wrist 1 (Muñeca) | Wrist orientation | −220° to 0° |
| Gripper | Gripper opening | 0 mm (closed) to 80 mm (open) |

**Ghost robot**: a visual 3D model (`SimpleArm3DOF`) shows the desired pose in real time as the sliders are adjusted, before the command is sent.

**Home button**: sends `manip_home` → `HOME_ALL` to the CL57T controller (runs a homing routine from the headset).

**Implement button**: sends the full pose in a single message `POSE base codo muneca` + `gripper_cmd mm`.

### Base control — `BaseCameraDirectControl.cs`

Slider in "base/camera" mode that continuously sends `base_joint_cmd` to the NUC to rotate the manipulator base independently.

---

## Drive teleop — right joystick

`QuestMobileDriveTeleop` reads the `Primary2DAxis` of the right controller and converts it into differential speeds:

```
joystick.y (±1) → v (forward/backward)
joystick.x (±1) → w (turn)

left  = clamp(v - w, -255, 255)
right = clamp(v + w, -255, 255)
```

| Parameter | Value |
|---|---|
| Send frequency | 15 Hz |
| Deadzone | 0.18 (18% of the total range) |
| Max speed | ±255 (raw) → ±70% duty cycle on hardware |
| NUC watchdog | 350 ms with no command → automatic stop |

The joystick is only active when "Mobile" mode is enabled in `ControlModeState`.

---

## Control mode management — `ControlModeState.cs`

The three control modes are **mutually exclusive** (only one active at a time). `ControlModeState` manages the toggles and arms/disarms the robot depending on the active mode:

| Toggle | Activates | Arm/Disarm |
|---|---|---|
| Mobile | Drive teleop (joystick) | Arm → enables traction motors |
| Manip | Manipulator + gripper sliders | Arm → enables CL57T |
| Base | Base slider (arm rotation) | — |

When all modes are deactivated: sends `stop_all` + `master_disarm`.

---

## Immersive 3D LiDAR

`Lidar3DSceneController` enables 3D-space visualizations using data from `:5007`:

| Mode | What it shows |
|---|---|
| Walls | Wall segments as 3D cubes (1.2 m height, 5 cm thickness) |
| Points | LiDAR point cloud (cyan particles, max. 4,000) |
| Both | Both simultaneously |
| Off | No 3D visualization |

Data travels over binary protocols with magic bytes (`WSNP`, `WDEL`, `LPSN`, `LPFR`) for maximum efficiency on the local WiFi network.

---

## Interaction feedback

The `UiInteractionFeedback` component adds multisensory feedback to all UI controls:

| Event | Audio | Haptic (right controller) |
|---|---|---|
| Hover (pointing at control) | Soft sound (vol. 0.6) | Vibration 0.08 amp / 0.08 Hz / 30 ms |
| Click (selecting an option) | Click sound (vol. 0.8) | Vibration 0.18 amp / 0.18 Hz / 50 ms |

---

## Validation

| Function | Status |
|---|---|
| World-space canvas over MR passthrough | ✅ Functional |
| VideoPanel with real-time RGB stream | ✅ Verified |
| 2D LidarPanel with configurable occupancy grid | ✅ Verified |
| StatusPanel with connection, sensors, and telemetry | ✅ Verified |
| Camera and LiDAR mode dropdowns | ✅ Verified |
| Haptic and sound feedback | ✅ Implemented |
| Mobile base control from headset (joystick) | ✅ Functional |
| 3DOF manipulator and gripper control (sliders) | ✅ Functional |
| Ghost robot with pose preview | ✅ Functional |
| Virtual keyboard for IP | ✅ Functional |
| 3D LiDAR (walls + point cloud) | ✅ Functional |
| URDF digital twin | ⏳ Medium term |
