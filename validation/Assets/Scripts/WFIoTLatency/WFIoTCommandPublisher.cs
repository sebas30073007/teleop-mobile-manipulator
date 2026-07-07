// WFIoTCommandPublisher.cs
// Publishes JSON commands to the NUC simulator via ZMQ PUB socket on port 5002.
// Part of the WF-IoT latency measurement toolset. Does NOT modify any existing project scripts.
//
// ZMQ note: PublisherSocket is owned exclusively by SendLoop (background thread).
// Timestamps (clientSendTs) must be captured in the main thread and passed as parameters.
// NetMQConfig.Cleanup() is intentionally NOT called to avoid affecting other project sockets.

using UnityEngine;
using System;
using System.Threading;
using System.Collections.Concurrent;
using System.Globalization;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

public class WFIoTCommandPublisher : MonoBehaviour
{
    [Header("Connection")]
    public int commandPort = 5002;

    private Thread sendThread;
    private volatile bool running = false;
    private readonly ConcurrentQueue<string> sendQueue = new ConcurrentQueue<string>();
    private string currentIp = "127.0.0.1";

    void Awake()
    {
        // Must be called before any NetMQ socket is created (required for Quest/Android IL2CPP)
        AsyncIO.ForceDotNet.Force();
    }

    void OnDestroy()
    {
        Disconnect();
    }

    // ── Public API ────────────────────────────────────────────────────────────

    public void Connect(string ip, int port = 5002)
    {
        Disconnect();
        currentIp   = ip;
        commandPort = port;
        running     = true;
        sendThread  = new Thread(SendLoop) { IsBackground = true, Name = "WFIoTCmdSend" };
        sendThread.Start();
        Debug.Log($"[WFIoT CMD] PUB connecting to tcp://{ip}:{port}");
    }

    public void Disconnect()
    {
        running = false;
        if (sendThread != null && sendThread.IsAlive)
            sendThread.Join(500);
        sendThread = null;
    }

    /// <param name="clientSendTs">Must be captured with Time.unscaledTime in the main thread.</param>
    public void SendLatencyProbe(int seq, float clientSendTs, string testId, string condition)
    {
        string payload =
            "{\"type\":\"latency_probe\",\"seq\":" + seq +
            ",\"client_send_ts\":" + clientSendTs.ToString("F6", CultureInfo.InvariantCulture) +
            ",\"test_id\":\""    + EscapeJson(testId)    + "\"" +
            ",\"condition\":\"" + EscapeJson(condition) + "\"}";
        Enqueue(payload);
    }

    public void SendCameraMode(string mode)
    {
        Enqueue("{\"type\":\"set_camera_mode\",\"mode\":\"" + EscapeJson(mode) + "\"}");
    }

    public void SendLidarMode(string mode)
    {
        Enqueue("{\"type\":\"set_lidar_mode\",\"mode\":\"" + EscapeJson(mode) + "\"}");
    }

    public void SendStreamConfig(bool videoEnabled, bool statEnabled, bool lidarEnabled,
                                  float videoFps, float statHz, float lidarHz)
    {
        string payload =
            "{\"type\":\"set_stream_config\"" +
            ",\"video_enabled\":"  + BoolStr(videoEnabled) +
            ",\"stat_enabled\":"   + BoolStr(statEnabled) +
            ",\"lidar_enabled\":"  + BoolStr(lidarEnabled) +
            ",\"video_fps\":"      + videoFps.ToString("F1", CultureInfo.InvariantCulture) +
            ",\"stat_hz\":"        + statHz.ToString("F1",  CultureInfo.InvariantCulture) +
            ",\"lidar_hz\":"       + lidarHz.ToString("F1", CultureInfo.InvariantCulture) + "}";
        Enqueue(payload);
    }

    public void SendStartCondition(string testId, string condition)
    {
        Enqueue("{\"type\":\"start_condition\",\"test_id\":\"" + EscapeJson(testId) +
                "\",\"condition\":\"" + EscapeJson(condition) + "\"}");
    }

    public void SendStopCondition(string testId)
    {
        Enqueue("{\"type\":\"stop_condition\",\"test_id\":\"" + EscapeJson(testId) + "\"}");
    }

    // ── Internal ──────────────────────────────────────────────────────────────

    private void Enqueue(string payload)
    {
        if (!string.IsNullOrEmpty(payload))
            sendQueue.Enqueue(payload);
    }

    private void SendLoop()
    {
        try
        {
            using (var pub = new PublisherSocket())
            {
                pub.Options.SendHighWatermark = 20;
                pub.Connect($"tcp://{currentIp}:{commandPort}");
                Thread.Sleep(300); // allow ZMQ slow-joiner handshake

                while (running)
                {
                    if (sendQueue.TryDequeue(out var payload))
                        pub.SendMoreFrame("cmd").SendFrame(payload);
                    else
                        Thread.Sleep(5);
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[WFIoT CMD] SendLoop error: " + e);
        }
    }

    private static string BoolStr(bool v) => v ? "true" : "false";

    private static string EscapeJson(string s)
    {
        if (s == null) return "";
        return s.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }
}
