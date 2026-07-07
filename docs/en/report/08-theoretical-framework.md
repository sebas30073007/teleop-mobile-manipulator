---
title: "Theoretical Framework"
nav_order: 8
parent: "Report"
---

# Theoretical Framework

## 1. E-commerce logistics and warehouse automation

E-commerce logistics differs from traditional logistics in the granularity of its operations: instead of moving whole pallets between fixed points, it manages thousands of individual orders with narrow time windows and high SKU variety. This granularity shifts operational complexity toward the interior of the warehouse, specifically toward picking, sortation, and packing operations [3].

The industry's response has been progressive automation through AGV (Automated Guided Vehicles) systems, picking robots, automated conveyors, and AS/RS (Automated Storage and Retrieval Systems) systems. However, these systems are optimized for high volumes with low product variability and present flexibility limitations when facing demand or catalog changes. Collaborative robotization — where the robot extends the human operator's capabilities rather than replacing them — emerges as a complementary alternative, especially relevant in medium-sized operations or those with high SKU variability [4].

The concept of *logistics teleoperation* extends the collaborative model by eliminating the physical proximity constraint: the operator can supervise and control the robot from any location with adequate connectivity. This opens the possibility of redistributing operational workload toward user profiles who cannot be physically present in the warehouse, including people with motor disabilities.

## 2. Motor disability, telework, and labor inclusion

The International Labour Organization (ILO) frames disability in the labor context from a social model: disability is not an attribute of the person but the result of the interaction between individual conditions and environmental barriers. Consequently, labor inclusion requires modifying the environment — not just the person — to remove barriers to employment access.

In Mexico, data from INEGI (2024 Economic Censuses) reveal that formal labor participation of people with disabilities is structurally low [7][8]. Barriers are of three types: physical (access to the workplace, workstation ergonomics), technological (non-adapted interfaces, software without accessibility), and social (hiring-process prejudice, lack of specific training).

Conventional telework reduces physical barriers for office roles, but does not apply to operational tasks that require interaction with the physical environment. Robotic teleoperation extends the telework principle into physical domains: the remote operator interacts with the environment through a system that acts as a bodily proxy, enabling the execution of physical tasks without on-site presence. For this model to be genuinely inclusive, the control interface must be designed with accessibility criteria from the start — not as a later adaptation.

## 3. Mobile robotics, manipulation, and teleoperation

### Indoor mobile platforms

Indoor mobile robots typically operate on differential-drive, omnidirectional, or Ackermann-type bases. Differential drive — two independently motorized wheels with a passive support wheel — is the most common in warehouse applications due to its mechanical simplicity, ability to turn in place, and ease of kinematic control. Speed and direction control reduces to independently modulating each drive wheel's speed, which makes it directly compatible with analog joysticks such as those offered by an XR controller.

### Robotic manipulation for pick-and-place

Pick-and-place operations in logistics require at least two active degrees of freedom to operate in the vertical plane (reach and elevation), complemented by an end effector capable of grasping and releasing objects in a controlled manner. For the target range of logistics tasks — picking up boxes or light containers from shelves or conveyors — a two-joint arm (shoulder + elbow) with a two-finger gripper offers sufficient coverage of the relevant workspace with the least possible mechanical complexity.

Controlling stepper motors with closed-loop drivers (such as the CL57T) combines the control simplicity of steppers with encoder-based position feedback, eliminating the problem of step loss under variable load. For a manipulation application where repeatable precision is more critical than movement speed, this solution offers a favorable cost-performance ratio compared to industrial-grade servomotors.

### Latency and feedback in teleoperation

Effective teleoperation requires the operator to maintain *situational awareness* — awareness of the robot's state and its environment — through sensory feedback mediated by the system. The primary channel is visual feedback (first-person camera); depth feedback, ambient audio, and, in more advanced systems, haptic feedback, complement the experience.

Closed-loop latency — the time between the operator issuing a command and perceiving its effect through the feedback video — is the most critical performance parameter. Teleoperation studies document that latencies above 150–200 ms significantly degrade the operator's ability to make fine adjustments, increasing both execution time and error rate. For the context of this project, operating on a local network allows targeting end-to-end latencies below 100 ms.

## 4. Extended reality (XR) for teleoperation interfaces

Extended reality encompasses virtual reality (VR), augmented reality (AR), and mixed reality (MR). For teleoperation applications, immersive VR offers advantages over conventional 2D interfaces: more natural spatial perception of the robot's environment, intuitive control through head movement and hand controllers, and reduced cognitive distance between the operator's intent and the robot's action.

Current consumer headsets — particularly the Meta Quest family — offer resolution, refresh rate, and tracking capabilities sufficient for light industrial teleoperation applications, with the advantage of a significantly lower cost than industrial-grade equipment. The Meta XR SDK for Unity allows integrating stereoscopic rendering, controller tracking, and external video stream projection within the virtual scene, combining the robot's camera feedback with overlaid UI elements.

For operators with motor disabilities, the XR interface must be designed with integrated accessibility criteria: minimum number of actions required per task, alternative control options, redundant feedback (visual and auditory), and tolerance for movement imprecision. The XR interface's adaptability to different user profiles is one of the key advantages of this approach compared to specialized physical interfaces.

## 5. Usability and evaluation metrics in teleoperation

The usability of an interactive system is defined per ISO 9241-11 across three dimensions: effectiveness (does the user achieve the goal?), efficiency (at what cost in time and effort?), and satisfaction (is the experience acceptable?). All three dimensions are relevant to a teleoperation system, though with different weights depending on the use context.

The *System Usability Scale* (SUS) is the most widely adopted instrument for rapid usability evaluation: a 10-item Likert-scale questionnaire that produces a score from 0 to 100. Scores above 68 correspond to systems classified as acceptable for general use; scores above 80 are considered good. SUS has been validated on remote-control systems and robots, and its brevity makes it compatible with test sessions where the user's cognitive load is already high.

Cognitive load in teleoperation — the amount of mental resources the system demands from the operator — is a key determinant of both usability and accessibility. The factors that increase it most are: high latency, limited field of view in the feedback video, number of simultaneously active controls, and absence of assisted autonomy in the robot. Reducing cognitive load is, in this project, synonymous with designing for inclusion: a system that is simpler to operate is simultaneously a system that is more accessible for people with disabilities.

---

*Next: [Schedule →]({{ "/docs/en/report/09-schedule" | relative_url }})*
