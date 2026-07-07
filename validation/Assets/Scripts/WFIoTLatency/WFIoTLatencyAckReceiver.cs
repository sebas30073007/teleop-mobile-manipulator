// WFIoTLatencyAckReceiver.cs
// Subscribes to port 5001 topic "latency_ack" and exposes received ACKs via AckQueue.
// Part of the WF-IoT latency measurement toolset.
//
// Design notes:
//   - SubscriberSocket is owned exclusively by ReceiveLoop (background thread).
//   - Polling timeout is 10 ms (not 100 ms) for low-latency ACK detection.
//   - RTT is calculated in the MAIN THREAD: rtt_ms = (Time.unscaledTime - ack.client_send_ts) * 1000f
//   - Time.unscaledTime is NOT read inside the receive thread.
//   - NetMQConfig.Cleanup() intentionally omitted to avoid affecting other project sockets.

using UnityEngine;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

[Serializable]
public class LatencyAckMessage
{
    public int    seq;
    public float  client_send_ts;
    public double server_recv_unix;
    public double server_send_unix;
    public string test_id;
    public string condition;
    public string active_camera_mode;
    public string active_lidar_mode;
    public bool   video_enabled;
    public bool   lidar_enabled;
}

public class WFIoTLatencyAckReceiver : MonoBehaviour
{
    [Header("Connection")]
    public int    sensorPort = 5001;

    /// <summary>Thread-safe queue drained by WFIoTLatencyTestManager.Update().</summary>
    public ConcurrentQueue<LatencyAckMessage> AckQueue { get; } =
        new ConcurrentQueue<LatencyAckMessage>();

    private Thread   recvThread;
    private volatile bool running = false;
    private string   currentIp   = "127.0.0.1";

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

        // Discard stale ACKs from a previous test session
        while (AckQueue.TryDequeue(out _)) { }

        running    = true;
        recvThread = new Thread(ReceiveLoop) { IsBackground = true, Name = "WFIoTAckRecv" };
        recvThread.Start();
        Debug.Log($"[WFIoT ACK] SUB connecting to tcp://{ip}:{port} (topic: latency_ack)");
    }

    public void Disconnect()
    {
        running = false;
        if (recvThread != null && recvThread.IsAlive)
            recvThread.Join(500);
        recvThread = null;
    }

    // ── Receive loop (background thread) ─────────────────────────────────────

    private void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 100;
                sub.Connect($"tcp://{currentIp}:{sensorPort}");
                sub.Subscribe("latency_ack");

                List<byte[]> msg = null;

                while (running)
                {
                    // 10 ms timeout — critical for measuring short RTTs accurately
                    if (!sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(10), ref msg))
                        continue;

                    if (msg == null || msg.Count < 2)
                        continue;

                    string topic = System.Text.Encoding.UTF8.GetString(msg[0]);
                    if (topic != "latency_ack")
                        continue;

                    try
                    {
                        string json = System.Text.Encoding.UTF8.GetString(msg[1]);
                        var ack = JsonUtility.FromJson<LatencyAckMessage>(json);
                        if (ack != null)
                            AckQueue.Enqueue(ack);
                    }
                    catch (Exception e)
                    {
                        Debug.LogWarning("[WFIoT ACK] Parse error: " + e.Message);
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[WFIoT ACK] ReceiveLoop error: " + e);
        }
    }
}
