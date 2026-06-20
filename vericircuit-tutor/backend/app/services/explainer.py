from __future__ import annotations

from app.models.solution_packet import SolutionPacket, TutorObservation


def _format_value(value: float, unit: str) -> str:
    abs_value = abs(value)
    if unit == "%":
        return f"{value:.6g}%"
    if unit == "V_rms":
        if 0 < abs_value < 1e-6:
            return f"{value * 1e9:.6g} nV rms"
        if 0 < abs_value < 1e-3:
            return f"{value * 1e6:.6g} uV rms"
        if 0 < abs_value < 1:
            return f"{value * 1000:.6g} mV rms"
        return f"{value:.6g} V rms"
    if unit == "A_rms":
        if 0 < abs_value < 1e-9:
            return f"{value * 1e12:.6g} pA rms"
        if 0 < abs_value < 1e-6:
            return f"{value * 1e9:.6g} nA rms"
        if 0 < abs_value < 1:
            return f"{value * 1e6:.6g} uA rms"
        return f"{value:.6g} A rms"
    if unit == "V" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mV"
    if unit == "A" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mA"
    if unit == "W" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mW"
    return f"{value:.6g} {unit}"


def _format_complex(magnitude: float, phase_deg: float, unit: str) -> str:
    return f"{_format_value(magnitude, unit)} angle {phase_deg:.6g} deg"


def _observation(packet: SolutionPacket, observation_id: str) -> TutorObservation | None:
    return next(
        (
            observation
            for observation in packet.tutor_observations
            if observation.id == observation_id
        ),
        None,
    )


def _observations_with_prefix(packet: SolutionPacket, prefix: str) -> list[TutorObservation]:
    return [
        observation
        for observation in packet.tutor_observations
        if observation.id.startswith(prefix)
    ]


def _format_observation(observation: TutorObservation | None) -> str | None:
    if observation is None or observation.value is None:
        return None
    return _format_value(observation.value, observation.unit or "")


def _format_frequency(value: float) -> str:
    if value >= 1000:
        return f"{value / 1000:.6g} kHz"
    return f"{value:.6g} Hz"


def _verification_sentence(packet: SolutionPacket) -> str:
    passed_checks = [check.name for check in packet.verification.checks if check.passed]
    if not passed_checks:
        return "The packet passed verification, but no individual check names were reported."
    residual = packet.verification.max_kcl_residual_a
    if packet.symbolic_requested_answers and not packet.requested_answers:
        return (
            "The symbolic expression above is from deterministic closed-form checks. "
            f"Passed checks: {', '.join(passed_checks)}."
        )
    return (
        "The numerical values above are from the verified Solution Packet. "
        f"Passed checks: {', '.join(passed_checks)}. "
        f"Max KCL residual: {residual:.3g} A."
    )


def _metadata_supply_window(metadata) -> tuple[float, float, float, float, float] | None:
    if metadata.supply_positive_v is not None and metadata.supply_negative_v is not None:
        rail_lower = min(metadata.supply_negative_v, metadata.supply_positive_v)
        rail_upper = max(metadata.supply_negative_v, metadata.supply_positive_v)
    elif metadata.nominal_supply_rails_v:
        rail_lower = min(metadata.nominal_supply_rails_v.values())
        rail_upper = max(metadata.nominal_supply_rails_v.values())
    else:
        return None

    margin = max(float(metadata.output_swing_margin_v or 0.0), 0.0)
    usable_lower = rail_lower + margin
    usable_upper = rail_upper - margin
    if usable_lower > usable_upper:
        usable_lower = rail_lower
        usable_upper = rail_upper
        margin = 0.0
    return usable_lower, usable_upper, rail_lower, rail_upper, margin


def _join_sentence_list(items: list[str]) -> str:
    return "; ".join(item.rstrip(".") for item in items) + "."


def _noise_budget_line(packet: SolutionPacket) -> str | None:
    bandwidth = _format_observation(_observation(packet, "noise_budget_bandwidth"))
    if bandwidth is None:
        return None

    parts = [f"Noise budget starter over {bandwidth}"]
    thermal_parts = [
        f"{observation.label}: {_format_observation(observation)}"
        for observation in _observations_with_prefix(packet, "thermal_noise_")
        if _format_observation(observation)
    ]
    if thermal_parts:
        parts.append("resistor thermal noise " + "; ".join(thermal_parts))

    shot_parts = [
        f"{observation.label}: {_format_observation(observation)}"
        for observation in _observations_with_prefix(packet, "photodiode_shot_noise_")
        if _format_observation(observation)
    ]
    if shot_parts:
        parts.append("photodiode shot noise " + "; ".join(shot_parts))

    op_amp_noise = _format_observation(_observation(packet, "op_amp_input_referred_noise"))
    if op_amp_noise:
        parts.append(f"op-amp input-referred noise {op_amp_noise}")

    line = ". ".join(parts) + "."
    boundary = _observation(packet, "noise_budget_boundary")
    if boundary and boundary.note:
        line += " " + boundary.note
    return line


def _bme_intro(packet: SolutionPacket) -> list[str]:
    metadata = packet.bme_metadata
    if metadata is None:
        return []
    lines = [
        metadata.biomedical_context,
        f"Signal-chain role: {metadata.signal_chain_role}",
    ]
    if metadata.typical_signal_range:
        lines.append(f"Typical signal range: {metadata.typical_signal_range}")
    if metadata.safety_note:
        lines.append(f"Safety note, not safety analysis: {metadata.safety_note}")
    supply_window = _metadata_supply_window(metadata)
    if supply_window is not None:
        usable_lower, usable_upper, rail_lower, rail_upper, margin = supply_window
        if margin > 0:
            lines.append(
                "Template nominal op-amp rails: "
                f"{rail_lower:.6g} V to {rail_upper:.6g} V, "
                f"with usable output window {usable_lower:.6g} V to {usable_upper:.6g} V after margin."
            )
        else:
            lines.append(f"Template nominal op-amp rails: {rail_lower:.6g} V to {rail_upper:.6g} V.")
    if metadata.recommended_next_block:
        lines.append(f"Recommended next block: {metadata.recommended_next_block}")
    if metadata.what_students_should_learn:
        lines.append("Learning focus: " + _join_sentence_list(metadata.what_students_should_learn))
    if metadata.common_lab_mistakes:
        lines.append("Common lab traps: " + _join_sentence_list(metadata.common_lab_mistakes))
    return lines


def _explain_ac(packet: SolutionPacket) -> str:
    lines = _bme_intro(packet)
    behavior = _observation(packet, "filter_behavior")
    transfer_ratio = _format_observation(_observation(packet, "transfer_magnitude_ratio"))
    requested_magnitude = _format_observation(_observation(packet, "requested_magnitude"))
    requested_phase = _format_observation(_observation(packet, "requested_phase"))

    if behavior and behavior.note == "low-pass":
        lines.append(
            "This is a low-pass filter: the output node follows slow input changes, while the capacitor provides a lower-impedance path for high-frequency current to ground."
        )
        cutoff = _observation(packet, "low_pass_cutoff_frequency")
        corner_ratio = _format_observation(_observation(packet, "first_order_corner_ratio"))
        if cutoff and cutoff.value is not None and corner_ratio:
            lines.append(
                f"The packet's RC corner frequency is {_format_frequency(cutoff.value)}. "
                f"At that first-order corner marker, the output magnitude ratio is about {corner_ratio}."
            )
        sampling = _observation(packet, "adc_sampling_frequency")
        nyquist = _observation(packet, "adc_nyquist_frequency")
        target_cutoff = _observation(packet, "adc_target_cutoff_frequency")
        attenuation = _observation(packet, "adc_attenuation_at_nyquist")
        quantization_step = _format_observation(_observation(packet, "adc_quantization_step"))
        quantization_noise = _format_observation(_observation(packet, "adc_quantization_noise_rms"))
        loading_ratio = _format_observation(_observation(packet, "adc_input_loading_ratio"))
        loading_warning = _observation(packet, "adc_input_loading_warning")
        aliasing_warning = _observation(packet, "aliasing_warning")
        if sampling and sampling.value is not None and nyquist and nyquist.value is not None:
            sampling_line = (
                f"ADC sampling context: fs = {_format_frequency(sampling.value)}, "
                f"so Nyquist is {_format_frequency(nyquist.value)}."
            )
            if target_cutoff and target_cutoff.value is not None:
                sampling_line += f" The target cutoff is {_format_frequency(target_cutoff.value)}."
            if attenuation and attenuation.value is not None:
                sampling_line += (
                    f" The estimated attenuation at Nyquist is {_format_observation(attenuation)}."
                )
                if attenuation.note:
                    sampling_line += f" {attenuation.note}"
            lines.append(sampling_line)
            if quantization_step:
                quantization_line = f"ADC quantization estimate: one LSB is {quantization_step}."
                if quantization_noise:
                    quantization_line += f" Ideal quantization-noise RMS is {quantization_noise}."
                quantization_line += " This is a teaching estimate, not a complete ADC noise model."
                lines.append(quantization_line)
            if loading_ratio:
                loading_line = f"ADC input loading marker: Rsource/Radc is {loading_ratio}."
                if loading_warning and loading_warning.note:
                    loading_line += " " + loading_warning.note
                lines.append(loading_line)
            if aliasing_warning and aliasing_warning.note:
                lines.append(aliasing_warning.note)
    elif behavior and behavior.note == "band-pass":
        lines.append(
            "This is a band-pass chain: the high-pass section suppresses slow drift, and the low-pass section rolls off faster noise."
        )
        high_cutoff = _observation(packet, "high_pass_cutoff_frequency")
        low_cutoff = _observation(packet, "low_pass_cutoff_frequency")
        cutoff_parts = []
        if high_cutoff and high_cutoff.value is not None:
            cutoff_parts.append(f"high-pass corner {_format_frequency(high_cutoff.value)}")
        if low_cutoff and low_cutoff.value is not None:
            cutoff_parts.append(f"low-pass corner {_format_frequency(low_cutoff.value)}")
        if cutoff_parts:
            lines.append("The packet records " + " and ".join(cutoff_parts) + ".")

    if packet.frequency_hz is not None:
        lines.append(f"At {_format_frequency(packet.frequency_hz)}, the verified requested phasor is reported below.")

    if packet.ac_requested_answers:
        answer_lines = []
        for goal_id, answer in packet.ac_requested_answers.items():
            answer_lines.append(
                f"{goal_id}: {_format_complex(answer.magnitude, answer.phase_deg, answer.unit)}"
            )
        lines.append("Requested phasor answer: " + "; ".join(answer_lines) + ".")

    if transfer_ratio:
        lines.append(f"Normalized to the source amplitude in the packet, the output magnitude is {transfer_ratio}.")
    elif requested_magnitude and requested_phase:
        lines.append(f"The requested output magnitude is {requested_magnitude} with phase {requested_phase}.")

    if packet.ac_sweep:
        first = packet.ac_sweep[0]
        last = packet.ac_sweep[-1]
        lines.append(
            f"The AC sweep spans {_format_frequency(first.frequency_hz)} to {_format_frequency(last.frequency_hz)} across {len(packet.ac_sweep)} verified points. "
            "Use the Bode plots to read the magnitude rolloff and phase trend."
        )

    noise_line = _noise_budget_line(packet)
    if noise_line:
        lines.append(noise_line)

    lines.append(_verification_sentence(packet) + " Signed AC complex power balance is checked with the packet's phasor convention.")
    return "\n\n".join(lines)


def _explain_rc_transient(packet: SolutionPacket) -> str:
    response = packet.transient_response
    if response is None:
        return _verification_sentence(packet)

    lines = _bme_intro(packet)
    if not response.is_first_order:
        lines.append(
            "This is a numerical transient analysis: storage elements are discretized with Backward Euler companion models and solved in the time domain."
        )
        lines.append(
            "From the verified packet: "
            f"V initial = {_format_value(response.initial_voltage_v, 'V')}, "
            f"V final DC target = {_format_value(response.final_voltage_v, 'V')}, "
            f"C = {_format_value(response.capacitance_f, 'F')}, "
            f"samples = {len(response.sample_points)}."
        )
        lines.append(_verification_sentence(packet))
        return "\n\n".join(lines)

    lines.append(
        "This is a first-order RC transient solved with numerical Backward Euler integration; the samples follow the expected exponential motion from initial value toward the final DC value."
    )
    lines.append(
        "From the verified packet: "
        f"V initial = {_format_value(response.initial_voltage_v, 'V')}, "
        f"V final = {_format_value(response.final_voltage_v, 'V')}, "
        f"R th = {_format_value(response.resistance_ohm, 'ohm')}, "
        f"C = {_format_value(response.capacitance_f, 'F')}, "
        f"tau = {_format_value(response.time_constant_s, 's')}."
    )
    tau_voltage = _format_observation(_observation(packet, "tau_marker_voltage"))
    if tau_voltage:
        lines.append(f"At one time constant, the packet's sample point gives Vc = {tau_voltage}.")
    lines.append(_verification_sentence(packet))
    return "\n\n".join(lines)


def _explain_dc(packet: SolutionPacket) -> str:
    lines = _bme_intro(packet)
    if not lines:
        lines.append(
            "This DC operating-point result is a verified circuit-law solution, not a direct language-model estimate."
        )

    differential = _format_observation(_observation(packet, "differential_input_voltage"))
    common_mode = _format_observation(_observation(packet, "common_mode_input_voltage"))
    ratio = _format_observation(_observation(packet, "differential_to_common_mode_ratio"))
    if differential and common_mode:
        cmrr_line = (
            "Differential-vs-common-mode: "
            f"the desired input difference is {differential}, while the common-mode level is {common_mode}."
        )
        if ratio:
            cmrr_line += f" The differential/common-mode ratio is {ratio}."
        cmrr_line += (
            " The ideal circuit responds to the differential signal; real CMRR depends on resistor matching, input stage design, and frequency."
        )
        lines.append(cmrr_line)

    mismatch = _format_observation(_observation(packet, "cmrr_mismatch_percent")) or "1 %"
    leakage = _format_observation(_observation(packet, "cmrr_common_mode_leakage_output"))
    leakage_gain = _format_observation(_observation(packet, "cmrr_common_mode_leakage_gain"))
    mismatch_cmrr = _format_observation(_observation(packet, "cmrr_mismatch_estimate_db"))
    if leakage:
        mismatch_line = (
            f"CMRR mismatch what-if: with a {mismatch} resistor-ratio mismatch and common-mode-only input, "
            f"the solved output error is {leakage}."
        )
        if leakage_gain:
            mismatch_line += f" The common-mode leakage gain is {leakage_gain}."
        if mismatch_cmrr:
            mismatch_line += f" The packet's differential-gain marker gives an estimated CMRR of {mismatch_cmrr}."
        mismatch_line += (
            " This is a teaching estimate, not a full resistor-tolerance, finite-op-amp, or frequency-dependent CMRR solver."
        )
        lines.append(mismatch_line)

    if packet.node_voltages:
        formatted_nodes = [
            f"{node} = {_format_value(value, 'V')}"
            for node, value in sorted(packet.node_voltages.items())
        ]
        lines.append("Verified node voltages: " + "; ".join(formatted_nodes) + ".")

    if packet.symbolic_requested_answers:
        answer_lines = []
        for goal_id, answer in packet.symbolic_requested_answers.items():
            coefficient = (
                f" (coefficient {answer.numeric_coefficient:.6g})"
                if answer.numeric_coefficient is not None
                else ""
            )
            answer_lines.append(f"{goal_id}: {answer.expression} (unit {answer.unit}){coefficient}")
        lines.append("Symbolic requested answer: " + "; ".join(answer_lines) + ".")

    if packet.requested_answers:
        answer_lines = []
        for goal_id, answer in packet.requested_answers.items():
            answer_lines.append(f"{goal_id}: {_format_value(answer.value, answer.unit)}")
        lines.append("Requested answer: " + "; ".join(answer_lines) + ".")

    if packet.bme_metadata is not None:
        lines.append(
            "Read the requested value as the signal-chain output for this biomedical stage, then check its sign and reference nodes before interpreting the physiology."
        )

    saturation = _observation(packet, "real_op_amp_saturation_warning")
    if saturation and saturation.note:
        lines.append(saturation.note)

    noise_line = _noise_budget_line(packet)
    if noise_line:
        lines.append(noise_line)

    lines.append(_verification_sentence(packet))
    lines.append(
        "Sign convention: component voltage is V(nodes[0]) - V(nodes[1]), current is positive from nodes[0] to nodes[1], and signed power is voltage times current."
    )
    return "\n\n".join(lines)


def explain_solution(packet: SolutionPacket) -> str:
    if packet.status != "solved":
        return (
            "VeriCircuit Tutor did not generate a numerical explanation because the "
            f"solution packet status is {packet.status!r}. The solver and verifier "
            "must produce verified values before the tutor explains them."
        )

    if not packet.verification.passed:
        return (
            "The numerical solver returned values, but the verification report did "
            "not pass. The tutor explanation is withheld so unverified numbers are "
            "not presented as final answers."
        )

    if packet.ac_requested_answers or packet.ac_sweep:
        return _explain_ac(packet)

    if packet.transient_response:
        return _explain_rc_transient(packet)

    return _explain_dc(packet)
