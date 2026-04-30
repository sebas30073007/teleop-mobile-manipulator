using UnityEngine;
using System;
using System.Threading;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

[Serializable]
public class GripperStateMessage
{
    public float mm;
    public float target_mm;
    public int count;
    public bool busy;
    public bool calibrated;
}

[Serializable]
public class GripperStatMessage
{
    public bool gripper_serial_ok;
}

public class ZmqGripperStateReceiver : MonoBehaviour
{
    [Header("Ports")]
    public int sensorPort = 5001;

    [Header("Fallback IP")]
    public string fallbackIp = "192.168.100.20";

    [Header("Behavior")]
    public bool autoReconnectOnIpChange = true;
    public bool logDebug = false;
    public float disconnectTimeout = 2.0f;

    private Thread subThread;
    private volatile bool running = false;
    private string lastResolvedIp = "";
    private readonly object stateLock = new object();

    private float actualMm = 0f;
    private float targetMm = 0f;
    private int count = 0;
    private bool busy = false;
    private bool calibrated = false;
    private bool serialOk = false;
    private bool stateValid = false;
    private float lastRxRealtime = -999f;

    public float ActualMm { get { lock (stateLock) return actualMm; } }
    public float TargetMm { get { lock (stateLock) return targetMm; } }
    public int Count { get { lock (stateLock) return count; } }
    public bool Busy { get { lock (stateLock) return busy; } }
    public bool Calibrated { get { lock (stateLock) return calibrated; } }
    public bool SerialOk { get { lock (stateLock) return serialOk; } }
    public bool StateValid
    {
        get
        {
            lock (stateLock)
                return stateValid && (Time.realtimeSinceStartup - lastRxRealtime) <= disconnectTimeout;
        }
    }

    void Start()
    {
        AsyncIO.ForceDotNet.Force();
        lastResolvedIp = ResolveIp();
        StartThread();
        if (logDebug) Debug.Log($"[GRIPPER RX] SUB tcp://{lastResolvedIp}:{sensorPort}");
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

    void OnDestroy()
    {
        StopThread();
    }

    public void Reconnect()
    {
        StopThread();
        StartThread();
        if (logDebug) Debug.Log($"[GRIPPER RX] Reconnected SUB tcp://{ResolveIp()}:{sensorPort}");
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
        subThread = new Thread(SubscriberLoop);
        subThread.IsBackground = true;
        subThread.Start();
    }

    private void StopThread()
    {
        running = false;

        if (subThread != null && subThread.IsAlive)
            subThread.Join(500);

        subThread = null;
    }

    private void SubscriberLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 100;
                sub.Connect($"tcp://{ResolveIp()}:{sensorPort}");
                sub.Subscribe("gripper_state");
                sub.Subscribe("stat");

                while (running)
                {
                    string topic;
                    string payload;

                    try
                    {
                        topic = sub.ReceiveFrameString();
                        payload = sub.ReceiveFrameString();
                    }
                    catch (Exception)
                    {
                        Thread.Sleep(10);
                        continue;
                    }

                    if (topic == "gripper_state")
                    {
                        try
                        {
                            var msg = JsonUtility.FromJson<GripperStateMessage>(payload);
                            lock (stateLock)
                            {
                                actualMm = msg.mm;
                                targetMm = msg.target_mm;
                                count = msg.count;
                                busy = msg.busy;
                                calibrated = msg.calibrated;
                                stateValid = true;
                                lastRxRealtime = Time.realtimeSinceStartup;
                            }

                            if (logDebug)
                                Debug.Log($"[GRIPPER RX] mm={msg.mm:F2} target={msg.target_mm:F2} busy={msg.busy}");
                        }
                        catch (Exception e)
                        {
                            if (logDebug)
                                Debug.LogWarning("[GRIPPER RX] Error parse gripper_state: " + e.Message + " | " + payload);
                        }
                    }
                    else if (topic == "stat")
                    {
                        try
                        {
                            var msg = JsonUtility.FromJson<GripperStatMessage>(payload);
                            lock (stateLock)
                            {
                                serialOk = msg.gripper_serial_ok;
                            }
                        }
                        catch (Exception)
                        {
                        }
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[GRIPPER RX] Error en SubscriberLoop: " + e);
        }
    }
}
