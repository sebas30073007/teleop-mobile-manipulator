---
title: "Methodology"
nav_order: 7
parent: "Report"
---

# Methodology

The project follows a four-phase sequential engineering design methodology, with iterations within each phase as new information emerges. The approach is artifact-oriented: knowledge is generated through the design, construction, and evaluation of a real system, not through theoretical models disconnected from its physical implementation.

## Phase 1 — Context analysis and task characterization

**Objective:** Establish what problem is being solved, for whom, and under what operational conditions.

**Process:** Literature review on e-commerce logistics, warehouse automation, motor disability, and existing teleoperation systems. Identification of candidate logistics tasks for teleoperation and evaluation of each according to three criteria: execution complexity, operational risk, and automation benefit potential. Prioritization of use cases for the prototype.

**Deliverables:** Task analysis table with prioritization criteria. Definition of the main use case: internal transfer and pick-and-place operation in a simulated warehouse.

## Phase 2 — Requirements definition and architecture design

**Objective:** Translate the characterized problem into a designable and evaluable system specification.

**Process:** Gathering of functional requirements (what the system must do) and non-functional requirements (precision, accessibility, cost). Evaluation and selection of technologies: Python + ZeroMQ (ZMQ) as coordination middleware, ESP32-C3 with MicroPython as the robotic platform's embedded controller, NEMA stepper motors with closed-loop CL57T drivers, Unity and Meta Quest for the XR layer. Design of the modular three-layer architecture and incremental integration plan.

**Deliverables:** System requirements specification. Architecture diagram and inter-subsystem communication diagram. Implementation plan with integration sequence.

## Phase 3 — Implementation and integration

**Objective:** Build the functional prototype that meets the requirements specification.

**Process:** Parallel development of the three subsystems with defined integration points. The robotic platform is validated first, independently: mobility, arm control, and sensor feedback. Then the Python/ZMQ server is integrated and robot-server communication over the local network is verified. Finally the XR layer is added and the complete teleoperation flow is validated: operator command → ZMQ → robot → visual feedback to the operator.

**Deliverables:** Integrated functional prototype. Documented operating protocol. Log of issues found and mitigations applied during integration.

## Phase 4 — Experimental validation

**Objective:** Generate quantitative evidence on the technical performance and usability of the system.

**Process:** Execution of test sessions with operators in simulated warehouse scenarios. Systematic data collection per task and per session: timed execution time, error event logging, application of the SUS questionnaire at the end of each session. Descriptive statistical analysis of the results and comparison against the reference thresholds defined in the objectives.

**Deliverables:** Test results dataset. Performance analysis by subsystem and by task. Conclusions on technical feasibility and recommendations for future iterations or system scaling.

---

*Next: [Theoretical Framework →]({{ "/docs/en/report/08-theoretical-framework" | relative_url }})*
