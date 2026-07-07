// WFIoTSimSensorReceiver.cs
// Subscribes to port 5001 topics "stat", "mode_ack", "lidar_grid".
// Counts messages and measures effective receive frequency.
// Does NOT render any grid — purely for throughput/frequency monitoring.
// Part of the WF-IoT latency measurement toolset.

using UnityEngine;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

public class WFIoTSimSensorReceiver : MonoBehaviour
{
    [Header("Connection")]
    public int sensorPort = 5001;

    // ── Publicly readable metrics (updated in Update — main thread only) ─────
    public int    StatCount              { get; private set; }
    public int    LidarGridCount         { get; private set; }
    public int    ModeAckCount           { get; private set; }
    public float  LastStatHz             { get; private set; }
    public float  LastLidarHz            { get; private set; }
    public int    LastSensorPayloadBytes { get; private set; }
    public string LastActiveCameraMode   { get; private set; } = "unknown";
    public string LastActiveLidarMode    { get; private set; } = "unknown";

    // ── Internal ──────────────────────────────────────────────────────────────
    private struct SensorMsg { public string topic; public string json; public int bytes; }
    private readonly ConcurrentQueue<SensorMsg> msgQueue = new ConcurrentQueue<SensorMsg>();

    private Thread   recvThread;
    private volatile bool running = false;
    private string   currentIp   = "127.0.0.1";

    // Hz window accumulators (main thread)
    private float statWindowStart  = 0f;
    private int   statWindowCount  = 0;
    private float lidarWindowStart = 0f;
    private int   lidarWindowCount = 0;

    void Awake()
    {
        AsyncIO.ForceDotNet.Force();
    }

    void OnDestroy()
    {
        Disconnect();
    }

    // ── Public API ────────────────────────────────────────────────────────────

    public void Connect(string ip, int port = 5001)
    {
        Disconnect();
        currentIp  = ip;
        sensorPort = port;
        running    = true;

        statWindowStart  = Time.unscaledTime;
        lidarWindowStart = Time.unscaledTime;

        recvThread = new Thread(ReceiveLoop) { IsBackground = true, Name = "WFIoTSensorRecv" };
        recvThread.Start();
        Debug.Log($"[WFIoT SENSOR] SUB connecting to tcp://{ip}:{port} (stat/mode_ack/lidar_grid)");
    }

    public void Disconnect()
    {
        running = false;
        if (recvThread != null && recvThread.IsAlive)
            recvThread.Join(500);
        recvThread = null;
    }

    // ── Update: drain queue and compute metrics in main thread ────────────────

    void Update()
    {
        float now = Time.unscaledTime;

        while (msgQueue.TryDequeue(out var item))
        {
            LastSensorPayloadBytes = item.bytes;

            switch (item.topic)
            {
                case "stat":
                    StatCount++;
                    statWindowCount++;
                    TryExtractModes(item.json);
                    break;

                case "mode_ack":
                    ModeAckCount++;
                    statWindowCount++;
                    TryExtractModes(item.json);
                    break;

                case "lidar_grid":
                    LidarGridCount++;
                    lidarWindowCount++;
                    break;
            }
        }

        // Recompute Hz once per second
        float statElapsed = now - statWindowStart;
        if (statElapsed >= 1f)
        {
            LastStatHz      = statWindowCount / statElapsed;
            statWindowCount = 0;
            statWindowStart = now;
        }

        float lidarElapsed = now - lidarWindowStart;
        if (lidarElapsed >= 1f)
        {
            LastLidarHz      = lidarWindowCount / lidarElapsed;
            lidarWindowCount = 0;
            lidarWindowStart = now;
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private void TryExtractModes(string json)
    {
        try
        {
            int camIdx = json.IndexOf("\"active_camera_mode\"", StringComparison.Ordinal);
            if (camIdx >= 0)
            {
                int vs = json.IndexOf('"', camIdx + 21) + 1;
                int ve = json.IndexOf('"', vs);
                if (vs > 0 && ve > vs)
                    LastActiveCameraMode = json.Substring(vs, ve - vs);
            }

            int lidIdx = json.IndexOf("\"active_lidar_mode\"", StringComparison.Ordinal);
            if (lidIdx >= 0)
            {
                int vs = json.IndexOf('"', lidIdx + 20) + 1;
                int ve = json.IndexOf('"', vs);
                if (vs > 0 && ve > vs)
                    LastActiveLidarMode = json.Substring(vs, ve - vs);
            }
        }
        catch { /* non-critical — ignore parse failures */ }
    }

    // ── Receive loop (background thread) ─────────────────────────────────────

    private void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 50;
                sub.Connect($"tcp://{currentIp}:{sensorPort}");
                sub.Subscribe("stat");
                sub.Subscribe("mode_ack");
                sub.Subscribe("lidar_grid");

                List<byte[]> msg = null;

                while (running)
                {
                    if (!sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(50), ref msg))
                        continue;

                    if (msg == null || msg.Count < 2)
                        continue;

                    string topic = System.Text.Encoding.UTF8.GetString(msg[0]);
                    string json  = System.Text.Encoding.UTF8.GetString(msg[1]);
                    msgQueue.Enqueue(new SensorMsg { topic = topic, json = json, bytes = msg[1].Length });
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[WFIoT SENSOR] ReceiveLoop error: " + e);
        }
    }
}
