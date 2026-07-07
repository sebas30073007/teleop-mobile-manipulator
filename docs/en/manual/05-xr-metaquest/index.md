---
title: "XR Meta Quest"
nav_order: 5
parent: "Documentation"
has_children: true
---

# XR Meta Quest

The teleoperation interface is a **Unity application for Meta Quest 3** that lets the operator visualize the robot's environment in mixed reality (MR), control the mobile base and manipulator, and switch perception modes. It runs in passthrough mode with a floating world-space canvas in front of the operator.

## System architecture

```
┌───────────────────────────────────────────────────────┐
│              Meta Quest 3 (Unity)                     │
│                                                       │
│  [Left]  StatusPanel + Camera + EmergStop + IP        │
│  [Center] VideoPanel (RGB) + LidarPanel (2D grid)     │
│  [Right]  ManipulatorPanel (sliders) + 3D LiDAR        │
│                                                       │
│  [Right joystick] → Drive teleop  (15 Hz)             │
└───────────────────────────────────────────────────────┘
     │  ZMQ SUB :5555   video_rgb JPEG
     │  ZMQ SUB :5001   stat, manip_state, gripper_state, lidar_grid
     │  ZMQ SUB :5007   walls, lidar_points (binary)
     │  ZMQ PUB :5002   cmd JSON (control + perception)
     ▼
┌───────────────────────────────────────────────────────┐
│              NUC — onboard the robot                  │
└───────────────────────────────────────────────────────┘
```

## Technology stack

| Component | Technology |
|---|---|
| Game engine | Unity (Android ARM64) |
| XR SDK | Meta XR SDK 83.0 (OpenXR) |
| NUC ↔ Unity communication | ZeroMQ (AsyncZMQ / NetMQ in C#) |
| Input controllers | OVRInput (joystick, buttons, haptics) |
| Computer vision | YOLOv8 nano (pose and segmentation, on the NUC) |
| Digital twin | Pending (medium term) |

## Subsections

- [Unity and ZMQ Communication]({{ "/docs/en/manual/05-xr-metaquest/unity" | relative_url }}) — project setup, all ZMQ components, full JSON command reference
- [Interface and Controls]({{ "/docs/en/manual/05-xr-metaquest/interface" | relative_url }}) — panels, drive teleop, manipulator, gripper, 3D LiDAR
- [Testing]({{ "/docs/en/manual/05-xr-metaquest/testing" | relative_url }}) — deployment, video, lidar, and control validations

## Subsystem status

| Feature | Status |
|---|---|
| Unity project built on Meta Quest 3 | ✅ Functional |
| RGB video stream 640×480 @ ~30 fps | ✅ Verified |
| 2D LiDAR panel with occupancy grid (3 modes) | ✅ Verified |
| StatusPanel with manipulator and gripper telemetry | ✅ Verified |
| Haptic and sound feedback | ✅ Implemented |
| Drive teleop from headset joystick | ✅ Functional |
| 3DOF manipulator control from headset | ✅ Functional |
| Gripper control (mm) from headset | ✅ Functional |
| 3D LiDAR — walls and point cloud | ✅ Functional |
| Virtual keyboard for IP change | ✅ Functional |
| URDF digital twin | ⏳ Medium term |
