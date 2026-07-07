---
title: "ZMQ Middleware"
nav_order: 1
parent: "Server / NUC"
---

# ZMQ Middleware

[View NUC source code](https://github.com/sebas30073007/teleop-mobile-manipulator/blob/main/assets/downloads/NUC_master_code.py){: .btn .btn-outline }

## Design

The Python master uses **ZeroMQ** with four ports differentiated by data type:

| Port | NUC role | Unity role | Type |
|---|---|---|---|
| `:5555` | PUB | SUB | Video — compressed JPEG frames |
| `:5001` | PUB | SUB | Sensors and state — JSON per topic |
| `:5002` | SUB | PUB | Commands from Unity to the NUC |
| `:5007` | PUB | SUB | Walls and LiDAR points — binary data |

**Design decisions:**
- **Port separation** — video and binary data on dedicated ports so they don't block the JSON channel
- **Selective streaming** — each mode publishes only if active; inactive modes consume no CPU or network
- **High watermark** — asynchronous queue handling to absorb spikes without accumulating latency

---

## Ports and topics

### Port :5555 — Video

Single topic `video_rgb`. JPEG frames at 640×480 px, up to 30 fps, quality 85.

### Port :5001 — Sensors and state (JSON)

| Topic | Frequency | Content |
|---|---|---|
| `stat` | ~2 Hz | Global system state (see structure below) |
| `mode_ack` | On mode change | Mode change confirmation |
| `lidar_grid` | ~12 Hz | Active occupancy grid (see structure below) |
| `cam_info` | Continuous | RealSense intrinsics and depth scale |
| `vision` | ~10 Hz | YOLOv8 results (keypoints or masks) |
| `error` | Per event | System error messages |
| `manip_state` | ~4 Hz | Current manipulator angles and limit switch state |
| `gripper_state` | ~4 Hz | Gripper position in mm, busy, calibrated |
| `walls_status` | Continuous | Immersive walls pipeline status |
| `points_status` | Continuous | LiDAR points pipeline status |

#### `stat` structure

```json
{
  "camera_ok": true,
  "lidar_ok": true,
  "cmd_link_ok": true,
  "master_serial_ok": true,
  "gripper_serial_ok": true,
  "active_camera_mode": "normal",
  "active_lidar_mode": "detail",
  "walls_enabled": false,
  "points_enabled": false,
  "drive_enabled": false,
  "manip_enabled": false,
  "actual_base_deg": 0.0,
  "actual_codo_deg": 0.0,
  "actual_muneca_deg": 0.0,
  "gripper_mm": 0.0,
  "gripper_calibrated": false,
  "uptime_s": 123.4,
  "ts": 1712000000.0
}
```

#### `lidar_grid` structure

```json
{
  "ts": 1712000000.0,
  "mode": "detail",
  "grid_size": 200,
  "cell_size_m": 0.01,
  "radius_m": 1.0,
  "hits": 1420,
  "occupancy": [0, 0, 1, 0, ...]
}
```

`occupancy[]` is the linearized grid (row-major). `1` = obstacle, `0` = free.

#### `manip_state` structure

```json
{
  "base_deg": 0.0,
  "codo_deg": 45.0,
  "muneca_deg": -30.0,
  "sw2": 0,
  "sw3": 1,
  "busy": false,
  "ts": 1712000000.0
}
```

#### `gripper_state` structure

```json
{
  "mm": 25.0,
  "target_mm": 30.0,
  "count": 1200,
  "busy": false,
  "calibrated": true,
  "ts": 1712000000.0
}
```

### Port :5007 — Binary walls and points

Binary channel for (optional) immersive modes. Publishes four packet types:

| Packet | Magic bytes | Content |
|---|---|---|
| `walls_snapshot` | `WSNP` | Complete snapshot of wall segments derived from LiDAR |
| `walls_delta` | `WDEL` | Additions and removals since the last snapshot |
| `lidar_points_snapshot` | `LPSN` | Full LiDAR point cloud in local frame |
| `lidar_points_frame` | `LPFR` | Incremental LiDAR points frame |

---

## Operating modes

### Camera modes

| Mode | Behavior |
|---|---|
| `normal` | RGB stream without processing |
| `pose` | RGB annotated with pose detection (YOLOv8 nano-pose) |
| `segment` | RGB annotated with semantic segmentation (YOLOv8 nano-seg) |
| `off` | Camera disabled; no video published |

### LiDAR modes

| Mode | Cell | Radius | Grid |
|---|---|---|---|
| `detail` | 1 cm | 1 m | 200×200 |
| `medium` | 1 cm | 2 m | 400×400 |
| `panorama` | 1 cm | 3 m | 600×600 |
| `off` | — | — | No publishing |

### Walls mode (`walls_enabled`)

When active, the walls pipeline processes the accumulated RPLiDAR buffer (4 s window, up to 150,000 points), applies morphological operations, and extracts simplified wall segments for the immersive XR mode. Processing frequency: ~1 Hz.

### Points mode (`points_enabled`)

Publishes raw LiDAR points in the local frame for volumetric representation in XR. Up to 12,000 points per packet at ~8 Hz.

---

## Commands (port :5002)

All commands are JSON. Some are continuous control commands; others are one-off events.

### Perception modes

```json
{"type": "set_camera_mode", "mode": "normal|pose|segment|off"}
{"type": "set_lidar_mode",  "mode": "detail|medium|panorama|off"}
{"type": "set_walls_mode",  "enabled": true}
{"type": "set_points_mode", "enabled": true}
```

### Control enable

```json
{"type": "set_control_enable", "drive_enabled": true, "manip_enabled": true, "base_enabled": true}
{"type": "master_arm"}
{"type": "master_disarm"}
{"type": "stop_all"}
```

### Mobile base control

```json
{"type": "drive_cmd", "v": 0.5, "w": -0.3, "enabled": true}
{"type": "drive_direct", "left": 150, "right": 120}
```

`drive_cmd` uses a unicycle model (v = linear speed, w = angular speed, range [-1, 1]). The NUC mixes and sends to the master bridge at 15 Hz.

### Manipulator control

```json
{"type": "manip_cmd",     "q": [base_deg, codo_deg, muneca_deg]}
{"type": "base_joint_cmd","q_base": 45.0}
{"type": "manip_home"}
{"type": "manip_ascii",   "line": "HOME_ALL"}
```

### Gripper control

```json
{"type": "gripper_cmd",   "opening_mm": 30.0}
{"type": "gripper_stop"}
{"type": "gripper_ascii", "line": "m 25.0"}
```

---

## Serial bridges

### Master bridge (COM4) — base and manipulator

The `serial_master_thread` thread manages COM4 at 115200 baud. Output protocol:

| Command | Format | Description |
|---|---|---|
| Drive | `{left},{right}\n` | Motor tokens, e.g. `150,120` or `S,S` to stop |
| Manipulator pose | `POSE {base} {codo} {muneca}\n` | Angles in degrees |
| Individual base | `BASE_GOTO {deg}\n` | Base axis only |
| Home | `HOME_ALL\n` | Zero search on all axes |
| Arm | `ARM\n` / `DISARM\n` | Enables or disables outputs |
| Stop all | `STOPALL\n` | Stops base and manipulator |
| State query | `M STATE?\n` | Requests manipulator state at ~4 Hz |

The NUC reads state responses using regex:
```
BASE={deg}deg(...) | CODO={deg}deg(...) | MUNECA={deg}deg(...) SW2={0|1} SW3={0|1}
```

### Gripper bridge (COM5) — gripper

The `serial_gripper_thread` thread manages COM5 at 115200 baud. Protocol:

| Command | Format | Description |
|---|---|---|
| Move to position | `m {mm}\n` | Target position in mm |
| Stop | `s\n` | Stops the gripper |
| State query | `p\n` | Requests state at ~4 Hz |

The NUC reads responses using regex:
```
GRIPPER_STATE mm={mm} count={count} target_mm={mm} target_count={count} busy={0|1} calibrated={0|1}
```

---

## Depth calibration

The master applies an **interpolated calibration curve** to the RealSense D435i measurements. The `(intel_mm, real_mm)` pairs cover 160 mm to 1000 mm and compensate for the sensor's systematic deviation at different distances. The correction is applied before publishing `cam_info`.

---

## Internal threads

| Thread | Responsibility |
|---|---|
| `camera_thread` | RealSense pipeline: capture, processes according to `camera_mode` |
| `video_pub_thread` | Publishes JPEG frames on :5555 |
| `lidar_async_worker` | Captures RPLiDAR, generates grid and runs the walls/points pipeline |
| `sensor_pub_thread` | Publishes all JSON topics on :5001 |
| `walls_pub_thread` | Publishes binary data on :5007 |
| `command_listener_thread` | Listens on :5002 and updates modes/state |
| `serial_master_thread` | Manages COM4: drive + manipulator |
| `serial_gripper_thread` | Manages COM5: gripper |

## Current status

| Feature | Status |
|---|---|
| Video, lidar grid, stat streaming | ✅ Verified |
| Camera and lidar mode switching from Unity | ✅ Verified via `mode_ack` |
| Mobile base control (`drive_cmd`) | ✅ Implemented |
| 3DOF manipulator control (`manip_cmd`) | ✅ Implemented |
| Gripper control (`gripper_cmd`) | ✅ Implemented |
| Manipulator telemetry (`manip_state`) | ✅ Implemented |
| Gripper telemetry (`gripper_state`) | ✅ Implemented |
| Immersive walls pipeline | ✅ Implemented |
| LiDAR points pipeline | ✅ Implemented |
| Disconnection watchdog with safe stop | ⏳ Partial — drive cmd timeout implemented (`DRIVE_CMD_TIMEOUT_S = 0.35 s`), ZMQ connection watchdog pending |
