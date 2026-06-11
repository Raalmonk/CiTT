# VeriCircuit Tutor Project Memo

## Motivation

Large language models can be helpful tutors, but circuit analysis is a domain where confident prose is not enough. A small sign error, a mistaken current direction, or an ungrounded node can change the answer while leaving the explanation sounding plausible. For introductory circuits courses, that creates a trust problem: students need explanations, but instructors need the numerical work to be anchored in circuit laws rather than generated language.

VeriCircuit Tutor explores a simulation-grounded design. The system does not ask an LLM to solve the circuit directly. Instead, it parses a problem into a formal Circuit IR, validates that representation, solves it with Modified Nodal Analysis, verifies the numerical solution, and only then generates a tutor explanation from the verified Solution Packet.

## Research And Engineering Question

The guiding question is: can an AI tutor for circuit analysis be made more reliable by separating language tasks from numerical truth tasks?

In this MVP, the LLM is allowed to help with translation and explanation, but it is not allowed to invent final numerical answers. The solver and verifier own the answer. The tutoring layer is constrained to cite values already present in the Solution Packet.

## System Design

The architecture is:

```text
natural language -> Circuit IR -> validation -> MNA solver -> verification -> Solution Packet -> explanation
```

The Circuit IR is a Pydantic model containing nodes, supported components, requested goals, assumptions, ambiguities, and unsupported features. The current supported analysis type is DC operating point for linear circuits with resistors, independent voltage sources, and independent current sources.

The solver uses Modified Nodal Analysis. Unknowns are non-ground node voltages plus currents through independent voltage sources. Resistors stamp conductance terms, current sources stamp RHS injections, and voltage sources add MNA rows and columns. The solver returns node voltages, component voltages, currents, powers, and requested answers.

## Verification Strategy

The verifier performs deterministic checks after solving:

- Ground node exists.
- Component nodes are valid.
- Component graph is connected to the ground-referenced circuit.
- Units are normalized to SI values.
- KCL residuals are near zero at every non-ground node.
- Signed component powers sum to approximately zero.
- Every requested goal has an answer.

The sign convention is consistent across the system: component voltage is `V(nodes[0]) - V(nodes[1])`, current is positive from `nodes[0]` to `nodes[1]`, and signed power is voltage times current. Negative source power means the source supplies energy to the circuit.

## MVP Scope

The MVP intentionally supports a narrow set of circuits: linear DC operating point, first-order RC transient templates, AC steady-state/sweep analysis for linear R/L/C circuits and independent sources, and ideal closed-loop op-amp DC. It does not include general transient analysis, DC inductor behavior, diodes, transistors, dependent sources, nonlinear solving, nonideal op-amp behavior, or schematic/image recognition.

On top of that solver scope, the demo includes named BME templates for ECG/EMG front-ends, pressure and strain bridges, thermistor dividers, photodiode transimpedance amplifiers, instrumentation amplifiers, and anti-aliasing filters. These templates are ordinary Circuit IR examples that still pass through the same validation, solving, and verification pipeline.

This narrow scope is a feature, not a defect. It makes the verification story clear and inspectable for a professor demo.

## Evaluation Plan

The initial benchmark should include 20 problems split across simple dividers, nodal-analysis circuits, Thevenin/Norton-style circuits, and future unsupported bridge/dependent-source examples. Metrics include parse correctness, numerical correctness, unit correctness, sign-convention correctness, explanation consistency, and honest uncertainty when unsupported.

## Why This Is More Than Prompt Engineering

Prompt engineering tries to elicit better answers from a language model. VeriCircuit Tutor changes the authority structure. The final numerical answer comes from a formal circuit representation, numerical solving, and circuit-law verification. Language generation is downstream of that verified packet. That separation is what makes the system interesting for trustworthy tutoring: the tutor can be conversational without being the source of numerical truth.
