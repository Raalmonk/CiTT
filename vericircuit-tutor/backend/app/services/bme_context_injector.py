from __future__ import annotations

import math

from app.models.circuit_ir import BMETemplateMetadata, CircuitProblem, Component, is_op_amp_type


def inject_dynamic_bme_context(problem: CircuitProblem) -> CircuitProblem:
    if problem.bme_metadata is not None:
        return problem

    metadata = _differential_front_end_metadata(problem) or _anti_aliasing_metadata(problem)
    if metadata is None:
        return problem
    assumptions = [
        *problem.assumptions,
        "Dynamic BME context: metadata inferred from Circuit IR topology features, not from a named template.",
    ]
    return problem.model_copy(
        deep=True,
        update={"bme_metadata": metadata, "assumptions": assumptions},
    )


def _differential_front_end_metadata(problem: CircuitProblem) -> BMETemplateMetadata | None:
    if not any(is_op_amp_type(component.type) for component in problem.components):
        return None
    voltage_sources = [
        component for component in problem.components if component.type == "voltage_source"
    ]
    if len(voltage_sources) < 2:
        return None
    paired_sources = [
        component
        for component in voltage_sources
        if problem.ground_node in component.nodes
    ]
    if len(paired_sources) < 2:
        return None
    marker = f"{problem.id} {problem.title}".lower()
    biomedical_hint = any(
        term in marker
        for term in ["ecg", "emg", "eeg", "bio", "biomedical", "instrumentation", "electrode"]
    )
    if not biomedical_hint and not _has_balanced_resistor_pairs(problem):
        return None
    return BMETemplateMetadata(
        biomedical_context=(
            "This circuit has differential-front-end features: paired input sources and op-amp-based gain. "
            "That pattern is common in biomedical sensor interfaces."
        ),
        signal_chain_role="Dynamically detected differential sensor front end before filtering, ADC driving, or isolation-aware design review.",
        assumptions=[
            "BME context was inferred from topology features rather than a named template.",
            "Paired grounded sources are treated as a differential/common-mode teaching cue.",
            "This is not a safety or device-level certification.",
        ],
        what_students_should_learn=[
            "Separate differential input from common-mode input.",
            "Check output polarity and reference direction before interpreting gain.",
            "Treat CMRR, input protection, and isolation as real-hardware follow-up checks.",
        ],
        common_lab_mistakes=[
            "Amplifying common-mode level as if it were the desired differential signal.",
            "Ignoring electrode or sensor source impedance mismatch.",
            "Reading output swing as ideal even when real rails would saturate.",
        ],
        typical_signal_range="Biomedical differential sensor signals are often microvolts to millivolts before gain.",
        safety_note="Patient-connected front ends require isolation, leakage-current limits, protection, and approved medical-device design practices.",
        noise_sources=[
            "Common-mode interference",
            "Input-referred amplifier noise",
            "Source impedance mismatch",
        ],
        real_world_nonidealities=[
            "Finite CMRR and resistor mismatch leak common-mode signal to output.",
            "Input bias current and offset can dominate small differential signals.",
            "Supply rails and output swing limit usable gain.",
        ],
        recommended_next_block="Add explicit protection/isolation context, band-limiting, anti-aliasing, and ADC interface checks.",
        noise_bandwidth_hz=150.0,
        op_amp_input_noise_nv_per_sqrt_hz=20.0,
        cmrr_mismatch_percent=1.0,
    )


def _anti_aliasing_metadata(problem: CircuitProblem) -> BMETemplateMetadata | None:
    motif = _rc_low_pass_motif(problem)
    if motif is None:
        return None
    resistor, capacitor = motif
    cutoff_hz = 1.0 / (2.0 * math.pi * resistor.value * capacitor.value)
    analysis_frequency = problem.frequency_hz or cutoff_hz
    sampling_hz = max(4.0 * analysis_frequency, 4.0 * cutoff_hz)
    marker = f"{problem.id} {problem.title}".lower()
    if not any(term in marker for term in ["adc", "alias", "sample", "biomedical", "bme"]):
        # The topology is still useful, but avoid over-medicalizing every RC filter.
        return None
    return BMETemplateMetadata(
        biomedical_context=(
            "This circuit has an RC low-pass feature at an output node, a common anti-aliasing pattern before ADC sampling."
        ),
        signal_chain_role="Dynamically detected RC anti-aliasing or bandwidth-limiting stage.",
        assumptions=[
            "BME context was inferred from an RC low-pass topology feature.",
            "Sampling metadata is an educational default derived from the analysis/cutoff frequency.",
        ],
        what_students_should_learn=[
            "Relate RC cutoff frequency to Nyquist and high-frequency attenuation.",
            "Remember that one RC pole is not a complete alias-energy proof.",
            "Check ADC input loading and sampling kickback in real hardware.",
        ],
        common_lab_mistakes=[
            "Using 1/(RC) instead of 1/(2*pi*RC) for cutoff in Hz.",
            "Choosing cutoff without comparing it to Nyquist frequency.",
            "Ignoring ADC input impedance and acquisition dynamics.",
        ],
        typical_signal_range="Biomedical ADC front ends often filter normalized small-signal stages before digitization.",
        safety_note="Anti-aliasing filters do not replace isolation or patient-safety controls in human-connected systems.",
        noise_sources=["Thermal noise", "ADC quantization noise", "Wideband amplifier noise"],
        real_world_nonidealities=[
            "Component tolerances shift the cutoff.",
            "ADC sampling capacitance can load the filter node.",
            "Higher-order filters may be needed for adequate stop-band attenuation.",
        ],
        recommended_next_block="ADC driver, acquisition-time check, and higher-order filter design when needed.",
        adc_sampling_frequency_hz=float(sampling_hz),
        adc_target_cutoff_hz=float(cutoff_hz),
        adc_resolution_bits=12,
        adc_full_scale_voltage_v=3.3,
        adc_input_impedance_ohm=1_000_000.0,
        noise_bandwidth_hz=float(cutoff_hz),
        thermal_noise_resistor_ids=[resistor.id],
    )


def _has_balanced_resistor_pairs(problem: CircuitProblem) -> bool:
    resistors = [component for component in problem.components if component.type == "resistor"]
    if len(resistors) < 4:
        return False
    values = sorted(round(component.value, 9) for component in resistors)
    repeated = sum(1 for idx in range(1, len(values)) if values[idx] == values[idx - 1])
    return repeated >= 2


def _rc_low_pass_motif(problem: CircuitProblem) -> tuple[Component, Component] | None:
    capacitors = [
        component
        for component in problem.components
        if component.type == "capacitor" and problem.ground_node in component.nodes
    ]
    for capacitor in capacitors:
        output_node = capacitor.nodes[0] if capacitor.nodes[1] == problem.ground_node else capacitor.nodes[1]
        resistor = next(
            (
                component
                for component in problem.components
                if component.type == "resistor"
                and output_node in component.nodes
                and problem.ground_node not in component.nodes
            ),
            None,
        )
        if resistor is not None and resistor.value > 0 and capacitor.value > 0:
            return resistor, capacitor
    return None
