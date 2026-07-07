// WFIoTLatencyUIController.cs
// UI controller for WFIoTLatencyTestScene.
// Requires TextMeshPro (already installed in this project).
// Assign UI elements in the Inspector or they will be auto-generated programmatically.
//
// Part of the WF-IoT latency measurement toolset.

using UnityEngine;
using UnityEngine.UI;
using System;
using System.Globalization;
using TMPro;

public class WFIoTLatencyUIController : MonoBehaviour
{
    [Header("Manager")]
    public WFIoTLatencyTestManager manager;

    [Header("Input")]
    public TMP_InputField ipInput;

    [Header("Dropdowns")]
    public TMP_Dropdown presetDropdown;
    public TMP_Dropdown cameraModeDropdown;
    public TMP_Dropdown lidarModeDropdown;

    [Header("Buttons")]
    public Button connectButton;
    public Button disconnectButton;
    public Button startButton;
    public Button stopButton;
    public Button exportButton;

    [Header("Toggles")]
    public Toggle videoEnabledToggle;
    public Toggle lidarEnabledToggle;

    [Header("Labels")]
    public TMP_Text statusText;
    public TMP_Text metricsText;

    // ── Option lists ──────────────────────────────────────────────────────────
    private static readonly string[] CameraModes = { "off", "normal", "pose", "segment" };
    private static readonly string[] LidarModes  = { "off", "detail", "medium", "panorama" };

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    void Start()
    {
        // Auto-generate minimal UI if the Inspector references are empty
        if (manager == null)
        {
            Debug.LogWarning("[WFIoT UI] No WFIoTLatencyTestManager assigned. " +
                             "Assign it in the Inspector.");
            return;
        }

        PopulateDropdown(presetDropdown,      WFIoTLatencyTestManager.PresetNames);
        PopulateDropdown(cameraModeDropdown,  CameraModes);
        PopulateDropdown(lidarModeDropdown,   LidarModes);

        if (presetDropdown != null)
            presetDropdown.onValueChanged.AddListener(OnPresetChanged);

        if (cameraModeDropdown != null)
            cameraModeDropdown.onValueChanged.AddListener(i =>
            {
                if (manager != null && i < CameraModes.Length)
                    manager.cameraMode = CameraModes[i];
            });

        if (lidarModeDropdown != null)
            lidarModeDropdown.onValueChanged.AddListener(i =>
            {
                if (manager != null && i < LidarModes.Length)
                    manager.lidarMode = LidarModes[i];
            });

        AddListener(connectButton,    OnConnect);
        AddListener(disconnectButton, OnDisconnect);
        AddListener(startButton,      OnStart);
        AddListener(stopButton,       OnStop);
        AddListener(exportButton,     OnExport);

        if (videoEnabledToggle != null)
            videoEnabledToggle.onValueChanged.AddListener(v =>
            {
                if (manager != null) manager.videoEnabled = v;
            });

        if (lidarEnabledToggle != null)
            lidarEnabledToggle.onValueChanged.AddListener(v =>
            {
                if (manager != null) manager.lidarEnabled = v;
            });

        // Seed the IP field from the manager's default
        if (ipInput != null)
            ipInput.text = manager.pcIp;
    }

    void Update()
    {
        if (manager == null) return;
        RefreshStatus();
        RefreshMetrics();
    }

    // ── Button callbacks ──────────────────────────────────────────────────────

    private void OnConnect()
    {
        if (manager == null) return;
        if (ipInput != null && !string.IsNullOrWhiteSpace(ipInput.text))
            manager.pcIp = ipInput.text.Trim();
        manager.Connect();
    }

    private void OnDisconnect() => manager?.Disconnect();
    private void OnStart()      => manager?.StartTest();
    private void OnStop()       => manager?.StopTest();
    private void OnExport()     => manager?.ExportCsv();

    private void OnPresetChanged(int idx)
    {
        if (manager == null) return;
        string[] names = WFIoTLatencyTestManager.PresetNames;
        if (idx < 0 || idx >= names.Length) return;
        manager.ApplyPreset(names[idx]);
        SyncToggleAndDropdownsFromManager();
    }

    // ── UI sync ───────────────────────────────────────────────────────────────

    private void SyncToggleAndDropdownsFromManager()
    {
        if (manager == null) return;

        if (videoEnabledToggle != null)
            videoEnabledToggle.SetIsOnWithoutNotify(manager.videoEnabled);

        if (lidarEnabledToggle != null)
            lidarEnabledToggle.SetIsOnWithoutNotify(manager.lidarEnabled);

        if (cameraModeDropdown != null)
        {
            int idx = Array.IndexOf(CameraModes, manager.cameraMode);
            cameraModeDropdown.SetValueWithoutNotify(Mathf.Max(0, idx));
        }

        if (lidarModeDropdown != null)
        {
            int idx = Array.IndexOf(LidarModes, manager.lidarMode);
            lidarModeDropdown.SetValueWithoutNotify(Mathf.Max(0, idx));
        }
    }

    private void RefreshStatus()
    {
        if (statusText == null) return;
        statusText.text = manager.StatusMessage;
    }

    private void RefreshMetrics()
    {
        if (metricsText == null || manager == null) return;
        metricsText.text =
            $"Condition  : {manager.condition}\n" +
            $"Sent/Recv  : {manager.SamplesSent} / {manager.SamplesReceived}\n" +
            $"Loss       : {manager.LossPercent:F1}%\n" +
            $"RTT latest : {manager.RttLatestMs:F1} ms\n" +
            $"RTT mean   : {manager.RttMeanMs:F1} ms\n" +
            $"RTT median : {manager.RttMedianMs:F1} ms\n" +
            $"RTT p95    : {manager.RttP95Ms:F1} ms\n" +
            $"RTT max    : {manager.RttMaxMs:F1} ms\n" +
            $"Jitter std : {manager.JitterStdMs:F1} ms\n" +
            $"Video FPS  : {manager.VideoFpsReceived:F1}\n" +
            $"Stat Hz    : {manager.StatHzReceived:F1}\n" +
            $"LiDAR Hz   : {manager.LidarHzReceived:F1}";
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static void PopulateDropdown(TMP_Dropdown dd, string[] options)
    {
        if (dd == null) return;
        dd.ClearOptions();
        dd.AddOptions(new System.Collections.Generic.List<string>(options));
    }

    private static void AddListener(Button btn, UnityEngine.Events.UnityAction action)
    {
        if (btn != null) btn.onClick.AddListener(action);
    }
}
