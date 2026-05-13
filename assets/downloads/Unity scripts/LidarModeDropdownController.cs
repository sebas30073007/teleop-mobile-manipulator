using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class LidarModeDropdownController : MonoBehaviour
{
    [Header("References")]
    public ZmqLidarGridView lidarView;
    public TMP_Dropdown tmpDropdown;   // puede quedar en None si tu dropdown es custom
    public Toggle powerToggle;

    [Header("Behavior")]
    public bool syncDropdownOnStart = true;
    public int startupIndex = 0;   // 0=Detail, 1=Medium, 2=Panorama
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

        ApplyCurrentLidarState();
    }

    public void OnDropdownValueChanged(int index)
    {
        startupIndex = Mathf.Clamp(index, 0, 2);

        if (IsLidarPowerOn())
            ApplySelectedMode();
    }

    public void OnLidarPowerToggleChanged(bool isOn)
    {
        if (lidarView == null)
            return;

        if (isOn)
            ApplySelectedMode();
        else
            lidarView.SetOff();
    }

    public void SelectDetail()
    {
        startupIndex = 0;
        ApplySelectedMode();
    }

    public void SelectMedium()
    {
        startupIndex = 1;
        ApplySelectedMode();
    }

    public void SelectPanorama()
    {
        startupIndex = 2;
        ApplySelectedMode();
    }

    private void ApplyCurrentLidarState()
    {
        if (lidarView == null)
            return;

        if (IsLidarPowerOn())
            ApplySelectedMode();
        else
            lidarView.SetOff();
    }

    private void ApplySelectedMode()
    {
        if (lidarView == null)
            return;

        switch (startupIndex)
        {
            case 0:
                lidarView.SetDetail();
                break;
            case 1:
                lidarView.SetMedium();
                break;
            case 2:
                lidarView.SetPanorama();
                break;
            default:
                lidarView.SetDetail();
                break;
        }
    }

    private bool IsLidarPowerOn()
    {
        if (powerToggle == null)
            return true;

        return powerToggle.isOn;
    }
}