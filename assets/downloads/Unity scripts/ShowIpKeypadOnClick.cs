using UnityEngine;
using UnityEngine.EventSystems;

public class ShowIpKeypadOnClick : MonoBehaviour, IPointerClickHandler
{
    public IpKeypadController keypadController;

    public void OnPointerClick(PointerEventData eventData)
    {
        if (keypadController != null)
            keypadController.ShowKeypad();
    }
}