# VeriCircuit Tutor

VeriCircuit Tutor is a graphical tutor layer for supported undergraduate circuit-analysis topics, BME circuits, signal-conditioning labs, MATLAB/Simscape playground artifacts, and reasoning-coach loops. It is not a general-purpose circuit simulator or a biomedical design-verification tool. The central design rule is simple:

**The LLM is not the numerical authority. CiTT grounds tutoring in explicit models, generated artifacts, hand checks, solver/verifier evidence, and student-visible reasoning steps.**

The LLM or deterministic parser may help translate a problem into a structured circuit representation, and a tutor layer may explain the result, but final numerical answers for supported circuit-answer workflows come only from verified solver output. The MATLAB/Simscape playground path adds generated artifacts, focus maps, probe plans, and Lab Delta comparisons without making students write MATLAB setup code.

The newer coaching path adds a second rule: students should own the next reasoning move. CiTT can now withhold final values, inspect a student's partial frame, and return one local nudge before revealing the verified solution.

CiTT now includes a MATLAB/Simscape-aware popup tutor direction for BME circuits and signal-conditioning labs. It keeps the guided graphical teaching experience while using MATLAB, Simulink, and Simscape as the engineering playground; see [docs/matlab_simscape_playground.md](docs/matlab_simscape_playground.md). The existing API, web UI, and internal solver pipeline remain part of the product: the solver is the hand-check and fallback verifier, while MATLAB/Simscape is the main lab playground.

## Why This Exists

Ordinary LLM tutors can produce fluent circuit explanations while making small but consequential mistakes in signs, units, node labels, or current directions. Those mistakes are hard for a student to detect because the prose still sounds confident.

VeriCircuit Tutor demonstrates a safer architecture:

```text
natural language -> Circuit IR -> validation -> MNA solver -> verification -> Solution Packet -> explanation
```

The explanation layer is deliberately constrained. It cites values from the Solution Packet instead of inventing answers directly.

## Product Capabilities And Scope

CiTT is organized around five product capabilities:

1. **Solver-verified circuit answers**
   - Converts supported prompts into Circuit IR, validates topology and units, solves with deterministic circuit engines, and returns a Solution Packet with requested answers, provenance, and a verification badge.
   - Product value: students and instructors can inspect where numbers came from instead of trusting fluent prose.
   - Boundary: only supported circuit families receive verified answers.

2. **Guided visual lessons**
   - Builds structured lesson packets with objectives, equation steps, diagram focus IDs, visual cues, common mistakes, checks, limitations, and verified value references.
   - Product value: students see what part of the schematic matters at each reasoning step.
   - Boundary: lessons are generated only for solved `PASS` packets.

3. **Reasoning coach before reveal**
   - Uses `/reasoning_coach` to inspect a student's partial frame, classify known or dynamic misconceptions, build a short diagnostic micro-graph, return one nudge, update a portable profile with BKT-style mastery estimates, and withhold final values until Level 5 reveal.
   - Product value: the tutor supports student reasoning instead of immediately acting as an answer machine.
   - Boundary: profiles and instructor dashboard summaries are stateless payloads, not persistent LMS analytics.

4. **Biomedical instrumentation teaching layer**
   - Adds named BME templates and topology-feature context injection for differential front ends and ADC-style RC low-pass stages.
   - Includes safety notes, nonideal reminders, CMRR what-ifs where supported, ADC sampling observations, starter and output-referred noise estimates, supply-rail warnings, and practice variants.
   - Product value: verified circuit results are connected to ECG, EMG, bridge-sensor, thermistor, photodiode, instrumentation-amplifier, and anti-aliasing contexts.
   - Boundary: BME notes are educational guardrails, not biomedical design verification or safety certification.

5. **Honest unsupported handling**
   - Returns `UNSUPPORTED` or `AMBIGUOUS` instead of fabricating answers, and exposes `/scope` so UI, docs, and demos share one boundary statement.
   - Product value: instructors can trust the tool's refusal behavior as much as its solved examples.
   - Boundary: scope transparency does not expand solver coverage by itself.

The supported circuit-analysis surface currently includes:

- Resistors
- Independent voltage sources
- Independent current sources
- Capacitors in DC operating point, treated as open circuits
- Numerical transient analysis for linear R/C/L/source circuits using Backward Euler companion models, with first-order RC time-constant reporting when applicable
- Single-frequency AC phasor analysis for linear R/L/C/source circuits
- AC sweep data for linear R/L/C/source circuits
- Inductors in DC steady state, AC phasor/sweep, and linear transient mode
- Shockley diode DC operating-point analysis with Newton-Raphson nonlinear MNA
- Ideal op-amp closed-loop DC analysis
- Educational nonideal op-amp macromodeling with finite open-loop gain, input offset, input resistance, finite output resistance, compensation capacitance, rail/output-swing clipping, input bias current, output-current limit checks, slew-rate notes, clipping-recovery notes, and AC gain-bandwidth frequency response
- Gemini schematic/image parsing through `/parse_image`, producing Circuit IR from visible labels and connectivity
- Ground node
- Node voltages
- Component voltages, currents, and powers
- Source power with an explicit signed-power convention
- Simple practice variants
- DC resistor-only incremental updates through a Sherman-Morrison rank-1 solver endpoint
- BME noise transfer estimates that inject configured thermal, shot, and 1/f noise sources through complex MNA and integrate output RMS noise
- SPICE-like netlist generation for transparency
- Deterministic SVG circuit diagrams generated through OptCPV from Circuit IR, including component/net metadata for tutor focus and visual inspection
- Answer provenance showing parser, solver, MNA matrix, RHS, and solution vector
- A `/reasoning_coach` loop that supports student commitment, local checks, hint ladder levels, dynamic diagnostic graphs, misconception tags, representation modes, adaptive practice, BKT-style profile updates, reflection journal entries, and Level 5 verified reveal
- An `/instructor_dashboard` summary endpoint for class-level misconception maps from submitted student profiles

Unsupported in this first version:

- Arbitrary waveform transient sources
- Nonlinear transient
- Transistors, arbitrary semiconductor models, diode AC/transient large-signal analysis, and arbitrary dependent-source behavior
- SPICE-grade vendor op-amp macro-model simulation
- Guaranteed recognition of unreadable, cropped, or ambiguous schematic images

Unsupported or ambiguous requests are reported honestly rather than forced through the solver.

## Current BME Boundaries

The BME tutor layer adds biomedical context, practice variants, safety notes, nonideal reminders, and differential/common-mode teaching observations on top of internally verified circuit results. Internal verification here means circuit-law consistency inside the supported solver scope; it is not biomedical design verification. These notes are educational guardrails, not safety certification or full nonideal simulation.

- Safety notes can remind students about isolation, leakage-current limits, patient-connected design, optical exposure, and ADC anti-aliasing, but the current implementation does not calculate leakage current, isolation-barrier ratings, IEC-style constraints, or device compliance.
- CMRR support currently explains differential input, common-mode input, their ratio, and a deterministic 1% resistor-ratio mismatch what-if for named ECG/instrumentation templates. It does not yet solve arbitrary resistor tolerance networks, finite-op-amp CMRR degradation, or frequency-dependent CMRR.
- ADC anti-aliasing support currently reports template or dynamically inferred sampling frequency, Nyquist frequency, target cutoff, first-order attenuation at Nyquist, ideal quantization step/noise, and an input-loading warning marker. It does not yet compute alias energy, aperture effects, switched-capacitor acquisition dynamics, ADC datasheet noise, or higher-order filter behavior.
- Noise budget support gives starter educational estimates and, when BME metadata provides noise sources, injects equivalent current-noise sources through the complex MNA network to integrate output-referred RMS noise over the configured bandwidth. Configured 1/f corner terms are included as teaching estimates. This still does not replace datasheet-level or IC-design noise verification.
- BME meaning is attached by deterministic templates or limited topology-feature injection for differential front ends and ADC-style RC low-pass stages. Gemini mode may parse explicit circuit connectivity into general Circuit IR, but safe biomedical interpretation still comes from validated metadata rather than guessed physiology.
- Supply-rail notes are tutor warnings from template metadata fields such as `supply_positive_v`, `supply_negative_v`, and `output_swing_margin_v`. For `nonideal_op_amp` components, the solver uses configured rails and output swing margin to clamp saturated DC output, checks output-current limits, stamps input bias current, input offset, input resistance, finite output resistance, and optional compensation capacitance, and uses gain-bandwidth or open-loop bandwidth for AC frequency response. Slew rate and clipping recovery are exposed as educational dynamic-limit observations, not full waveform simulation.

## Architecture

1. **Parser service**
   - `demo_parser.py` recognizes bundled examples without external API keys.
   - `gemini_parser.py` calls Gemini when `GEMINI_API_KEY` or `GOOGLE_API_KEY` is present. If Gemini is unavailable or cannot produce validated Circuit IR, parsing returns controlled ambiguity instead of using bundled parser fallback.

2. **Circuit IR**
   - Pydantic models define the supported circuit graph, components, goals, assumptions, ambiguities, and unsupported features.
   - `/scope` exposes the current product boundary as a typed API object so the UI, docs, and demos can share the same supported/unsupported and BME-boundary language.

3. **Validator**
   - Checks ground, unique component IDs, finite values, positive resistors/capacitors, normalized SI units, valid goal targets, analysis-specific AC settings, ideal op-amp node shape, and ground-connected graph structure.

4. **Solvers**
   - Uses Modified Nodal Analysis with NumPy.
   - Unknowns are non-ground node voltages plus currents through independent voltage sources.
   - Current sources inject current according to their node order.
   - Voltage source currents are solved as MNA unknowns.
   - AC analysis uses a complex MNA solver for phasor values.
   - Ideal op-amps add an output-current unknown and enforce `V(+) = V(-)`.
   - DC diode circuits use Newton-Raphson nonlinear MNA with a Shockley-device Jacobian.
   - Nonideal op-amps can stamp educational macromodel terms such as input offset, input resistance, output resistance, and compensation capacitance.
   - BME noise observations can inject equivalent noise sources through complex MNA and integrate output RMS noise.

5. **Verifier**
   - Recomputes KCL residuals from solved component currents.
   - Checks signed power balance for DC.
   - Checks complex KCL, finite phasor values, and signed complex-power balance for AC.
   - Confirms every requested goal has a value.
   - Emits a verification badge: `PASS`, `FAIL`, `AMBIGUOUS`, or `UNSUPPORTED`.

6. **Explainer**
   - Template-based in the current implementation.
   - Explains only values present in the Solution Packet.

7. **Lesson builder**
   - `guided_steps.py` builds deterministic step focus for the diagram.
   - `lesson_builder.py` wraps those steps into a structured `LessonPacket` with objectives, conceptual overview, equation steps, visual cues, common mistakes, checks, practice prompts, verified value references, and limitations.
   - `LessonPacket` is generated only for solved packets with a `PASS` verification badge.
   - User-visible lesson numbers are formatted from `SolutionPacket` fields or deterministic `TutorObservation` values, not from Gemini prose.

8. **Reasoning coach**
   - `/reasoning_coach` runs parse and solve internally, but does not expose final values unless reveal is explicitly allowed at Level 5 after a student commitment.
   - It extracts a lightweight `StudentFrame`, detects built-in or dynamic misconception tags, returns a short diagnostic graph, returns one `CoachNudge`, supports diagram/KCL/physical/unit/biomedical representation modes, generates adaptive practice prompts, and updates a portable `StudentProfile` with BKT-style `knowledge_state`.
   - In `gemini` or `gemini_strict` mode, Gemini may also classify the student's partial reasoning into a `StudentFrame`. If that call fails, the coach falls back to deterministic heuristics and records a warning.
   - `/instructor_dashboard` aggregates submitted student profiles into class-level misconception percentages and suggested interventions. It is a stateless endpoint, not persistent analytics storage.
   - Student-frame extraction is never allowed to compute or reveal numerical answers; numerical authority remains solver/verifier-grounded.

9. **Visual layer**
   - `visual_layout.py` builds a lightweight `VisualCircuit` semantic layout with nodes, components, wires, annotations, overlays, and focus regions for interaction.
   - `/visual_layout` exposes that semantic layout for lesson overlays and future renderer improvements.
   - `/schematic` is backed by `optcpv_bridge.py`, converts Circuit IR into OptCPV native IR, and returns OptCPV SVG with `data-component-id`, net, pin, renderer, and circuit metadata.

10. **OptCPV schematic integration**
   - CiTT no longer ships its own SVG schematic renderer or fallback HTML renderer.
   - OptCPV is the drawing source of truth for `/schematic`; unsupported OptCPV failures are returned as explicit API errors instead of silently falling back to CiTT drawings.
   - The CiTT -> OptCPV adapter canonicalizes known motif naming quirks, including two-electrode voltage clamp nets (`Vc`, `Vm`, `Vo`, `0`) so OptCPV motif routes are used instead of generic routes.

## Gemini Boundary

Gemini mode is optional. The backend reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`; keys are never sent to the frontend. `GEMINI_MODEL` defaults to `gemini-flash-latest` and can be overridden per server environment.

`gemini_client.py` owns Google GenAI client creation and structured JSON calls. `gemini_parser.py` owns the Circuit IR schema and prompt. Gemini may parse natural language into Circuit IR, but final node voltages, currents, powers, phasors, transient values, requested answers, explanations, and lesson numbers come from deterministic solver/verifier outputs.

The reasoning coach can also use Gemini to classify a student's freeform partial attempt into `StudentFrame` fields such as suspected method, confusion, confidence, likely misconception, and a short causal diagnostic graph. That prompt explicitly forbids solving or revealing final values, and the deterministic coach falls back if Gemini is unavailable.

## Running Tests And Evaluation

From `vericircuit-tutor/backend`:

```bash
python -m pytest
python scripts/run_evaluation.py
```

The evaluation script uses offline benchmark fixtures by default and does not require Gemini credentials or network access.

## Sign Convention

VeriCircuit uses one sign convention everywhere in the solver, verifier, Solution Packet, and tutor explanation. This is important because the tutor never silently flips directions to make an answer look friendlier.

For every two-terminal component:

- Voltage is `V(nodes[0]) - V(nodes[1])`.
- Current is positive from `nodes[0]` to `nodes[1]`.
- Signed power is `voltage * current`.

For resistors, positive signed power is absorbed under the passive sign convention. For independent sources, negative signed power means the source supplies power to the circuit. The verifier checks power balance by summing all signed component powers and requiring that sum to be approximately zero.

Voltage-source currents are MNA unknowns. Their positive direction is also from `nodes[0]` to `nodes[1]`, so source power uses the same signed-power rule as every other component.

For ideal op-amps, the Circuit IR node order is `[non_inverting, inverting, output, reference]`. The reported op-amp branch voltage is `V(output) - V(reference)`, and output current is positive from output to reference.

## Verification Badge

Every Solution Packet includes:

```json
{
  "verification_badge": {
    "label": "PASS",
    "message": "Solver output passed validation, KCL, power-balance, unit, and requested-answer checks."
  }
}
```

Badge meanings:

- `PASS`: validation, solving, and verification passed.
- `FAIL`: validation, solving, or verification failed.
- `AMBIGUOUS`: the parser found unresolved ambiguity and did not solve.
- `UNSUPPORTED`: the request contains features outside the supported CiTT scope.

## Run The Backend

From the backend directory:

```powershell
cd vericircuit-tutor\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m pip install -e ..\..\..\..\OptCPV
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

On macOS/Linux, install the local OptCPV checkout similarly:

```bash
cd vericircuit-tutor/backend
python -m venv .venv
./.venv/bin/python -m pip install -e '.[dev]'
./.venv/bin/python -m pip install -e /Users/Raalm/Documents/OptCPV
./.venv/bin/python -m uvicorn app.main:app --reload
```

If OptCPV lives somewhere else, set `OPTCPV_PATH` or `OPTCPV_HOME` to its project root before starting the backend.

Open:

```text
http://127.0.0.1:8000
```

## Optional Gemini Parser Setup

Gemini mode uses the official Google GenAI SDK on the backend only. It may produce CircuitProblem JSON, but it never produces final numerical answers.

Copy `.env.example` as a reference and see [docs/api_setup.md](docs/api_setup.md) for Windows PowerShell and macOS/Linux setup.

## Run Tests

```powershell
cd vericircuit-tutor\backend
.\.venv\Scripts\python.exe -m pytest
```

## Demo Examples

The deterministic parser recognizes:

- Voltage divider: 10 V source with R1 = 2 kOhm and R2 = 3 kOhm
- Current source with parallel resistors: 3 mA into 2 kOhm and 1 kOhm to ground
- Bridge-like resistor network: 5 resistors and one DC voltage source
- Second bridge-like resistor network: different 5-resistor values and one DC voltage source
- RC low-pass AC steady-state example
- Numerical RC transient charging example
- Shockley diode DC limiter example
- Ideal non-inverting op-amp DC example
- BME templates:
  - ECG front-end differential amplifier
  - EMG RC band-pass chain
  - Pressure sensor divider and bridge
  - Strain gauge Wheatstone bridge
  - Thermistor divider
  - Photodiode transimpedance amplifier
  - Instrumentation amplifier
  - Anti-aliasing RC low-pass

The same examples are stored as Circuit IR JSON under:

```text
backend/app/examples/
```

## API Endpoints

- `GET /health`
- `GET /scope`
- `GET /examples`
- `POST /parse`
- `POST /parse_image`
- `POST /solve`
- `POST /explain`
- `POST /variant`
- `POST /reasoning_coach`
- `POST /instructor_dashboard`
- `POST /incremental_resistor_update`
- `GET /matlab_playground/manifest`
- `GET /matlab_playground/labs`
- `GET /matlab_playground/labs/{lab_id}`
- `POST /matlab_playground/labs/{lab_id}/artifacts`
- `GET /matlab_playground/labs/{lab_id}/focus_map`
- `GET /matlab_playground/labs/{lab_id}/probe_plans`
- `POST /matlab_playground/labs/{lab_id}/lab_delta`
- `GET /matlab_plugin/manifest`
- `GET /matlab_plugin/labs`
- `POST /matlab_plugin/labs/{lab_id}/artifact`
- `GET /matlab_plugin/labs/{lab_id}/plan`
- `GET /matlab_plugin/labs/{lab_id}/adapter_plan`
- `POST /matlab_plugin/labs/{lab_id}/offline_bundle`
- `GET /matlab_plugin/labs/{lab_id}/focus_map`
- `GET /matlab_plugin/labs/{lab_id}/probe_plan`
- `POST /matlab_plugin/labs/{lab_id}/lab_delta`
- `POST /matlab_plugin/labs/{lab_id}/lab_delta/parse_upload`
- `POST /full_pipeline`
- `POST /full_pipeline_image`

The preferred `/matlab_playground` endpoints expose generated MATLAB/Simulink/Simscape artifacts, included lab definitions, focus maps, probe plans, and Lab Delta comparisons for the graphical popup tutor. The older `/matlab_plugin` endpoints remain as compatibility aliases for previous generated bundles and tests. See [docs/matlab_simscape_playground.md](docs/matlab_simscape_playground.md).

`/full_pipeline` accepts:

```json
{
  "problem_text": "A 10 V voltage source is connected in series with R1 = 2 kOhm and R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit.",
  "mode": "gemini"
}
```

and returns Circuit IR, Solution Packet, explanation, variants, parser used, and warnings.

`/full_pipeline_image` accepts the same image payload as `/parse_image`:

```json
{
  "problem_text": "Find Vout from this uploaded schematic.",
  "mime_type": "image/png",
  "image_base64": "..."
}
```

It returns the same full pipeline response after parsing the image into Circuit IR.

`/reasoning_coach` accepts the same problem text plus a student commitment:

```json
{
  "problem_text": "A 10 V voltage source is connected in series with R1 = 2 kOhm and R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit.",
  "mode": "gemini",
  "requested_hint_level": 1,
  "representation_mode": "physical_intuition",
  "student_commitment": {
    "attempt_text": "I think it is a divider, but I am unsure about current direction.",
    "confidence_percent": 45
  }
}
```

It returns a local check, one nudge, next choices, adaptive practice, diagnostic graph, profile update, and reflection. `solution_packet` stays `null` until Level 5 reveal is requested after a student-owned attempt. See [docs/reasoning_coach.md](docs/reasoning_coach.md).

## Future Work

- ngspice integration for cross-checking
- Full WYSIWYG schematic editing
- Interactive correction flow for ambiguous schematic/image parses
- Extend CMRR mismatch analysis beyond named templates, dynamic front-end detection, and single-ratio what-ifs
- Expand ADC/sampling support with higher-order filters and alias-energy estimates
- SPICE-grade or vendor macro-model op-amp simulation
- Expand noise budget support toward device-library, datasheet, and IC-design-grade models
- BME lab-style report export
- Dependent sources
- Arbitrary waveform and nonlinear transient simulation
- Persistent AC/frequency-sweep factorization for slider-speed interaction beyond DC resistor updates
- Persistent student-model storage beyond stateless profile payloads
- Benchmarking against general LLM answers
