---
title: "Commissioning"
nav_order: 7
parent: "Documentation"
---

# Commissioning

Estimated time from zero to operational system: **~5 minutes** (mostly corresponding to the NUC's boot time).

## Power supply

The system uses three independent LiPo batteries, one per power subsystem:

| Battery | Cells | Subsystem powered | Note |
|---|---|---|---|
| LiPo 6S | 6 cells | H-bridges — mobile platform | Directly powers the traction MOSFETs |
| LiPo 3S — NUC | 3 cells | NUC + gripper motor | The gripper's DC motor (12 V) runs in parallel with the NUC |
| LiPo 3S — manipulator | 3 cells | CL57T drivers | Powers the manipulator's three drivers |

Connecting the three batteries before powering on the NUC ensures that all embedded modules and drivers are energized from the start.

## Startup sequence

### 1. Connect the three batteries

Connect in any order. Once powered, the ESP32-C3 modules start automatically and remain in `DISARMED` state waiting for commands.

### 2. Power on the NUC

On boot, the NUC automatically runs the main Python 3.12 script. This brings up the ZMQ middleware, initializes the video (RealSense D435i) and LiDAR (RPLiDAR C1) streaming channels, and opens the serial connections with the embedded modules (COM4 — master H-bridge, COM5 — gripper controller).

No manual intervention is required: the system reaches operational state on its own.

### 3. Check the NUC's dynamic IP

The school network does not allow fixed IPs, so the NUC receives a dynamic IP on each boot. The NUC and the debug PC are connected to the same local network (TileSkate); the Meta Quest headset is **not** on that network.

To obtain the NUC's current IP from the debug PC:

```bash
arp -a
```

or, if the hostname is known:

```bash
ping <NUC-hostname>
```

More direct alternative: connect an external monitor to the NUC on boot and read the IP from the terminal.

### 4. Enter the IP in the Meta Quest application

When opening the application on the headset, the server IP field must point to the dynamic IP obtained in the previous step. Once entered, the application establishes the ZMQ connections and begins receiving video, robot status, and LiDAR data.

If the IP were fixed, this step would disappear; it is the only friction point in the current startup process.

### 5. System ready

With the correct IP configured on the headset, the system is operational: live video, telemetry, and movement control available from the XR interface.

{: .warning }
Before arming (`ARM`) any controller, verify that the robot's work area is clear. Modules start in `DISARMED` by design, but arming is immediate once the command is sent.
