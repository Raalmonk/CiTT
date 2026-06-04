# VeriCircuit Tutor Agent Instructions

- Be explicit and conservative.
- Do not fake solver results.
- Do not let the LLM generate final numerical answers directly.
- Numerical answers must come from the MNA solver or a verified deterministic calculation.
- Any explanation must cite values from the Solution Packet.
- If a requested circuit feature is unsupported, return a clear unsupported-feature message instead of pretending to solve it.
- Always run tests after meaningful changes.
- Prefer small, readable modules over clever abstractions.

