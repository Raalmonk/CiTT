# Evaluation Plan

## Benchmark Size

Use a 20-problem benchmark for the MVP evaluation.

## Problem Mix

- 5 voltage-divider or current-divider problems
- 5 nodal-analysis resistor/source circuits
- 5 Thevenin/Norton-style circuits within the supported linear DC scope
- 5 bridge or dependent-source future examples

The fourth group should include unsupported examples on purpose. The expected behavior for unsupported dependent-source examples in the MVP is honest refusal, not numerical solving.

## Metrics

- Parse correctness: Circuit IR matches intended topology, component values, units, nodes, and goals.
- Numerical answer correctness: node voltages, component currents, component voltages, and powers match trusted reference solutions.
- Unit correctness: values are normalized to SI units and reported with the correct output unit.
- Sign convention correctness: current directions, source power, and component voltage references are explicit and consistent.
- Explanation consistency: every numerical value in the explanation appears in the Solution Packet.
- Honest uncertainty when unsupported: unsupported or ambiguous problems are marked clearly and not solved by guesswork.

## Procedure

1. Write each problem in natural language.
2. Define the expected Circuit IR or a reference netlist.
3. Run `/full_pipeline` in demo or Gemini mode.
4. Compare parsed IR against the expected topology and values.
5. Compare solver output against a trusted hand solution or SPICE result.
6. Check verification report fields.
7. Inspect explanation text for unsupported invented numbers.

## Pass Criteria

For supported circuits, the solver should pass KCL and power-balance checks within default tolerance. For unsupported circuits, the system should return status `unsupported` or `ambiguous` and should not generate a final numerical tutoring explanation.

