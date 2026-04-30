using UnityEngine;
using UnityEngine.UI;
using TMPro;
using System.Globalization;

public class ManipulatorUIController : MonoBehaviour
{
    [Header("Robot")]
    public SimpleArm3DOF ghostRobot;
    public SimpleArm3DOF realRobot;
    public ZmqSensorReceiver sensorReceiver;
    public NucControlCommandSender commandSender;
    public GameObject ghostRoot;

    [Header("Sliders")]
    public Slider joint1Slider;
    public Slider joint2Slider;
    public Slider gripperSlider;

    [Header("Value Labels")]
    public TMP_Text joint1ValueText;
    public TMP_Text joint2ValueText;
    public TMP_Text gripperValueText;

    [Header("Buttons")]
    public Button homeButton;
    public Button implementButton;

    [Header("Behavior")]
    public bool activeOnStart = false;
    public bool copyRealPoseWhenEnabled = true;
    public bool sendHomeCommandToNuc = true;
    public bool mirrorDesiredToRealWhenNoFeedback = true;
    public bool sendAsAsciiCommands = true;

    [Header("Command Strategy")]
    public bool preferSingleJointCommands = true;
    public float commandCompareToleranceDeg = 0.25f;
    public bool logDebug = true;

    [Header("Gripper")]
    public bool usePhysicalGripperMmRange = true;
    public float gripperOpenMm = 80f;
    public float gripperClosedMm = 0f;
    public bool forceRightToLeftGripperSlider = true;
    public bool sendGripperOnImplement = true;
    public bool sendGripperOnHome = false;
    public bool syncGripperFromFeedback = true;

    [Tooltip("Si está activo, Unity manda exactamente la línea serial del script de Python: m <mm>, encapsulada como gripper_ascii. Si tu servidor ya usa gripper_cmd, déjalo apagado.")]
    public bool sendGripperAsAsciiMCommand = false;

    private bool manipModeActive = false;
    private float desiredQ1;
    private float desiredQ2;
    private float desiredGripper;

    private float lastKnownQ1;
    private float lastKnownQ2;
    private float lastKnownGripper;

    void Start()
    {
        if (ghostRobot == null)
        {
            Debug.LogError("ManipulatorUIController: ghostRobot no asignado.");
            return;
        }

        ConfigureRobotGripperRange(ghostRobot);
        ConfigureRobotGripperRange(realRobot);

        if (joint1Slider != null)
        {
            joint1Slider.minValue = ghostRobot.q1Min;
            joint1Slider.maxValue = ghostRobot.q1Max;
            joint1Slider.onValueChanged.RemoveListener(OnJoint1SliderChanged);
            joint1Slider.onValueChanged.AddListener(OnJoint1SliderChanged);
        }

        if (joint2Slider != null)
        {
            joint2Slider.minValue = ghostRobot.q2Min;
            joint2Slider.maxValue = ghostRobot.q2Max;
            joint2Slider.onValueChanged.RemoveListener(OnJoint2SliderChanged);
            joint2Slider.onValueChanged.AddListener(OnJoint2SliderChanged);
        }

        if (gripperSlider != null)
        {
            if (usePhysicalGripperMmRange)
            {
                gripperSlider.minValue = gripperClosedMm;
                gripperSlider.maxValue = gripperOpenMm;
                if (forceRightToLeftGripperSlider)
                    gripperSlider.direction = Slider.Direction.RightToLeft;
            }
            else
            {
                gripperSlider.minValue = ghostRobot.gripperMin;
                gripperSlider.maxValue = ghostRobot.gripperMax;
            }

            gripperSlider.onValueChanged.RemoveListener(OnGripperSliderChanged);
            gripperSlider.onValueChanged.AddListener(OnGripperSliderChanged);
        }

        if (homeButton != null)
        {
            homeButton.onClick.RemoveListener(OnHomePressed);
            homeButton.onClick.AddListener(OnHomePressed);
        }

        if (implementButton != null)
        {
            implementButton.onClick.RemoveListener(OnImplementPressed);
            implementButton.onClick.AddListener(OnImplementPressed);
        }

        SetManipModeActive(activeOnStart);
    }

    void Update()
    {
        if (realRobot != null && sensorReceiver != null && sensorReceiver.ManipStateValid)
        {
            realRobot.SetBase(sensorReceiver.ActualBaseDeg);
            realRobot.SetJoint1(sensorReceiver.ActualCodoDeg);
            realRobot.SetJoint2(sensorReceiver.ActualMunecaDeg);

            lastKnownQ1 = sensorReceiver.ActualCodoDeg;
            lastKnownQ2 = sensorReceiver.ActualMunecaDeg;
        }

        if (realRobot != null && sensorReceiver != null && sensorReceiver.GripperStateValid)
        {
            float feedbackGrip = ClampGripperMm(sensorReceiver.ActualGripperMm);
            realRobot.SetGripper(feedbackGrip);
            lastKnownGripper = feedbackGrip;

            if (syncGripperFromFeedback && !manipModeActive && gripperSlider != null)
            {
                gripperSlider.SetValueWithoutNotify(feedbackGrip);
                desiredGripper = feedbackGrip;
                RefreshLabels();
            }
        }
    }

    private void ConfigureRobotGripperRange(SimpleArm3DOF robot)
    {
        if (robot == null || !usePhysicalGripperMmRange)
            return;

        robot.gripperMin = gripperClosedMm;
        robot.gripperMax = gripperOpenMm;
        robot.homeGripper = gripperOpenMm;
        robot.gripperOpening = ClampGripperMm(robot.gripperOpening);
    }

    public void SetManipModeActive(bool active)
    {
        manipModeActive = active;

        if (ghostRoot != null)
            ghostRoot.SetActive(active);

        SetSliderInteractable(active);

        if (active)
        {
            ConfigureRobotGripperRange(ghostRobot);

            if (copyRealPoseWhenEnabled)
                SyncDesiredFromBestAvailablePose();
            else
                ApplyDesiredToGhost();
        }
    }

    private void SetSliderInteractable(bool enabled)
    {
        if (joint1Slider != null) joint1Slider.interactable = enabled;
        if (joint2Slider != null) joint2Slider.interactable = enabled;
        if (gripperSlider != null) gripperSlider.interactable = enabled;
        if (homeButton != null) homeButton.interactable = enabled;
        if (implementButton != null) implementButton.interactable = enabled;
    }

    private void SyncDesiredFromBestAvailablePose()
    {
        float srcQ1 = 0f;
        float srcQ2 = 0f;
        float srcGrip = usePhysicalGripperMmRange ? gripperOpenMm : (ghostRobot != null ? ghostRobot.gripperOpening : 0f);

        if (sensorReceiver != null && sensorReceiver.ManipStateValid)
        {
            srcQ1 = sensorReceiver.ActualCodoDeg;
            srcQ2 = sensorReceiver.ActualMunecaDeg;
        }
        else if (realRobot != null)
        {
            srcQ1 = realRobot.q1;
            srcQ2 = realRobot.q2;
        }

        if (sensorReceiver != null && sensorReceiver.GripperStateValid)
        {
            srcGrip = sensorReceiver.ActualGripperMm;
        }
        else if (realRobot != null)
        {
            srcGrip = realRobot.gripperOpening;
        }

        desiredQ1 = srcQ1;
        desiredQ2 = srcQ2;
        desiredGripper = ClampGripperMm(srcGrip);

        lastKnownQ1 = srcQ1;
        lastKnownQ2 = srcQ2;
        lastKnownGripper = desiredGripper;

        if (joint1Slider != null) joint1Slider.SetValueWithoutNotify(desiredQ1);
        if (joint2Slider != null) joint2Slider.SetValueWithoutNotify(desiredQ2);
        if (gripperSlider != null) gripperSlider.SetValueWithoutNotify(desiredGripper);

        ApplyDesiredToGhost();
    }

    public void OnJoint1SliderChanged(float value)
    {
        desiredQ1 = value;
        ApplyDesiredToGhost();
    }

    public void OnJoint2SliderChanged(float value)
    {
        desiredQ2 = value;
        ApplyDesiredToGhost();
    }

    public void OnGripperSliderChanged(float value)
    {
        desiredGripper = ClampGripperMm(value);
        ApplyDesiredToGhost();
    }

    public void OnHomePressed()
    {
        desiredQ1 = 0f;
        desiredQ2 = 0f;
        desiredGripper = usePhysicalGripperMmRange ? gripperOpenMm : (ghostRobot != null ? ghostRobot.homeGripper : 0f);
        desiredGripper = ClampGripperMm(desiredGripper);

        if (joint1Slider != null) joint1Slider.SetValueWithoutNotify(desiredQ1);
        if (joint2Slider != null) joint2Slider.SetValueWithoutNotify(desiredQ2);
        if (gripperSlider != null) gripperSlider.SetValueWithoutNotify(desiredGripper);

        ApplyDesiredToGhost();

        if (sendHomeCommandToNuc && commandSender != null)
        {
            if (sendAsAsciiCommands)
                commandSender.SendManipulatorAscii("HOME_ALL");
            else
                commandSender.SendManipulatorHome();
        }

        if (sendGripperOnHome)
            SendGripperCommand(desiredGripper);

        if (realRobot != null && (sensorReceiver == null || !sensorReceiver.ManipStateValid))
            realRobot.GoHome();

        if (realRobot != null && (sensorReceiver == null || !sensorReceiver.GripperStateValid))
            realRobot.SetGripper(desiredGripper);

        lastKnownQ1 = 0f;
        lastKnownQ2 = 0f;
        lastKnownGripper = desiredGripper;
    }

    public void OnImplementPressed()
    {
        if (commandSender != null)
        {
            if (sendAsAsciiCommands)
            {
                float refQ1 = (sensorReceiver != null && sensorReceiver.ManipStateValid) ? sensorReceiver.ActualCodoDeg : lastKnownQ1;
                float refQ2 = (sensorReceiver != null && sensorReceiver.ManipStateValid) ? sensorReceiver.ActualMunecaDeg : lastKnownQ2;

                bool q1Changed = Mathf.Abs(desiredQ1 - refQ1) > commandCompareToleranceDeg;
                bool q2Changed = Mathf.Abs(desiredQ2 - refQ2) > commandCompareToleranceDeg;

                if (preferSingleJointCommands && q1Changed && !q2Changed)
                {
                    string cmd = "CODO_GOTO " + desiredQ1.ToString("F3", CultureInfo.InvariantCulture);
                    commandSender.SendManipulatorAscii(cmd);
                    if (logDebug) Debug.Log("[ManipulatorUIController] " + cmd);
                }
                else if (preferSingleJointCommands && !q1Changed && q2Changed)
                {
                    string cmd = "MUNECA_GOTO " + desiredQ2.ToString("F3", CultureInfo.InvariantCulture);
                    commandSender.SendManipulatorAscii(cmd);
                    if (logDebug) Debug.Log("[ManipulatorUIController] " + cmd);
                }
                else
                {
                    string cmd = "POSE NA " +
                                 desiredQ1.ToString("F3", CultureInfo.InvariantCulture) + " " +
                                 desiredQ2.ToString("F3", CultureInfo.InvariantCulture);
                    commandSender.SendManipulatorAscii(cmd);
                    if (logDebug) Debug.Log("[ManipulatorUIController] " + cmd);
                }
            }
            else
            {
                commandSender.SendManipulatorPose(null, desiredQ1, desiredQ2);
            }

            if (sendGripperOnImplement)
                SendGripperCommand(desiredGripper);
        }

        if (realRobot != null && (sensorReceiver == null || !sensorReceiver.ManipStateValid) && mirrorDesiredToRealWhenNoFeedback)
        {
            realRobot.SetJoint1(desiredQ1);
            realRobot.SetJoint2(desiredQ2);
        }

        if (realRobot != null && (sensorReceiver == null || !sensorReceiver.GripperStateValid) && mirrorDesiredToRealWhenNoFeedback)
        {
            realRobot.SetGripper(desiredGripper);
        }

        lastKnownQ1 = desiredQ1;
        lastKnownQ2 = desiredQ2;
        lastKnownGripper = desiredGripper;
    }

    private void SendGripperCommand(float mm)
    {
        if (commandSender == null)
            return;

        mm = ClampGripperMm(mm);

        if (sendGripperAsAsciiMCommand)
        {
            string line = "m " + mm.ToString("F3", CultureInfo.InvariantCulture);
            commandSender.SendGripperAscii(line);
            if (logDebug) Debug.Log("[ManipulatorUIController] gripper ascii -> " + line);
        }
        else
        {
            commandSender.SendGripperMm(mm);
            if (logDebug) Debug.Log("[ManipulatorUIController] gripper_cmd mm -> " + mm.ToString("F3", CultureInfo.InvariantCulture));
        }
    }

    private void ApplyDesiredToGhost()
    {
        if (ghostRobot == null)
            return;

        ghostRobot.SetJoint1(desiredQ1);
        ghostRobot.SetJoint2(desiredQ2);
        ghostRobot.SetGripper(ClampGripperMm(desiredGripper));
        RefreshLabels();
    }

    private float ClampGripperMm(float value)
    {
        if (!usePhysicalGripperMmRange)
            return value;

        float min = Mathf.Min(gripperClosedMm, gripperOpenMm);
        float max = Mathf.Max(gripperClosedMm, gripperOpenMm);
        return Mathf.Clamp(value, min, max);
    }

    private void RefreshLabels()
    {
        if (joint1ValueText != null)
            joint1ValueText.text = desiredQ1.ToString("F1") + "°";

        if (joint2ValueText != null)
            joint2ValueText.text = desiredQ2.ToString("F1") + "°";

        if (gripperValueText != null)
            gripperValueText.text = ClampGripperMm(desiredGripper).ToString("F1") + " mm";
    }
}
