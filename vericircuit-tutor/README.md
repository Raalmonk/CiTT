# VeriCircuit Tutor

VeriCircuit Tutor is a professor-facing MVP of a simulation-grounded AI tutor for undergraduate circuit analysis. The central design rule is simple:

**The LLM is not the source of truth. The circuit solver and verification engine are the source of truth.**

The LLM or deterministic parser may help translate a problem into a structured circuit representation, and a tutor layer may explain the result, but final numerical answers come only from verified solver output.

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
- Single-frequency AC phasor analysis for linear R/C/source circuits
- AC sweep data for linear R/C/source circuits
- Ideal op-amp closed-loop DC analysis
- Ground node
- Node voltages
- Component voltages, currents, and powers
- Source power with an explicit signed-power convention
- Simple practice variants
- SPICE-like netlist generation for transparency
- Deterministic SVG circuit diagrams generated from Circuit IR
- Answer provenance showing parser, solver, MNA matrix, RHS, and solution vector

Unsupported in this first version:

- Inductors
- Diodes
- Transistors
- Dependent sources
- Transient analysis
- Nonlinear solving
- Nonideal op-amp behavior, including rails, saturation, slew rate, input bias current, finite bandwidth, and op-amp frequency response
- Handwritten image recognition
- Arbitrary schematic recognition

Unsupported or ambiguous requests are reported honestly rather than forced through the solver.

## Architecture

1. **Parser service**
   - `demo_parser.py` recognizes bundled examples without external API keys.
   - `gemini_parser.py` can call Gemini if `GEMINI_API_KEY` is present, then falls back to the demo parser if unavailable.

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

7. **Schematic generator**
   - Creates deterministic SVG diagrams from Circuit IR.
   - Uses named templates for bundled demos and a fallback graph renderer for other supported layouts.

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
- `POST /full_pipeline`

`/full_pipeline` accepts:

```json
{
  "problem_text": "A 10 V voltage source is connected in series with R1 = 2 kOhm and R2 = 3 kOhm. Find the voltage across R2 and the current through the circuit.",
  "mode": "demo"
}
```

and returns Circuit IR, Solution Packet, explanation, variants, parser used, and warnings.

## Future Work

- ngspice integration for cross-checking
- Schematic rendering
- Image/PDF circuit parsing
- Dependent sources
- Inductors and transient analysis
- Student-solution diagnosis
- Benchmarking against general LLM answers
