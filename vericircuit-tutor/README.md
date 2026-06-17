# VeriCircuit Tutor

VeriCircuit Tutor is a professor-facing MVP of a simulation-grounded AI tutor for undergraduate circuit analysis. The central design rule is simple:

**The LLM is not the source of truth. The circuit solver and verification engine are the source of truth.**

The LLM or deterministic parser may help translate a problem into a structured circuit representation, and a tutor layer may explain the result, but final numerical answers come only from verified solver output.

The newer coaching path adds a second rule: students should own the next reasoning move. CiTT can now withhold final values, inspect a student's partial frame, and return one local nudge before revealing the verified solution.

## Why This Exists

Ordinary LLM tutors can produce fluent circuit explanations while making small but consequential mistakes in signs, units, node labels, or current directions. Those mistakes are hard for a student to detect because the prose still sounds confident.

VeriCircuit Tutor demonstrates a safer architecture:

```text
natural language -> Circuit IR -> validation -> MNA solver -> verification -> Solution Packet -> explanation
```

The explanation layer is deliberately constrained. It cites values from the Solution Packet instead of inventing answers directly.

## Current Scope

The MVP supports:

- Resistors
- Independent voltage sources
- Independent current sources
- Capacitors in DC operating point, treated as open circuits
- First-order RC transient template
- Single-frequency AC phasor analysis for linear R/L/C/source circuits
- AC sweep data for linear R/L/C/source circuits
- AC inductors in phasor/sweep mode
- Ideal op-amp closed-loop DC analysis
- Ground node
- Node voltages
- Component voltages, currents, and powers
- Source power with an explicit signed-power convention
- Simple practice variants
- SPICE-like netlist generation for transparency
- Deterministic SVG circuit diagrams generated from Circuit IR
- Answer provenance showing parser, solver, MNA matrix, RHS, and solution vector
- A `/reasoning_coach` loop that supports student commitment, local checks, hint ladder levels, misconception tags, representation modes, adaptive practice, reflection journal entries, profile updates, and Level 5 verified reveal
- An `/instructor_dashboard` summary endpoint for class-level misconception maps from submitted student profiles

Unsupported in this first version:

- General transient simulation
- RLC transient
- nonlinear transient
- nonideal op amp behavior
- arbitrary schematic/image recognition

Unsupported or ambiguous requests are reported honestly rather than forced through the solver.

## Current BME Boundaries

The BME tutor layer adds biomedical context, practice variants, safety notes, nonideal reminders, and differential/common-mode teaching observations on top of verified circuit results. These notes are educational guardrails, not safety certification or full nonideal simulation.

- Safety notes can remind students about isolation, leakage-current limits, patient-connected design, optical exposure, and ADC anti-aliasing, but the MVP does not calculate leakage current, isolation-barrier ratings, IEC-style constraints, or device compliance.
- CMRR support currently explains differential input, common-mode input, their ratio, and a deterministic 1% resistor-ratio mismatch what-if for named ECG/instrumentation templates. It does not yet solve arbitrary resistor tolerance networks, finite-op-amp CMRR degradation, or frequency-dependent CMRR.
- ADC anti-aliasing support currently reports template sampling frequency, Nyquist frequency, target cutoff, first-order attenuation at Nyquist, ideal quantization step/noise, and an input-loading warning marker. It does not yet compute alias energy, aperture effects, switched-capacitor acquisition dynamics, ADC datasheet noise, or higher-order filter behavior.
- Noise budget support currently gives starter educational estimates for resistor thermal noise, photodiode shot noise, and op-amp input-referred voltage noise from template metadata. It does not yet propagate noise through arbitrary transfer functions, integrate spectral density over shaped bandwidths, include flicker noise, or replace datasheet-level design work.
- BME meaning is currently attached by deterministic templates. Gemini mode may parse explicit circuit connectivity into general Circuit IR, but safe biomedical interpretation still comes from template matching and validated metadata rather than guessed physiology.
- Supply-rail notes are tutor warnings from template metadata fields such as `supply_positive_v`, `supply_negative_v`, and `output_swing_margin_v`. They identify when an ideal op-amp answer would exceed the template's usable output window, but they do not model saturation dynamics, slew rate, clipping recovery, or output-current limits.

## Architecture

1. **Parser service**
   - `demo_parser.py` recognizes bundled examples without external API keys.
   - `gemini_parser.py` can call Gemini if `GEMINI_API_KEY` or `GOOGLE_API_KEY` is present, then falls back to the demo parser if unavailable.

2. **Circuit IR**
   - Pydantic models define the supported circuit graph, components, goals, assumptions, ambiguities, and unsupported features.

3. **Validator**
   - Checks ground, unique component IDs, finite values, positive resistors/capacitors, normalized SI units, valid goal targets, analysis-specific AC settings, ideal op-amp node shape, and ground-connected graph structure.

4. **Solvers**
   - Uses Modified Nodal Analysis with NumPy.
   - Unknowns are non-ground node voltages plus currents through independent voltage sources.
   - Current sources inject current according to their node order.
   - Voltage source currents are solved as MNA unknowns.
   - AC analysis uses a complex MNA solver for phasor values.
   - Ideal op-amps add an output-current unknown and enforce `V(+) = V(-)`.

5. **Verifier**
   - Recomputes KCL residuals from solved component currents.
   - Checks signed power balance for DC.
   - Checks complex KCL and finite phasor values for AC; AC complex power is not verified in this MVP.
   - Confirms every requested goal has a value.
   - Emits a verification badge: `PASS`, `FAIL`, `AMBIGUOUS`, or `UNSUPPORTED`.

6. **Explainer**
   - Template-based for the MVP.
   - Explains only values present in the Solution Packet.

7. **Lesson builder**
   - `guided_steps.py` builds deterministic step focus for the diagram.
   - `lesson_builder.py` wraps those steps into a structured `LessonPacket` with objectives, conceptual overview, equation steps, visual cues, common mistakes, checks, practice prompts, verified value references, and limitations.
   - `LessonPacket` is generated only for solved packets with a `PASS` verification badge.
   - User-visible lesson numbers are formatted from `SolutionPacket` fields or deterministic `TutorObservation` values, not from Gemini prose.

8. **Reasoning coach**
   - `/reasoning_coach` runs parse and solve internally, but does not expose final values unless reveal is explicitly allowed at Level 5 after a student commitment.
   - It extracts a lightweight `StudentFrame`, detects teachable misconception tags, returns one `CoachNudge`, supports diagram/KCL/physical/unit/biomedical representation modes, generates adaptive practice prompts, and updates a portable `StudentProfile`.
   - In `gemini` or `gemini_strict` mode, Gemini may also classify the student's partial reasoning into a `StudentFrame`. If that call fails, the coach falls back to deterministic heuristics and records a warning.
   - `/instructor_dashboard` aggregates submitted student profiles into class-level misconception percentages and suggested interventions. It is a stateless MVP endpoint, not persistent analytics storage.
   - Student-frame extraction is never allowed to compute or reveal numerical answers; numerical authority remains solver/verifier-grounded.

9. **Visual layer**
   - `visual_layout.py` builds a lightweight `VisualCircuit` semantic layout with nodes, components, wires, annotations, overlays, and focus regions.
   - `/visual_layout` exposes that semantic layout for lesson overlays and future renderer improvements.
   - `render_schematic_svg(circuit)` remains the public SVG path and preserves `data-component-id` and `data-node-id`.

10. **Schematic generator**
   - Creates deterministic SVG diagrams from Circuit IR.
   - Uses named templates for bundled demos and a fallback graph renderer for other supported layouts.

## Gemini Boundary

Gemini mode is optional. The backend reads `GEMINI_API_KEY` or `GOOGLE_API_KEY`; keys are never sent to the frontend. `GEMINI_MODEL` defaults to `gemini-flash-latest` and can be overridden per server environment.

`gemini_client.py` owns Google GenAI client creation and structured JSON calls. `gemini_parser.py` owns the Circuit IR schema and prompt. Gemini may parse natural language into Circuit IR, but final node voltages, currents, powers, phasors, transient values, requested answers, explanations, and lesson numbers come from deterministic solver/verifier outputs.

The reasoning coach can also use Gemini to classify a student's freeform partial attempt into `StudentFrame` fields such as suspected method, confusion, confidence, and likely misconception. That prompt explicitly forbids solving or revealing final values, and the deterministic coach falls back if Gemini is unavailable.

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
- `UNSUPPORTED`: the request contains features outside the MVP scope.

## Run The Backend

From the backend directory:

```powershell
cd vericircuit-tutor\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[dev]'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

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
- First-order RC transient charging example
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
- `GET /examples`
- `POST /parse`
- `POST /solve`
- `POST /explain`
- `POST /variant`
- `POST /reasoning_coach`
- `POST /instructor_dashboard`
- `POST /full_pipeline`

`/full_pipeline` accepts:

```json
{
  "problem_text": "A 10 V voltage source is connected in series with R1 = 2 kOhm and R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit.",
  "mode": "demo"
}
```

and returns Circuit IR, Solution Packet, explanation, variants, parser used, and warnings.

`/reasoning_coach` accepts the same problem text plus a student commitment:

```json
{
  "problem_text": "A 10 V voltage source is connected in series with R1 = 2 kOhm and R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit.",
  "mode": "demo",
  "requested_hint_level": 1,
  "representation_mode": "physical_intuition",
  "student_commitment": {
    "attempt_text": "I think it is a divider, but I am unsure about current direction.",
    "confidence_percent": 45
  }
}
```

It returns a local check, one nudge, next choices, adaptive practice, profile update, and reflection. `solution_packet` stays `null` until Level 5 reveal is requested after a student-owned attempt. See [docs/reasoning_coach.md](docs/reasoning_coach.md).

## Future Work

- ngspice integration for cross-checking
- General schematic rendering beyond named templates
- Interactive schematic editing
- Arbitrary schematic/image recognition
- Extend CMRR mismatch analysis beyond named templates and single-ratio what-ifs
- Expand ADC/sampling support with higher-order filters and alias-energy estimates
- Component-level rail and output-current limits for op-amp sanity checks
- Expand noise budget support with transfer-function propagation, flicker noise, and output-referred totals
- BME lab-style report export
- Dependent sources
- General, RLC, and nonlinear transient simulation
- Persistent student-model storage beyond stateless profile payloads
- Benchmarking against general LLM answers
