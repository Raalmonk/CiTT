# Evaluation Plan

## Benchmark Scope

Use a growing offline benchmark, starting with the structured cases in `backend/tests/fixtures/benchmark_cases/core_cases.json`. The first suite is intentionally small and fast; expand it toward a 30- to 50-problem set as new supported circuit families are added.

## Categories

- Parsing correctness: intended topology, component values, units, nodes, references, and goals.
- Solver correctness: node voltages, branch currents, component voltages, powers, phasors, sweeps, and RC transient values.
- Visual clarity: SVG validity, component/node metadata, readable template layouts, focus regions, and overlay semantics.
- Explanation depth: step coverage, conceptual overview, circuit-law explanation, equation clarity, and requested-answer extraction.
- Source-of-truth compliance: every user-visible numerical lesson value must come from `SolutionPacket`, `TutorObservation`, `AnalysisView`, or deterministic metadata.
- Unsupported honesty: unsupported or ambiguous cases must not produce fake numerical answers or structured lessons.
- BME caution quality: biomedical context must remain educational and non-certifying.
- Gemini fallback behavior: fallback mode must recover to demo parsing, strict mode must return controlled ambiguity, and all Gemini tests must be mock-only by default.

## Tutor-Quality Rubric

Score each solved case from 0 to 2 in each dimension:

- Step coverage: identifies source/reference, target, law, readout, and verification boundary.
- Circuit-law explanation: explains KCL, series/parallel behavior, impedance, or transient law appropriate to the circuit.
- Equation clarity: shows the governing symbolic relation without inventing raw numbers.
- Visual grounding: each major step has component/node/goal focus where possible.
- Common mistakes: names at least one plausible student error.
- Verification explanation: explains what the PASS badge checks and what it does not prove.
- No invented values: numerical values are traceable to verified packet fields or deterministic observations.

## Procedure

1. Run `python scripts/run_evaluation.py` from `backend`.
2. Run `python -m pytest` to cover parser, solver, lesson, visual, Gemini mock, and frontend API contracts.
3. For each supported benchmark case, compare requested answers against expected values and tolerances.
4. For AC and transient cases, compare magnitude/phase or transient metadata rather than flattening them into DC scalar checks.
5. For unsupported cases, assert `unsupported` or `ambiguous`, no PASS badge, and no `lesson_packet`.
6. Inspect any changed SVG template with XML tests before relying on manual screenshots.

## Pass Criteria

Supported circuits should validate, solve, and pass internal verification. Unsupported circuits should remain honest and avoid final answers. Structured lessons should exist only for solved PASS packets and should expose focus references, checks, common mistakes, limitations, and verified value references.

## Expansion Backlog

- Add more bridge/nodal cases with asymmetric values and multiple requested currents.
- Add op-amp gain, differential amplifier, and transimpedance amplifier benchmark cases.
- Add AC sweep benchmark expectations for several sampled frequencies.
- Add fixture-driven mocked Gemini parse outputs for common prompt phrasings.
- Add visual clarity review notes for each named schematic template.
