using UnityEngine;
using System;
using System.Threading;
using System.Collections.Concurrent;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

public class ZmqLidar3DCommandSender : MonoBehaviour
{
    [Header("Ports")]
    public int commandPort = 5002;

    [Header("Fallback IP")]
    public string fallbackIp = "192.168.100.20";

    [Header("Behavior")]
    public bool autoReconnectOnIpChange = false;

    private Thread cmdThread;
    private volatile bool running = false;
    private readonly ConcurrentQueue<string> commandQueue = new ConcurrentQueue<string>();
    private string lastResolvedIp = "";

    public string ServerIp => ResolveIp();

    void Start()
    {
        AsyncIO.ForceDotNet.Force();
        StartThread();
        lastResolvedIp = ResolveIp();
        Debug.Log($"[LIDAR3D CMD] PUB tcp://{lastResolvedIp}:{commandPort}");
    }

    void Update()
    {
        if (!autoReconnectOnIpChange)
            return;

        string ip = ResolveIp();
        if (ip != lastResolvedIp)
        {
            lastResolvedIp = ip;
            Reconnect();
        }
    }

    public void Reconnect()
    {
        StopThread();
        StartThread();
        Debug.Log($"[LIDAR3D CMD] Reconnected PUB tcp://{ResolveIp()}:{commandPort}");
    }

    public void SetModeOff() => SetLidar3DMode("off");
    public void SetModeWalls() => SetLidar3DMode("walls");
    public void SetModePoints() => SetLidar3DMode("points");
    public void SetModeBoth() => SetLidar3DMode("both");

    public void SetLidar3DMode(string mode)
    {
        string clean = Sanitize3DMode(mode);
        EnqueueCommand($"{{\"type\":\"set_lidar_3d_mode\",\"mode\":\"{clean}\"}}");
    }

    public void SetWallsEnabled(bool enabled)
    {
        EnqueueCommand($"{{\"type\":\"set_walls_mode\",\"enabled\":{enabled.ToString().ToLowerInvariant()}}}");
    }

    public void SetPointsEnabled(bool enabled)
    {
        EnqueueCommand($"{{\"type\":\"set_points_mode\",\"enabled\":{enabled.ToString().ToLowerInvariant()}}}");
    }

    public void RequestWallsSnapshot()
    {
        EnqueueCommand("{\"type\":\"request_walls_snapshot\"}");
    }

    public void RequestPointsSnapshot()
    {
        EnqueueCommand("{\"type\":\"request_points_snapshot\"}");
    }

    public void RequestBothSnapshots()
    {
        RequestWallsSnapshot();
        RequestPointsSnapshot();
    }

    public void ApplyToggleState(bool wallsOn, bool pointsOn)
    {
        if (wallsOn && pointsOn)
            SetModeBoth();
        else if (wallsOn)
            SetModeWalls();
        else if (pointsOn)
            SetModePoints();
        else
            SetModeOff();
    }

    private string Sanitize3DMode(string mode)
    {
        if (string.IsNullOrWhiteSpace(mode))
            return "off";

        string m = mode.Trim().ToLowerInvariant();
        if (m == "off" || m == "walls" || m == "points" || m == "both")
            return m;

        return "off";
    }

    private void EnqueueCommand(string payload)
    {
        if (string.IsNullOrWhiteSpace(payload))
            return;

        commandQueue.Enqueue(payload);
        Debug.Log("[LIDAR3D CMD] Queued -> " + payload);
    }

    private string ResolveIp()
    {
        if (NucIpManager.Instance != null)
            return NucIpManager.Instance.GetIp();

        return fallbackIp;
    }

    private void StartThread()
    {
        running = true;
        cmdThread = new Thread(CommandLoop);
        cmdThread.IsBackground = true;
        cmdThread.Start();
    }

    private void StopThread()
    {
        running = false;

        if (cmdThread != null && cmdThread.IsAlive)
            cmdThread.Join(500);

        cmdThread = null;
    }

    private void CommandLoop()
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
            Debug.LogError("[LIDAR3D CMD] Error en CommandLoop: " + e);
        }
    }

    void OnDestroy()
    {
        StopThread();
    }
}
