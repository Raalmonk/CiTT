# 2026 Medtronic/BMES Competition Strategy

## Recommended Positioning

Submit VeriCircuit Tutor to the Electrical/Computer Science/AI track as:

> A verification-grounded AI tutor for safer biomedical instrumentation education.

The strongest story is not that this is a generic circuit tutor. The strongest story is that biomedical engineering students now use AI tools for circuit reasoning, but free-text LLM answers can silently hallucinate signs, units, current directions, and unsupported assumptions. VeriCircuit Tutor changes the authority structure: language can help parse or explain, but validated Circuit IR, deterministic solvers, verification checks, and Solution Packets own the numerical answer.

## Competition Fit

The provided 2026 judging packet asks for five submission criteria: product need and market potential, device utility and novelty, technical feasibility, budget and economic plan, and writing clarity. The live presentation rubric then emphasizes product requirements, design description, actual performance, economic plan, and professional presentation.

VeriCircuit Tutor fits the competition if it is presented as a BME education-support product, not as a medical device, clinical diagnostic system, or biomedical design-verification tool.

## Product Capability Narrative

Frame the product as a controlled learning environment with five visible capabilities:

1. **Verified answer engine**
   - Student prompts become explicit Circuit IR, then validation, deterministic solving, verification badges, and answer provenance.
   - The value is not "AI solves circuits"; the value is that numerical authority is inspectable.

2. **Guided visual tutoring**
   - The tutor turns a verified packet into step-by-step lessons tied to schematic focus regions, equation steps, common mistakes, and verified value references.
   - This makes the product feel like an instructor-led walkthrough rather than a static calculator.

3. **Reasoning coach**
   - Before revealing final numbers, the coach asks students to commit to a frame, detects local misconception tags, gives one nudge, and tracks portable learning signals.
   - This is the main education differentiator: it protects student reasoning time.

4. **BME instrumentation context**
   - Named ECG, EMG, bridge, thermistor, photodiode, instrumentation-amplifier, and anti-aliasing templates attach signal-chain role, safety reminders, nonideal cautions, and practice variants to verified circuit results.
   - Keep the claim educational: these are teaching templates, not device-level biomedical verification.

5. **Honest boundary behavior**
   - Unsupported or ambiguous cases return controlled statuses instead of polished fake answers, and the `/scope` endpoint makes the current product boundary visible in the UI.
   - This honesty is part of the product capability, not just a disclaimer.

## Judging Criteria Map

| Criterion | Current CiTT Strength | Current Gap |
| --- | --- | --- |
| Product need and market potential | Clear user: BME instructors and students in biomedical instrumentation, circuits, and sensor-interface labs. Clear pain: unverified AI tutoring can teach wrong numerical reasoning. | Need sourced market/user evidence before final submission. Avoid unsupported market-size claims until sourced. |
| Device utility and novelty | Novel authority split: LLM is not the truth source; solver, verifier, and Solution Packet are. BME templates cover ECG, EMG, pressure, strain, thermistor, photodiode, instrumentation amplifier, and anti-aliasing cases. | Need a polished product demo that makes the difference obvious within 60 seconds. |
| Technical feasibility | Working FastAPI backend, Circuit IR, validation, MNA solver, AC solver, linear numerical transient solver, verification badges, lesson packets, BME metadata, and automated tests. | Need a benchmark table and one baseline comparison against ordinary LLM free-text answers. |
| Budget and economic plan | Software-first prototype has low marginal cost and can run deterministic demos without external LLM calls. | Need a credible per-institution pricing/support/deployment model and a small cost table. |
| Writing clarity and style | Core idea is concise: "The LLM is not the source of truth." | Need application-length drafts under the official word limits. |

## Submission Evidence Now In Repo

Run from `backend`:

```bash
python scripts/run_evaluation.py --format markdown
```

Current result after adding BME submission-evidence fixtures:

| Evidence slice | Result |
| --- | ---: |
| Total benchmark cases | 15 |
| Passed | 14 |
| Failed | 0 |
| Skipped | 1 |
| BME template submission-evidence cases | 9/9 passed |

The skipped case is the mocked Gemini contract fixture. It is intentionally validated by pytest rather than by network evaluation.

The BME evidence set now checks:

- ECG front-end differential amplifier
- EMG RC band-pass chain
- Pressure sensor divider
- Pressure sensor Wheatstone bridge
- Strain gauge Wheatstone bridge
- Thermistor divider
- Photodiode transimpedance amplifier
- Instrumentation amplifier
- Anti-aliasing RC low-pass filter

Each BME benchmark requires a solved PASS packet, expected requested answers, BME metadata, and named tutor observations where relevant.

## Application Draft Pieces

### Problem To Be Solved (<=125 Words)

Biomedical engineering students increasingly use AI tutors while learning circuits for ECG front ends, sensor bridges, photodiode amplifiers, anti-aliasing filters, and other biomedical instrumentation blocks. General LLM tutors can produce fluent explanations while making hidden numerical mistakes in signs, units, current directions, node references, or unsupported circuit assumptions. In patient-connected engineering domains, that teaches unsafe intuition even when the tool is used only for education. Instructors need a tutor that can explain circuit reasoning while keeping final numerical answers tied to circuit laws, explicit assumptions, and verification checks.

### Project Objective (<=125 Words)

VeriCircuit Tutor addresses this problem with a solver-verified AI tutoring architecture. A student prompt is converted into Circuit IR, validated, solved with deterministic circuit-analysis engines, checked for KCL, power balance, requested-answer coverage, and support boundaries, then explained from the verified Solution Packet. BME templates add biomedical context, safety reminders, nonideal cautions, and practice variants for ECG, EMG, bridge sensors, thermistors, photodiode TIAs, instrumentation amplifiers, and anti-aliasing filters. The goal is not to certify medical devices, but to help BME students learn instrumentation circuits from verified numerical evidence rather than ungrounded generated prose.

### Final Design Summary (<=250 Words)

The prototype is a FastAPI software system with a deterministic circuit-analysis core and an optional LLM parsing layer. It supports DC operating point analysis for supported linear circuits, Shockley diode DC operating points through Newton-Raphson nonlinear MNA, single-frequency AC phasor analysis, AC sweeps, linear numerical transient analysis, ideal closed-loop op-amp analysis, educational nonideal op-amp macromodeling, BME output-noise transfer estimates, SPICE-like netlist export, deterministic SVG schematics, verification badges, answer provenance, and structured lesson packets. The core design rule is that the LLM never owns final numerical answers. Numerical values come from the solver and are packaged in a Solution Packet before any tutor explanation is generated.

For biomedical instrumentation education, the system includes named templates and metadata for ECG front-end differential amplification, EMG filtering, pressure and strain bridges, thermistor dividers, photodiode transimpedance amplification, instrumentation amplification, and ADC anti-aliasing. It also includes limited topology-feature injection for student-built differential front ends and ADC-style RC low-pass stages. The tutor layer attaches biomedical context, common lab mistakes, typical signal ranges, safety notes, nonideal reminders, CMRR mismatch what-if observations, ADC sampling observations, and output-referred noise estimates where appropriate.

Risk controls include explicit unsupported/ambiguous statuses, no fabricated numerical answers for unsupported circuits, visible verification badges, answer provenance, and a boundary statement that the tool is educational software, not clinical diagnosis, patient-specific decision support, safety certification, IEC compliance, or regulatory clearance.

### Proof Of Function (<=250 Words)

The current offline benchmark contains 15 cases across core circuits and BME submission-evidence templates. Running `python scripts/run_evaluation.py --format markdown` reports 14 passed, 0 failed, and 1 skipped Gemini mock contract. The BME subset is 9/9 passed and covers ECG, EMG, pressure divider, pressure bridge, strain bridge, thermistor divider, photodiode TIA, instrumentation amplifier, and anti-aliasing low-pass examples.

Each solved PASS case must produce expected requested answers within tolerance and a structured lesson packet. BME cases additionally require biomedical metadata such as context, signal-chain role, typical signal range, safety note, learning objectives, common lab mistakes, and real-world nonidealities. Selected BME cases also require tutor observations for differential/common-mode inputs, CMRR mismatch, noise-boundary estimates, ADC sampling, Nyquist frequency, and aliasing warnings.

The benchmark also includes an unsupported AC diode rectifier-style request. The system correctly returns UNSUPPORTED rather than fabricating a numerical result, demonstrating the product's honesty boundary beyond the supported DC Shockley diode scope.

### Regulatory Pathway (<=125 Words)

VeriCircuit Tutor should be positioned as educational software for engineering instruction. It is not intended for clinical diagnosis, treatment, patient-specific decision-making, medical-device certification, IEC compliance verification, or regulatory approval support. The current prototype does not connect to patients, acquire physiological signals, control therapy, or make clinical recommendations. Therefore, the submission should avoid claiming a 510(k) or PMA pathway for the current educational product. If future versions were marketed for clinical design verification, patient-specific decision support, or regulated device development, the intended use would need to be reassessed with regulatory counsel.

## Demo Plan

1. Open with the failure mode: ordinary AI can explain a biomedical instrumentation circuit fluently while silently getting a sign, unit, or unsupported assumption wrong.
2. Show the architecture: natural language -> Circuit IR -> validation -> solver -> verification -> Solution Packet -> explanation.
3. Run the ECG or anti-aliasing BME template live.
4. Point to the PASS badge, requested answer, provenance, BME context, safety note, and limitation boundary.
5. Run an unsupported AC diode rectifier or transistor case to show honest refusal instead of fake confidence.
6. Close with the benchmark table and the phrase: "The tutor can be conversational, but it is not the source of numerical truth."

## Next Highest-Value Work

1. Record a 90-second demo video using ECG front-end or anti-aliasing as the main BME story.
2. Build an 8 to 10 case GPT-only baseline comparison for numerical correctness, unit correctness, sign convention, and unsupported-honesty behavior.
3. Source the market section: number of BME programs, instrumentation/circuits course fit, LMS/software purchasing model, and comparable ed-tech pricing.
4. Create one architecture figure and one benchmark figure for upload.
5. Draft the final executive summary after the baseline comparison is complete.
