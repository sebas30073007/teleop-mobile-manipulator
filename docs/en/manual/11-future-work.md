---
title: "Future Work"
nav_order: 11
parent: "Documentation"
---

# Future Work

Development directions identified from the results and limitations of the terminal project.

## Hardware

- **Dedicated PCB for the gripper** — design a proper board for the gripper controller to replace the current protoboard assembly, improving mechanical robustness and reducing loose wiring.

## Control and mathematical models

- **Mathematical model for unicycle mobile robots** — implement the AGV's differential kinematic model to compute odometry and execute programmed trajectories, instead of relying exclusively on direct manual control from the XR interface.
- **Manipulator inverse kinematics** — implement the inverse kinematics model for the 3 DOF to command the end-effector by Cartesian position, instead of individual joint angles.
- **Encoder capture for closed-loop control** — integrate reading of the traction motors' encoders into the H-bridge firmware to implement closed-loop speed and position control, eliminating the dependency on the current open-loop control.
