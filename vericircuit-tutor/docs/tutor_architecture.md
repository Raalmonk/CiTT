# Tutor Architecture

VeriCircuit Tutor separates solving from teaching.

## Authority Chain

Natural language is parsed into Circuit IR. The validator, solver, and verifier produce a `SolutionPacket`. The explainer and lesson builder may only teach from that packet, `TutorObservation`, `AnalysisView`, or deterministic circuit metadata.

Gemini is the only natural-language parser for API entrypoints, and it does not produce final numerical answers. If Gemini is unavailable or cannot produce validated Circuit IR, the parser returns controlled ambiguity instead of falling back to bundled template matching.

## Structured Lesson

`LessonPacket` is attached to `SolutionPacket.lesson_packet` only when the packet status is `solved` and the verification badge is `PASS`.

It contains:

- Summary and learning objectives.
- Conceptual overview.
- Step-by-step derivation backed by `TutorStep` focus data.
- Equation steps.
- Visual cues and common mistakes.
- Verification checks.
- Practice prompts.
- Verified value references.
- Limitations.

The plain `explanation: str` path remains for backward compatibility.

## Numeric Safety

Lesson numbers are formatted from verified packet fields or deterministic tutor observations. Teaching prose should avoid raw final numbers; if a lesson needs a number, it should use a `LessonValueRef`.

Allowed conceptual constants in prose are limited to simple symbolic constants such as 0, 1, and 2 when describing KCL, node references, or first-order formulas.

## BME Boundary

BME context is educational. It may describe signal-chain role, typical mistakes, warnings, and starter estimates, but it is not patient-safety certification, IEC compliance, leakage-current analysis, or a medical-device design review.
