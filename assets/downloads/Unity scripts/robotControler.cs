using UnityEngine;

public class SimpleArm3DOF : MonoBehaviour
{
    [Header("Arm Joints")]
    public Transform jointBase;
    public Transform jointPrimerEslabon;
    public Transform jointSegundoEslabon;

    [Header("Gripper")]
    public Transform gripperLeft;
    public Transform gripperRight;

    [Header("Current Angles (deg)")]
    public float qBase = 0f;
    public float q1 = 0f;
    public float q2 = 0f;

    [Header("Joint Limits")]
    public float qBaseMin = -80f;
    public float qBaseMax = 80f;
    public float q1Min = 0f;
    public float q1Max = 146f;
    public float q2Min = -220f;
    public float q2Max = 0f;

    [Header("Home Position")]
    public float homeBase = 0f;
    public float homeQ1 = 0f;
    public float homeQ2 = 0f;

    [Header("Gripper - Physical Opening mm")]
    [Tooltip("Apertura física del gripper en milímetros. 80 = abierto, 0 = cerrado.")]
    public float gripperOpening = 80f;
    public float gripperMin = 0f;
    public float gripperMax = 80f;
    public float homeGripper = 80f;

    [Header("Axis Mapping")]
    public Vector3 baseAxis = Vector3.up;
    public Vector3 joint1Axis = Vector3.right;
    public Vector3 joint2Axis = Vector3.right;

    [Header("Axis Direction")]
    public bool invertBase = false;
    public bool invertQ1 = false;
    public bool invertQ2 = false;

    [Header("Zero Offsets")]
    public Vector3 baseZeroEuler = Vector3.zero;
    public Vector3 joint1ZeroEuler = Vector3.zero;
    public Vector3 joint2ZeroEuler = Vector3.zero;

    [Header("Gripper Reference Local Positions")]
    [Tooltip("Posición local tomada como referencia. Se cachea automáticamente antes del primer movimiento.")]
    public Vector3 leftInitialLocalPos;
    public Vector3 rightInitialLocalPos;

    [Header("Gripper Visual Mapping")]
    [Tooltip("Actívalo si el modelo 3D ya arranca visualmente ABIERTO. Desactívalo si arranca CERRADO.")]
    public bool gripperInitialPoseIsOpen = true;

    [Tooltip("Si 1 unidad de Unity = 1 metro, deja 0.001. Si tu modelo está escalado, ajusta este valor.")]
    public float gripperMmToUnity = 0.001f;

    [Tooltip("Normalmente la apertura indicada es distancia total entre dedos, por eso cada dedo se mueve la mitad.")]
    public bool gripperOpeningIsTotalGap = true;

    [Tooltip("Multiplicador visual por si el modelo necesita más/menos recorrido sin cambiar los mm enviados al robot.")]
    public float gripperVisualMultiplier = 1f;

    [Tooltip("Dirección local en la que este dedo se mueve cuando el gripper ABRE.")]
    public Vector3 gripperLeftAxis = Vector3.left;

    [Tooltip("Dirección local en la que este dedo se mueve cuando el gripper ABRE.")]
    public Vector3 gripperRightAxis = Vector3.right;

    [Header("Startup")]
    public bool goHomeOnStart = true;

    [Header("Debug")]
    public bool logPoseChanges = false;

    private bool gripperReferenceCached = false;

    void Awake()
    {
        EnsureGripperReferenceCached();
    }

    void Start()
    {
        EnsureGripperReferenceCached();

        if (goHomeOnStart)
        {
            qBase = homeBase;
            q1 = homeQ1;
            q2 = homeQ2;
            gripperOpening = homeGripper;
        }

        ApplyPoseImmediate();
    }

    [ContextMenu("Cache Current Gripper Pose As Reference")]
    public void CacheInitialGripperPositions()
    {
        if (gripperLeft != null) leftInitialLocalPos = gripperLeft.localPosition;
        if (gripperRight != null) rightInitialLocalPos = gripperRight.localPosition;
        gripperReferenceCached = true;

        if (logPoseChanges)
            Debug.Log($"[SimpleArm3DOF] Gripper reference cached. L={leftInitialLocalPos}, R={rightInitialLocalPos}");
    }

    private void EnsureGripperReferenceCached()
    {
        if (!gripperReferenceCached)
            CacheInitialGripperPositions();
    }

    public void SetBase(float angleDeg)
    {
        qBase = Mathf.Clamp(angleDeg, qBaseMin, qBaseMax);
        ApplyPoseImmediate();
    }

    public void SetJoint1(float angleDeg)
    {
        q1 = Mathf.Clamp(angleDeg, q1Min, q1Max);
        ApplyPoseImmediate();
    }

    public void SetJoint2(float angleDeg)
    {
        q2 = Mathf.Clamp(angleDeg, q2Min, q2Max);
        ApplyPoseImmediate();
    }

    public void SetGripper(float openingMm)
    {
        gripperOpening = Mathf.Clamp(openingMm, gripperMin, gripperMax);
        ApplyPoseImmediate();
    }

    public void GoHome()
    {
        qBase = homeBase;
        q1 = homeQ1;
        q2 = homeQ2;
        gripperOpening = homeGripper;
        ApplyPoseImmediate();
    }

    public void CopyPoseFrom(SimpleArm3DOF other)
    {
        if (other == null) return;

        qBase = other.qBase;
        q1 = other.q1;
        q2 = other.q2;
        gripperOpening = other.gripperOpening;
        ApplyPoseImmediate();
    }

    public float[] GetJointPoseArray()
    {
        return new float[] { qBase, q1, q2 };
    }

    public void ApplyPoseImmediate()
    {
        if (jointBase != null)
            jointBase.localRotation = Quaternion.Euler(baseZeroEuler + NormalizedAxis(baseAxis) * SignedAngle(qBase, invertBase));

        if (jointPrimerEslabon != null)
            jointPrimerEslabon.localRotation = Quaternion.Euler(joint1ZeroEuler + NormalizedAxis(joint1Axis) * SignedAngle(q1, invertQ1));

        if (jointSegundoEslabon != null)
            jointSegundoEslabon.localRotation = Quaternion.Euler(joint2ZeroEuler + NormalizedAxis(joint2Axis) * SignedAngle(q2, invertQ2));

        ApplyGripper();

        if (logPoseChanges)
            Debug.Log($"[SimpleArm3DOF] qBase={qBase:0.0}, q1={q1:0.0}, q2={q2:0.0}, gripMm={gripperOpening:0.0}");
    }

    private void ApplyGripper()
    {
        EnsureGripperReferenceCached();

        float openingMm = Mathf.Clamp(gripperOpening, gripperMin, gripperMax);
        float referenceMm = gripperInitialPoseIsOpen ? gripperMax : gripperMin;
        float deltaMmFromReference = openingMm - referenceMm;

        float perJawFactor = gripperOpeningIsTotalGap ? 0.5f : 1f;
        float deltaUnity = deltaMmFromReference * gripperMmToUnity * perJawFactor * gripperVisualMultiplier;

        if (gripperLeft != null)
            gripperLeft.localPosition = leftInitialLocalPos + NormalizedAxis(gripperLeftAxis) * deltaUnity;

        if (gripperRight != null)
            gripperRight.localPosition = rightInitialLocalPos + NormalizedAxis(gripperRightAxis) * deltaUnity;
    }

    private static Vector3 NormalizedAxis(Vector3 axis)
    {
        if (axis.sqrMagnitude < 0.0001f)
            return Vector3.right;
        return axis.normalized;
    }

    private static float SignedAngle(float angleDeg, bool invert)
    {
        return invert ? -angleDeg : angleDeg;
    }
}
