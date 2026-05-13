using UnityEngine;
using UnityEngine.SceneManagement;

public class SceneSwitcher : MonoBehaviour
{
    [Header("Scene Names")]
    public string sceneA = "main_v2";
    public string sceneB = "mr_view";

    [Header("Controller Debug")]
    public bool useLeftControllerButtons = true;

    private void Update()
    {
        if (!useLeftControllerButtons)
            return;

        // X en control izquierdo
        if (OVRInput.GetDown(OVRInput.Button.Three))
        {
            LoadSceneA();
        }

        // Y en control izquierdo
        if (OVRInput.GetDown(OVRInput.Button.Four))
        {
            LoadSceneB();
        }
    }

    public void LoadSceneA()
    {
        if (SceneManager.GetActiveScene().name == sceneA)
            return;

        Debug.Log("[SceneSwitcher] Loading scene A: " + sceneA);
        SceneManager.LoadScene(sceneA);
    }

    public void LoadSceneB()
    {
        if (SceneManager.GetActiveScene().name == sceneB)
            return;

        Debug.Log("[SceneSwitcher] Loading scene B: " + sceneB);
        SceneManager.LoadScene(sceneB);
    }

    public void ToggleScene()
    {
        string current = SceneManager.GetActiveScene().name;

        if (current == sceneA)
            LoadSceneB();
        else
            LoadSceneA();
    }
}