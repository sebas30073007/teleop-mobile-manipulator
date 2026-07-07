---
title: "Perception"
nav_order: 2
parent: "Server / NUC"
---

# Perception

## Sensors

| Sensor | Port | Main use |
|---|---|---|
| RPLiDAR C1 | COM3 (460800 baud) | 2D occupancy grid, immersive walls pipeline, points in local frame |
| Intel RealSense D435i | USB | RGB stream to XR, calibrated depth, point cloud |

## Perception pipeline

```
RPLiDAR C1 (COM3)          RealSense D435i (USB)
      │                           │
  lidar_async_worker          camera_thread
      │                           │
  ┌───┴────────────┐    ┌─────────┴────────────┐
  │ lidar_grid     │    │ video (JPEG)          │
  │ walls_snapshot │    │ cam_info              │
  │ walls_delta    │    │ depth (calibrated)     │
  │ lidar_points   │    │ YOLOv8 vision          │
  └───┬────────────┘    └─────────┬────────────┘
      │                           │
      └──────────┬────────────────┘
                 │
          NUC Python 3.12
                 │
    ┌────────────┼────────────────┐
    │ :5555 video_rgb             │
    │ :5001 JSON topics           │
    │ :5007 binary (walls/pts)   │
    └─────────────────────────────┘
```

## RPLiDAR C1 — Occupancy grid

- Generates a local occupancy grid in 3 modes: `detail` (1 m), `medium` (2 m), `panorama` (3 m)
- Fixed 1 cm cell size across all modes
- Published as JSON on the `lidar_grid` topic at ~12 Hz
- Points older than 0.35 s are discarded (`LIDAR_STALE_S`)

## RPLiDAR C1 — Immersive walls pipeline

When `walls_enabled = true`, the system accumulates up to 150,000 points over a 4-second window and processes at ~1 Hz:

1. Projection onto a 2D grid (10 cm resolution)
2. Morphological operations: dilate → close → open
3. Connected component extraction (min. 80 px)
4. Polyline simplification (4 px tolerance)
5. Detection and merging of orthogonal segments (15° tolerance)

Result: compact wall segments for representation in the immersive XR scene. Published in binary (`WSNP`/`WDEL`) on :5007.

## RPLiDAR C1 — Points in local frame

When `points_enabled = true`, publishes a raw point cloud in the LiDAR's local frame at ~8 Hz. Up to 12,000 points per packet, 0.35 s window. Published in binary (`LPSN`/`LPFR`) on :5007.

![RealSense mounted — front-facing position on the manipulator base]({{ "/assets/raw_assets/20260428_160728.jpg" | relative_url }})

## Intel RealSense D435i — RGB stream

- Video stream for the XR headset (first-person view from the robot)
- Resolution: 640×480 px, up to 30 fps, JPEG compression quality 85
- Published on the `video_rgb` topic on :5555

## Intel RealSense D435i — Depth calibration

The master applies an interpolated calibration curve to the depth measurements before publishing them. The curve corrects the sensor's systematic deviation between 160 mm and 1000 mm.

## Intel RealSense D435i — Computer vision

Processed on the NUC (CPU) with YOLOv8 nano:

| Mode | Model | Output |
|---|---|---|
| `pose` | `yolov8n-pose.pt` | Body pose keypoints |
| `segment` | `yolov8n-seg.pt` | Semantic segmentation masks |

Results published on the `vision` topic at ~10 Hz.

## Current status

| Function | Status |
|---|---|
| LiDAR grid (3 modes) | ✅ Verified |
| RGB stream 640×480 @ ~30 fps | ✅ Verified |
| Depth calibration | ✅ Implemented |
| Immersive walls pipeline | ✅ Implemented |
| LiDAR points pipeline | ✅ Implemented |
| Full RGB-D transmission to Meta Quest | ⏳ Pending |
| Global environment mapping (SLAM) | ⏳ Future phase |
