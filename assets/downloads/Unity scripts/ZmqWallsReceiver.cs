using UnityEngine;
using TMPro;
using System;
using System.Threading;
using System.Collections.Generic;
using System.Collections.Concurrent;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

public class ZmqWallsReceiver : MonoBehaviour
{
    [Serializable]
    private class IncomingPacket
    {
        public string topic;
        public byte[] payload;
    }

    [Header("NUC")]
    public int wallsPort = 5007;
    public string fallbackIp = "192.168.100.20";

    [Header("Scene")]
    public Transform wallsRoot;
    public TMP_Text statusLabel;

    [Header("Connection")]
    public float disconnectTimeout = 2.0f;

    [Header("Wall Visual")]
    public Material wallMaterial;
    public float wallHeight = 1.2f;
    public float wallThickness = 0.05f;
    public float minSegmentLengthM = 0.08f;
    public float baseY = 0.0f;
    public bool useLocalSpace = true;
    public bool visualsEnabled = true;

    private const string TOPIC_SNAPSHOT = "walls_snapshot";
    private const string TOPIC_DELTA = "walls_delta";

    private static readonly byte[] MAGIC_SNAPSHOT = new byte[] { (byte)'W', (byte)'S', (byte)'N', (byte)'P' };
    private static readonly byte[] MAGIC_DELTA = new byte[] { (byte)'W', (byte)'D', (byte)'E', (byte)'L' };
    private const byte PROTOCOL_VERSION = 1;

    private Thread recvThread;
    private volatile bool running = false;

    private readonly ConcurrentQueue<IncomingPacket> packetQueue = new ConcurrentQueue<IncomingPacket>();
    private readonly Dictionary<string, GameObject> activeWalls = new Dictionary<string, GameObject>();

    private float lastPacketRealtime = -999f;
    private uint lastSeq = 0;
    private bool snapshotReceived = false;
    private int activeWallCount = 0;
    private string lastTopic = "--";

    public bool IsConnected => (Time.unscaledTime - lastPacketRealtime) <= disconnectTimeout;
    public int ActiveWallCount => activeWallCount;
    public uint LastSeq => lastSeq;
    public bool SnapshotReceived => snapshotReceived;
    public string LastTopic => lastTopic;
    public string ServerIp => ResolveIp();

    void Start()
    {
        if (wallsRoot == null)
            wallsRoot = transform;

        AsyncIO.ForceDotNet.Force();
        StartThread();
        UpdateVisualState();
        UpdateStatusLabel();

        Debug.Log($"[WALLS] SUB tcp://{ResolveIp()}:{wallsPort}");
    }

    public void Reconnect()
    {
        StopThread();
        StartThread();
        Debug.Log($"[WALLS] Reconnected SUB tcp://{ResolveIp()}:{wallsPort}");
    }

    public void RequestSnapshot(ZmqLidar3DCommandSender commandSender)
    {
        if (commandSender != null)
            commandSender.RequestWallsSnapshot();
    }

    public void SetVisualsEnabled(bool enabled)
    {
        visualsEnabled = enabled;
        UpdateVisualState();
    }

    public void ClearAllWalls()
    {
        foreach (var kv in activeWalls)
        {
            if (kv.Value != null)
                Destroy(kv.Value);
        }
        activeWalls.Clear();
        activeWallCount = 0;
        snapshotReceived = false;
        UpdateStatusLabel();
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
        recvThread = new Thread(ReceiveLoop);
        recvThread.IsBackground = true;
        recvThread.Start();
    }

    private void StopThread()
    {
        running = false;
        if (recvThread != null && recvThread.IsAlive)
            recvThread.Join(500);
        recvThread = null;
    }

    void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 50;
                sub.Connect($"tcp://{ResolveIp()}:{wallsPort}");
                sub.Subscribe(TOPIC_SNAPSHOT);
                sub.Subscribe(TOPIC_DELTA);

                List<byte[]> msg = null;
                while (running)
                {
                    if (sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(100), ref msg))
                    {
                        if (msg == null || msg.Count < 2)
                            continue;

                        packetQueue.Enqueue(new IncomingPacket
                        {
                            topic = System.Text.Encoding.UTF8.GetString(msg[0]),
                            payload = msg[1]
                        });
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[WALLS] Error en ReceiveLoop: " + e);
        }
    }

    void Update()
    {
        while (packetQueue.TryDequeue(out var packet))
        {
            try
            {
                if (packet.topic == TOPIC_SNAPSHOT)
                    ApplySnapshot(packet.payload);
                else if (packet.topic == TOPIC_DELTA)
                    ApplyDelta(packet.payload);

                lastPacketRealtime = Time.unscaledTime;
                lastTopic = packet.topic;
            }
            catch (Exception e)
            {
                Debug.LogError("[WALLS] Error aplicando paquete " + packet.topic + ": " + e);
            }
        }

        UpdateStatusLabel();
    }

    private void ApplySnapshot(byte[] payload)
    {
        const int headerSize = 13;
        const int segSize = 16;

        if (payload == null || payload.Length < headerSize)
            return;
        if (!CheckMagic(payload, MAGIC_SNAPSHOT))
            return;
        if (payload[4] != PROTOCOL_VERSION)
            return;

        uint seq = BitConverter.ToUInt32(payload, 5);
        uint n = BitConverter.ToUInt32(payload, 9);
        int expected = headerSize + (int)n * segSize;
        if (payload.Length < expected)
            return;

        ClearExistingWallsImmediate();

        int offset = headerSize;
        for (int i = 0; i < n; i++)
        {
            int x1mm = BitConverter.ToInt32(payload, offset + 0);
            int y1mm = BitConverter.ToInt32(payload, offset + 4);
            int x2mm = BitConverter.ToInt32(payload, offset + 8);
            int y2mm = BitConverter.ToInt32(payload, offset + 12);
            offset += segSize;
            AddWallBySegment(x1mm, y1mm, x2mm, y2mm);
        }

        lastSeq = seq;
        snapshotReceived = true;
        activeWallCount = activeWalls.Count;
    }

    private void ApplyDelta(byte[] payload)
    {
        const int headerSize = 13;
        const int segSize = 16;

        if (payload == null || payload.Length < headerSize)
            return;
        if (!CheckMagic(payload, MAGIC_DELTA))
            return;
        if (payload[4] != PROTOCOL_VERSION)
            return;

        uint seq = BitConverter.ToUInt32(payload, 5);
        ushort nAdd = BitConverter.ToUInt16(payload, 9);
        ushort nRem = BitConverter.ToUInt16(payload, 11);
        int expected = headerSize + (nAdd + nRem) * segSize;
        if (payload.Length < expected)
            return;

        int offset = headerSize;
        for (int i = 0; i < nAdd; i++)
        {
            int x1mm = BitConverter.ToInt32(payload, offset + 0);
            int y1mm = BitConverter.ToInt32(payload, offset + 4);
            int x2mm = BitConverter.ToInt32(payload, offset + 8);
            int y2mm = BitConverter.ToInt32(payload, offset + 12);
            offset += segSize;
            AddWallBySegment(x1mm, y1mm, x2mm, y2mm);
        }

        for (int i = 0; i < nRem; i++)
        {
            int x1mm = BitConverter.ToInt32(payload, offset + 0);
            int y1mm = BitConverter.ToInt32(payload, offset + 4);
            int x2mm = BitConverter.ToInt32(payload, offset + 8);
            int y2mm = BitConverter.ToInt32(payload, offset + 12);
            offset += segSize;
            RemoveWallBySegment(x1mm, y1mm, x2mm, y2mm);
        }

        lastSeq = seq;
        activeWallCount = activeWalls.Count;
    }

    private bool CheckMagic(byte[] payload, byte[] expected)
    {
        if (payload == null || payload.Length < 4 || expected == null || expected.Length != 4)
            return false;
        return payload[0] == expected[0] && payload[1] == expected[1] && payload[2] == expected[2] && payload[3] == expected[3];
    }

    private string MakeKey(int x1mm, int y1mm, int x2mm, int y2mm)
    {
        return $"{x1mm}:{y1mm}:{x2mm}:{y2mm}";
    }

    private void AddWallBySegment(int x1mm, int y1mm, int x2mm, int y2mm)
    {
        string key = MakeKey(x1mm, y1mm, x2mm, y2mm);
        if (activeWalls.ContainsKey(key))
            return;

        Vector3 p1 = MmSegmentPointToUnity(x1mm, y1mm);
        Vector3 p2 = MmSegmentPointToUnity(x2mm, y2mm);
        Vector3 mid = (p1 + p2) * 0.5f;
        Vector3 flatDir = p2 - p1;
        flatDir.y = 0f;

        float length = flatDir.magnitude;
        if (length < minSegmentLengthM)
            return;

        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = $"Wall_{key}";
        go.transform.SetParent(wallsRoot, false);

        if (useLocalSpace)
        {
            go.transform.localPosition = new Vector3(mid.x, baseY + wallHeight * 0.5f, mid.z);
            go.transform.localRotation = Quaternion.LookRotation(flatDir.normalized, Vector3.up);
            go.transform.localScale = new Vector3(wallThickness, wallHeight, length);
        }
        else
        {
            go.transform.position = new Vector3(mid.x, baseY + wallHeight * 0.5f, mid.z);
            go.transform.rotation = Quaternion.LookRotation(flatDir.normalized, Vector3.up);
            go.transform.localScale = new Vector3(wallThickness, wallHeight, length);
        }

        if (wallMaterial != null)
        {
            var renderer = go.GetComponent<Renderer>();
            if (renderer != null)
                renderer.sharedMaterial = wallMaterial;
        }

        go.SetActive(visualsEnabled);
        activeWalls[key] = go;
    }

    private void RemoveWallBySegment(int x1mm, int y1mm, int x2mm, int y2mm)
    {
        string key = MakeKey(x1mm, y1mm, x2mm, y2mm);
        if (!activeWalls.TryGetValue(key, out var go))
            return;

        if (go != null)
            Destroy(go);

        activeWalls.Remove(key);
    }

    private void ClearExistingWallsImmediate()
    {
        foreach (var kv in activeWalls)
        {
            if (kv.Value != null)
                Destroy(kv.Value);
        }
        activeWalls.Clear();
        activeWallCount = 0;
    }

    private Vector3 MmSegmentPointToUnity(int xmm, int ymm)
    {
        return new Vector3(xmm / 1000.0f, 0f, ymm / 1000.0f);
    }

    private void UpdateVisualState()
    {
        foreach (var kv in activeWalls)
        {
            if (kv.Value != null)
                kv.Value.SetActive(visualsEnabled);
        }
    }

    private void UpdateStatusLabel()
    {
        if (statusLabel == null)
            return;

        statusLabel.text =
            $"Walls: {(IsConnected ? "Connected" : "Disconnected")}\n" +
            $"Seq: {lastSeq}\n" +
            $"Snapshot: {(snapshotReceived ? "Yes" : "No")}\n" +
            $"Active: {activeWallCount}\n" +
            $"Topic: {lastTopic}";
    }

    void OnDestroy()
    {
        StopThread();
    }
}
