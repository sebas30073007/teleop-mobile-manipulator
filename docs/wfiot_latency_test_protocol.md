---
title: "Protocolo WF-IoT: Latencia MR–Edge"
nav_order: 6
parent: "Documentación"
has_children: false
---

# Protocolo de Prueba de Latencia WF-IoT: MR–Edge
{: .no_toc }

<details open markdown="block">
  <summary>Contenido</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

---

## 1. Objetivo

Medir la **latencia round-trip time (RTT) a nivel de aplicación** entre la interfaz de realidad mixta (Meta Quest / Unity) y un nodo edge simulado en PC, usando ZeroMQ sobre red WiFi local, bajo distintas condiciones de carga de comunicación.

---

## 2. Alcance y limitaciones

**Esta prueba mide:**
- Latencia de protocolo MR–edge: tiempo desde que Unity envía `latency_probe` hasta que recibe `latency_ack`.
- Impacto de cargas concurrentes (video JPEG 640×480, LiDAR 2D grid JSON) sobre la latencia de comandos.

**Esta prueba NO mide:**
- Latencia física del robot (serial, ESP32, drivers, motores, respuesta mecánica).
- Latencia de actuación total del sistema teleoperado.
- Latencia de ida vs. vuelta por separado (requeriría sincronización de relojes NTP/PTP entre dispositivos).

**Definición de RTT:**
```
RTT = client_receive_ts − client_send_ts   [usando Time.unscaledTime de Unity]
```
No se asume ninguna sincronización de reloj entre Quest y PC. El campo `server_recv_unix` / `server_send_unix` en el ACK es informativo pero no se usa para calcular RTT.

---

## 3. Requisitos

| Componente | Requisito |
|---|---|
| PC (simulador) | Windows / Linux / macOS, Python 3.10+ |
| Python | `pyzmq ≥ 25`, `opencv-python ≥ 4.8`, `numpy ≥ 1.24` |
| Red | PC y Quest en **la misma red WiFi** (preferible 5 GHz) |
| Quest | Meta Quest 3, APK instalado con `WFIoTLatencyTestScene` |
| Unity scripts | Copiados desde `validation/Assets/Scripts/WFIoTLatency/` al proyecto Unity |

### Instalar dependencias Python

```bash
pip install pyzmq opencv-python numpy
```

---

## 4. Cómo correr el simulador Python

### Inicio rápido

```bash
cd <repo>/validation/tools
python wfiot_nuc_latency_simulator.py
```

### Con parámetros completos

```bash
python wfiot_nuc_latency_simulator.py \
  --host 0.0.0.0 \
  --video-fps 30 \
  --stat-hz 2 \
  --lidar-hz 12 \
  --jpeg-quality 85
```

### Para condición C5 / C7 (LiDAR panorama — payload reducido)

```bash
python wfiot_nuc_latency_simulator.py --lidar-hz 4 --compact-lidar
```

Al iniciar, el simulador imprime la IP local detectada y los puertos activos. Dejar corriendo durante toda la sesión de pruebas.

---

## 5. Cómo obtener la IP de la PC

El simulador detecta la IP automáticamente usando un socket UDP hacia 8.8.8.8 (sin enviar datos). Para verificarla manualmente:

**Windows:**
```cmd
ipconfig | findstr "IPv4"
```

**Linux / macOS:**
```bash
ip addr show | grep "inet "
```

Usar la IP de la interfaz WiFi (ej. `192.168.1.X`). Si tienes múltiples interfaces, asegúrate de que Quest y PC estén en la misma subred.

---

## 6. Cómo configurar Unity y Quest

### Paso 1 — Copiar scripts al proyecto Unity

Copiar todos los archivos de `validation/Assets/Scripts/WFIoTLatency/` a la carpeta `Assets/Scripts/WFIoTLatency/` del proyecto Unity (crear la carpeta si no existe).

### Paso 2 — Crear escena nueva

1. `File → New Scene (Empty)` → guardar como `Assets/Scenes/WFIoTLatencyTestScene.unity`.

### Paso 3 — Crear el GameObject principal

1. `Hierarchy → Create Empty` → renombrar **`WFIoTLatencySystem`**.
2. Adjuntar los componentes en el Inspector:
   - `WFIoTCommandPublisher`
   - `WFIoTLatencyAckReceiver`
   - `WFIoTSimSensorReceiver`
   - `WFIoTSimVideoReceiver`
   - `WFIoTLatencyCsvLogger`
   - `WFIoTLatencyTestManager`

### Paso 4 — Crear la UI

1. `Hierarchy → UI → Canvas` (Screen Space Overlay).
2. Si no existe, agregar `EventSystem` (`Hierarchy → UI → Event System`).
3. Crear un **Panel** vacío hijo del Canvas.
4. Adjuntar `WFIoTLatencyUIController` al Panel.

### Paso 5 — Crear los elementos de UI en el Panel

Crear los siguientes GameObjects hijos del Panel y asignarlos en el Inspector de `WFIoTLatencyUIController`:

| Nombre sugerido | Tipo de componente | Campo en Inspector |
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

### Paso 6 — Asignar referencias en Inspector

En **`WFIoTLatencyTestManager`** (en `WFIoTLatencySystem`): arrastrar cada componente desde el mismo GameObject a sus campos de referencia (`publisher`, `ackReceiver`, `sensorReceiver`, `videoReceiver`, `csvLogger`, `uiController`).

En **`WFIoTLatencyUIController`**: asignar la referencia a `WFIoTLatencyTestManager`.

### Paso 7 — RawImage opcional (preview de video)

Crear un `RawImage` en el Panel y arrastrarlo al campo `previewImage` de `WFIoTSimVideoReceiver`. Marcar `decodePreview = true` en el Inspector si deseas ver el video sintético. En Quest, dejarlo desactivado para ahorrar CPU.

### Paso 8 — Build Settings

1. `File → Build Settings → Android`.
2. Agregar `WFIoTLatencyTestScene` a la lista de escenas.
3. `Player Settings → XR Management`: verificar que **Oculus XR Plugin** está habilitado.
4. Build → instalar APK:
   ```bash
   adb install -r WFIoTLatencyTest.apk
   ```

### Paso 9 — Conectar

En la UI del Quest: escribir la IP de la PC en el campo de texto → presionar **Connect**.

---

## 7. Condiciones experimentales C1–C7

| ID | Nombre | Video | LiDAR | Modo cámara | Modo LiDAR | LiDAR Hz |
|---|---|---|---|---|---|---|
| C1 | `C1_control_only`  | No  | No  | off    | off      | — |
| C2 | `C2_video_normal`  | Sí  | No  | normal | off      | — |
| C3 | `C3_lidar_detail`  | No  | Sí  | off    | detail   | 12 |
| C4 | `C4_lidar_medium`  | No  | Sí  | off    | medium   | 8 |
| C5 | `C5_lidar_panorama`| No  | Sí  | off    | panorama | 4 |
| C6 | `C6_full_detail`   | Sí  | Sí  | normal | detail   | 12 |
| C7 | `C7_full_panorama` | Sí  | Sí  | normal | panorama | 4 |

Para cada condición:

1. Seleccionar el preset en el dropdown de Unity.
2. Verificar que los toggles de video/LiDAR y dropdowns de modo reflejan el preset.
3. Hacer clic en **Start**. La prueba corre 60 s a 10 Hz (≈ 600 muestras).
4. Al terminar, el CSV se exporta automáticamente.
5. Extraer el CSV con ADB (ver sección 10).

---

## 8. Parámetros recomendados

| Parámetro | Valor recomendado |
|---|---|
| Duración por condición | 60 s |
| Probe rate | 10 Hz |
| Repeticiones | 3 por condición si hay tiempo |
| Warm-up descartado | Primeras 10 muestras (`warmup=true` en CSV) |
| Red WiFi | 5 GHz, distancia < 5 m sin obstáculos |
| Escenario de prueba | Mismo cuarto, sin otros dispositivos en la misma red si es posible |

---

## 9. Dónde se guarda el CSV en Quest

```
/sdcard/Android/data/<bundle_id>/files/
  wfiot_latency_results_YYYYMMDD_HHMMSS.csv   ← detalle por muestra
  wfiot_latency_summary_YYYYMMDD_HHMMSS.csv   ← resumen estadístico
```

`<bundle_id>` es el Package Name configurado en `Player Settings` (ej. `com.tuuniversidad.wfiot`).

Unity imprime la ruta exacta en el Debug Log al exportar.

---

## 10. Cómo extraer el CSV con ADB

Con el Quest conectado por USB y ADB instalado:

```bash
# Ver el bundle_id (si no lo recuerdas)
adb shell pm list packages | grep wfiot

# Extraer todos los archivos al directorio local csv_export/
adb pull /sdcard/Android/data/<bundle_id>/files/ ./csv_export/
```

Ejemplo concreto:

```bash
adb pull /sdcard/Android/data/com.tuuniversidad.wfiot/files/ ./csv_export/
```

---

## 11. Cómo interpretar los resultados

### CSV de detalle (`wfiot_latency_results_*.csv`)

| Columna | Descripción |
|---|---|
| `rtt_ms` | RTT observado en milisegundos |
| `warmup` | `true` = muestra de warm-up — **excluir del análisis estadístico** |
| `video_fps_received` | FPS de video recibido en ese momento |
| `lidar_hz_received` | Hz de LiDAR recibido en ese momento |
| `loss_percent` | Calculado en el resumen; en detalle usar: `rtt_ms = 0` indica no recibido |

### CSV de resumen (`wfiot_latency_summary_*.csv`)

| Métrica | Descripción |
|---|---|
| `rtt_mean_ms` | Latencia promedio |
| `rtt_median_ms` | Mediana — robusta ante outliers |
| `rtt_p95_ms` | Percentil 95: 95% de las muestras tuvieron RTT ≤ este valor |
| `rtt_p99_ms` | Percentil 99: representa los casos más lentos |
| `rtt_max_ms` | Máximo observado |
| `jitter_std_ms` | Desviación estándar: variabilidad de la latencia |
| `loss_percent` | Porcentaje de probes sin ACK recibido |

### Análisis rápido en Python

```python
import pandas as pd

df = pd.read_csv("wfiot_latency_results_*.csv")
df = df[df["warmup"] == False]  # excluir warm-up

for cond, g in df.groupby("condition"):
    r = g["rtt_ms"]
    print(f"{cond:25s}  mean={r.mean():.1f} ms  "
          f"p95={r.quantile(0.95):.1f} ms  "
          f"jitter={r.std():.1f} ms  n={len(r)}")
```

---

## 12. Cómo reportar en el paper

### Tabla de resultados sugerida

| Condición | RTT mean (ms) | RTT median (ms) | RTT p95 (ms) | Jitter std (ms) | Loss (%) |
|---|---|---|---|---|---|
| C1 solo comandos | | | | | |
| C2 + video normal | | | | | |
| C3 + LiDAR detail | | | | | |
| C4 + LiDAR medium | | | | | |
| C5 + LiDAR panorama | | | | | |
| C6 full detail | | | | | |
| C7 full panorama | | | | | |

### Texto de limitaciones recomendado para el paper

> La prueba mide latencia de protocolo de la capa de aplicación MR–edge (RTT entre Unity/Quest y el nodo edge simulado), usando ZeroMQ sobre IEEE 802.11ac (WiFi 5 GHz). El RTT incluye serialización JSON, latencia de red WiFi (ida y vuelta) y deserialización, pero **no incluye** latencia serial, control de motores ni respuesta mecánica del robot. El RTT no puede separarse en latencia de ida y vuelta sin sincronización de relojes (NTP/PTP) entre los dispositivos; se reporta como RTT observado desde la perspectiva del operador en el visor MR. La carga de video y LiDAR es sintética pero usa los mismos canales ZMQ, frecuencias y tamaños de payload aproximados del sistema real.

---

## Apéndice: Puertos ZMQ del simulador

| Puerto | Socket (simulador) | Dirección | Contenido |
|---|---|---|---|
| 5002 | SUB bind | Quest → PC | Comandos JSON (topic `cmd`) |
| 5001 | PUB bind | PC → Quest | `latency_ack`, `stat`, `mode_ack`, `lidar_grid` |
| 5555 | PUB bind | PC → Quest | `video_rgb` (JPEG bytes) |
| 5007 | PUB bind | PC → Quest | Placeholder (reservado para datos binarios) |

---

*Documentación del proyecto de teleoperación móvil-manipulador — IEEE WF-IoT.*
