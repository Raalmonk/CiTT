from __future__ import annotations

from app.models.scope_boundary import ProductCapability, ScopeBoundary, ScopeItem


SUPPORTED_ANALYSIS_MODES = [
    ScopeItem(
        label="Linear DC operating point",
        detail="Resistor/source networks, capacitor open-circuit behavior, ideal closed-loop op-amp DC, and simplified nonideal op-amp DC within validator limits.",
    ),
    ScopeItem(
        label="AC phasor and sweep",
        detail="Linear R/L/C/source circuits with finite phasor values, plus simplified nonideal op-amp single-pole gain-bandwidth behavior.",
    ),
    ScopeItem(
        label="Educational nonideal op-amp model",
        detail="Finite open-loop gain, rail/output-swing clipping, input bias current, output-current limit checks, slew-rate notes, clipping-recovery notes, and AC frequency response.",
    ),
    ScopeItem(
        label="Gemini schematic/image parsing",
        detail="The /parse_image endpoint can ask Gemini to convert visible schematic connectivity and text labels into Circuit IR, with ambiguities preserved instead of guessed.",
    ),
    ScopeItem(
        label="First-order RC transient template",
        detail="Single-capacitor educational charging/discharging template, not a general transient engine.",
    ),
    ScopeItem(
        label="Reasoning coach",
        detail="Student-frame checks, hint ladder, adaptive practice, and Level 5 reveal after student commitment.",
    ),
]

UNSUPPORTED_FEATURES = [
    ScopeItem(
        label="General transient simulation",
        detail="Includes arbitrary time-domain, RLC transient, and nonlinear transient solving.",
    ),
    ScopeItem(
        label="Nonlinear or semiconductor devices",
        detail="Diodes, transistors, nonlinear solving, and arbitrary dependent-source behavior are outside the current solver scope.",
    ),
    ScopeItem(
        label="SPICE-grade device macro-models",
        detail="The nonideal op-amp path is an educational model, not a transistor-level or vendor macro-model simulator.",
    ),
    ScopeItem(
        label="Guaranteed recognition of ambiguous images",
        detail="Unreadable, cropped, or ambiguous schematics should return ambiguities rather than guessed Circuit IR.",
    ),
]

SCOPE_BOUNDARY = ScopeBoundary(
    product_positioning=(
        "Professor-facing MVP for supported undergraduate circuit-analysis topics, "
        "educational BME templates, and reasoning-coach loops."
    ),
    source_of_truth_rule=(
        "Final numerical values come from Circuit IR validation, deterministic solving, "
        "and internal verification, not direct LLM generation."
    ),
    product_capabilities=[
        ProductCapability(
            capability="Solver-verified circuit answers",
            user_value=(
                "Lets students and instructors inspect numerical answers that are tied to "
                "explicit topology, sign convention, units, and requested goals."
            ),
            current_evidence=(
                "PASS Solution Packets include requested answers, MNA provenance, KCL checks, "
                "supported power-balance checks, and a verification badge."
            ),
            boundary="Only applies inside the supported linear and template-based solver scope.",
        ),
        ProductCapability(
            capability="Educational nonideal op-amp modeling",
            user_value=(
                "Lets students compare ideal answers against rail clipping, finite gain, input bias, "
                "frequency response, and output-current limits without leaving the verified tutor path."
            ),
            current_evidence=(
                "nonideal_op_amp components are accepted in Circuit IR; DC solving stamps finite gain, "
                "bias current, and rail clamp, while AC solving uses a single-pole gain-bandwidth model."
            ),
            boundary=(
                "Educational model only; slew rate and clipping recovery are reported as dynamic limits, "
                "not full waveform or vendor macro-model simulation."
            ),
        ),
        ProductCapability(
            capability="Schematic/image-to-Circuit-IR parsing",
            user_value=(
                "Allows an instructor or student to submit a schematic image and keep the numerical "
                "answer path grounded in explicit Circuit IR."
            ),
            current_evidence=(
                "/parse_image accepts base64 PNG/JPEG/WebP input and asks Gemini for structured "
                "CircuitProblem JSON before deterministic validation and solving."
            ),
            boundary=(
                "Image parsing is only trusted as a parser; unreadable values or connectivity become "
                "ambiguities, and final numbers still come from the deterministic solvers."
            ),
        ),
        ProductCapability(
            capability="Guided visual lessons",
            user_value=(
                "Turns a verified solution into step-by-step teaching moves that point to the "
                "specific schematic nodes, components, currents, and references students should inspect."
            ),
            current_evidence=(
                "LessonPacket output includes learning objectives, equation steps, visual focus IDs, "
                "common mistakes, checks, limitations, and verified value references."
            ),
            boundary="Lessons are generated only after a solved PASS packet; unsupported cases do not get polished explanations.",
        ),
        ProductCapability(
            capability="Reasoning coach before reveal",
            user_value=(
                "Encourages students to commit to a method, checks the local frame, gives one nudge, "
                "and delays final numbers until a Level 5 reveal."
            ),
            current_evidence=(
                "/reasoning_coach returns StudentFrame, CoachNudge, misconception tags, adaptive practice, "
                "profile updates, and instructor-dashboard summaries."
            ),
            boundary="Profiles are portable stateless payloads in this MVP, not persistent LMS analytics.",
        ),
        ProductCapability(
            capability="Biomedical instrumentation teaching layer",
            user_value=(
                "Places verified circuit results in ECG, EMG, bridge-sensor, thermistor, photodiode, "
                "instrumentation-amplifier, and anti-aliasing learning contexts."
            ),
            current_evidence=(
                "Named BME templates carry metadata, safety notes, common lab mistakes, CMRR what-ifs, "
                "ADC sampling observations, noise starter estimates, and practice variants."
            ),
            boundary="Educational context only; not biomedical design verification, IEC compliance, or safety certification.",
        ),
        ProductCapability(
            capability="Honest unsupported handling",
            user_value=(
                "Makes product limits visible so an instructor can trust the tutor to refuse or ask "
                "for clarification instead of inventing answers."
            ),
            current_evidence=(
                "UNSUPPORTED and AMBIGUOUS badges block numerical answers, lessons, variants, and probe mode; "
                "/scope exposes the shared product boundary."
            ),
            boundary="Does not expand solver coverage by itself; it keeps unsupported requests from being overclaimed.",
        ),
    ],
    supported_analysis_modes=SUPPORTED_ANALYSIS_MODES,
    supported_components=[
        "resistor",
        "independent voltage source",
        "independent current source",
        "capacitor in DC and RC-template contexts",
        "inductor in AC phasor/sweep contexts",
        "ideal op amp in closed-loop DC contexts",
        "nonideal op amp with simplified educational rail, bias, current-limit, slew, recovery, and frequency-response fields",
    ],
    supported_workflows=[
        "natural-language-to-Circuit-IR parsing with deterministic fallback",
        "schematic/image-to-Circuit-IR parsing through Gemini image mode",
        "MNA-backed solution packets with provenance",
        "verification badges for PASS, FAIL, AMBIGUOUS, and UNSUPPORTED outcomes",
        "structured lesson packets and diagram focus steps for verified PASS solutions",
        "practice variants for supported circuits and named BME templates",
    ],
    unsupported_features=UNSUPPORTED_FEATURES,
    verification_boundary=[
        "PASS means internal validation, solving, KCL, supported power-balance checks, and requested-answer coverage passed.",
        "PASS does not mean independent reference cross-checking, universal simulator correctness, or device-level design approval.",
        "For image input, PASS applies to the parsed Circuit IR, not to a claim that Gemini perfectly recognized the original image.",
        "Unsupported or ambiguous requests should return controlled statuses instead of guessed numerical answers.",
    ],
    bme_boundary=[
        "BME metadata is educational context attached to named templates, not physiological inference from arbitrary circuits.",
        "Safety notes can remind students about isolation, leakage-current limits, patient-connected design, optical exposure, and ADC anti-aliasing.",
        "The MVP does not calculate leakage current, isolation-barrier ratings, IEC-style constraints, device compliance, alias energy, or full noise propagation.",
        "CMRR, ADC, noise, and nonideal op-amp observations are deterministic teaching estimates, not full device-level models.",
    ],
    bme_templates=[
        "ECG front-end differential amplifier",
        "EMG RC band-pass chain",
        "pressure sensor divider and bridge",
        "strain gauge Wheatstone bridge",
        "thermistor divider",
        "photodiode transimpedance amplifier",
        "instrumentation amplifier",
        "anti-aliasing RC low-pass filter",
    ],
)


def get_scope_boundary() -> ScopeBoundary:
    return SCOPE_BOUNDARY
