using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class CameraModeDropdownController : MonoBehaviour
{
    [Header("References")]
    public ZmqVideoReceiver videoReceiver;
    public TMP_Dropdown tmpDropdown;
    public Toggle powerToggle;

    [Header("Behavior")]
    public bool syncDropdownOnStart = true;
    public int startupIndex = 0;   // 0=Normal, 1=Pose, 2=Segment
    public bool startupPowerOn = true;

    void Start()
    {
        startupIndex = Mathf.Clamp(startupIndex, 0, 2);

        if (syncDropdownOnStart && tmpDropdown != null)
        {
            tmpDropdown.SetValueWithoutNotify(startupIndex);
            tmpDropdown.RefreshShownValue();
        }

        if (powerToggle != null)
        {
            powerToggle.SetIsOnWithoutNotify(startupPowerOn);
        }

        ApplyCurrentCameraState();
    }

    public void OnDropdownValueChanged(int index)
    {
        startupIndex = Mathf.Clamp(index, 0, 2);

        // Solo aplicamos el modo si la cámara está encendida
        if (IsCameraPowerOn())
        {
            ApplySelectedMode();
        }
    }

    public void OnCameraPowerToggleChanged(bool isOn)
    {
        if (videoReceiver == null)
            return;

        if (isOn)
        {
            ApplySelectedMode();
        }
        else
        {
            videoReceiver.SetCameraOff();
        }
    }

    public void SelectNormal()
    {
        startupIndex = 0;

        if (tmpDropdown != null)
        {
            tmpDropdown.SetValueWithoutNotify(0);
            tmpDropdown.RefreshShownValue();
        }

        if (IsCameraPowerOn())
            ApplySelectedMode();
    }

    public void SelectPose()
    {
        startupIndex = 1;

        if (tmpDropdown != null)
        {
            tmpDropdown.SetValueWithoutNotify(1);
            tmpDropdown.RefreshShownValue();
        }

        if (IsCameraPowerOn())
            ApplySelectedMode();
    }

    public void SelectSegment()
    {
        startupIndex = 2;

        if (tmpDropdown != null)
        {
            tmpDropdown.SetValueWithoutNotify(2);
            tmpDropdown.RefreshShownValue();
        }

        if (IsCameraPowerOn())
            ApplySelectedMode();
    }

    private void ApplyCurrentCameraState()
    {
        if (videoReceiver == null)
            return;

        if (IsCameraPowerOn())
            ApplySelectedMode();
        else
            videoReceiver.SetCameraOff();
    }

    private void ApplySelectedMode()
    {
        if (videoReceiver == null)
            return;

        int index = startupIndex;

        if (tmpDropdown != null)
            index = Mathf.Clamp(tmpDropdown.value, 0, 2);

        switch (index)
        {
            case 0:
                videoReceiver.SetCameraNormal();
                break;
            case 1:
                videoReceiver.SetCameraPose();
                break;
            case 2:
                videoReceiver.SetCameraSegment();
                break;
            default:
                videoReceiver.SetCameraNormal();
                break;
        }
    }

    private bool IsCameraPowerOn()
    {
        if (powerToggle == null)
            return true; // si no hay toggle, asumimos encendida

        return powerToggle.isOn;
    }
}