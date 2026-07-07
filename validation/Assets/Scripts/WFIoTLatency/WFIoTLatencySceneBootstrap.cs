// WFIoTLatencySceneBootstrap.cs  —  Passive display for Quest
// ─────────────────────────────────────────────────────────────────────────────
// Creates a World Space status panel visible in the Quest headset.
// NO user interaction required — Quest only receives probes and sends ACKs.
// The PC orchestrates everything automatically.
//
// USAGE:
//   1. New Scene (Empty)
//   2. Create Empty → Add Component → WFIoTLatencySceneBootstrap
//   3. Set "Server Ip" in the Inspector to your PC's IP (e.g. 192.168.100.5)
//   4. Build & deploy to Quest — panel appears automatically.
//
// The panel shows:
//   • Connection status
//   • Current test condition (updated by PC)
//   • Probes received / ACKs sent
//   • Camera and LiDAR mode
// ─────────────────────────────────────────────────────────────────────────────

using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using TMPro;

public class WFIoTLatencySceneBootstrap : MonoBehaviour
{
    [Header("PC Connection")]
    [Tooltip("IP of the PC running wfiot_nuc_latency_simulator.py")]
    [SerializeField] public string serverIp = "192.168.100.5";

    [Header("Panel Position")]
    [Tooltip("Distance from camera to the panel (meters)")]
    [SerializeField] private float uiDistance = 1.6f;
    [Tooltip("Vertical offset from camera center (negative = lower)")]
    [SerializeField] private float uiVerticalOffset = -0.1f;

    // ── Runtime ───────────────────────────────────────────────────────────────
    private WFIoTLatencyResponder responder;
    private TMP_Text              statusLabel;
    private TMP_Text              metricsLabel;
    private GameObject            canvasGO;

    // ── Layout ────────────────────────────────────────────────────────────────
    private const float PANEL_W   = 600f;
    private const float PANEL_H   = 440f;
    private const float WORLD_SCL = 0.001f;   // 1 px = 1 mm  →  60 cm × 44 cm

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    void Awake()
    {
        BuildSystem();
        BuildUI();
    }

    void Start()
    {
        PositionCanvas();
    }

    void Update()
    {
        if (responder == null || statusLabel == null) return;
        RefreshDisplay();
    }

    // ── System ────────────────────────────────────────────────────────────────

    void BuildSystem()
    {
        var go       = new GameObject("WFIoTSystem");
        responder    = go.AddComponent<WFIoTLatencyResponder>();
        responder.serverIp = serverIp;
        // responder.Start() calls Connect() automatically
    }

    // ── Canvas ────────────────────────────────────────────────────────────────

    void BuildUI()
    {
        EnsureEventSystem();

        canvasGO = new GameObject("WFIoTCanvas");
        var cv   = canvasGO.AddComponent<Canvas>();
        cv.renderMode   = RenderMode.WorldSpace;   // required for Meta Quest XR
        cv.sortingOrder = 10;
        canvasGO.transform.localScale = Vector3.one * WORLD_SCL;
        canvasGO.AddComponent<GraphicRaycaster>();

        // ── Panel ─────────────────────────────────────────────────────────────
        var panel    = GO("Panel", canvasGO.transform);
        var panelImg = panel.AddComponent<Image>();
        panelImg.color = new Color(0.06f, 0.07f, 0.10f, 0.95f);
        var panelRT  = panel.GetComponent<RectTransform>();
        panelRT.anchorMin        = panelRT.anchorMax = new Vector2(0.5f, 0.5f);
        panelRT.pivot            = new Vector2(0.5f, 0.5f);
        panelRT.anchoredPosition = Vector2.zero;
        panelRT.sizeDelta        = new Vector2(PANEL_W, PANEL_H);

        var vlg = panel.AddComponent<VerticalLayoutGroup>();
        vlg.padding           = new RectOffset(14, 14, 14, 14);
        vlg.spacing           = 8f;
        vlg.childAlignment    = TextAnchor.UpperCenter;
        vlg.childControlWidth = true;  vlg.childForceExpandWidth  = true;
        vlg.childControlHeight = false; vlg.childForceExpandHeight = false;

        var t = panel.transform;

        // ── Title ─────────────────────────────────────────────────────────────
        TMP(t, "WF-IoT Latency Responder", 22f, FontStyles.Bold,
            TextAlignmentOptions.Center, Color.white, 38f);
        Sep(t);

        // ── IP line ───────────────────────────────────────────────────────────
        TMP(t, $"Listening to PC:  {serverIp}", 17f, FontStyles.Normal,
            TextAlignmentOptions.Center, new Color(0.6f, 0.6f, 0.6f), 28f);
        Sep(t);

        // ── Status line (connection) ──────────────────────────────────────────
        statusLabel = TMP(t, "Connecting…", 19f, FontStyles.Normal,
            TextAlignmentOptions.Center, new Color(0.9f, 0.9f, 0.4f), 32f);
        Sep(t);

        // ── Metrics block ─────────────────────────────────────────────────────
        metricsLabel = TMP(t, "Waiting for first probe…", 18f, FontStyles.Normal,
            TextAlignmentOptions.TopLeft, new Color(0.75f, 0.95f, 0.75f), 240f);
        metricsLabel.overflowMode = TextOverflowModes.Overflow;
    }

    // ── Display update ────────────────────────────────────────────────────────

    void RefreshDisplay()
    {
        // Status
        if (responder.IsConnected)
            statusLabel.text = $"● Connected  —  {serverIp}";
        else
            statusLabel.text = $"○ Waiting for probes from {serverIp}…";

        statusLabel.color = responder.IsConnected
            ? new Color(0.3f, 1f, 0.5f)
            : new Color(0.9f, 0.7f, 0.2f);

        // Metrics
        metricsLabel.text =
            $"Test          :  {responder.CurrentTestId}\n" +
            $"Condition     :  {responder.CurrentCondition}\n" +
            $"Camera mode   :  {responder.CurrentCameraMode}\n" +
            $"LiDAR mode    :  {responder.CurrentLidarMode}\n" +
            $"Video stream  :  {(responder.VideoEnabled  ? "ON" : "off")}\n" +
            $"LiDAR stream  :  {(responder.LidarEnabled  ? "ON" : "off")}\n" +
            "─────────────────────────────────\n" +
            $"Probes recv'd :  {responder.ProbesReceived}\n" +
            $"ACKs sent     :  {responder.AcksSent}";
    }

    // ── Canvas positioning ────────────────────────────────────────────────────

    void PositionCanvas()
    {
        if (canvasGO == null) return;

        Camera cam = FindXRCamera();
        if (cam != null)
        {
            Vector3 fwd = cam.transform.forward;
            fwd.y = 0f;
            if (fwd.sqrMagnitude < 0.001f) fwd = Vector3.forward;
            fwd.Normalize();

            canvasGO.transform.position = cam.transform.position
                + fwd        * uiDistance
                + Vector3.up * uiVerticalOffset;
            canvasGO.transform.rotation = Quaternion.LookRotation(fwd, Vector3.up);
        }
        else
        {
            canvasGO.transform.position = new Vector3(0f, 1.4f + uiVerticalOffset, uiDistance);
            canvasGO.transform.rotation = Quaternion.identity;
        }
    }

    static Camera FindXRCamera()
    {
        foreach (var name in new[] { "CenterEyeAnchor", "OVRCameraRig", "Main Camera", "MainCamera" })
        {
            var go = GameObject.Find(name);
            if (go != null)
            {
                var cam = go.GetComponent<Camera>();
                if (cam != null) return cam;
            }
        }
        return Camera.main ?? UnityEngine.Object.FindObjectOfType<Camera>();
    }

    // ── UI helpers ────────────────────────────────────────────────────────────

    static TMP_Text TMP(Transform parent, string text, float size, FontStyles style,
        TextAlignmentOptions align, Color col, float h)
    {
        var go  = GO("TMP", parent);
        var tmp = go.AddComponent<TextMeshProUGUI>();
        tmp.text      = text;
        tmp.fontSize  = size;
        tmp.fontStyle = style;
        tmp.alignment = align;
        tmp.color     = col;
        var le = go.AddComponent<LayoutElement>();
        le.preferredHeight = h;
        le.flexibleWidth   = 1f;
        return tmp;
    }

    static void Sep(Transform parent)
    {
        var go  = GO("Sep", parent);
        var img = go.AddComponent<Image>();
        img.color = new Color(0.25f, 0.28f, 0.36f, 0.7f);
        var le = go.AddComponent<LayoutElement>();
        le.preferredHeight = 1f;
        le.flexibleWidth   = 1f;
    }

    static GameObject GO(string name, Transform parent)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        return go;
    }

    static void EnsureEventSystem()
    {
        if (FindObjectOfType<EventSystem>() != null) return;
        var es = new GameObject("EventSystem");
        es.AddComponent<EventSystem>();
        es.AddComponent<StandaloneInputModule>();
    }
}
