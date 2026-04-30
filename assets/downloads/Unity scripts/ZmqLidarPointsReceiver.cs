using UnityEngine;
using TMPro;
using System;
using System.Threading;
using System.Collections.Generic;
using System.Collections.Concurrent;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

public class ZmqLidarPointsReceiver : MonoBehaviour
{
    [Serializable]
    private class IncomingPacket
    {
        public string topic;
        public byte[] payload;
    }

    [Header("NUC")]
    public int pointsPort = 5007;
    public string fallbackIp = "192.168.100.20";

    [Header("Scene")]
    public Transform pointsRoot;
    public TMP_Text statusLabel;
    public ParticleSystem particleSystemTarget;

    [Header("Connection")]
    public float disconnectTimeout = 2.0f;

    [Header("Points Visual")]
    public bool visualsEnabled = false;
    public float baseY = 0.0f;
    public float pointSize = 0.035f;
    public Color pointColor = new Color(0.1f, 0.9f, 1.0f, 0.95f);
    public int maxRenderPoints = 4000;
    public bool useLocalSpace = true;

    private const string TOPIC_SNAPSHOT = "lidar_points_snapshot";
    private const string TOPIC_FRAME = "lidar_points_frame";

    private static readonly byte[] MAGIC_SNAPSHOT = new byte[] { (byte)'L', (byte)'P', (byte)'S', (byte)'N' };
    private static readonly byte[] MAGIC_FRAME = new byte[] { (byte)'L', (byte)'P', (byte)'F', (byte)'R' };
    private const byte PROTOCOL_VERSION = 1;

    private Thread recvThread;
    private volatile bool running = false;
    private readonly ConcurrentQueue<IncomingPacket> packetQueue = new ConcurrentQueue<IncomingPacket>();

    private float lastPacketRealtime = -999f;
    private uint lastSeq = 0;
    private bool snapshotReceived = false;
    private int activePointCount = 0;
    private string lastTopic = "--";

    private ParticleSystem.Particle[] particles = Array.Empty<ParticleSystem.Particle>();

    public bool IsConnected => (Time.unscaledTime - lastPacketRealtime) <= disconnectTimeout;
    public int ActivePointCount => activePointCount;
    public uint LastSeq => lastSeq;
    public bool SnapshotReceived => snapshotReceived;
    public string LastTopic => lastTopic;
    public string ServerIp => ResolveIp();

    void Start()
    {
        if (pointsRoot == null)
            pointsRoot = transform;

        if (particleSystemTarget == null)
            particleSystemTarget = GetComponent<ParticleSystem>();

        if (particleSystemTarget == null)
            particleSystemTarget = gameObject.AddComponent<ParticleSystem>();

        ConfigureParticleSystem();

        AsyncIO.ForceDotNet.Force();
        StartThread();
        SetVisualsEnabled(visualsEnabled);
        UpdateStatusLabel();

        Debug.Log($"[POINTS] SUB tcp://{ResolveIp()}:{pointsPort}");
    }

    public void Reconnect()
    {
        StopThread();
        StartThread();
        Debug.Log($"[POINTS] Reconnected SUB tcp://{ResolveIp()}:{pointsPort}");
    }

    public void RequestSnapshot(ZmqLidar3DCommandSender commandSender)
    {
        if (commandSender != null)
            commandSender.RequestPointsSnapshot();
    }

    public void SetVisualsEnabled(bool enabled)
    {
        visualsEnabled = enabled;
        if (particleSystemTarget != null)
        {
            var renderer = particleSystemTarget.GetComponent<ParticleSystemRenderer>();
            if (renderer != null)
                renderer.enabled = enabled;
        }
    }

    public void ClearPoints()
    {
        activePointCount = 0;
        if (particleSystemTarget != null)
            particleSystemTarget.Clear();
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

    private void ConfigureParticleSystem()
    {
        var main = particleSystemTarget.main;
        main.loop = false;
        main.playOnAwake = false;
        main.startLifetime = 9999f;
        main.startSpeed = 0f;
        main.startSize = pointSize;
        main.maxParticles = Mathf.Max(maxRenderPoints, 1);
        main.simulationSpace = useLocalSpace ? ParticleSystemSimulationSpace.Local : ParticleSystemSimulationSpace.World;

        var emission = particleSystemTarget.emission;
        emission.enabled = false;

        var shape = particleSystemTarget.shape;
        shape.enabled = false;

        var renderer = particleSystemTarget.GetComponent<ParticleSystemRenderer>();
        renderer.renderMode = ParticleSystemRenderMode.Billboard;
        renderer.enabled = visualsEnabled;
    }

    void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 50;
                sub.Connect($"tcp://{ResolveIp()}:{pointsPort}");
                sub.Subscribe(TOPIC_SNAPSHOT);
                sub.Subscribe(TOPIC_FRAME);

                List<byte[]> msg = null;

                while (running)
                {
                    if (sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(100), ref msg))
                    {
                        if (msg == null || msg.Count < 2)
                            continue;

                        string topic = System.Text.Encoding.UTF8.GetString(msg[0]);
                        byte[] payload = msg[1];

                        packetQueue.Enqueue(new IncomingPacket
                        {
                            topic = topic,
                            payload = payload
                        });
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[POINTS] Error en ReceiveLoop: " + e);
        }
    }

    void Update()
    {
        while (packetQueue.TryDequeue(out var packet))
        {
            try
            {
                if (packet.topic == TOPIC_SNAPSHOT)
                    ApplyPacket(packet.payload, true, TOPIC_SNAPSHOT);
                else if (packet.topic == TOPIC_FRAME)
                    ApplyPacket(packet.payload, false, TOPIC_FRAME);

                lastPacketRealtime = Time.unscaledTime;
                lastTopic = packet.topic;
            }
            catch (Exception e)
            {
                Debug.LogError("[POINTS] Error aplicando paquete " + packet.topic + ": " + e);
            }
        }

        UpdateStatusLabel();
    }

    private void ApplyPacket(byte[] payload, bool markSnapshotReceived, string expectedTopic)
    {
        const int headerSize = 13;
        const int pointSizeBytes = 8;

        if (payload == null || payload.Length < headerSize)
            return;

        bool okMagic = expectedTopic == TOPIC_SNAPSHOT ? CheckMagic(payload, MAGIC_SNAPSHOT) : CheckMagic(payload, MAGIC_FRAME);
        if (!okMagic)
        {
            Debug.LogWarning("[POINTS] Packet con magic inválido.");
            return;
        }

        byte version = payload[4];
        if (version != PROTOCOL_VERSION)
        {
            Debug.LogWarning($"[POINTS] Version no soportada: {version}");
            return;
        }

        uint seq = BitConverter.ToUInt32(payload, 5);
        uint n = BitConverter.ToUInt32(payload, 9);

        int expected = headerSize + (int)n * pointSizeBytes;
        if (payload.Length < expected)
        {
            Debug.LogWarning("[POINTS] Packet truncado.");
            return;
        }

        int renderCount = Mathf.Min((int)n, Mathf.Max(1, maxRenderPoints));
        EnsureParticleArray(renderCount);

        int step = Mathf.Max(1, Mathf.CeilToInt((float)n / renderCount));
        int srcIndex = 0;
        int dst = 0;
        int offset = headerSize;

        for (int i = 0; i < n && dst < renderCount; i++)
        {
            int xmm = BitConverter.ToInt32(payload, offset + 0);
            int ymm = BitConverter.ToInt32(payload, offset + 4);
            offset += pointSizeBytes;

            if (i != srcIndex)
                continue;

            Vector3 pos = MmPointToUnity(xmm, ymm);
            particles[dst].position = pos;
            particles[dst].startColor = pointColor;
            particles[dst].startSize = pointSize;
            particles[dst].remainingLifetime = 9999f;
            particles[dst].startLifetime = 9999f;
            dst++;
            srcIndex += step;
        }

        if (particleSystemTarget != null)
        {
            particleSystemTarget.SetParticles(particles, dst);
        }

        activePointCount = dst;
        lastSeq = seq;
        if (markSnapshotReceived)
            snapshotReceived = true;
    }

    private void EnsureParticleArray(int count)
    {
        if (particles == null || particles.Length != count)
            particles = new ParticleSystem.Particle[count];
    }

    private bool CheckMagic(byte[] payload, byte[] expected)
    {
        if (payload == null || payload.Length < 4 || expected == null || expected.Length != 4)
            return false;

        return payload[0] == expected[0] &&
               payload[1] == expected[1] &&
               payload[2] == expected[2] &&
               payload[3] == expected[3];
    }

    private Vector3 MmPointToUnity(int xmm, int ymm)
    {
        float x = xmm / 1000.0f;
        float z = ymm / 1000.0f;
        return new Vector3(x, baseY, z);
    }

    private void UpdateStatusLabel()
    {
        if (statusLabel == null)
            return;

        statusLabel.text =
            $"Points: {(IsConnected ? "Connected" : "Disconnected")}\n" +
            $"Seq: {lastSeq}\n" +
            $"Snapshot: {(snapshotReceived ? "Yes" : "No")}\n" +
            $"Count: {activePointCount}\n" +
            $"Topic: {lastTopic}";
    }

    void OnDestroy()
    {
        StopThread();
    }
}
