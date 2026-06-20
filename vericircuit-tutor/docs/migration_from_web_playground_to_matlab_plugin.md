# Migration From Web Playground To MATLAB Plugin

CiTT is not replacing the existing web MVP, API, or solver pipeline. The migration is an additive path from a web-first internal solver playground toward a MATLAB-native popup tutor for BME circuits and signal-conditioning labs.

## Old Center Of Gravity

```text
Prompt / image
    -> Circuit IR
    -> validation
    -> internal solver/checker
    -> verification
    -> SolutionPacket
    -> lesson / coach / explanation
```

This remains useful for hand checks, fallback verification, scoped examples, reasoning coach flows, and advanced provenance.

## New Additive Path

```text
Prompt / lab selection / Circuit IR
    -> Learning Lab IR or Plugin Manifest
    -> MATLAB artifact generator
    -> MATLAB script / Simulink build plan / focus map / probe plan / lab delta plan
    -> offline bundle files or optional API response
    -> future MATLAB popup plugin
```

The generated artifacts are the first contract. The MATLAB popup should load bundled files by default; the API is optional for development, web preview, and refresh. MATLAB execution comes later through optional adapters.

## Preservation Rules

- Keep the existing API layer.
- Keep the web MVP.
- Keep the internal solver pipeline.
- Keep guided steps, lesson packet, reasoning coach, BME context, scope boundary, probe/KCL ideas, variants, current-path/highlight concepts, and answer provenance.
- Reframe solver provenance as advanced transparency and hand-check evidence.
- Do not require MATLAB in Python CI.
- Do not require a local FastAPI server for the MATLAB plugin's default student path.

## Product Framing

Use:

> CiTT is evolving into a MATLAB-native popup tutor for BME circuits and signal-conditioning labs. It keeps the graphical teaching experience while using MATLAB/Simulink artifacts as the learning playground. The LLM is not the numerical authority; tutoring is grounded in explicit models, hand checks, generated artifacts, simulation evidence, and student-visible reasoning steps.

Avoid:

- CiTT is now just a MATLAB code generator.
- Students must write MATLAB code.
- The old API is obsolete.
- The internal solver should be deleted.
- The web MVP should be removed.

## Migration Milestones

1. Add typed MATLAB plugin models.
2. Add deterministic lab artifact generation.
3. Add API endpoints for manifest, labs, artifacts, focus maps, probe plans, and Lab Delta.
4. Add tests that inspect generated JSON and text without MATLAB.
5. Add a web preview section when it is cheap and low-risk.
6. Add a four-tab lab plan endpoint that a MATLAB App Designer popup can consume.
7. Add a dry-run MATLAB agent adapter plan with explicit runtime hooks and refusal rules.
8. Add an offline bundle contract for future `.mltbx` package contents.
9. Add optional local MATLAB execution and Simulink highlight adapters.
10. Package a `.mltbx` toolbox once the popup workflow is stable.

Milestones 1 through 8 are API-contract work and can be tested without MATLAB. Milestones 9 and 10 are runtime adapter work and must report execution evidence before the product claims they ran.

## First Vertical Slice

`rc_antialias_adc` bridges the current BME anti-aliasing teaching work to MATLAB/Simulink artifacts:

- Overview: sampling rate, cutoff target, R, C, assumptions, safety boundary.
- Teach: cutoff calculation, Nyquist context, model focus targets.
- Probe: RC output voltage, input/output logs, 60 Hz comparison, sampled output.
- Lab Delta: hand/simulation/measured comparisons and likely causes.

## Next Slices

- Instrumentation amplifier intro.
- ECG front end.
- EMG band-pass.
- Photodiode TIA.
- Thermistor divider.

Each slice should reuse the four-tab API contract instead of inventing a separate one-off script flow.

## MATLAB Agent Boundary

The current adapter contract tells a future MATLAB agent what to do without letting it overclaim:

- It may fetch manifests, lab plans, artifacts, focus maps, probe plans, and Lab Delta comparisons.
- It may render Overview, Teach, Probe, and Lab Delta tabs from bundled JSON without a server.
- It may optionally call the API for development or refresh.
- It may show dry-run Simulink build plans and MATLAB script text.
- It must mark `hilite_system`, signal logging insertion, Simscape sensor insertion, simulation execution, and `.mltbx` packaging as future runtime hooks until an adapter reports evidence.
- It must refuse unsupported runtime claims rather than inventing MATLAB results.
