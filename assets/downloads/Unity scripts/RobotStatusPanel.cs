using System.Net;
using System.Net.Sockets;
using TMPro;
using UnityEngine;

public class RobotStatusPanel : MonoBehaviour
{
    [Header("Fuentes de datos")]
    [SerializeField] private ZmqVideoReceiver videoReceiver;
    [SerializeField] private ZmqSensorReceiver sensorReceiver;

    [Header("Refresco UI")]
    [SerializeField] private float refreshHz = 5f;

    [Header("Texto por defecto")]
    [SerializeField] private string defaultLidarText = "N/A";

    private TMP_Text robotStatusValue;
    private TMP_Text targetIpValue;
    private TMP_Text myIpValue;
    private TMP_Text modeValue;
    private TMP_Text fpsValue;
    private TMP_Text resValue;
    private TMP_Text cameraOkValue;
    private TMP_Text lidarOkValue;

    private float nextRefreshTime = 0f;
    private string cachedMyIp = "Unknown";

    void Awake()
    {
        AutoBind();
        cachedMyIp = GetLocalIPv4();
    }

    void Update()
    {
        if (Time.unscaledTime < nextRefreshTime)
            return;

        nextRefreshTime = Time.unscaledTime + 1f / Mathf.Max(refreshHz, 1f);
        RefreshTexts();
    }

    private void RefreshTexts()
    {
        bool connected = videoReceiver != null && videoReceiver.IsConnected;

        SetValue(robotStatusValue, connected ? "Connected" : "Disconnected");
        SetValue(targetIpValue, videoReceiver != null ? videoReceiver.ServerIp : "--");
        SetValue(myIpValue, cachedMyIp);

        string modeText = "--";
        if (sensorReceiver != null)
            modeText = "Cam:" + PrettyCameraMode(sensorReceiver.CurrentCameraMode) + " | L:" + PrettyLidarMode(sensorReceiver.CurrentLidarMode);
        else if (videoReceiver != null)
            modeText = PrettyCameraMode(videoReceiver.CurrentCameraMode);
        SetValue(modeValue, modeText);

        SetValue(
            fpsValue,
            videoReceiver != null && videoReceiver.CurrentFps > 0f
                ? $"{videoReceiver.CurrentFps:0.0}"
                : "--"
        );

        SetValue(
            resValue,
            videoReceiver != null && videoReceiver.CurrentWidth > 0 && videoReceiver.CurrentHeight > 0
                ? $"{videoReceiver.CurrentWidth}x{videoReceiver.CurrentHeight}"
                : "--"
        );

        if (sensorReceiver != null && sensorReceiver.IsConnected)
        {
            SetValue(cameraOkValue, sensorReceiver.CameraOk ? "OK" : "NO");
            SetValue(lidarOkValue, sensorReceiver.LidarOk ? "OK" : "NO");
        }
        else
        {
            bool camOk = connected;
            SetValue(cameraOkValue, camOk ? "OK" : "NO");
            SetValue(lidarOkValue, defaultLidarText);
        }
    }

    private void AutoBind()
    {
        robotStatusValue = FindValueLabel("RobotStatusText");
        targetIpValue = FindValueLabel("TargetIpText");
        myIpValue = FindValueLabel("MyIpText");
        modeValue = FindValueLabel("ModeText");
        fpsValue = FindValueLabel("FpsText");
        resValue = FindValueLabel("ResText");
        cameraOkValue = FindValueLabel("CameraOkText");
        lidarOkValue = FindValueLabel("LidarOkText");
    }

    private TMP_Text FindValueLabel(string groupName)
    {
        Transform group = transform.Find(groupName);
        if (group == null)
        {
            Debug.LogWarning($"[RobotStatusPanel] No encontré el grupo: {groupName}");
            return null;
        }

        Transform valueNode = group.Find("Label (1)");
        if (valueNode == null)
        {
            Debug.LogWarning($"[RobotStatusPanel] No encontré 'Label (1)' dentro de: {groupName}");
            return null;
        }

        TMP_Text tmp = valueNode.GetComponent<TMP_Text>();
        if (tmp == null)
            tmp = valueNode.GetComponentInChildren<TMP_Text>(true);

        if (tmp == null)
            Debug.LogWarning($"[RobotStatusPanel] 'Label (1)' no tiene TMP_Text en: {groupName}");

        return tmp;
    }

    private void SetValue(TMP_Text textField, string value)
    {
        if (textField != null)
            textField.text = value;
    }

    private string PrettyCameraMode(string mode)
    {
        if (string.IsNullOrWhiteSpace(mode))
            return "--";

        string m = mode.ToLowerInvariant();
        if (m == "normal") return "Normal";
        if (m == "pose") return "Pose";
        if (m == "segment") return "Segment";
        if (m == "off") return "Off";
        if (m == "rgb") return "Normal";
        return mode;
    }

    private string PrettyLidarMode(string mode)
    {
        if (string.IsNullOrWhiteSpace(mode))
            return defaultLidarText;

        string m = mode.ToLowerInvariant();
        if (m == "off") return "Off";
        if (m == "detail") return "Detail";
        if (m == "medium") return "Medium";
        if (m == "panorama") return "Panorama";
        return mode;
    }

    private string GetLocalIPv4()
    {
        try
        {
            var host = Dns.GetHostEntry(Dns.GetHostName());
            foreach (var ip in host.AddressList)
            {
                if (ip.AddressFamily == AddressFamily.InterNetwork && !IPAddress.IsLoopback(ip))
                    return ip.ToString();
            }
        }
        catch
        {
        }

        return "Unknown";
    }
}
