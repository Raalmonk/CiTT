# BMES Application Answers

This document is written in the order of the requested BMES application fields. It is optimized for first-round scoring: product need and market, novelty, technical feasibility, economic plan, and writing clarity.

## Executive Summary

CiTT, also known as VeriCircuit Tutor, is a MATLAB-native AI tutor for biomedical circuit education. Its core idea is simple: the language model helps students communicate with the system, but it is not the source of numerical truth. A student prompt or circuit image is converted into a structured circuit specification, handed to a SATK/MCP-enabled model-building workflow, and grounded in generated Simulink/Simscape artifacts. The tutor then teaches from visible models, focus-map highlights, natural-language probes, plots, simulation metrics, and exported evidence.

The product need is clear: biomedical engineering students increasingly use AI tools while learning ECG front ends, anti-aliasing filters, electrode interfaces, sensor bridges, and mixed-signal biomedical instrumentation. General-purpose chatbots can produce fluent explanations while hiding unit mistakes, sign errors, unsupported assumptions, or missing nonideal behavior. CiTT addresses that risk by making assumptions, generated models, measurements, and limitations visible.

The current release candidate demonstrates three live GUI benchmarks: an RC anti-aliasing filter, a two-electrode voltage clamp equivalent circuit, and a mixed-signal neural clamp benchmark. The goal is educational feasibility, not clinical validation or medical-device certification.

## Problem

Biomedical instrumentation courses ask students to connect circuit theory to physiological measurement systems. That bridge is hard: students must reason about units, node references, sign conventions, filters, amplifiers, sampling, electrode interfaces, saturation, and nonideal behavior while also learning domain context.

LLM tutors can make this worse when they answer confidently without executable evidence. A small error in capacitance units, current direction, cutoff frequency, node labeling, or saturation behavior can produce a polished but wrong explanation. Students may not have enough experience to detect the mistake, and instructors cannot easily audit how the answer was produced.

The problem is not that language models are useless. The problem is authority. In engineering education, final claims should be tied to explicit assumptions, inspectable models, and verifiable computations. CiTT is designed around that separation.

## Objective

CiTT's objective is to give biomedical engineering students an AI-assisted tutor that remains grounded in model evidence. The product should:

- accept a circuit prompt or image,
- produce a structured circuit/model specification,
- build an inspectable MATLAB/Simulink/Simscape model through a SATK/MCP-enabled agent flow,
- create focus and probe maps that connect teaching steps to model elements,
- let students ask natural-language measurement questions,
- export evidence that reviewers and instructors can inspect,
- report ambiguity and limitations honestly instead of fabricating unsupported results.

The near-term objective is a release candidate suitable for BMES review and classroom-style demonstration. The longer-term objective is an instructor-facing educational tool for biomedical instrumentation labs where students learn from executable models rather than ungrounded prose.

## Final Design Documentation

The release demo surface is the MATLAB plugin:

```matlab
addpath("vericircuit-tutor/matlab")
citt
```

Design components:

- MATLAB plugin UI: the main learning surface. Students enter prompts/images, trigger parse/build steps, inspect teaching output, ask probes, and export evidence.
- Gemini parsing layer: converts natural language or schematic images into structured circuit/model specifications. Gemini is not treated as numerical authority.
- SATK/MCP model-building flow: hands the structured spec to an agent that uses MATLAB/Simulink model tools to construct a Simulink/Simscape model.
- Simulink/Simscape artifact layer: stores generated `.slx` models, focus maps, probe maps, agent reports, simulation outputs, and plots.
- Teaching layer: converts model/focus/probe artifacts into guided explanation and highlight actions.
- Probe layer: maps natural-language measurement requests to known probe targets.
- Evidence export: produces reviewable evidence packs linking inputs, assumptions, generated artifacts, model checks, screenshots, plots, limitations, and risk controls.

Release documentation:

- [Release setup](release_setup.md)
- [Live GUI evidence demo](demo_live_gui_evidence.md)
- [MATLAB plugin details](../matlab/README.md)
- [Final live evidence package](../submission_assets/live_gui_evidence/)

Design risk controls:

- API keys and `.env` files are excluded from release commits.
- Local work cache stays in `matlab/work/` and is ignored by Git.
- MATLAB/Simulink caches such as `slprj/` and `*.slxc` are ignored.
- Offline draft evidence is labeled as non-final.
- Benchmark limitations are recorded next to the evidence instead of hidden.
- The product is explicitly scoped as educational software, not clinical decision support or medical-device verification.

## Functional Proof

Functional proof is stored under:

```text
vericircuit-tutor/submission_assets/live_gui_evidence/
```

Benchmark 1 demonstrates an RC anti-aliasing filter for an ECG-style signal before an ADC. Evidence includes the parsed problem, generated/opened Simscape model, teaching UI, model highlight, natural-language probe, and Bode plots. Recorded values include `R = 39.8 kOhm`, `C = 100 nF`, `fc = 39.9887 Hz`, `60 Hz attenuation = -5.1205 dB`, and `250 Hz attenuation = -16.0298 dB`. The evidence also shows the impact of a 100 uF unit mistake.

Benchmark 2 demonstrates a two-electrode voltage clamp equivalent circuit. CiTT generated a Simscape-first physical model with command source, buffer path, finite-gain amplifier, membrane branch, probes, electrical reference, solver configuration, focus map, and probe map. The benchmark honestly preserves symbolic `V_c` and `R_e` because numeric values were not supplied.

Benchmark 3 demonstrates a closed-loop mixed-signal neural clamp with educational scaled parameters. The live evidence includes generated model screenshots, command/ADC/feedback highlights, teaching/probe evidence, simulation plots, metrics JSON, and exported evidence pack. The model did not settle in the 60 ms window and showed saturation/current-limit behavior. This is framed as limitation-discovery evidence: CiTT exposed behavior a text-only answer could easily miss.

Key proof files:

- `submission_assets/live_gui_evidence/bmes_live_evidence_report.md`
- `submission_assets/live_gui_evidence/benchmark_01_textbook_rc/`
- `submission_assets/live_gui_evidence/benchmark_02_tevc_equilibrium/`
- `submission_assets/live_gui_evidence/benchmark_03_mixed_signal/`

Gemini-only no-tools baselines are archived beside each benchmark. They show a balanced comparison: Gemini-only performs well on the textbook RC calculation, gives a plausible but slightly inconsistent symbolic TEVC explanation, and correctly admits that the mixed-signal benchmark requires executable simulation while still making unit/model-assumption mistakes. CiTT's added value is not that LLM reasoning is useless; it is that CiTT turns reasoning into inspectable model evidence: Simulink/Simscape artifacts, focus/probe maps, GUI screenshots, plots, metrics JSON, and exported evidence packs.

## Prior Art

Current alternatives each solve part of the problem but leave an educational gap:

- General AI chatbots can explain circuits conversationally, but their outputs can contain hallucinated facts, incorrect reasoning, and fabricated confidence. In circuit education, subtle errors in sign, units, or assumptions can materially change the answer.
- The archived Gemini-only no-tools baseline demonstrates the boundary directly: it can do hand calculations and qualitative reasoning, but it cannot generate or inspect Simscape models, verify GUI highlights, produce ADC code traces, or compute mixed-signal saturation/settling metrics without tools.
- Traditional circuit simulators and MATLAB/Simulink/Simscape provide powerful modeling and simulation, but they do not automatically turn a student's prompt into a model-linked tutoring loop with focus maps, probes, and submission-ready evidence.
- Existing intelligent tutoring systems can guide learners, but they usually do not create inspectable Simulink/Simscape biomedical circuit artifacts as part of the lesson.
- SATK/MCP tooling enables agentic interaction with Simulink. CiTT builds on that infrastructure and contributes the domain-specific educational workflow: biomedical circuit prompts, structured specs, model-linked teaching, natural-language probes, and evidence export.

CiTT's novelty is the authority structure. The language model is helpful, but the reviewable artifacts are the product: generated models, explicit assumptions, focus/probe maps, model checks, plots, metrics, and limitations.

## Regulatory Pathway

The current CiTT release candidate should be positioned as educational software for engineering instruction. It is not intended to diagnose, treat, mitigate, prevent, or cure disease. It does not connect to patients, acquire live physiological signals, control therapy, produce patient-specific recommendations, certify medical-device designs, or replace IEC/FDA design verification.

For the current intended use, the submission should not claim a 510(k), De Novo, PMA, or Software as a Medical Device pathway. The correct pathway is non-clinical educational software with clear labeling and scope controls.

If a future version were marketed for clinical decision support, regulated device development, patient-specific design decisions, or automated verification of medical-device safety, the intended use would need to be reassessed. That future pathway could require regulatory counsel, quality-system controls, risk management, cybersecurity review, software validation, and possibly FDA premarket interaction depending on claims and risk class.

## Manufacturing Cost

CiTT is a software-first educational product, so there is no custom hardware bill of materials, inventory, sterilization, or physical manufacturing line.

Expected cost structure:

| Cost item | Release-candidate status |
| --- | --- |
| Custom hardware BOM | `$0`; no custom hardware required |
| Manufacturing tooling | `$0`; software distribution only |
| Distribution | Git/zip/release archive |
| Required platform | MATLAB, Simulink, Simscape, SATK/MCP, and agent CLI supplied by the lab/institution/user |
| Variable runtime cost | Gemini/API and agent-compute usage, depending on provider and run volume |
| Main development cost | Software engineering, model templates, validation, documentation, classroom support |
| Main commercialization cost | QA, onboarding, instructor materials, support, enterprise/security review, optional LMS integration |

Economic plan:

- Beachhead: biomedical instrumentation and circuits labs that already use MATLAB/Simulink.
- Early deployment: course or lab license bundled with setup support and curated benchmark packs.
- Scaling path: instructor dashboard, reusable lab templates, assessment exports, and controlled institutional deployment.
- Cost advantage: CiTT leverages existing academic MATLAB/Simulink infrastructure rather than requiring new lab hardware.

## Market And Impact

Initial users are biomedical engineering instructors, teaching assistants, and students in circuits, biomedical instrumentation, neural engineering, sensor-interface, and systems-modeling labs.

Market need:

- Biomedical engineering programs must teach students to connect math, circuits, experimentation, and engineering judgment.
- AIMBE's Academic Council lists 100 U.S. universities offering medical and biological engineering education at undergraduate and graduate levels.
- The U.S. Bureau of Labor Statistics projects bioengineer and biomedical engineer employment growth from 2024 to 2034, supporting continued demand for technically prepared graduates.
- Many institutions already use MATLAB/Simulink in engineering education, making a MATLAB-native tutor a realistic adoption path.

Impact:

- Students get explanations tied to visible models and probes instead of black-box answers.
- Instructors get evidence artifacts they can inspect, grade, or use for lab discussion.
- The product encourages honest uncertainty and limitations reporting.
- The mixed-signal benchmark shows a valuable teaching moment: a generated model can fail to settle and reveal saturation/current-limit behavior, which is more educational than a polished but unsupported chatbot explanation.

Success metrics for future pilots:

- Reduced unit/sign/node-reference errors on biomedical circuit assignments.
- Faster student transition from prompt to inspectable Simscape model.
- Instructor-rated usefulness of focus/probe evidence.
- Student ability to explain limitations, assumptions, and nonideal behavior.
- Number of assignments where CiTT refuses or marks ambiguity instead of giving unsupported answers.

## References

- Google AI for Developers, [Using Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key).
- MathWorks, [Simulink Agentic Toolkit](https://www.mathworks.com/products/simulink-agentic-toolkit.html).
- MathWorks, [MATLAB MCP Server](https://www.mathworks.com/products/matlab-mcp-server.html).
- MathWorks, [Simscape documentation](https://www.mathworks.com/help/simscape/index.html).
- MathWorks, [Simscape Electrical documentation](https://www.mathworks.com/help/sps/index.html).
- FDA, [Device Software Functions Including Mobile Medical Applications](https://www.fda.gov/medical-devices/digital-health-center-excellence/device-software-functions-including-mobile-medical-applications).
- FDA, [Clinical Decision Support Software Guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software).
- FDA, [General Wellness: Policy for Low Risk Devices](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/general-wellness-policy-low-risk-devices).
- AIMBE, [Academic Council information](https://aimbe.org/).
- U.S. Bureau of Labor Statistics, [Bioengineers and Biomedical Engineers Occupational Outlook](https://www.bls.gov/ooh/architecture-and-engineering/biomedical-engineers.htm).
- ABET, [Criteria for Accrediting Engineering Programs, 2025-2026](https://www.abet.org/accreditation/accreditation-criteria/criteria-for-accrediting-engineering-programs-2025-2026/).
- Educational Data Mining 2025, [When LLMs Hallucinate: Examining the Effects of Erroneous Feedback in Math Tutoring Systems](https://educationaldatamining.org/EDM2025/proceedings/2025.EDM.doctoral-consortium-papers.254/index.html).
- PMC, [Survey and analysis of hallucinations in large language models](https://pmc.ncbi.nlm.nih.gov/articles/PMC12518350/).
