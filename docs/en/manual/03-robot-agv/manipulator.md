---
title: "3DOF Manipulator"
nav_order: 3
parent: "Robot AGV"
---

# 3DOF Manipulator

## Requirements

The manipulator had to perform pick-and-place tasks in e-commerce logistics environments. Baseline elements:

- Available materials: 18-gauge (1.2 mm) and 24-gauge (0.6 mm) steel sheet
- Available tools: laser cutter
- Available motors: NEMA17 (lab stock)
- Light and compact enough to mount on the AGV platform
- Gripping capability for medium-sized objects


## Design

![Full manipulator — side view]({{ "/assets/img/render.png" | relative_url }})

The arm has **3 rotational joints** plus a **linear gripper**:

| Component | Description |
|---|---|
| Link 1 | 0.6 mm steel, HTD3M 50T transmission (2.5:1) |
| Link 2 | 0.6 mm steel, HTD3M 50T transmission (2.5:1) |
| Base / shoulder | 1.2 mm steel, HTD3M 50T transmission (1:1) |
| Gripper | Rack and pinion, Pololu motor with gearbox (100:1) |
| Actuators | NEMA17 + 10:1 planetary gearbox + HTD3M pulley (2.5:1) |
| Bearings | Bearings at each joint |
| Mounted sensors | Intel RealSense D435i + RPLiDAR C1 |

Design principles:
- **Structural rigidity** via laser-cut steel
- **HTD3M belt transmission** to increase the robot's load capacity
- **Compound reduction (10:1 × 2.5:1 = 25:1)** for sufficient torque with NEMA17



## Manufacturing

### Laser cutting

The structural parts were laser-cut from steel sheet. The DXF files are in [`assets/raw_assets/CADs manipulador/DXF/`](https://github.com/sebas30073007/teleop-mobile-manipulator/tree/main/assets/raw_assets/CADs%20manipulador/DXF) of the repository.

![Laser cutting manufacturing]({{ "/assets/img/manipulador_corte_laser.jpg" | relative_url }})

{% include video_youtube.html id="HL85R2YZLBA" title="Building the 3DOF manipulator — Capstone Project 2026" %}

The process combined **laser cutting** and **manual bending** with the bender available in the lab. The parts were designed considering the accessible tools, which imposed an important constraint: the bend angles were very tight, at the limit of what was feasible with the manual bender. When a section required bends that couldn't be executed without risk of fracture or excessive deformation, the solution was to **split the part** into two or more sections and join them afterward with fasteners.

### First parts

The parts that required the most iterations were the **L-shaped pieces** connecting the base to the first link and the motor: the combination of manufacturing tolerances and design adjustments forced several versions of this particular part. The other parts also went through iterations, though minor ones. Most were due to missing drill holes that didn't justify a full new cut — it was enough to drill the hole into the already-cut part.

As a lesson learned from the process, the bent-sheet-metal methodology proved suitable for prototyping, but presented a notable limitation: **unwanted flexibility on the axis perpendicular to the load axis**. The structure was robust along the main axis, but on the perpendicular axis any minimal force generated visible oscillation. These are stresses that were not accounted for in the original design and are characteristic of this type of sheet-metal assembly — strong in one direction, weaker in the orthogonal one. In no case was there permanent deformation or damage to the system, but the mechanical play — due to material flexibility, not looseness in the joints — was noticeable during operation.

![First assembled parts]({{ "/assets/img/manipulador_primeras_piezas.jpg" | relative_url }})

## Assembly

The assembly integrates all of the manipulator's mechanical subsystems. The sections below detail each one of them: gripper, transmission mechanisms, base rotational axis, and pulley and limit-sensor system.

![Full manipulator assembly]({{ "/assets/img/AGV_manipulador completo.png" | relative_url }})


### Gripper


The manipulator's gripper is made of two 3D-printed red jaws, designed to open and close symmetrically via a rack-and-pinion mechanism. The collage shows different views of the system: a view mounted on the manipulator, a top view, and a front view of the mechanism.

The gripper is actuated by a Pololu motor with mechanical reduction, which transmits motion to a central pinion. This pinion meshes with the internal racks of both jaws, allowing them to move in opposite directions. The jaw geometry includes internal rib-type reinforcements, which keep the structure lightweight without losing rigidity.

This design was intended for basic manipulation tasks, where the robot can grip objects without requiring an overly heavy or complex mechanism. Located at the end of the second link, the gripper is the manipulator's end tool and directly defines the robot's capacity for physical interaction with its environment.
![Gripper]({{ "/assets/img/Manipulador gripper.png" | relative_url }})

The gripper is controlled by a dedicated ESP32-C3, connected directly to the NUC over an independent USB (COM5). See [Driver Controller]({{ "/docs/en/manual/03-robot-agv/driver-controller-cl57t" | relative_url }}) and [Embedded Software]({{ "/docs/en/manual/03-robot-agv/embedded-software" | relative_url }}).



### Transmission and support mechanisms


This collage shows details of the manipulator's mechanical transmission system, mainly in the areas where pulleys, belts, and bearings transmit motion from the motors to the links. The toothed-belt transmission allows the joints to move without placing all the motors directly on the final axes, helping to better distribute the system's weight.

The left image shows one of the manipulator's main joints, where a red pulley transmits motion to the rotation axis. The bearing supports the shaft and prevents it from rubbing directly against the structural sheet metal. This allows for cleaner, more stable motion with less friction.

The right image shows a close-up of the pulley, belt, and tensioner bearing system. The bearing acts as an additional support to improve belt tension and reduce play during movement. This kind of solution was important so the manipulator could move in a more controlled way, especially considering that the structure works with several axes, belts, and bolted elements.

![Lateral transmission and link rotational axis]({{ "/assets/img/Mecanismos.png" | relative_url }})



### Manipulator base rotational axis

The base rotational axis allows the entire manipulator to rotate relative to the mobile platform. The image shows the mechanical assembly responsible for generating this rotation, as well as the metal structure that supports the arm's weight.

Rotation is transmitted by a motor located at the rear of the manipulator, using a pulley-and-belt reduction. Unlike the links, which use a larger reduction, the base uses a smaller reduction, sufficient to generate rotation of the full assembly. This configuration allows the manipulator's orientation motion to be separated from the motion of the upper links.

The "C"-shaped structure that raises the manipulator above the mobile base is also visible. This part was manufactured from bent, reinforced sheet metal, since testing showed that rigidity was critical to support the manipulator's weight. The double layer of material helps reduce deformation and improves the system's stability during movement.

The internal volume of this structure is also used to house electronic components, such as CL57T drivers and wiring, reducing the robot's visual clutter and optimizing the use of available space.


![Rotating base — motor and rotating base support]({{ "/assets/img/Eje rotacional.png" | relative_url }})



### Pulley, belt, and limit-sensor system

This collage shows the main pulley and belt system responsible for transmitting motion from the motors to the manipulator's links. The mechanical architecture uses two motors placed in parallel and symmetrically: one controls the first link, and the other controls the second link via an additional transmission.

The first motor transmits motion directly to the first link. The second motor starts from the same shaft area, but its pulley is not rigidly attached to the first link; this allows motion to be transmitted independently to the second link through another belt that runs up to the upper joint. This way, each degree of freedom retains its own transmission, even though they share nearby physical zones within the structure.

The images also show the tensioning systems implemented with bearings. These tensioners help keep the belts at the proper tension and reduce issues such as slipping, play, or vibration. In the lower area, a transverse bar with bearings serves as a common tensioner for the links' transmission systems.

The right-hand view shows one of the limit switches mounted near the manipulator's physical travel path. These sensors were placed at strategic points to serve as calibration reference and mechanical limit. Their location allows a position close to the system's zero to be defined without interfering with the arm's normal movement.


![Pulleys and belts — diagonal view]({{ "/assets/img/Poleas.png" | relative_url }})



## CAD and source files

The full CAD project (Autodesk Inventor 2026) is in [`assets/raw_assets/CADs manipulador/`](https://github.com/sebas30073007/teleop-mobile-manipulator/tree/main/assets/raw_assets/CADs%20manipulador) of the repository:

- `Ensamble final.iam` — full manipulator assembly
- `Gripper_0.iam` — gripper subassembly
- Individual `.ipt` files per part
- DXF laser-cutting files in `DXF/`
- STEP files for reference motors and gearboxes

## Validation

| Test | Result |
|---|---|
| Range of motion per joint | ✅ Reached |
| Play in HTD3M transmissions | ✅ No excessive play |
| Fast movement speed | ✅ Functional |
| Integrated remote control XR → NUC → manipulator | ⏳ Pending |

See full evidence in [Testing and Calibration]({{ "/docs/en/manual/03-robot-agv/testing-calibration" | relative_url }}).
