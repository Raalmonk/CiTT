# Project Narrative

CiTT is a MATLAB-native, Simscape-grounded AI tutor for biomedical circuit and signal-conditioning education. The project responds to a practical teaching gap: biomedical engineering students need electrical and computer engineering concepts for electrophysiology, biosignal acquisition, instrumentation amplifiers, filtering, ADCs, feedback control, sensing, imaging hardware, and medical-device signal chains, but students increasingly study these topics with general LLM tutors that are not engineering simulators.

The author narrative begins from BME coursework in circuits and instrumentation, including the observation that many curricula, including the author's own BME coursework, require circuit and instrumentation training. A course discussion led by Professor Pak Wong on agent-based teaching motivated the question: can an AI tutor produce precise, visually useful, simulation-grounded engineering outputs rather than only fluent prose?

The project initially explored an internal modified nodal analysis solver. That path worked for simple circuits but was difficult to generalize: model generation was brittle, every new component required additional code and interaction design, and nonlinear biomedical systems would require a full simulator effort. A second phase explored circuit-diagram generation and visualization, but topology understanding and physical correctness remained difficult.

The project then shifted to MATLAB, Simulink, and Simscape. Prior exposure to Simulink in BME coursework suggested that simulation could make the tutor more concrete, but transfer-function diagrams alone can be unintuitive for physical circuits. Simscape offered physical components, libraries, solver infrastructure, and multiphysics modeling. The final direction became a MATLAB plugin controlled by an agentic workflow: Gemini parses circuit prompts/images into structured specs; a SATK/MCP-compatible agent builds Simscape/Simulink models; CiTT teaches from focus maps, highlights model regions, supports natural-language probes, and exports evidence.

CiTT's intended advantages are:

- Strong simulation: executable Simscape/Simulink artifacts rather than text-only explanations.
- Strong teaching: Socratic prompts, measurement/probe workflows, lab-analysis framing, and explicit limitations.
- Strong visualization: model-centered UI, highlight/zoom links, and reviewable screenshots.

The primary comparison is LLM-only tutoring. LLMs can be helpful for simple arithmetic and conceptual explanation, but they do not inherently provide stable executable engineering models or repeatable MATLAB/Simscape evidence. CiTT positions language reasoning as useful but incomplete without model grounding.

Current scope: educational design-assistance software for courses and labs. It is not patient-facing software and does not diagnose, monitor, treat, or control patient care.
