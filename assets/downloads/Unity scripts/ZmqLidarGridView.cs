using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System;
using System.Threading;
using System.Collections.Generic;
using System.Collections.Concurrent;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

[Serializable]
public class LidarGridPayload
{
    public float ts;
    public string mode;
    public int grid_size;
    public float cell_size_m;
    public float radius_m;
    public int hits;
    public int[] occupancy;
}

public class ZmqLidarGridView : MonoBehaviour
{
    [Header("UI")]
    public RawImage targetImage;
    public TMP_Text modeLabel;

    [Header("Ports")]
    public int sensorPort = 5001;
    public int commandPort = 5002;

    [Header("Fallback IP")]
    public string fallbackIp = "192.168.100.20";

    [Header("Startup")]
    public string startupMode = "detail";
    public bool requestModeOnStart = true;

    [Header("Connection")]
    public float disconnectTimeout = 2.0f;

    [Header("Visual")]
    public Color32 emptyColor = new Color32(245, 245, 245, 255);
    public Color32 occupiedColor = new Color32(10, 10, 10, 255);
    public Color32 gridLineColor = new Color32(210, 210, 210, 255);
    public Color32 robotColor = new Color32(64, 220, 120, 255);
    public Color32 forwardColor = new Color32(80, 160, 255, 255);
    [Range(0, 10)] public int robotMarkerRadius = 0;
    public bool drawGridLines = false;
    [Min(1)] public int pointSize = 3;
    public bool roundPoints = true;
    [Range(0f, 1f)] public float pointAlpha = 1f;
    [Min(1)] public int detailPointSize = 3;
    [Min(1)] public int mediumPointSize = 5;
    [Min(1)] public int panoramaPointSize = 7;
    public bool autoPointSizeByMode = true;
    [Header("Texture")]
    public bool useBilinearFilter = false;

    private Thread recvThread;
    private Thread cmdThread;
    private volatile bool running = false;
    private readonly ConcurrentQueue<LidarGridPayload> gridQueue = new ConcurrentQueue<LidarGridPayload>();
    private readonly ConcurrentQueue<string> commandQueue = new ConcurrentQueue<string>();
    private Texture2D gridTexture;
    private Color32[] pixelBuffer;
    private float lastGridRealtime = -999f;
    private string requestedMode = "detail";

    public string ServerIp => ResolveIp();
    public bool IsConnected => (Time.unscaledTime - lastGridRealtime) <= disconnectTimeout;
    public string CurrentMode { get; private set; } = "detail";
    public int CurrentGridSize { get; private set; } = 0;
    public float CurrentCellSizeM { get; private set; } = 0f;
    public float CurrentRadiusM { get; private set; } = 0f;
    public int CurrentHits { get; private set; } = 0;

    void Start()
    {
        if (targetImage == null)
        {
            Debug.LogError("[LIDAR] No asignaste targetImage");
            return;
        }

        requestedMode = SanitizeMode(startupMode);
        CurrentMode = requestedMode;
        AsyncIO.ForceDotNet.Force();
        CreateTexture(40);
        StartThreads();

        if (requestModeOnStart)
        {
            RequestMode(requestedMode);
            RequestMode(requestedMode);
        }

        UpdateModeLabel();
    }

    public void Reconnect()
    {
        StopThreads();
        StartThreads();
    }

    public void SetDetail() => RequestMode("detail");
    public void SetMedium() => RequestMode("medium");
    public void SetPanorama() => RequestMode("panorama");
    public void SetOff() => RequestMode("off");

    public void RequestMode(string mode)
    {
        string clean = SanitizeMode(mode);
        requestedMode = clean;
        CurrentMode = clean;
        UpdateModeLabel();
        commandQueue.Enqueue("{\"type\":\"set_lidar_mode\",\"mode\":\"" + clean + "\"}");
    }

    private string ResolveIp()
    {
        if (NucIpManager.Instance != null) return NucIpManager.Instance.GetIp();
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

    private string SanitizeMode(string mode)
    {
        if (string.IsNullOrWhiteSpace(mode)) return "detail";
        string m = mode.Trim().ToLowerInvariant();
        if (m == "detail" || m == "medium" || m == "panorama" || m == "off") return m;
        return "detail";
    }

    void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 10;
                sub.Connect($"tcp://{ResolveIp()}:{sensorPort}");
                sub.Subscribe("lidar_grid");
                List<byte[]> msg = null;
                while (running)
                {
                    if (sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(100), ref msg))
                    {
                        if (msg == null || msg.Count < 2) continue;
                        if (System.Text.Encoding.UTF8.GetString(msg[0]) != "lidar_grid") continue;
                        try
                        {
                            var payload = JsonUtility.FromJson<LidarGridPayload>(System.Text.Encoding.UTF8.GetString(msg[1]));
                            if (payload != null && payload.occupancy != null)
                            {
                                while (gridQueue.Count > 1) gridQueue.TryDequeue(out _);
                                gridQueue.Enqueue(payload);
                            }
                        }
                        catch (Exception e)
                        {
                            Debug.LogWarning("[LIDAR] Error parseando lidar_grid: " + e.Message);
                        }
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[LIDAR] Error en ReceiveLoop: " + e);
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
                    else Thread.Sleep(10);
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[LIDAR] Error en CommandLoop: " + e);
        }
    }

    void Update()
    {
        LidarGridPayload latest = null;
        while (gridQueue.TryDequeue(out var grid)) latest = grid;
        if (latest != null)
        {
            RenderGrid(latest);
            lastGridRealtime = Time.unscaledTime;
        }
    }

    private void CreateTexture(int gridSize)
    {
        CurrentGridSize = gridSize;
        gridTexture = new Texture2D(gridSize, gridSize, TextureFormat.RGBA32, false);
        gridTexture.filterMode = useBilinearFilter ? FilterMode.Bilinear : FilterMode.Point;
        gridTexture.wrapMode = TextureWrapMode.Clamp;
        pixelBuffer = new Color32[gridSize * gridSize];
        ClearTexture();
        targetImage.texture = gridTexture;
    }

    private void ClearTexture()
    {
        if (pixelBuffer == null || gridTexture == null) return;
        for (int i = 0; i < pixelBuffer.Length; i++) pixelBuffer[i] = emptyColor;
        gridTexture.SetPixels32(pixelBuffer);
        gridTexture.Apply(false);
    }

    private int GetPointSizeForCurrentMode()
    {
        if (!autoPointSizeByMode) return Mathf.Max(1, pointSize);
        switch (CurrentMode)
        {
            case "detail": return Mathf.Max(1, detailPointSize);
            case "medium": return Mathf.Max(1, mediumPointSize);
            case "panorama": return Mathf.Max(1, panoramaPointSize);
            default: return Mathf.Max(1, pointSize);
        }
    }

    private void RenderGrid(LidarGridPayload grid)
    {
        if (grid.grid_size <= 0 || grid.occupancy == null) return;
        if (gridTexture == null || gridTexture.width != grid.grid_size || gridTexture.height != grid.grid_size)
            CreateTexture(grid.grid_size);

        CurrentMode = string.IsNullOrWhiteSpace(grid.mode) ? requestedMode : grid.mode;
        CurrentCellSizeM = grid.cell_size_m;
        CurrentRadiusM = grid.radius_m;
        CurrentHits = grid.hits;

        int size = grid.grid_size;
        for (int i = 0; i < pixelBuffer.Length; i++) pixelBuffer[i] = emptyColor;

        int maxCount = Mathf.Min(grid.occupancy.Length, size * size);
        Color32 lidarPointColor = occupiedColor;
        lidarPointColor.a = (byte)Mathf.RoundToInt(Mathf.Clamp01(pointAlpha) * 255f);
        int effectivePointSize = GetPointSizeForCurrentMode();

        for (int idx = 0; idx < maxCount; idx++)
        {
            if (grid.occupancy[idx] == 0) continue;
            int row = idx / size;
            int col = idx % size;
            int texY = (size - 1) - row;
            PaintPoint(col, texY, effectivePointSize, lidarPointColor, roundPoints);
        }

        gridTexture.SetPixels32(pixelBuffer);
        gridTexture.Apply(false);
        targetImage.texture = gridTexture;
        UpdateModeLabel();
    }

    private void PaintPoint(int cx, int cy, int sizePx, Color32 color, bool round)
    {
        int texSize = gridTexture.width;
        int r = Mathf.Max(0, sizePx - 1);
        for (int dy = -r; dy <= r; dy++)
        {
            for (int dx = -r; dx <= r; dx++)
            {
                if (round && (dx * dx + dy * dy > r * r)) continue;
                int x = cx + dx;
                int y = cy + dy;
                if (x < 0 || x >= texSize || y < 0 || y >= texSize) continue;
                pixelBuffer[y * texSize + x] = color;
            }
        }
    }

    private void UpdateModeLabel()
    {
        if (modeLabel == null) return;
        string pretty = CurrentMode == "detail" ? "Detail" : CurrentMode == "medium" ? "Medium" : CurrentMode == "panorama" ? "Panorama" : CurrentMode == "off" ? "Off" : CurrentMode;
        if (CurrentRadiusM > 0f && CurrentCellSizeM > 0f)
            modeLabel.text = $"{pretty} | {CurrentCellSizeM:0.000} m | R={CurrentRadiusM:0.0} m | Grid {CurrentGridSize}x{CurrentGridSize}";
        else
            modeLabel.text = pretty;
    }

    void OnDestroy()
    {
        StopThreads();
    }
}
