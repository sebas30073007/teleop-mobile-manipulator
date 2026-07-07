// WFIoTSimVideoReceiver.cs
// Subscribes to port 5555 topic "video_rgb" and measures FPS and payload size.
// Optional: decodes JPEG and displays in a RawImage (disable on Quest to save CPU).
// Part of the WF-IoT latency measurement toolset.

using UnityEngine;
using UnityEngine.UI;
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Threading;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

public class WFIoTSimVideoReceiver : MonoBehaviour
{
    [Header("Connection")]
    public int videoPort = 5555;

    [Header("Preview (optional — disable on Quest to save CPU)")]
    [SerializeField] private RawImage previewImage;
    [SerializeField] private bool     decodePreview = false;

    // ── Public metrics ────────────────────────────────────────────────────────
    public int   FramesReceived { get; private set; }
    public float CurrentFps     { get; private set; }
    public int   LastFrameBytes { get; private set; }
    public bool  IsReceiving    { get; private set; }

    // ── Internal ──────────────────────────────────────────────────────────────
    private readonly ConcurrentQueue<byte[]> frameQueue = new ConcurrentQueue<byte[]>();

    private Thread   recvThread;
    private volatile bool running = false;
    private string   currentIp   = "127.0.0.1";

    private Texture2D previewTexture;
    private float     fpsWindowStart = 0f;
    private int       fpsWindowCount = 0;

    void Awake()
    {
        AsyncIO.ForceDotNet.Force();
    }

    void OnDestroy()
    {
        Disconnect();
    }

    // ── Public API ────────────────────────────────────────────────────────────

    public void Connect(string ip, int port = 5555)
    {
        Disconnect();
        currentIp  = ip;
        videoPort  = port;
        running    = false; // will be set true after reset
        IsReceiving    = false;
        FramesReceived = 0;
        CurrentFps     = 0f;
        LastFrameBytes = 0;
        fpsWindowStart = Time.unscaledTime;
        fpsWindowCount = 0;

        if (decodePreview && previewTexture == null)
            previewTexture = new Texture2D(2, 2, TextureFormat.RGB24, false);

        running    = true;
        recvThread = new Thread(ReceiveLoop) { IsBackground = true, Name = "WFIoTVideoRecv" };
        recvThread.Start();
        Debug.Log($"[WFIoT VIDEO] SUB connecting to tcp://{ip}:{port} (topic: video_rgb)");
    }

    public void Disconnect()
    {
        running     = false;
        IsReceiving = false;
        if (recvThread != null && recvThread.IsAlive)
            recvThread.Join(500);
        recvThread = null;
    }

    // ── Update: drain latest frame and update metrics ─────────────────────────

    void Update()
    {
        float now    = Time.unscaledTime;
        byte[] latest = null;

        // Drain queue — keep only the most recent frame
        while (frameQueue.TryDequeue(out var frame))
            latest = frame;

        if (latest != null)
        {
            FramesReceived++;
            LastFrameBytes = latest.Length;
            IsReceiving    = true;
            fpsWindowCount++;

            if (decodePreview && previewTexture != null && previewImage != null)
            {
                previewTexture.LoadImage(latest);
                previewImage.texture = previewTexture;
            }
        }

        // Update FPS estimate every second
        float elapsed = now - fpsWindowStart;
        if (elapsed >= 1f)
        {
            CurrentFps     = fpsWindowCount / elapsed;
            fpsWindowCount = 0;
            fpsWindowStart = now;
        }
    }

    // ── Receive loop (background thread) ─────────────────────────────────────

    private void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 2; // drop stale frames
                sub.Connect($"tcp://{currentIp}:{videoPort}");
                sub.Subscribe("video_rgb");

                List<byte[]> msg = null;

                while (running)
                {
                    if (!sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(10), ref msg))
                        continue;

                    if (msg == null || msg.Count < 2)
                        continue;

                    // Keep at most 1 pending frame to avoid stale display
                    while (frameQueue.Count > 1)
                        frameQueue.TryDequeue(out _);

                    frameQueue.Enqueue(msg[1]);
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[WFIoT VIDEO] ReceiveLoop error: " + e);
        }
    }
}
