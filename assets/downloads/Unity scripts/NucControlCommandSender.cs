using UnityEngine;
using System;
using System.Threading;
using System.Collections.Concurrent;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;
using System.Globalization;

public class NucControlCommandSender : MonoBehaviour
{
    [Header("Ports")]
    public int commandPort = 5002;

    [Header("Fallback IP")]
    public string fallbackIp = "192.168.100.20";

    [Header("Behavior")]
    public bool autoReconnectOnIpChange = true;

    private Thread cmdThread;
    private volatile bool running = false;
    private readonly ConcurrentQueue<string> commandQueue = new ConcurrentQueue<string>();
    private string lastResolvedIp = "";

    public string ServerIp => ResolveIp();

    void Start()
    {
        AsyncIO.ForceDotNet.Force();
        lastResolvedIp = ResolveIp();
        StartThread();
        Debug.Log($"[CONTROL CMD] PUB tcp://{lastResolvedIp}:{commandPort}");
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
        Debug.Log($"[CONTROL CMD] Reconnected PUB tcp://{ResolveIp()}:{commandPort}");
    }

    public void SendControlEnable(bool driveEnabled, bool manipEnabled, bool baseEnabled)
    {
        string payload =
            "{\"type\":\"set_control_enable\",\"drive_enabled\":" + BoolStr(driveEnabled) +
            ",\"manip_enabled\":" + BoolStr(manipEnabled) +
            ",\"base_enabled\":" + BoolStr(baseEnabled) + "}";
        Enqueue(payload);
    }

    public void SendDriveDirect(int left, int right)
    {
        left = Mathf.Clamp(left, -255, 255);
        right = Mathf.Clamp(right, -255, 255);
        string payload = $"{{\"type\":\"drive_direct\",\"left\":{left},\"right\":{right}}}";
        Enqueue(payload);
    }

    public void SendStopAll()
    {
        Enqueue("{\"type\":\"stop_all\"}");
    }

    public void SendManipulatorPose(float? qBase, float? q1, float? q2)
    {
        string payload =
            "{\"type\":\"manip_cmd\",\"q\":[" +
            NullableFloatJson(qBase) + "," +
            NullableFloatJson(q1) + "," +
            NullableFloatJson(q2) + "]}";
        Enqueue(payload);
    }

    public void SendManipulatorPose(float qBase, float q1, float q2)
    {
        SendManipulatorPose((float?)qBase, (float?)q1, (float?)q2);
    }

    public void SendBaseAngle(float qBase)
    {
        string payload =
            "{\"type\":\"base_joint_cmd\",\"q_base\":" +
            qBase.ToString("F3", CultureInfo.InvariantCulture) + "}";
        Enqueue(payload);
    }

    public void SendManipulatorHome()
    {
        Enqueue("{\"type\":\"manip_home\"}");
    }

    public void SendMasterArm()
    {
        Enqueue("{\"type\":\"master_arm\"}");
    }

    public void SendMasterDisarm()
    {
        Enqueue("{\"type\":\"master_disarm\"}");
    }

    public void SendManipulatorAscii(string line)
    {
        if (string.IsNullOrWhiteSpace(line))
            return;

        string escaped = EscapeJson(line.Trim());
        Enqueue($"{{\"type\":\"manip_ascii\",\"line\":\"{escaped}\"}}");
    }

    public void SendGripperMm(float mm)
    {
        mm = Mathf.Clamp(mm, 0f, 80f);
        string payload =
            "{\"type\":\"gripper_cmd\",\"mm\":" +
            mm.ToString("F3", CultureInfo.InvariantCulture) + "}";
        Enqueue(payload);
    }

    public void SendGripperMoveAsciiMm(float mm)
    {
        mm = Mathf.Clamp(mm, 0f, 80f);
        SendGripperAscii("m " + mm.ToString("F3", CultureInfo.InvariantCulture));
    }

    public void SendGripperStop()
    {
        Enqueue("{\"type\":\"gripper_stop\"}");
    }

    public void SendGripperAscii(string line)
    {
        if (string.IsNullOrWhiteSpace(line))
            return;

        string escaped = EscapeJson(line.Trim());
        Enqueue($"{{\"type\":\"gripper_ascii\",\"line\":\"{escaped}\"}}");
    }

    private string BoolStr(bool value) => value ? "true" : "false";

    private static string NullableFloatJson(float? value)
    {
        if (!value.HasValue)
            return "null";
        return value.Value.ToString("F3", CultureInfo.InvariantCulture);
    }

    private static string EscapeJson(string value)
    {
        return value.Replace("\\", "\\\\").Replace("\"", "\\\"");
    }

    private void Enqueue(string payload)
    {
        if (string.IsNullOrWhiteSpace(payload))
            return;

        commandQueue.Enqueue(payload);
        Debug.Log("[CONTROL CMD] Queued -> " + payload);
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
                pub.Options.SendHighWatermark = 20;
                pub.Connect($"tcp://{ResolveIp()}:{commandPort}");
                Thread.Sleep(300);

                while (running)
                {
                    if (commandQueue.TryDequeue(out var payload))
                    {
                        pub.SendMoreFrame("cmd").SendFrame(payload);
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
            Debug.LogError("[CONTROL CMD] Error en CommandLoop: " + e);
        }
    }
}
