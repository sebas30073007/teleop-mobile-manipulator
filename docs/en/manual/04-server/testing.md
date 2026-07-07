---
title: "Server Testing"
nav_order: 3
parent: "Server / NUC"
---

# Server / Middleware Testing

## Data channel verification

Validation that the architecture's channels publish data at the expected frequency.

| Channel | Expected frequency | Status |
|---|---|---|
| `lidar_grid` (RPLiDAR C1) | ~10-12 Hz | ✅ Verified |
| `video_rgb` (RealSense) | ~30 fps | ✅ Verified |
| `stat` | ~2 Hz | ✅ Verified |
| `cmd` (5002) → motor | — | ✅ Verified (partial) |
| Encoder telemetry | 10-20 Hz | ⏳ Integration pending |

## WiFi communication robot ↔ NUC

- Connection stability: no disconnections during a 10-minute test

> **Pending:** Measure and document local network latency and end-to-end latency (XR → robot → XR).

## Pending

| Test | Status |
|---|---|
| SLAM: map generation in a structured corridor | ⏳ Pending |
| End-to-end latency (XR → robot → XR) | ⏳ Pending |
| Watchdog: verify the robot stops on connection loss | ⏳ Pending |
| Full RGB-D video stream to the XR headset | ⏳ Pending |
