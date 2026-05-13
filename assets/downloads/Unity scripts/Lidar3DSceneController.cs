using UnityEngine;
using TMPro;
using UnityEngine.UI;

public class Lidar3DSceneController : MonoBehaviour
{
    [Header("References")]
    public ZmqLidar3DCommandSender commandSender;
    public ZmqWallsReceiver wallsReceiver;
    public ZmqLidarPointsReceiver pointsReceiver;
    public ZmqSensorReceiver sensorReceiver;

    [Header("UI")]
    public TMP_Text headerText;
    public TMP_Text infoText;
    public Toggle wallsToggle;
    public Toggle pointsToggle;

    [Header("Startup")]
    public bool autoApplyOnStart = true;
    public bool startupWalls = true;
    public bool startupPoints = false;
    public bool requestSnapshotsOnStart = true;

    void Start()
    {
        if (commandSender == null)
            commandSender = FindObjectOfType<ZmqLidar3DCommandSender>();
        if (wallsReceiver == null)
            wallsReceiver = FindObjectOfType<ZmqWallsReceiver>();
        if (pointsReceiver == null)
            pointsReceiver = FindObjectOfType<ZmqLidarPointsReceiver>();

        if (wallsToggle != null)
            wallsToggle.SetIsOnWithoutNotify(startupWalls);
        if (pointsToggle != null)
            pointsToggle.SetIsOnWithoutNotify(startupPoints);

        if (autoApplyOnStart)
            ApplyCurrentMode(requestSnapshotsOnStart);

        UpdateLabels();
    }

    void Update()
    {
        UpdateLabels();
    }

    public void OnWallsToggleChanged(bool isOn)
    {
        startupWalls = isOn;
        ApplyCurrentMode(false);
    }

    public void OnPointsToggleChanged(bool isOn)
    {
        startupPoints = isOn;
        ApplyCurrentMode(false);
    }

    public void ApplyCurrentMode(bool requestSnapshots)
    {
        if (commandSender != null)
        {
            commandSender.ApplyToggleState(startupWalls, startupPoints);
            if (requestSnapshots)
            {
                if (startupWalls)
                    commandSender.RequestWallsSnapshot();
                if (startupPoints)
                    commandSender.RequestPointsSnapshot();
            }
        }

        if (wallsReceiver != null)
            wallsReceiver.SetVisualsEnabled(startupWalls);

        if (pointsReceiver != null)
            pointsReceiver.SetVisualsEnabled(startupPoints);

        UpdateLabels();
    }

    public void ActivateWallsOnly()
    {
        startupWalls = true;
        startupPoints = false;
        SyncToggles();
        ApplyCurrentMode(true);
    }

    public void ActivatePointsOnly()
    {
        startupWalls = false;
        startupPoints = true;
        SyncToggles();
        ApplyCurrentMode(true);
    }

    public void ActivateBoth()
    {
        startupWalls = true;
        startupPoints = true;
        SyncToggles();
        ApplyCurrentMode(true);
    }

    public void DisableAll3D()
    {
        startupWalls = false;
        startupPoints = false;
        SyncToggles();
        ApplyCurrentMode(false);
    }

    public void RequestSnapshots()
    {
        if (commandSender == null)
            return;

        if (startupWalls)
            commandSender.RequestWallsSnapshot();
        if (startupPoints)
            commandSender.RequestPointsSnapshot();
    }

    public void ClearVisuals()
    {
        if (wallsReceiver != null)
            wallsReceiver.ClearAllWalls();
        if (pointsReceiver != null)
            pointsReceiver.ClearPoints();
    }

    public void ReconnectAll()
    {
        if (commandSender != null)
            commandSender.Reconnect();
        if (wallsReceiver != null)
            wallsReceiver.Reconnect();
        if (pointsReceiver != null)
            pointsReceiver.Reconnect();
        if (sensorReceiver != null)
            sensorReceiver.Reconnect();

        ApplyCurrentMode(true);
    }

    private void SyncToggles()
    {
        if (wallsToggle != null)
            wallsToggle.SetIsOnWithoutNotify(startupWalls);
        if (pointsToggle != null)
            pointsToggle.SetIsOnWithoutNotify(startupPoints);
    }

    private void UpdateLabels()
    {
        if (headerText != null)
        {
            string mode = startupWalls && startupPoints ? "Both" : startupWalls ? "Walls" : startupPoints ? "Points" : "Off";
            headerText.text = "Lidar 3D View | " + mode;
        }

        if (infoText != null)
        {
            string wallsText = wallsReceiver != null
                ? $"Walls: {(wallsReceiver.IsConnected ? "OK" : "Waiting")} | Seq {wallsReceiver.LastSeq} | N {wallsReceiver.ActiveWallCount}"
                : "Walls: --";

            string pointsText = pointsReceiver != null
                ? $"Points: {(pointsReceiver.IsConnected ? "OK" : "Waiting")} | Seq {pointsReceiver.LastSeq} | N {pointsReceiver.ActivePointCount}"
                : "Points: --";

            string sensorText = sensorReceiver != null
                ? $"Lidar2D: {(sensorReceiver.LidarOk ? "OK" : "Off/NoData")} | Mode {sensorReceiver.CurrentLidarMode}"
                : "Lidar2D: --";

            infoText.text = wallsText + "\n" + pointsText + "\n" + sensorText;
        }
    }
}
