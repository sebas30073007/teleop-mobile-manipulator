// WFIoTLatencyCsvLogger.cs
// Accumulates LatencySample structs in memory and exports two CSV files:
//   - Detail  (one row per sample):  wfiot_latency_results_YYYYMMDD_HHMMSS.csv
//   - Summary (one row per condition): wfiot_latency_summary_YYYYMMDD_HHMMSS.csv
//
// Written to Application.persistentDataPath.
// On Quest (Android), extract with:
//   adb pull /sdcard/Android/data/<bundle_id>/files/  ./csv_export/
// Part of the WF-IoT latency measurement toolset.

using UnityEngine;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

/// <summary>One latency measurement sample.</summary>
public struct LatencySample
{
    public string test_id;
    public string condition;
    public int    seq;
    public float  client_send_ts;
    public float  client_receive_ts;
    public float  rtt_ms;
    public string camera_mode;
    public string lidar_mode;
    public bool   video_enabled;
    public bool   lidar_enabled;
    public float  probe_rate_hz;
    public float  video_fps_received;
    public float  stat_hz_received;
    public float  lidar_hz_received;
    public int    video_payload_bytes;
    public int    sensor_payload_bytes;
    public bool   warmup;   // true = warm-up sample, excluded from summary stats
    public string notes;
}

public class WFIoTLatencyCsvLogger : MonoBehaviour
{
    private readonly List<LatencySample> samples = new List<LatencySample>();

    /// <summary>Full path of the most recently exported detail file.</summary>
    public string LastExportPath { get; private set; } = "";

    // ── Public API ────────────────────────────────────────────────────────────

    public void AddSample(LatencySample sample)
    {
        samples.Add(sample);
    }

    public void Clear()
    {
        samples.Clear();
        LastExportPath = "";
    }

    /// <summary>
    /// Writes detail and summary CSVs to Application.persistentDataPath.
    /// Logs the full path to Debug.Log for ADB extraction reference.
    /// </summary>
    public void ExportResults(string testId)
    {
        if (samples.Count == 0)
        {
            Debug.LogWarning("[WFIoT CSV] No samples to export.");
            return;
        }

        string ts       = DateTime.Now.ToString("yyyyMMdd_HHmmss");
        string basePath = Application.persistentDataPath;

        string detailPath  = Path.Combine(basePath, $"wfiot_latency_results_{ts}.csv");
        string summaryPath = Path.Combine(basePath, $"wfiot_latency_summary_{ts}.csv");

        try
        {
            WriteDetailCsv(detailPath);
            WriteSummaryCsv(summaryPath);

            LastExportPath = detailPath;
            Debug.Log($"[WFIoT CSV] Detail  → {detailPath}");
            Debug.Log($"[WFIoT CSV] Summary → {summaryPath}");
            Debug.Log($"[WFIoT CSV] ADB: adb pull \"{Application.persistentDataPath}\"");
        }
        catch (Exception e)
        {
            Debug.LogError("[WFIoT CSV] Export error: " + e);
        }
    }

    // ── Detail CSV ────────────────────────────────────────────────────────────

    private void WriteDetailCsv(string path)
    {
        using (var sw = new StreamWriter(path, false, Encoding.UTF8))
        {
            sw.WriteLine(
                "test_id,condition,seq,client_send_ts,client_receive_ts,rtt_ms," +
                "camera_mode,lidar_mode,video_enabled,lidar_enabled," +
                "probe_rate_hz,video_fps_received,stat_hz_received,lidar_hz_received," +
                "video_payload_bytes,sensor_payload_bytes,warmup,notes"
            );

            foreach (var s in samples)
            {
                sw.WriteLine(
                    $"{Esc(s.test_id)},{Esc(s.condition)},{s.seq}," +
                    $"{F(s.client_send_ts)},{F(s.client_receive_ts)},{F(s.rtt_ms)}," +
                    $"{Esc(s.camera_mode)},{Esc(s.lidar_mode)}," +
                    $"{B(s.video_enabled)},{B(s.lidar_enabled)}," +
                    $"{F(s.probe_rate_hz)},{F(s.video_fps_received)}," +
                    $"{F(s.stat_hz_received)},{F(s.lidar_hz_received)}," +
                    $"{s.video_payload_bytes},{s.sensor_payload_bytes}," +
                    $"{B(s.warmup)},{Esc(s.notes)}"
                );
            }
        }
    }

    // ── Summary CSV ───────────────────────────────────────────────────────────

    private void WriteSummaryCsv(string path)
    {
        // Group by condition — exclude warmup samples from stats
        var groups = samples
            .GroupBy(s => s.condition)
            .OrderBy(g => g.Key);

        using (var sw = new StreamWriter(path, false, Encoding.UTF8))
        {
            sw.WriteLine(
                "condition,samples_sent,samples_received,loss_percent," +
                "rtt_mean_ms,rtt_median_ms,rtt_min_ms,rtt_max_ms," +
                "rtt_p95_ms,rtt_p99_ms,jitter_std_ms"
            );

            foreach (var group in groups)
            {
                int   sent     = group.Count();
                var   measured = group.Where(s => !s.warmup && s.rtt_ms > 0f)
                                      .Select(s => s.rtt_ms)
                                      .ToList();
                int   received = measured.Count;
                float loss     = sent > 0 ? (sent - received) * 100f / sent : 0f;

                if (received == 0)
                {
                    sw.WriteLine($"{Esc(group.Key)},{sent},{received},{F(loss)}," +
                                 "0,0,0,0,0,0,0");
                    continue;
                }

                float mean    = measured.Average();
                float min     = measured.Min();
                float max     = measured.Max();
                measured.Sort();
                float median  = Percentile(measured, 50f);
                float p95     = Percentile(measured, 95f);
                float p99     = Percentile(measured, 99f);
                float variance = measured.Sum(r => (r - mean) * (r - mean)) / received;
                float jitter  = Mathf.Sqrt(variance);

                sw.WriteLine(
                    $"{Esc(group.Key)},{sent},{received},{F(loss)}," +
                    $"{F(mean)},{F(median)},{F(min)},{F(max)}," +
                    $"{F(p95)},{F(p99)},{F(jitter)}"
                );
            }
        }
    }

    // ── Percentile (linear interpolation, input must be sorted) ──────────────

    private static float Percentile(List<float> sorted, float p)
    {
        if (sorted.Count == 0) return 0f;
        if (sorted.Count == 1) return sorted[0];
        float idx = (p / 100f) * (sorted.Count - 1);
        int   lo  = (int)idx;
        int   hi  = Mathf.Min(lo + 1, sorted.Count - 1);
        return sorted[lo] + (idx - lo) * (sorted[hi] - sorted[lo]);
    }

    // ── Format helpers ────────────────────────────────────────────────────────

    private static string F(float v) =>
        v.ToString("F4", System.Globalization.CultureInfo.InvariantCulture);

    private static string B(bool v) => v ? "true" : "false";

    /// <summary>Escapes commas and quotes for CSV safety (no external libraries needed).</summary>
    private static string Esc(string s)
    {
        if (s == null) return "";
        if (s.Contains(',') || s.Contains('"') || s.Contains('\n'))
            return "\"" + s.Replace("\"", "\"\"") + "\"";
        return s;
    }
}
