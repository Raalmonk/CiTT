# Executive Summary Variants

These alternatives are shorter than the full application answer and can be used if the portal text box or reviewer format favors a different tone.

## Variant A: Technical

CiTT is a MATLAB-native, Simscape-grounded AI tutor for biomedical circuit and instrumentation learning. It addresses a core problem in engineering education: students increasingly use large language models for help, but text-only tutoring can hide incorrect units, signs, assumptions, or transient behavior. CiTT keeps language useful while moving engineering authority into executable artifacts.

The workflow accepts a prompt or circuit image, creates a structured circuit specification, builds or opens a Simulink/Simscape model, and teaches from model-linked focus maps, highlights, probes, plots, and evidence exports. The current prototype uses an agent-assisted circuit interpretation path, agentic Simulink/Simscape model generation, Socratic tutoring, natural-language probes, and release-ready evidence packaging.

The release candidate demonstrates three live benchmarks: an RC anti-aliasing filter, a two-electrode voltage clamp equivalent circuit, and a mixed-signal neural clamp using educational scaled parameters. The evidence includes model screenshots, Bode plots, simulation metrics, ADC/digital behavior, focus/probe maps, and limitation reporting. CiTT is educational software, not patient-facing or diagnostic software.

## Variant B: Reviewer-Friendly

Biomedical engineering students need circuits, signals, sensors, ADCs, feedback, and instrumentation, but these topics are difficult to learn from text alone. AI chatbots can help explain ideas, yet they can also give fluent answers without executable proof. CiTT was built to make AI tutoring inspectable.

CiTT is a MATLAB toolbox that turns circuit prompts or images into structured specifications, Simulink/Simscape models, guided teaching, natural-language probes, and evidence exports. Instead of asking students to trust a chatbot, CiTT lets them inspect the model, view highlights, ask measurements, and see assumptions and limitations.

The prototype has live evidence for three benchmark tasks: RC anti-aliasing, voltage-clamp equilibrium, and a mixed-signal neural clamp with educational scaled parameters. Its intended users are BME/EE students, instructors, and lab courses that already use MATLAB/Simulink. The product is scoped as educational software and does not make patient-care claims.

## Variant C: Short

CiTT is a MATLAB-native AI tutor that grounds biomedical circuit learning in executable Simulink/Simscape evidence. It was developed by a single undergraduate student to address a gap in AI-assisted education: text-only LLM tutoring can explain circuits fluently while hiding unit errors, unsupported assumptions, or missing simulations.

CiTT accepts circuit prompts or images, creates structured specifications, builds or opens Simscape models, teaches through focus/highlight maps, answers natural-language probes, and exports reviewable evidence. Live benchmarks cover RC anti-aliasing, voltage-clamp equilibrium, and a mixed-signal neural clamp using educational scaled parameters. The system targets BME/EE courses and instructors. It is educational software, not patient-facing or diagnostic software.
