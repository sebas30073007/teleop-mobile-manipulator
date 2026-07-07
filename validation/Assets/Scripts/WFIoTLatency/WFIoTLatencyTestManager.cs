// WFIoTLatencyTestManager.cs
// Orchestrates the WF-IoT latency experiment: connects all ZMQ receivers/senders,
// applies experimental presets (C1–C7), runs timed probe loops, accumulates RTT
// metrics in real time, and triggers CSV export when a test finishes.
//
// RTT calculation (clock-safe, no cross-device synchronization required):
//   sendTs         = Time.unscaledTime  (captured in main thread, in Coroutine)
//   client_send_ts = sendTs             (embedded in latency_probe JSON)
//   rtt_ms         = (Time.unscaledTime - ack.client_send_ts) * 1000f  (main thread, Update)
//
// Part of the WF-IoT latency measurement toolset.

using UnityEngine;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;

public class WFIoTLatencyTestManager : MonoBehaviour
{
    // ── Inspector-editable parameters ────────────────────────────────────────

    [Header("Connection")]
    public string pcIp = "192.168.100.5";

    [Header("Test Parameters")]
    public int   probeCount               = 600;
    public float probeRateHz              = 10f;
    public float testDurationSeconds      = 60f;
    public bool  useDurationInsteadOfCount = true;

    [Header("Current Condition")]
    public string condition    = "C1_control_only";
    public bool   videoEnabled = false;
    public bool   statEnabled  = true;
    public bool   lidarEnabled = false;
    public string cameraMode   = "off";
    public string lidarMode    = "off";
    public float  videoFps     = 30f;
    public float  statHz       = 2f;
    public float  lidarHz      = 12f;

    [Header("References")]
    public WFIoTCommandPublisher    publisher;
    public WFIoTLatencyAckReceiver  ackReceiver;
    public WFIoTSimSensorReceiver   sensorReceiver;
    public WFIoTSimVideoReceiver    videoReceiver;
    public WFIoTLatencyCsvLogger    csvLogger;
    public WFIoTLatencyUIController uiController;

    // ── Real-time metrics (read-only from UI / external code) ────────────────

    public int   SamplesSent     { get; private set; }
    public int   SamplesReceived { get; private set; }
    public float LossPercent     => SamplesSent > 0
                                    ? (SamplesSent - SamplesReceived) * 100f / SamplesSent
                                    : 0f;
    public float RttLatestMs  { get; private set; }
    public float RttMeanMs    { get; private set; }
    public float RttMedianMs  { get; private set; }
    public float RttP95Ms     { get; private set; }
    public float RttMaxMs     { get; private set; }
    public float JitterStdMs  { get; private set; }

    public float VideoFpsReceived  => videoReceiver  != null ? videoReceiver.CurrentFps       : 0f;
    public float StatHzReceived    => sensorReceiver != null ? sensorReceiver.LastStatHz       : 0f;
    public float LidarHzReceived   => sensorReceiver != null ? sensorReceiver.LastLidarHz      : 0f;

    public bool   IsConnected  { get; private set; }
    public bool   IsRunning    { get; private set; }
    public string StatusMessage { get; private set; } = "Disconnected";

    // ── Internal ─────────────────────────────────────────────────────────────

    private const int WARMUP_SAMPLES = 10;

    private int                       nextSeq      = 0;
    private Dictionary<int, float>    pendingProbes = new Dictionary<int, float>();
    private List<float>               rttHistory    = new List<float>();
    private Coroutine                 testCoroutine;

    // ── Presets (C1–C7) ───────────────────────────────────────────────────────

    private static readonly Dictionary<string, Action<WFIoTLatencyTestManager>> Presets =
        new Dictionary<string, Action<WFIoTLatencyTestManager>>
    {
        ["C1_control_only"] = m =>
        {
            m.videoEnabled = false; m.lidarEnabled = false;
            m.cameraMode = "off"; m.lidarMode = "off";
            m.probeRateHz = 10f; m.videoFps = 0f; m.lidarHz = 0f;
        },
        ["C2_video_normal"] = m =>
        {
            m.videoEnabled = true; m.lidarEnabled = false;
            m.cameraMode = "normal"; m.lidarMode = "off";
            m.probeRateHz = 10f; m.videoFps = 30f; m.lidarHz = 0f;
        },
        ["C3_lidar_detail"] = m =>
        {
            m.videoEnabled = false; m.lidarEnabled = true;
            m.cameraMode = "off"; m.lidarMode = "detail";
            m.probeRateHz = 10f; m.videoFps = 0f; m.lidarHz = 12f;
        },
        ["C4_lidar_medium"] = m =>
        {
            m.videoEnabled = false; m.lidarEnabled = true;
            m.cameraMode = "off"; m.lidarMode = "medium";
            m.probeRateHz = 10f; m.videoFps = 0f; m.lidarHz = 8f;
        },
        ["C5_lidar_panorama"] = m =>
        {
            m.videoEnabled = false; m.lidarEnabled = true;
            m.cameraMode = "off"; m.lidarMode = "panorama";
            m.probeRateHz = 10f; m.videoFps = 0f; m.lidarHz = 4f;
        },
        ["C6_full_detail"] = m =>
        {
            m.videoEnabled = true; m.lidarEnabled = true;
            m.cameraMode = "normal"; m.lidarMode = "detail";
            m.probeRateHz = 10f; m.videoFps = 30f; m.lidarHz = 12f;
        },
        ["C7_full_panorama"] = m =>
        {
            m.videoEnabled = true; m.lidarEnabled = true;
            m.cameraMode = "normal"; m.lidarMode = "panorama";
            m.probeRateHz = 10f; m.videoFps = 30f; m.lidarHz = 4f;
        },
    };

    /// <summary>Ordered list of preset names for UI dropdowns.</summary>
    public static readonly string[] PresetNames = {
        "C1_control_only", "C2_video_normal",
        "C3_lidar_detail",  "C4_lidar_medium", "C5_lidar_panorama",
        "C6_full_detail",   "C7_full_panorama",
    };

    // ── Public API ────────────────────────────────────────────────────────────

    public void Connect()
    {
        if (IsConnected)
            Disconnect();

        publisher?.Connect(pcIp);
        ackReceiver?.Connect(pcIp);
        sensorReceiver?.Connect(pcIp);
        videoReceiver?.Connect(pcIp);

        IsConnected   = true;
        StatusMessage = $"Connected → {pcIp}";
        Debug.Log($"[WFIoT MGR] Connected to {pcIp}");
    }

    public void Disconnect()
    {
        StopTest();
        publisher?.Disconnect();
        ackReceiver?.Disconnect();
        sensorReceiver?.Disconnect();
        videoReceiver?.Disconnect();
        IsConnected   = false;
        StatusMessage = "Disconnected";
    }

    public void ApplyPreset(string presetName)
    {
        if (Presets.TryGetValue(presetName, out var action))
        {
            condition = presetName;
            action(this);
            Debug.Log($"[WFIoT MGR] Preset applied: {presetName}");
        }
        else
        {
            Debug.LogWarning($"[WFIoT MGR] Unknown preset: {presetName}");
        }
    }

    public void StartTest()
    {
        if (!IsConnected)
        {
            Debug.LogWarning("[WFIoT MGR] Call Connect() before StartTest().");
            return;
        }
        if (IsRunning)
        {
            Debug.LogWarning("[WFIoT MGR] Test already running. Call StopTest() first.");
            return;
        }
        testCoroutine = StartCoroutine(TestCoroutine());
    }

    public void StopTest()
    {
        if (testCoroutine != null)
        {
            StopCoroutine(testCoroutine);
            testCoroutine = null;
        }
        if (IsRunning)
        {
            publisher?.SendStopCondition(condition);
            IsRunning     = false;
            StatusMessage = $"Stopped — {SamplesReceived}/{SamplesSent} samples";
        }
    }

    public void ExportCsv()
    {
        csvLogger?.ExportResults(condition);
    }

    // ── Update: drain ACK queue and compute RTT ───────────────────────────────

    void Update()
    {
        if (ackReceiver == null) return;

        while (ackReceiver.AckQueue.TryDequeue(out var ack))
        {
            if (!pendingProbes.TryGetValue(ack.seq, out float sendTs))
                continue;

            pendingProbes.Remove(ack.seq);

            // RTT uses Unity's own clock — no cross-device synchronization needed
            float receiveTs = Time.unscaledTime;
            float rtt       = (receiveTs - sendTs) * 1000f;
            bool  isWarmup  = ack.seq < WARMUP_SAMPLES;

            SamplesReceived++;
            RttLatestMs = rtt;
            rttHistory.Add(rtt);
            UpdateRttStats();

            var sample = new LatencySample
            {
                test_id             = ack.test_id             ?? condition,
                condition           = ack.condition           ?? condition,
                seq                 = ack.seq,
                client_send_ts      = sendTs,
                client_receive_ts   = receiveTs,
                rtt_ms              = rtt,
                camera_mode         = ack.active_camera_mode  ?? cameraMode,
                lidar_mode          = ack.active_lidar_mode   ?? lidarMode,
                video_enabled       = ack.video_enabled,
                lidar_enabled       = ack.lidar_enabled,
                probe_rate_hz       = probeRateHz,
                video_fps_received  = VideoFpsReceived,
                stat_hz_received    = StatHzReceived,
                lidar_hz_received   = LidarHzReceived,
                video_payload_bytes = videoReceiver?.LastFrameBytes         ?? 0,
                sensor_payload_bytes = sensorReceiver?.LastSensorPayloadBytes ?? 0,
                warmup              = isWarmup,
                notes               = "",
            };
            csvLogger?.AddSample(sample);
        }
    }

    // ── Test coroutine ────────────────────────────────────────────────────────

    private IEnumerator TestCoroutine()
    {
        IsRunning       = true;
        nextSeq         = 0;
        SamplesSent     = 0;
        SamplesReceived = 0;
        RttLatestMs     = 0f;
        RttMeanMs       = 0f;
        RttMedianMs     = 0f;
        RttP95Ms        = 0f;
        RttMaxMs        = 0f;
        JitterStdMs     = 0f;
        rttHistory.Clear();
        pendingProbes.Clear();
        csvLogger?.Clear();

        StatusMessage = $"Configuring {condition}...";

        // Step 1: Send condition + mode + stream configuration
        publisher.SendStartCondition(condition, condition);
        publisher.SendCameraMode(cameraMode);
        publisher.SendLidarMode(lidarMode);
        publisher.SendStreamConfig(videoEnabled, statEnabled, lidarEnabled,
                                    videoFps, statHz, lidarHz);

        // Step 2: Wait for streams to stabilize (warm-up delay)
        StatusMessage = "Warm-up (1 s)...";
        yield return new WaitForSecondsRealtime(1.0f);

        // Step 3: Probe loop
        StatusMessage     = $"Running {condition}";
        float testStart   = Time.unscaledTime;
        float lastSend    = Time.unscaledTime;
        float interval    = 1f / Mathf.Max(probeRateHz, 0.1f);

        while (IsRunning)
        {
            float now = Time.unscaledTime;

            bool doneByTime  = useDurationInsteadOfCount && (now - testStart) >= testDurationSeconds;
            bool doneByCount = !useDurationInsteadOfCount && SamplesSent >= probeCount;

            if (doneByTime || doneByCount)
                break;

            if ((now - lastSend) >= interval)
            {
                lastSend = now;

                // Capture timestamp in main thread before enqueuing
                float sendTs = Time.unscaledTime;
                int   seq    = nextSeq++;
                pendingProbes[seq] = sendTs;
                publisher.SendLatencyProbe(seq, sendTs, condition, condition);
                SamplesSent++;
            }

            yield return null;
        }

        // Step 4: Finalize
        publisher.SendStopCondition(condition);
        IsRunning     = false;
        StatusMessage = $"Done — {SamplesReceived}/{SamplesSent} | mean={RttMeanMs:F1} ms";

        csvLogger?.ExportResults(condition);
        Debug.Log($"[WFIoT MGR] {condition} complete — " +
                  $"recv={SamplesReceived}/{SamplesSent} " +
                  $"mean={RttMeanMs:F1} ms  p95={RttP95Ms:F1} ms  " +
                  $"jitter={JitterStdMs:F1} ms  loss={LossPercent:F1}%");
    }

    // ── RTT stats (updated every ACK, main thread) ────────────────────────────

    private void UpdateRttStats()
    {
        if (rttHistory.Count == 0) return;

        float sum = 0f, max = float.MinValue;
        foreach (var r in rttHistory) { sum += r; if (r > max) max = r; }
        RttMeanMs = sum / rttHistory.Count;
        RttMaxMs  = max;

        var sorted = new List<float>(rttHistory);
        sorted.Sort();
        RttMedianMs = Percentile(sorted, 50f);
        RttP95Ms    = Percentile(sorted, 95f);

        float variance = rttHistory.Sum(r => (r - RttMeanMs) * (r - RttMeanMs)) / rttHistory.Count;
        JitterStdMs = Mathf.Sqrt(variance);
    }

    private static float Percentile(List<float> sorted, float p)
    {
        if (sorted.Count == 0) return 0f;
        if (sorted.Count == 1) return sorted[0];
        float idx = (p / 100f) * (sorted.Count - 1);
        int   lo  = (int)idx;
        int   hi  = Mathf.Min(lo + 1, sorted.Count - 1);
        return sorted[lo] + (idx - lo) * (sorted[hi] - sorted[lo]);
    }
}
