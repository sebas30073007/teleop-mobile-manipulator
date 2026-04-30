using UnityEngine;
using UnityEngine.UI;
using System;
using System.Threading;
using System.Collections.Generic;
using System.Collections.Concurrent;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

public class ZmqVideoReceiver : MonoBehaviour
{
    [Header("UI")]
    public RawImage targetImage;

    [Header("Ports")]
    public int videoPort = 5555;
    public int commandPort = 5002;

    [Header("Fallback IP")]
    public string fallbackIp = "192.168.100.20";

    [Header("Startup")]
    public string startupCameraMode = "normal";
    public bool requestModeOnStart = true;

    [Header("Connection")]
    [SerializeField] private float disconnectTimeout = 1.0f;

    private const string VideoTopic = "video_rgb";

    private Texture2D videoTexture;
    private Thread recvThread;
    private Thread cmdThread;
    private volatile bool running = false;

    private readonly ConcurrentQueue<byte[]> frameQueue = new ConcurrentQueue<byte[]>();
    private readonly ConcurrentQueue<string> commandQueue = new ConcurrentQueue<string>();

    private float lastFrameRealtime = -999f;
    private float fpsWindowStart = 0f;
    private int fpsFrames = 0;

    private string currentCameraMode = "normal";

    public string CurrentTopic => VideoTopic;
    public string ServerIp => ResolveIp();
    public float CurrentFps { get; private set; } = 0f;
    public int CurrentWidth { get; private set; } = 0;
    public int CurrentHeight { get; private set; } = 0;
    public bool IsConnected => (Time.unscaledTime - lastFrameRealtime) <= disconnectTimeout;
    public string CurrentCameraMode => currentCameraMode;

    void Start()
    {
        if (targetImage == null)
        {
            Debug.LogError("[CAM] No asignaste targetImage");
            return;
        }

        fpsWindowStart = Time.unscaledTime;
        videoTexture = new Texture2D(2, 2, TextureFormat.RGB24, false);
        targetImage.texture = videoTexture;
        currentCameraMode = SanitizeCameraMode(startupCameraMode);

        AsyncIO.ForceDotNet.Force();
        StartThreads();

        if (requestModeOnStart)
            EnqueueCameraModeCommand(currentCameraMode);

        Debug.Log($"[ZMQ] Video SUB tcp://{ResolveIp()}:{videoPort} | topic fijo={VideoTopic}");
        Debug.Log($"[ZMQ] Cmd PUB  tcp://{ResolveIp()}:{commandPort} | camera_mode={currentCameraMode}");
    }

    public void Reconnect()
    {
        StopThreads();
        ClearPendingFrames();
        lastFrameRealtime = -999f;
        CurrentFps = 0f;
        fpsFrames = 0;
        fpsWindowStart = Time.unscaledTime;
        StartThreads();
        if (requestModeOnStart)
            EnqueueCameraModeCommand(currentCameraMode);
    }

    public void SetCameraNormal() => RequestCameraMode("normal");
    public void SetCameraPose() => RequestCameraMode("pose");
    public void SetCameraSegment() => RequestCameraMode("segment");
    public void SetCameraOff() => RequestCameraMode("off");

    public void RequestCameraMode(string mode)
    {
        string clean = SanitizeCameraMode(mode);
        currentCameraMode = clean;
        EnqueueCameraModeCommand(clean);
        Debug.Log($"[CAM] Cmd queued -> {clean}");
    }

    private string ResolveIp()
    {
        if (NucIpManager.Instance != null)
            return NucIpManager.Instance.GetIp();
        return fallbackIp;
    }

    private void StartThreads()
    {
        running = true;
        recvThread = new Thread(ReceiveLoop) { IsBackground = true };
        recvThread.Start();
        cmdThread = new Thread(CommandLoop) { IsBackground = true };
        cmdThread.Start();
    }

    private void StopThreads()
    {
        running = false;
        if (recvThread != null && recvThread.IsAlive) recvThread.Join(500);
        if (cmdThread != null && cmdThread.IsAlive) cmdThread.Join(500);
        recvThread = null;
        cmdThread = null;
    }

    private string SanitizeCameraMode(string mode)
    {
        if (string.IsNullOrWhiteSpace(mode)) return "normal";
        string m = mode.Trim().ToLowerInvariant();
        if (m == "normal" || m == "pose" || m == "segment" || m == "off") return m;
        if (m == "rgb") return "normal";
        return "normal";
    }

    private void EnqueueCameraModeCommand(string mode)
    {
        commandQueue.Enqueue("{\"type\":\"set_camera_mode\",\"mode\":\"" + mode + "\"}");
    }

    private void ClearPendingFrames()
    {
        while (frameQueue.TryDequeue(out _)) { }
    }

    void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 1;
                sub.Connect($"tcp://{ResolveIp()}:{videoPort}");
                sub.Subscribe(VideoTopic);

                List<byte[]> msg = null;
                while (running)
                {
                    if (sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(100), ref msg))
                    {
                        if (msg == null || msg.Count < 2)
                            continue;
                        while (frameQueue.Count > 1)
                            frameQueue.TryDequeue(out _);
                        frameQueue.Enqueue(msg[1]);
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[ZMQ] Error en Video ReceiveLoop: " + e);
        }
    }

    void CommandLoop()
    {
        try
        {
            using (var pub = new PublisherSocket())
            {
                pub.Options.SendHighWatermark = 10;
                pub.Connect($"tcp://{ResolveIp()}:{commandPort}");
                Thread.Sleep(300);

                while (running)
                {
                    if (commandQueue.TryDequeue(out var payload))
                    {
                        for (int i = 0; i < 2; i++)
                        {
                            pub.SendMoreFrame("cmd").SendFrame(payload);
                            Thread.Sleep(30);
                        }
                    }
                    else
                    {
                        Thread.Sleep(10);
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[ZMQ] Error en Video CommandLoop: " + e);
        }
    }

    void Update()
    {
        byte[] latestFrame = null;
        while (frameQueue.TryDequeue(out var frame)) latestFrame = frame;

        if (latestFrame != null && latestFrame.Length > 0)
        {
            bool ok = videoTexture.LoadImage(latestFrame);
            if (ok)
            {
                targetImage.texture = videoTexture;
                lastFrameRealtime = Time.unscaledTime;
                CurrentWidth = videoTexture.width;
                CurrentHeight = videoTexture.height;

                fpsFrames++;
                float elapsed = Time.unscaledTime - fpsWindowStart;
                if (elapsed >= 1f)
                {
                    CurrentFps = fpsFrames / elapsed;
                    fpsFrames = 0;
                    fpsWindowStart = Time.unscaledTime;
                }
            }
        }
    }

    void OnDestroy()
    {
        StopThreads();
    }
}
