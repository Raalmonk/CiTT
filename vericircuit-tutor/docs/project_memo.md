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

The Circuit IR is a Pydantic model containing nodes, supported components, requested goals, assumptions, ambiguities, and unsupported features. The current supported analysis modes are linear DC operating point, AC phasor/sweep analysis for linear R/L/C/source circuits, first-order RC transient templates, ideal closed-loop op-amp DC, simplified nonideal op-amp analysis, and Gemini image-to-Circuit-IR parsing, all behind explicit validation boundaries.

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

## Product Capabilities

The current product is not a general simulator wrapped in chat. It is a controlled learning environment with a few deliberately visible capabilities:

- Verified circuit answers: supported prompts become explicit Circuit IR, solver output, verification badges, and provenance.
- Guided visual lessons: solved PASS packets become step-by-step teaching moves tied to schematic focus regions and verified value references.
- Reasoning coach: students can commit a partial frame, receive one local nudge, and reveal final values only after the coach boundary is satisfied.
- BME teaching templates: biomedical instrumentation context is attached to verified circuit results through named templates and deterministic metadata.
- Honest unsupported handling: unsupported or ambiguous requests block polished lessons and numerical answers instead of guessing.

Each capability is paired with a boundary. Internal verification means circuit-law consistency inside the supported solver scope, not universal simulation correctness, independent reference checking, or biomedical device verification.

## MVP Scope

The MVP intentionally supports a narrow set of circuits: linear DC operating point, first-order RC transient templates, AC steady-state/sweep analysis for linear R/L/C circuits and independent sources, ideal closed-loop op-amp DC, simplified nonideal op-amp modeling, and Gemini schematic/image-to-Circuit-IR parsing. The nonideal op-amp model covers finite open-loop gain, rail/output-swing clipping, input bias current, output-current limit checks, slew-rate notes, clipping-recovery notes, and single-pole AC frequency response. The image parser can turn visible schematic labels and connectivity into Circuit IR through Gemini, but ambiguous or unreadable images remain ambiguous. The MVP still does not include general transient analysis, DC inductor behavior, diodes, transistors, dependent sources, nonlinear solving, SPICE-grade op-amp macro-models, or guaranteed recognition of unclear images.

On top of that solver scope, the demo includes named BME teaching templates for ECG/EMG front-ends, pressure and strain bridges, thermistor dividers, photodiode transimpedance amplifiers, instrumentation amplifiers, and anti-aliasing filters. These templates are ordinary Circuit IR examples that still pass through the same validation, solving, and internal verification pipeline; their biomedical notes are educational guardrails, not device-level design verification.

This narrow scope is a feature, not a defect. It makes the verification story clear and inspectable for a professor demo.

## Evaluation Plan

The initial benchmark should include 20 problems split across simple dividers, nodal-analysis circuits, Thevenin/Norton-style circuits, and future unsupported bridge/dependent-source examples. Metrics include parse correctness, numerical correctness, unit correctness, sign-convention correctness, explanation consistency, and honest uncertainty when unsupported.

## Why This Is More Than Prompt Engineering

Prompt engineering tries to elicit better answers from a language model. VeriCircuit Tutor changes the authority structure. The final numerical answer comes from a formal circuit representation, numerical solving, and circuit-law verification. Language generation is downstream of that verified packet. That separation is what makes the system interesting for trustworthy tutoring: the tutor can be conversational without being the source of numerical truth.
