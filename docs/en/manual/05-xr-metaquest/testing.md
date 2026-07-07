---
title: "XR Testing"
nav_order: 3
parent: "XR Meta Quest"
---

# XR Meta Quest Testing

## Interface demo

{% include video_youtube.html id="G229ZIQ-Y1g" title="UI testing with Meta Quest 3 — Terminal Project 2026" %}

---

## Tests performed

### Unity setup and deployment

| Test | Result |
|---|---|
| Project built and deployed on Meta Quest 3 | ✅ No errors |
| Meta XR SDK initialized correctly | ✅ Verified |
| MR passthrough active, world-space canvas visible | ✅ Verified |
| Ray interaction with controllers across all UI controls | ✅ Functional |

### ZMQ communication

| Test | Result |
|---|---|
| ZMQ connection Meta Quest 3 ↔ NUC over local WiFi | ✅ Established |
| `video_rgb` topic received on port 5555 | ✅ Verified |
| `stat` and `mode_ack` topics received on port 5001 | ✅ Verified |
| `manip_state` and `gripper_state` topics on port 5001 | ✅ Verified |
| `lidar_grid` topic received and rendered in LidarPanel | ✅ Verified |
| `walls_snapshot` and `lidar_points_*` topics on port 5007 | ✅ Verified |
| Commands from Unity confirmed by `mode_ack` on port 5002 | ✅ Verified |

### Video stream

| Test | Result |
|---|---|
| Stable RGB stream 640×480 @ ~30 fps (RealSense D435i) | ✅ Verified |
| Normal mode | ✅ |
| Pose mode (YOLOv8) | ✅ |
| Segment mode (YOLOv8) | ✅ |
| Off mode | ✅ |

Note: resolutions above 640×480 caused instability (blank frames, FPS drops).

### 2D LiDAR panel

| Test | Result |
|---|---|
| Grid rendered in Detail mode (200×200) | ✅ Verified |
| Grid rendered in Medium mode (400×400) | ✅ Verified |
| Grid rendered in Panorama mode (600×600) | ✅ Verified |
| Dynamic texture size change on mode switch | ✅ Verified |
| Correct visual representation (color convention) | ✅ Verified |

### Immersive 3D LiDAR

| Test | Result |
|---|---|
| Reception of walls_snapshot on port 5007 | ✅ Verified |
| Walls reconstructed as 3D cubes in Unity | ✅ Verified |
| Point cloud rendered with ParticleSystem | ✅ Verified |
| Walls, points, and both modes | ✅ Functional |

### Drive teleop

| Test | Result |
|---|---|
| Right joystick read by `QuestMobileDriveTeleop` | ✅ Functional |
| `drive_direct` commands sent at 15 Hz via ZMQ | ✅ Verified |
| 18% deadzone applied correctly | ✅ Verified |
| NUC watchdog (stop after 350 ms with no command) | ✅ Verified |
| Exclusive modes: only mobile active at a time | ✅ Functional |

### Manipulator and gripper control

| Test | Result |
|---|---|
| Elbow, wrist, and gripper sliders on the right panel | ✅ Functional |
| Ghost robot updates visually before sending | ✅ Functional |
| Implement button sends `POSE base codo muneca` | ✅ Verified |
| Home button executes `HOME_ALL` on CL57T | ✅ Verified |
| Gripper slider sends `gripper_cmd mm` (0–80 mm) | ✅ Verified |
| Real position feedback (manip_state → slider updates) | ✅ Verified |
| Base control with `BaseCameraDirectControl` | ✅ Functional |

### General UI interface

| Test | Result |
|---|---|
| Camera and lidar dropdowns synced with NUC state | ✅ Verified |
| StatusPanel updated at ~5 Hz | ✅ Verified |
| Haptic and sound feedback (hover + click + vibration) | ✅ Functional |
| Virtual keyboard for IP change | ✅ Functional |
| Emergency Stop — stop_all + master_disarm | ✅ Verified |
| IP persisted across sessions (PlayerPrefs) | ✅ Verified |

## Pending

| Test | Status |
|---|---|
| Real robot telemetry in StatusPanel (battery, temperature) | ⏳ Pending |
| Performance with large grids under sustained load | ⏳ Pending |
| Formal usability tests with target users | ⏳ Pending |
| Digital twin with URDF and pose synchronization | ⏳ Medium term |
