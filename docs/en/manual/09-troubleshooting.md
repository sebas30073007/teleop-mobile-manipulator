---
title: "Troubleshooting"
nav_order: 9
parent: "Documentation"
---

# Troubleshooting

## Common failures

| Case | Symptom | Probable causes | What to check |
|---|---|---|---|
| No ZMQ communication | No data reaching XR | Invalid network, service not started, ports unavailable | Backend status, local network, documented ports |
| XR does not receive data | Empty or non-updating panels | Inactive subscription, incorrect endpoint | Endpoint configuration, topic status |
| Robot does not move | Command received without physical action | Incomplete control bridge, firmware not running | ESP32-C3 status, power, control link |
| One motor does not respond | Partial movement | Embedded module or physical connection | Wiring, module, output signals |
| ESP32-C3 not running firmware | No response from module | Missing firmware or incorrect deployment | Flashing and boot method |
| Computer does not detect device | Sensor/control not visible | Physical connection or driver | Physical port, USB link, module status |
| Physical movement does not match virtual | Inconsistent action | Partial mapping or lack of calibration | Control configuration and spatial references |
| Irregular response or delay | Unstable control | System load, network, or synchronization | Network status and resource consumption |

> **Pending:** Add diagnostic procedures with concrete commands per subsystem and a historical log of resolved failures.
