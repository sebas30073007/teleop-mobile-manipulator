// WFIoTLatencyResponder.cs
// ─────────────────────────────────────────────────────────────────────────────
// PASSIVE Quest-side responder for PC-orchestrated latency experiments.
//
// Flow (new architecture):
//   PC  → Quest  latency_probe  via SUB :5001   (Quest receives probe)
//   Quest → PC   latency_ack   via PUB :5002   (Quest echoes ACK immediately)
//
// RTT is measured entirely on the PC clock (no Quest clock needed).
// Quest just echoes seq back — no float precision issues.
//
// This script has NO UI interaction. Attach it to a GameObject and it runs
// automatically. Status properties are read by WFIoTLatencySceneBootstrap
// for the passive display panel.
// ─────────────────────────────────────────────────────────────────────────────

using UnityEngine;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Globalization;
using System.Threading;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

[Serializable]
public class LatencyProbeMsg
{
    public int    seq;
    public string test_id;
    public string condition;
}

[Serializable]
public class StatFromPC
{
    public string active_camera_mode;
    public string active_lidar_mode;
    public string current_test_id;
    public bool   video_enabled;
    public bool   lidar_enabled;
}

public class WFIoTLatencyResponder : MonoBehaviour
{
    [Header("Connection — must match PC simulator")]
    [SerializeField] public string serverIp  = "192.168.100.5";
    [SerializeField] public int    subPort   = 5001;  // receive probes from PC
    [SerializeField] public int    pubPort   = 5002;  // send ACKs to PC

    // ── Public status (read by Bootstrap display, updated in Update) ──────────
    public int    ProbesReceived   { get; private set; }
    public int    AcksSent         { get; private set; }
    public string CurrentTestId    { get; private set; } = "—";
    public string CurrentCondition { get; private set; } = "—";
    public string CurrentCameraMode{ get; private set; } = "off";
    public string CurrentLidarMode { get; private set; } = "off";
    public bool   VideoEnabled     { get; private set; }
    public bool   LidarEnabled     { get; private set; }
    public bool   IsConnected      { get; private set; }

    // ── Internal ──────────────────────────────────────────────────────────────
    private struct AckToSend { public int seq; public string test_id; public string condition; }
    private struct DisplayUpdate { public string test_id; public string cond;
                                   public string cam;     public string lid;
                                   public bool vid;       public bool lid_en; }

    private readonly ConcurrentQueue<AckToSend>     ackQueue     = new ConcurrentQueue<AckToSend>();
    private readonly ConcurrentQueue<DisplayUpdate>  displayQueue = new ConcurrentQueue<DisplayUpdate>();

    private Thread   recvThread;
    private Thread   sendThread;
    private volatile bool running = false;

    private float    lastProbeRealtime = -999f;

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    void Awake()
    {
        AsyncIO.ForceDotNet.Force();
    }

    void Start()
    {
        Connect();
    }

    void OnDestroy()
    {
        Disconnect();
    }

    // ── Connection ────────────────────────────────────────────────────────────

    public void Connect()
    {
        Disconnect();
        running    = true;
        recvThread = new Thread(ReceiveLoop) { IsBackground = true, Name = "WFIoTProbeRecv" };
        sendThread = new Thread(SendLoop)    { IsBackground = true, Name = "WFIoTAckSend"   };
        recvThread.Start();
        sendThread.Start();
        Debug.Log($"[WFIoT RESP] SUB tcp://{serverIp}:{subPort} | PUB tcp://{serverIp}:{pubPort}");
    }

    public void Disconnect()
    {
        running = false;
        if (recvThread != null && recvThread.IsAlive) recvThread.Join(500);
        if (sendThread != null && sendThread.IsAlive) sendThread.Join(500);
        recvThread = null;
        sendThread = null;
        IsConnected = false;
    }

    // ── Update: drain display queue ───────────────────────────────────────────

    void Update()
    {
        IsConnected = (Time.unscaledTime - lastProbeRealtime) < 5f;

        while (displayQueue.TryDequeue(out var upd))
        {
            CurrentTestId     = upd.test_id;
            CurrentCondition  = upd.cond;
            CurrentCameraMode = upd.cam;
            CurrentLidarMode  = upd.lid;
            VideoEnabled      = upd.vid;
            LidarEnabled      = upd.lid_en;
        }
    }

    // ── Receive loop (background thread) ─────────────────────────────────────
    // Subscribes to :5001: receives latency_probe and stat from PC.

    private void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 200;
                sub.Connect($"tcp://{serverIp}:{subPort}");
                sub.Subscribe("latency_probe");
                sub.Subscribe("stat");
                sub.Subscribe("start_condition");

                List<byte[]> msg = null;

                while (running)
                {
                    // 10 ms polling — minimizes ACK round-trip delay
                    if (!sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(10), ref msg))
                        continue;

                    if (msg == null || msg.Count < 2)
                        continue;

                    string topic = System.Text.Encoding.UTF8.GetString(msg[0]);
                    string json  = System.Text.Encoding.UTF8.GetString(msg[1]);

                    // ── latency_probe: echo ACK immediately ───────────────────
                    if (topic == "latency_probe")
                    {
                        try
                        {
                            var probe = JsonUtility.FromJson<LatencyProbeMsg>(json);
                            if (probe != null)
                            {
                                ackQueue.Enqueue(new AckToSend
                                {
                                    seq       = probe.seq,
                                    test_id   = probe.test_id   ?? "",
                                    condition = probe.condition ?? "",
                                });
                                ProbesReceived++;
                                lastProbeRealtime = UnityEngine.Time.unscaledTime;

                                // Update display from probe metadata
                                displayQueue.Enqueue(new DisplayUpdate
                                {
                                    test_id = probe.test_id   ?? "",
                                    cond    = probe.condition ?? "",
                                    cam     = CurrentCameraMode,
                                    lid     = CurrentLidarMode,
                                    vid     = VideoEnabled,
                                    lid_en  = LidarEnabled,
                                });
                            }
                        }
                        catch (Exception e)
                        {
                            Debug.LogWarning("[WFIoT RESP] probe parse: " + e.Message);
                        }
                    }

                    // ── stat: update mode display ─────────────────────────────
                    else if (topic == "stat")
                    {
                        try
                        {
                            var st = JsonUtility.FromJson<StatFromPC>(json);
                            if (st != null)
                            {
                                displayQueue.Enqueue(new DisplayUpdate
                                {
                                    test_id = st.current_test_id        ?? CurrentTestId,
                                    cond    = CurrentCondition,
                                    cam     = st.active_camera_mode     ?? "",
                                    lid     = st.active_lidar_mode      ?? "",
                                    vid     = st.video_enabled,
                                    lid_en  = st.lidar_enabled,
                                });
                                lastProbeRealtime = UnityEngine.Time.unscaledTime;
                            }
                        }
                        catch { /* silent */ }
                    }

                    // ── start_condition: update test display ──────────────────
                    else if (topic == "start_condition")
                    {
                        try
                        {
                            // parse test_id from json field
                            int idx = json.IndexOf("\"test_id\"", StringComparison.Ordinal);
                            if (idx >= 0)
                            {
                                int vs = json.IndexOf('"', idx + 10) + 1;
                                int ve = json.IndexOf('"', vs);
                                if (vs > 0 && ve > vs)
                                {
                                    string tid = json.Substring(vs, ve - vs);
                                    displayQueue.Enqueue(new DisplayUpdate
                                    {
                                        test_id = tid, cond = tid,
                                        cam = CurrentCameraMode, lid = CurrentLidarMode,
                                        vid = VideoEnabled, lid_en = LidarEnabled,
                                    });
                                }
                            }
                        }
                        catch { /* silent */ }
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[WFIoT RESP] ReceiveLoop: " + e);
        }
    }

    // ── Send loop (background thread) ─────────────────────────────────────────
    // Drains ackQueue and publishes latency_ack to :5002 as fast as possible.

    private void SendLoop()
    {
        try
        {
            using (var pub = new PublisherSocket())
            {
                pub.Options.SendHighWatermark = 200;
                pub.Connect($"tcp://{serverIp}:{pubPort}");
                Thread.Sleep(300); // ZMQ slow-joiner

                while (running)
                {
                    if (ackQueue.TryDequeue(out var item))
                    {
                        // ACK payload: echo seq + test_id back to PC.
                        // PC looks up RTT via seq in its pending_probes dict.
                        string payload =
                            "{\"type\":\"latency_ack\",\"seq\":" + item.seq +
                            ",\"test_id\":\""   + EscapeJson(item.test_id)   + "\"" +
                            ",\"condition\":\"" + EscapeJson(item.condition) + "\"}";

                        pub.SendMoreFrame("latency_ack").SendFrame(payload);
                        AcksSent++;
                    }
                    else
                    {
                        Thread.Sleep(1); // 1ms idle sleep — keep CPU usage low
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[WFIoT RESP] SendLoop: " + e);
        }
    }

    private static string EscapeJson(string s)
    {
        if (s == null) return "";
        return s.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }
}
