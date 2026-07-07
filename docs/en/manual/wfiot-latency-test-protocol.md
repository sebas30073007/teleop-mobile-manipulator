---
title: "WF-IoT Protocol: MR-Edge Latency"
nav_order: 6
parent: "Documentation"
has_children: false
---

# WF-IoT Latency Test Protocol: MR–Edge
{: .no_toc }

<details open markdown="block">
  <summary>Contents</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

---

## 1. Objective

Measure the **application-level round-trip time (RTT) latency** between the mixed reality interface (Meta Quest / Unity) and a simulated edge node on a PC, using ZeroMQ over a local WiFi network, under different communication load conditions.

---

## 2. Scope and limitations

**This test measures:**
- MR–edge protocol latency: time from when Unity sends `latency_probe` until it receives `latency_ack`.
- Impact of concurrent loads (JPEG video 640×480, 2D LiDAR grid JSON) on command latency.

**This test does NOT measure:**
- Physical robot latency (serial, ESP32, drivers, motors, mechanical response).
- Total actuation latency of the teleoperated system.
- Outbound vs. return latency separately (would require NTP/PTP clock synchronization between devices).

**RTT definition:**
```
RTT = client_receive_ts − client_send_ts   [using Unity's Time.unscaledTime]
```
No clock synchronization between Quest and PC is assumed. The `server_recv_unix` / `server_send_unix` field in the ACK is informative but not used to calculate RTT.

---

## 3. Requirements

| Component | Requirement |
|---|---|
| PC (simulator) | Windows / Linux / macOS, Python 3.10+ |
| Python | `pyzmq ≥ 25`, `opencv-python ≥ 4.8`, `numpy ≥ 1.24` |
| Network | PC and Quest on **the same WiFi network** (preferably 5 GHz) |
| Quest | Meta Quest 3, APK installed with `WFIoTLatencyTestScene` |
| Unity scripts | Copied from `validation/Assets/Scripts/WFIoTLatency/` into the Unity project |

### Install Python dependencies

```bash
pip install pyzmq opencv-python numpy
```

---

## 4. How to run the Python simulator

### Quick start

```bash
cd <repo>/validation/tools
python wfiot_nuc_latency_simulator.py
```

### With full parameters

```bash
python wfiot_nuc_latency_simulator.py \
  --host 0.0.0.0 \
  --video-fps 30 \
  --stat-hz 2 \
  --lidar-hz 12 \
  --jpeg-quality 85
```

### For condition C5 / C7 (LiDAR panorama — reduced payload)

```bash
python wfiot_nuc_latency_simulator.py --lidar-hz 4 --compact-lidar
```

On startup, the simulator prints the detected local IP and the active ports. Leave it running for the entire test session.

---

## 5. How to get the PC's IP

The simulator detects the IP automatically using a UDP socket toward 8.8.8.8 (without sending data). To verify it manually:

**Windows:**
```cmd
ipconfig | findstr "IPv4"
```

**Linux / macOS:**
```bash
ip addr show | grep "inet "
```

Use the IP of the WiFi interface (e.g., `192.168.1.X`). If you have multiple interfaces, make sure Quest and PC are on the same subnet.

---

## 6. How to configure Unity and Quest

### Step 1 — Copy scripts into the Unity project

Copy all files from `validation/Assets/Scripts/WFIoTLatency/` into the `Assets/Scripts/WFIoTLatency/` folder of the Unity project (create the folder if it does not exist).

### Step 2 — Create a new scene

1. `File → New Scene (Empty)` → save as `Assets/Scenes/WFIoTLatencyTestScene.unity`.

### Step 3 — Create the main GameObject

1. `Hierarchy → Create Empty` → rename to **`WFIoTLatencySystem`**.
2. Attach the components in the Inspector:
   - `WFIoTCommandPublisher`
   - `WFIoTLatencyAckReceiver`
   - `WFIoTSimSensorReceiver`
   - `WFIoTSimVideoReceiver`
   - `WFIoTLatencyCsvLogger`
   - `WFIoTLatencyTestManager`

### Step 4 — Create the UI

1. `Hierarchy → UI → Canvas` (Screen Space Overlay).
2. If it does not exist, add `EventSystem` (`Hierarchy → UI → Event System`).
3. Create an empty **Panel** child of the Canvas.
4. Attach `WFIoTLatencyUIController` to the Panel.

### Step 5 — Create the UI elements in the Panel

Create the following child GameObjects of the Panel and assign them in the Inspector of `WFIoTLatencyUIController`:

| Suggested name | Component type | Inspector field |
|---|---|---|
| `IpInputField` | `TMP_InputField` | `ipInput` |
| `PresetDropdown` | `TMP_Dropdown` | `presetDropdown` |
| `CameraDropdown` | `TMP_Dropdown` | `cameraModeDropdown` |
| `LidarDropdown` | `TMP_Dropdown` | `lidarModeDropdown` |
| `BtnConnect` | `Button` | `connectButton` |
| `BtnDisconnect` | `Button` | `disconnectButton` |
| `BtnStart` | `Button` | `startButton` |
| `BtnStop` | `Button` | `stopButton` |
| `BtnExport` | `Button` | `exportButton` |
| `VideoToggle` | `Toggle` | `videoEnabledToggle` |
| `LidarToggle` | `Toggle` | `lidarEnabledToggle` |
| `StatusLabel` | `TMP_Text` | `statusText` |
| `MetricsLabel` | `TMP_Text` | `metricsText` |

### Step 6 — Assign references in the Inspector

On **`WFIoTLatencyTestManager`** (inside `WFIoTLatencySystem`): drag each component from the same GameObject into its reference fields (`publisher`, `ackReceiver`, `sensorReceiver`, `videoReceiver`, `csvLogger`, `uiController`).

On **`WFIoTLatencyUIController`**: assign the reference to `WFIoTLatencyTestManager`.

### Step 7 — Optional RawImage (video preview)

Create a `RawImage` in the Panel and drag it into the `previewImage` field of `WFIoTSimVideoReceiver`. Check `decodePreview = true` in the Inspector if you want to see the synthetic video. On Quest, leave it disabled to save CPU.

### Step 8 — Build Settings

1. `File → Build Settings → Android`.
2. Add `WFIoTLatencyTestScene` to the scene list.
3. `Player Settings → XR Management`: verify that the **Oculus XR Plugin** is enabled.
4. Build → install APK:
   ```bash
   adb install -r WFIoTLatencyTest.apk
   ```

### Step 9 — Connect

In the Quest UI: type the PC's IP into the text field → press **Connect**.

---

## 7. Experimental conditions C1–C7

| ID | Name | Video | LiDAR | Camera mode | LiDAR mode | LiDAR Hz |
|---|---|---|---|---|---|---|
| C1 | `C1_control_only`  | No  | No  | off    | off      | — |
| C2 | `C2_video_normal`  | Yes | No  | normal | off      | — |
| C3 | `C3_lidar_detail`  | No  | Yes | off    | detail   | 12 |
| C4 | `C4_lidar_medium`  | No  | Yes | off    | medium   | 8 |
| C5 | `C5_lidar_panorama`| No  | Yes | off    | panorama | 4 |
| C6 | `C6_full_detail`   | Yes | Yes | normal | detail   | 12 |
| C7 | `C7_full_panorama` | Yes | Yes | normal | panorama | 4 |

For each condition:

1. Select the preset in the Unity dropdown.
2. Verify that the video/LiDAR toggles and mode dropdowns reflect the preset.
3. Click **Start**. The test runs for 60 s at 10 Hz (≈ 600 samples).
4. When finished, the CSV is exported automatically.
5. Extract the CSV via ADB (see section 10).

---

## 8. Recommended parameters

| Parameter | Recommended value |
|---|---|
| Duration per condition | 60 s |
| Probe rate | 10 Hz |
| Repetitions | 3 per condition if time allows |
| Warm-up discarded | First 10 samples (`warmup=true` in CSV) |
| WiFi network | 5 GHz, distance < 5 m with no obstacles |
| Test scenario | Same room, no other devices on the same network if possible |

---

## 9. Where the CSV is saved on Quest

```
/sdcard/Android/data/<bundle_id>/files/
  wfiot_latency_results_YYYYMMDD_HHMMSS.csv   ← per-sample detail
  wfiot_latency_summary_YYYYMMDD_HHMMSS.csv   ← statistical summary
```

`<bundle_id>` is the Package Name configured in `Player Settings` (e.g., `com.tuuniversidad.wfiot`).

Unity prints the exact path in the Debug Log when exporting.

---

## 10. How to extract the CSV with ADB

With Quest connected via USB and ADB installed:

```bash
# View the bundle_id (if you don't remember it)
adb shell pm list packages | grep wfiot

# Extract all files to the local csv_export/ directory
adb pull /sdcard/Android/data/<bundle_id>/files/ ./csv_export/
```

Concrete example:

```bash
adb pull /sdcard/Android/data/com.tuuniversidad.wfiot/files/ ./csv_export/
```

---

## 11. How to interpret the results

### Detail CSV (`wfiot_latency_results_*.csv`)

| Column | Description |
|---|---|
| `rtt_ms` | RTT observed in milliseconds |
| `warmup` | `true` = warm-up sample — **exclude from statistical analysis** |
| `video_fps_received` | FPS of video received at that moment |
| `lidar_hz_received` | LiDAR Hz received at that moment |
| `loss_percent` | Calculated in the summary; in detail use: `rtt_ms = 0` indicates not received |

### Summary CSV (`wfiot_latency_summary_*.csv`)

| Metric | Description |
|---|---|
| `rtt_mean_ms` | Average latency |
| `rtt_median_ms` | Median — robust to outliers |
| `rtt_p95_ms` | 95th percentile: 95% of samples had RTT ≤ this value |
| `rtt_p99_ms` | 99th percentile: represents the slowest cases |
| `rtt_max_ms` | Maximum observed |
| `jitter_std_ms` | Standard deviation: latency variability |
| `loss_percent` | Percentage of probes with no ACK received |

### Quick analysis in Python

```python
import pandas as pd

df = pd.read_csv("wfiot_latency_results_*.csv")
df = df[df["warmup"] == False]  # exclude warm-up

for cond, g in df.groupby("condition"):
    r = g["rtt_ms"]
    print(f"{cond:25s}  mean={r.mean():.1f} ms  "
          f"p95={r.quantile(0.95):.1f} ms  "
          f"jitter={r.std():.1f} ms  n={len(r)}")
```

---

## 12. How to report in the paper

### Suggested results table

| Condition | RTT mean (ms) | RTT median (ms) | RTT p95 (ms) | Jitter std (ms) | Loss (%) |
|---|---|---|---|---|---|
| C1 commands only | | | | | |
| C2 + normal video | | | | | |
| C3 + LiDAR detail | | | | | |
| C4 + LiDAR medium | | | | | |
| C5 + LiDAR panorama | | | | | |
| C6 full detail | | | | | |
| C7 full panorama | | | | | |

### Recommended limitations text for the paper

> This test measures application-layer MR–edge protocol latency (RTT between Unity/Quest and the simulated edge node), using ZeroMQ over IEEE 802.11ac (5 GHz WiFi). The RTT includes JSON serialization, WiFi network latency (round-trip), and deserialization, but **does not include** serial latency, motor control, or the robot's mechanical response. The RTT cannot be separated into outbound and return latency without clock synchronization (NTP/PTP) between devices; it is reported as the observed RTT from the operator's perspective in the MR headset. The video and LiDAR load is synthetic but uses the same ZMQ channels, frequencies, and approximate payload sizes of the real system.

---

## Appendix: Simulator ZMQ ports

| Port | Socket (simulator) | Direction | Content |
|---|---|---|---|
| 5002 | SUB bind | Quest → PC | JSON commands (topic `cmd`) |
| 5001 | PUB bind | PC → Quest | `latency_ack`, `stat`, `mode_ack`, `lidar_grid` |
| 5555 | PUB bind | PC → Quest | `video_rgb` (JPEG bytes) |
| 5007 | PUB bind | PC → Quest | Placeholder (reserved for binary data) |

---

*Documentation for the mobile-manipulator teleoperation project — IEEE WF-IoT.*
