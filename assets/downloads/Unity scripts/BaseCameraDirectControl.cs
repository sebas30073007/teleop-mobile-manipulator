using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Globalization;

public class BaseCameraDirectControl : MonoBehaviour
{
    [Header("References")]
    public Slider baseSlider;
    public TMP_Text baseValueText;
    public SimpleArm3DOF previewRobot;
    public NucControlCommandSender commandSender;

    [Header("Behavior")]
    public bool directControlEnabled = false;
    public float sendHz = 8f;
    public bool syncSliderFromRobotOnStart = true;
    public bool logDebug = true;

    [Header("Command Mapping")]
    public bool invertVisualBase = false;
    public bool invertCommandBase = false;

    private float lastSendTime = -999f;

    void Start()
    {
        if (baseSlider == null || previewRobot == null)
        {
            Debug.LogWarning("[BaseCameraDirectControl] Faltan referencias.");
            return;
        }

        baseSlider.onValueChanged.RemoveListener(OnBaseSliderChanged);
        baseSlider.onValueChanged.AddListener(OnBaseSliderChanged);

        baseSlider.minValue = previewRobot.qBaseMin;
        baseSlider.maxValue = previewRobot.qBaseMax;

        if (syncSliderFromRobotOnStart)
        {
            float startValue = invertVisualBase ? -previewRobot.qBase : previewRobot.qBase;
            baseSlider.SetValueWithoutNotify(startValue);
            UpdateValueLabel(startValue);
        }

        baseSlider.interactable = directControlEnabled;
    }

    public void SetDirectControlEnabled(bool enabled)
    {
        directControlEnabled = enabled;

        if (baseSlider != null)
            baseSlider.interactable = enabled;

        if (logDebug)
            Debug.Log("[BaseCameraDirectControl] directControlEnabled = " + enabled);
    }

    public void OnBaseSliderChanged(float sliderValue)
    {
        if (previewRobot == null)
            return;

        float visualAngle = invertVisualBase ? -sliderValue : sliderValue;
        previewRobot.SetBase(visualAngle);
        UpdateValueLabel(sliderValue);

        if (!directControlEnabled)
            return;

        float now = Time.unscaledTime;
        if (now - lastSendTime < 1f / Mathf.Max(sendHz, 1f))
            return;

        lastSendTime = now;

        if (commandSender != null)
        {
            // Usar exactamente el camino que sí funcionó en tu CLI:
            // mbase <deg> -> manip_ascii("BASE_GOTO ...")
            float cmdAngle = invertCommandBase ? -sliderValue : sliderValue;
            string cmd = "BASE_GOTO " + cmdAngle.ToString("F3", CultureInfo.InvariantCulture);
            commandSender.SendManipulatorAscii(cmd);

            if (logDebug)
                Debug.Log($"[BaseCameraDirectControl] slider={sliderValue:0.0}, visual={visualAngle:0.0}, cmd={cmd}");
        }
        else if (logDebug)
        {
            Debug.LogWarning("[BaseCameraDirectControl] commandSender es null.");
        }
    }

    private void UpdateValueLabel(float sliderValue)
    {
        if (baseValueText != null)
            baseValueText.text = sliderValue.ToString("F1") + "°";
    }
}
