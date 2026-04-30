using UnityEngine;
using UnityEngine.XR;

public class QuestMobileDriveTeleop : MonoBehaviour
{
    [Header("XR Node")]
    public XRNode controllerNode = XRNode.RightHand;

    [Header("Control")]
    public bool teleopEnabled = false;
    public NucControlCommandSender commandSender;

    [Header("Joystick Mapping")]
    public bool swapAxes = true;
    public bool invertForward = false;
    public bool invertTurn = false;
    public float deadzone = 0.18f;
    public float sendHz = 15f;
    public float turnGain = 1.0f;
    public int maxRaw = 255;

    [Header("Debug")]
    public bool showDebugLogs = false;
    public bool moveDebugObject = false;
    public Transform objectToMove;
    public float moveSpeed = 1.5f;

    private InputDevice device;
    private Vector2 joystickInput = Vector2.zero;
    private float lastSendTime = -999f;
    private int lastSentLeft = 9999;
    private int lastSentRight = 9999;

    void Start()
    {
        TryInitializeDevice();
    }

    void Update()
    {
        if (!teleopEnabled)
        {
            joystickInput = Vector2.zero;
            return;
        }

        if (!device.isValid)
            TryInitializeDevice();

        ReadJoystick();

        if (moveDebugObject)
            MoveObject();

        SendDriveCommand();
    }

    void OnDisable()
    {
        SendZeroOnce();
    }

    void OnDestroy()
    {
        SendZeroOnce();
    }

    void TryInitializeDevice()
    {
        device = InputDevices.GetDeviceAtXRNode(controllerNode);

        if (showDebugLogs)
        {
            if (device.isValid)
                Debug.Log("[XR] Control detectado correctamente: " + controllerNode);
            else
                Debug.LogWarning("[XR] No se pudo detectar el control: " + controllerNode);
        }
    }

    void ReadJoystick()
    {
        bool gotValue = device.TryGetFeatureValue(CommonUsages.primary2DAxis, out joystickInput);

        if (!gotValue)
        {
            joystickInput = Vector2.zero;

            if (showDebugLogs)
                Debug.LogWarning("[XR] No se pudo leer primary2DAxis del control.");
            return;
        }

        // deadzone sobre valores crudos
        if (Mathf.Abs(joystickInput.x) < deadzone) joystickInput.x = 0f;
        if (Mathf.Abs(joystickInput.y) < deadzone) joystickInput.y = 0f;

        if (showDebugLogs)
            Debug.Log($"[RIGHT JOYSTICK RAW] X={joystickInput.x:F3}, Y={joystickInput.y:F3}");
    }

    void SendDriveCommand()
    {
        if (commandSender == null)
            return;

        float now = Time.unscaledTime;
        if (now - lastSendTime < 1f / Mathf.Max(sendHz, 1f))
            return;

        lastSendTime = now;

        // Tu síntoma fue:
        // - izquierda/derecha => avanza/retrocede
        // - adelante/atrás   => gira
        // Por eso aquí intercambiamos los ejes por defecto.
        float rawForward = swapAxes ? joystickInput.x : joystickInput.y;
        float rawTurn = swapAxes ? joystickInput.y : joystickInput.x;

        float v = invertForward ? -rawForward : rawForward;
        float w = (invertTurn ? -rawTurn : rawTurn) * turnGain;

        float left = Mathf.Clamp(v - w, -1f, 1f);
        float right = Mathf.Clamp(v + w, -1f, 1f);

        int leftRaw = Mathf.RoundToInt(left * maxRaw);
        int rightRaw = Mathf.RoundToInt(right * maxRaw);

        // Enviar SIEMPRE a la frecuencia indicada para no caer en watchdog.
        commandSender.SendDriveDirect(leftRaw, rightRaw);

        if (showDebugLogs && (leftRaw != lastSentLeft || rightRaw != lastSentRight))
        {
            Debug.Log(
                $"[QuestMobileDriveTeleop] rawX={joystickInput.x:F3}, rawY={joystickInput.y:F3}, " +
                $"forward={v:F3}, turn={w:F3}, left={leftRaw}, right={rightRaw}"
            );
        }

        lastSentLeft = leftRaw;
        lastSentRight = rightRaw;
    }

    void MoveObject()
    {
        if (objectToMove == null) return;

        float rawForward = swapAxes ? joystickInput.x : joystickInput.y;
        float rawTurn = swapAxes ? joystickInput.y : joystickInput.x;
        float v = invertForward ? -rawForward : rawForward;
        float w = invertTurn ? -rawTurn : rawTurn;

        Vector3 movement = new Vector3(w, 0f, v);
        objectToMove.Translate(movement * moveSpeed * Time.deltaTime, Space.World);
    }

    public void SetTeleopEnabled(bool enabled)
    {
        teleopEnabled = enabled;

        if (!teleopEnabled)
        {
            joystickInput = Vector2.zero;
            SendZeroOnce();
        }

        if (showDebugLogs)
            Debug.Log("[QuestMobileDriveTeleop] Teleop " + (enabled ? "ENABLED" : "DISABLED"));
    }

    private void SendZeroOnce()
    {
        if (commandSender == null)
            return;

        commandSender.SendDriveDirect(0, 0);
        lastSentLeft = 0;
        lastSentRight = 0;
    }
}
