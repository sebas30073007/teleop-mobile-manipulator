using UnityEngine;
using System;
using System.Threading;
using System.Collections.Generic;
using NetMQ;
using NetMQ.Sockets;
using AsyncIO;

[Serializable]
public class StatPayload
{
    public float start_ts;
    public bool camera_ok;
    public bool lidar_ok;
    public bool walls_ok;
    public bool points_ok;
    public bool cmd_link_ok;
    public bool master_serial_ok;
    public bool drive_enabled;
    public bool manip_enabled;
    public bool base_enabled;
    public float last_camera_ts;
    public float last_lidar_ts;
    public float last_walls_ts;
    public float last_points_ts;
    public float last_cmd_ts;
    public float last_serial_tx_ts;
    public float last_serial_rx_ts;
    public float last_drive_cmd_ts;
    public float last_manip_cmd_ts;
    public float last_manip_state_ts;
    public float depth_scale;
    public int dropped_video_frames;
    public int dropped_sensor_msgs;
    public int dropped_walls_msgs;
    public float uptime_s;
    public float ts;
    public string active_camera_mode;
    public string active_lidar_mode;
    public bool pose_model_ready;
    public bool seg_model_ready;
    public string video_mode;
    public string lidar_mode;
    public bool manip_state_valid;
    public bool manip_busy;
    public int manip_sw2;
    public int manip_sw3;
    public float actual_base_deg;
    public float actual_codo_deg;
    public float actual_muneca_deg;

    // NUEVO: gripper incluido en stat
    public bool gripper_serial_ok;
}

[Serializable]
public class ManipStatePayload
{
    public float ts;
    public float base_deg;
    public float codo_deg;
    public float muneca_deg;
    public int sw2;
    public int sw3;
    public bool busy;
    public string source_line;
}

[Serializable]
public class GripperStatePayload
{
    public float mm;
    public float target_mm;
    public int count;
    public bool busy;
    public bool calibrated;
}

public class ZmqSensorReceiver : MonoBehaviour
{
    [Header("Connection")]
    [SerializeField] private float disconnectTimeout = 2.0f;
    public int sensorPort = 5001;
    public string fallbackIp = "192.168.100.20";

    private Thread recvThread;
    private volatile bool running = false;
    private float lastSensorRealtime = -999f;
    private float lastGripperRealtime = -999f;

    public string ServerIp => ResolveIp();
    public bool IsConnected => (Time.unscaledTime - lastSensorRealtime) <= disconnectTimeout;

    public bool CameraOk { get; private set; } = false;
    public bool LidarOk { get; private set; } = false;
    public bool WallsOk { get; private set; } = false;
    public bool PointsOk { get; private set; } = false;
    public bool CmdLinkOk { get; private set; } = false;
    public bool MasterSerialOk { get; private set; } = false;
    public bool DriveEnabled { get; private set; } = false;
    public bool ManipEnabled { get; private set; } = false;
    public bool BaseEnabled { get; private set; } = false;
    public bool PoseModelReady { get; private set; } = false;
    public bool SegModelReady { get; private set; } = false;
    public string CurrentCameraMode { get; private set; } = "normal";
    public string CurrentLidarMode { get; private set; } = "off";

    public bool ManipStateValid { get; private set; } = false;
    public bool ManipBusy { get; private set; } = false;
    public int ManipSw2 { get; private set; } = -1;
    public int ManipSw3 { get; private set; } = -1;
    public float ActualBaseDeg { get; private set; } = 0f;
    public float ActualCodoDeg { get; private set; } = 0f;
    public float ActualMunecaDeg { get; private set; } = 0f;

    // NUEVO: gripper integrado aquí
    public bool GripperSerialOk { get; private set; } = false;
    public bool GripperStateValid => (Time.unscaledTime - lastGripperRealtime) <= disconnectTimeout;
    public float ActualGripperMm { get; private set; } = 0f;
    public float TargetGripperMm { get; private set; } = 0f;
    public int GripperCount { get; private set; } = 0;
    public bool GripperBusy { get; private set; } = false;
    public bool GripperCalibrated { get; private set; } = false;

    void Start()
    {
        AsyncIO.ForceDotNet.Force();
        StartReceiver();
        Debug.Log($"[ZMQ] Sensor SUB tcp://{ResolveIp()}:{sensorPort}");
    }

    void OnDestroy()
    {
        StopReceiver();
    }

    private string ResolveIp()
    {
        if (NucIpManager.Instance != null)
            return NucIpManager.Instance.GetIp();
        return fallbackIp;
    }

    private void StartReceiver()
    {
        running = true;
        recvThread = new Thread(ReceiveLoop);
        recvThread.IsBackground = true;
        recvThread.Start();
    }

    private void StopReceiver()
    {
        running = false;
        if (recvThread != null && recvThread.IsAlive)
            recvThread.Join(500);
        recvThread = null;
    }

    public void Reconnect()
    {
        StopReceiver();
        StartReceiver();
        Debug.Log($"[ZMQ] Sensor reconnected SUB tcp://{ResolveIp()}:{sensorPort}");
    }

    void ReceiveLoop()
    {
        try
        {
            using (var sub = new SubscriberSocket())
            {
                sub.Options.ReceiveHighWatermark = 50;
                sub.Connect($"tcp://{ResolveIp()}:{sensorPort}");
                sub.Subscribe("stat");
                sub.Subscribe("mode_ack");
                sub.Subscribe("manip_state");
                sub.Subscribe("gripper_state");

                List<byte[]> msg = null;

                while (running)
                {
                    if (!sub.TryReceiveMultipartBytes(TimeSpan.FromMilliseconds(100), ref msg))
                        continue;

                    if (msg == null || msg.Count < 2)
                        continue;

                    string topic = System.Text.Encoding.UTF8.GetString(msg[0]);
                    string json = System.Text.Encoding.UTF8.GetString(msg[1]);

                    try
                    {
                        if (topic == "stat" || topic == "mode_ack")
                        {
                            var stat = JsonUtility.FromJson<StatPayload>(json);
                            if (stat != null)
                            {
                                CameraOk = stat.camera_ok;
                                LidarOk = stat.lidar_ok;
                                WallsOk = stat.walls_ok;
                                PointsOk = stat.points_ok;
                                CmdLinkOk = stat.cmd_link_ok;
                                MasterSerialOk = stat.master_serial_ok;
                                DriveEnabled = stat.drive_enabled;
                                ManipEnabled = stat.manip_enabled;
                                BaseEnabled = stat.base_enabled;
                                PoseModelReady = stat.pose_model_ready;
                                SegModelReady = stat.seg_model_ready;
                                GripperSerialOk = stat.gripper_serial_ok;

                                if (!string.IsNullOrWhiteSpace(stat.active_camera_mode))
                                    CurrentCameraMode = stat.active_camera_mode;
                                else if (!string.IsNullOrWhiteSpace(stat.video_mode))
                                    CurrentCameraMode = stat.video_mode.ToLowerInvariant() == "rgb" ? "normal" : stat.video_mode;

                                if (!string.IsNullOrWhiteSpace(stat.active_lidar_mode))
                                    CurrentLidarMode = stat.active_lidar_mode;
                                else if (!string.IsNullOrWhiteSpace(stat.lidar_mode))
                                    CurrentLidarMode = stat.lidar_mode;

                                ManipStateValid = stat.manip_state_valid;
                                ManipBusy = stat.manip_busy;
                                ManipSw2 = stat.manip_sw2;
                                ManipSw3 = stat.manip_sw3;
                                ActualBaseDeg = stat.actual_base_deg;
                                ActualCodoDeg = stat.actual_codo_deg;
                                ActualMunecaDeg = stat.actual_muneca_deg;

                                lastSensorRealtime = Time.unscaledTime;
                            }
                        }
                        else if (topic == "manip_state")
                        {
                            var manip = JsonUtility.FromJson<ManipStatePayload>(json);
                            if (manip != null)
                            {
                                ActualBaseDeg = manip.base_deg;
                                ActualCodoDeg = manip.codo_deg;
                                ActualMunecaDeg = manip.muneca_deg;
                                ManipSw2 = manip.sw2;
                                ManipSw3 = manip.sw3;
                                ManipBusy = manip.busy;
                                ManipStateValid = true;
                                lastSensorRealtime = Time.unscaledTime;
                            }
                        }
                        else if (topic == "gripper_state")
                        {
                            var grip = JsonUtility.FromJson<GripperStatePayload>(json);
                            if (grip != null)
                            {
                                ActualGripperMm = grip.mm;
                                TargetGripperMm = grip.target_mm;
                                GripperCount = grip.count;
                                GripperBusy = grip.busy;
                                GripperCalibrated = grip.calibrated;
                                lastGripperRealtime = Time.unscaledTime;
                                lastSensorRealtime = Time.unscaledTime;
                            }
                        }
                    }
                    catch (Exception e)
                    {
                        Debug.LogWarning("[ZMQ] Error parseando topic '" + topic + "': " + e.Message);
                    }
                }
            }
        }
        catch (Exception e)
        {
            Debug.LogError("[ZMQ] Error en ReceiveLoop: " + e);
        }
    }
}
