using UnityEngine;
using UnityEngine.UI;

public class ControlModeState : MonoBehaviour
{
    [Header("Toggles")]
    public Toggle mobileToggle;
    public Toggle manipToggle;
    public Toggle baseCamToggle;

    [Header("References")]
    public NucControlCommandSender commandSender;
    public QuestMobileDriveTeleop mobileTeleop;
    public ManipulatorUIController manipulatorUI;
    public BaseCameraDirectControl baseCameraControl;

    [Header("Behavior")]
    public bool exclusiveModes = true;

    public bool MobileEnabled => mobileToggle != null && mobileToggle.isOn;
    public bool ManipEnabled => manipToggle != null && manipToggle.isOn;
    public bool BaseEnabled => baseCamToggle != null && baseCamToggle.isOn;

    void Start()
    {
        if (mobileToggle != null) mobileToggle.onValueChanged.AddListener(OnMobileToggleChanged);
        if (manipToggle != null) manipToggle.onValueChanged.AddListener(OnManipToggleChanged);
        if (baseCamToggle != null) baseCamToggle.onValueChanged.AddListener(OnBaseCamToggleChanged);
        ApplyState();
    }

    public void OnMobileToggleChanged(bool isOn)
    {
        if (exclusiveModes && isOn)
        {
            if (manipToggle != null) manipToggle.SetIsOnWithoutNotify(false);
            if (baseCamToggle != null) baseCamToggle.SetIsOnWithoutNotify(false);
        }
        ApplyState();
    }

    public void OnManipToggleChanged(bool isOn)
    {
        if (exclusiveModes && isOn)
        {
            if (mobileToggle != null) mobileToggle.SetIsOnWithoutNotify(false);
            if (baseCamToggle != null) baseCamToggle.SetIsOnWithoutNotify(false);
        }
        ApplyState();
    }

    public void OnBaseCamToggleChanged(bool isOn)
    {
        if (exclusiveModes && isOn)
        {
            if (mobileToggle != null) mobileToggle.SetIsOnWithoutNotify(false);
            if (manipToggle != null) manipToggle.SetIsOnWithoutNotify(false);
        }
        ApplyState();
    }

    public void DisableAllModes()
    {
        if (mobileToggle != null) mobileToggle.SetIsOnWithoutNotify(false);
        if (manipToggle != null) manipToggle.SetIsOnWithoutNotify(false);
        if (baseCamToggle != null) baseCamToggle.SetIsOnWithoutNotify(false);
        ApplyState();
    }

    private void ApplyState()
    {
        bool drive = MobileEnabled;
        bool manip = ManipEnabled;
        bool baseCtrl = BaseEnabled;

        if (mobileTeleop != null)
            mobileTeleop.SetTeleopEnabled(drive);

        if (manipulatorUI != null)
            manipulatorUI.SetManipModeActive(manip);

        if (baseCameraControl != null)
            baseCameraControl.SetDirectControlEnabled(baseCtrl);

        if (commandSender != null)
        {
            commandSender.SendControlEnable(drive, manip, baseCtrl);

            if (drive)
            {
                commandSender.SendMasterArm();
            }
            else
            {
                commandSender.SendStopAll();
                commandSender.SendMasterDisarm();
            }
        }
    }
}
