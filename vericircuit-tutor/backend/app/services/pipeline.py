from __future__ import annotations

import math

from app.models.circuit_ir import CircuitProblem, Component
from app.models.solution_packet import (
    ACFrequencyPoint,
    CalculationTrace,
    CheckResult,
    SolutionPacket,
    TutorObservation,
    VerificationBadge,
    VerificationReport,
)
from app.services.ac_solver import generate_sweep_frequencies, solve_ac
from app.services.ac_verifier import verify_ac_solution
from app.services.guided_steps import build_guided_steps
from app.services.lesson_builder import build_lesson_packet
from app.services.mna_solver import solve_mna
from app.services.netlist_generator import generate_netlist
from app.services.rc_transient_solver import solve_rc_transient
from app.services.validator import validate_circuit
from app.services.verifier import verify_solution


BOLTZMANN_J_PER_K = 1.380649e-23
ELEMENTARY_CHARGE_C = 1.602176634e-19


def _component_by_id(circuit: CircuitProblem, component_id: str) -> Component | None:
    return next((component for component in circuit.components if component.id == component_id), None)


def _cutoff_frequency_hz(resistor: Component | None, capacitor: Component | None) -> float | None:
    if resistor is None or capacitor is None:
        return None
    if resistor.value <= 0 or capacitor.value <= 0:
        return None
    return 1.0 / (2.0 * math.pi * resistor.value * capacitor.value)


def _first_ac_source_magnitude(circuit: CircuitProblem) -> float | None:
    for component in circuit.components:
        if component.type in {"voltage_source", "current_source"} and component.ac_magnitude:
            return float(component.ac_magnitude)
    return None


def _first_ac_answer(packet: SolutionPacket):
    return next(iter(packet.ac_requested_answers.values()), None)


def _first_resistor(circuit: CircuitProblem) -> Component | None:
    return next((component for component in circuit.components if component.type == "resistor"), None)


def _add_cutoff_observation(
    observations: list[TutorObservation],
    observation_id: str,
    label: str,
    cutoff_hz: float | None,
) -> None:
    if cutoff_hz is None:
        return
    observations.append(
        TutorObservation(
            id=observation_id,
            label=label,
            value=float(cutoff_hz),
            unit="Hz",
            note="Computed from the template R and C values before being written to the Solution Packet.",
        )
    )


def _supply_window(
    circuit: CircuitProblem,
) -> tuple[float, float, float, float, float] | None:
    metadata = circuit.bme_metadata
    if metadata is None:
        return None

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


def _add_adc_sampling_observations(
    observations: list[TutorObservation],
    circuit: CircuitProblem,
    cutoff_hz: float | None,
) -> None:
    metadata = circuit.bme_metadata
    if metadata is None or metadata.adc_sampling_frequency_hz is None:
        return

    sampling_hz = float(metadata.adc_sampling_frequency_hz)
    nyquist_hz = sampling_hz / 2.0
    observations.extend(
        [
            TutorObservation(
                id="adc_sampling_frequency",
                label="ADC sampling frequency",
                value=sampling_hz,
                unit="Hz",
                note="Template sampling-rate context for anti-aliasing discussion.",
            ),
            TutorObservation(
                id="adc_nyquist_frequency",
                label="ADC Nyquist frequency",
                value=nyquist_hz,
                unit="Hz",
                note="Half the template sampling frequency.",
            ),
        ]
    )

    if metadata.adc_target_cutoff_hz is not None:
        observations.append(
            TutorObservation(
                id="adc_target_cutoff_frequency",
                label="ADC target cutoff frequency",
                value=float(metadata.adc_target_cutoff_hz),
                unit="Hz",
                note="Template design target for the anti-aliasing pole.",
            )
        )

    if metadata.adc_resolution_bits is not None and metadata.adc_full_scale_voltage_v is not None:
        quantization_step_v = (
            float(metadata.adc_full_scale_voltage_v) / (2 ** int(metadata.adc_resolution_bits))
        )
        observations.append(
            TutorObservation(
                id="adc_quantization_step",
                label="ADC quantization step",
                value=float(quantization_step_v),
                unit="V",
                note=(
                    f"Educational estimate for an ideal {metadata.adc_resolution_bits}-bit ADC over "
                    f"{metadata.adc_full_scale_voltage_v:.6g} V full scale."
                ),
            )
        )
        observations.append(
            TutorObservation(
                id="adc_quantization_noise_rms",
                label="ADC quantization noise estimate",
                value=float(quantization_step_v / math.sqrt(12.0)),
                unit="V_rms",
                note="Ideal uniform-quantizer RMS estimate, not an ADC datasheet noise model.",
            )
        )

    resistor = _first_resistor(circuit)
    if (
        resistor is not None
        and resistor.value > 0
        and metadata.adc_input_impedance_ohm is not None
        and metadata.adc_input_impedance_ohm > 0
    ):
        loading_ratio_percent = resistor.value / float(metadata.adc_input_impedance_ohm) * 100.0
        observations.append(
            TutorObservation(
                id="adc_input_loading_ratio",
                label="ADC input loading marker",
                value=float(loading_ratio_percent),
                unit="%",
                note=(
                    f"Rsource/Radc using {resistor.id} and the template ADC input impedance. "
                    "This is a loading warning marker, not a switched-capacitor ADC input model."
                ),
            )
        )
        if loading_ratio_percent >= 1.0:
            loading_note = (
                "ADC input impedance is close enough to the RC source resistance that loading may shift gain and cutoff."
            )
        else:
            loading_note = (
                "ADC input impedance is much larger than the RC source resistance in this template, "
                "but real ADC sampling capacitance and acquisition time still need checking."
            )
        observations.append(
            TutorObservation(
                id="adc_input_loading_warning",
                label="ADC input loading warning",
                note=loading_note,
            )
        )

    effective_cutoff_hz = cutoff_hz or metadata.adc_target_cutoff_hz
    if effective_cutoff_hz is None or effective_cutoff_hz <= 0:
        return

    magnitude_ratio = 1.0 / math.sqrt(1.0 + (nyquist_hz / effective_cutoff_hz) ** 2)
    attenuation_db = 20.0 * math.log10(magnitude_ratio)
    observations.append(
        TutorObservation(
            id="adc_attenuation_at_nyquist",
            label="Attenuation at Nyquist",
            value=float(attenuation_db),
            unit="dB",
            note=f"First-order RC estimate at Nyquist; magnitude ratio is {magnitude_ratio:.6g} V/V.",
        )
    )
    observations.append(
        TutorObservation(
            id="aliasing_warning",
            label="Aliasing warning",
            note=(
                "A single-pole RC anti-aliasing stage reduces high-frequency content before the ADC, "
                "but it does not prove alias-free sampling; choose cutoff, filter order, and sampling rate together."
            ),
        )
    )


def _add_noise_budget_observations(
    observations: list[TutorObservation],
    circuit: CircuitProblem,
) -> None:
    metadata = circuit.bme_metadata
    if metadata is None or metadata.noise_bandwidth_hz is None:
        return

    bandwidth_hz = float(metadata.noise_bandwidth_hz)
    temperature_k = float(metadata.thermal_noise_temperature_k)
    observations.append(
        TutorObservation(
            id="noise_budget_bandwidth",
            label="Noise estimate bandwidth",
            value=bandwidth_hz,
            unit="Hz",
            note="Template bandwidth used for educational RMS noise estimates.",
        )
    )

    for resistor_id in metadata.thermal_noise_resistor_ids:
        resistor = _component_by_id(circuit, resistor_id)
        if resistor is None or resistor.type != "resistor" or resistor.value <= 0:
            continue
        thermal_noise_v = math.sqrt(
            4.0 * BOLTZMANN_J_PER_K * temperature_k * resistor.value * bandwidth_hz
        )
        observations.append(
            TutorObservation(
                id=f"thermal_noise_{resistor.id}",
                label=f"{resistor.id} thermal noise",
                value=float(thermal_noise_v),
                unit="V_rms",
                note=(
                    "Educational estimate using sqrt(4*k*T*R*B); it ignores circuit transfer functions, "
                    "correlation, and noise gain."
                ),
            )
        )

    current_source_id = metadata.photodiode_shot_noise_current_id
    if current_source_id:
        current_source = _component_by_id(circuit, current_source_id)
        if (
            current_source is not None
            and current_source.type == "current_source"
            and abs(current_source.value) > 0
        ):
            shot_noise_a = math.sqrt(
                2.0 * ELEMENTARY_CHARGE_C * abs(current_source.value) * bandwidth_hz
            )
            observations.append(
                TutorObservation(
                    id=f"photodiode_shot_noise_{current_source.id}",
                    label=f"{current_source.id} shot noise",
                    value=float(shot_noise_a),
                    unit="A_rms",
                    note="Educational estimate using sqrt(2*q*I*B) for the template photocurrent.",
                )
            )

    if metadata.op_amp_input_noise_nv_per_sqrt_hz is not None:
        input_noise_v = (
            float(metadata.op_amp_input_noise_nv_per_sqrt_hz)
            * 1e-9
            * math.sqrt(bandwidth_hz)
        )
        observations.append(
            TutorObservation(
                id="op_amp_input_referred_noise",
                label="Op-amp input-referred noise",
                value=float(input_noise_v),
                unit="V_rms",
                note=(
                    f"Educational estimate using en*sqrt(BW) with "
                    f"en = {metadata.op_amp_input_noise_nv_per_sqrt_hz:.6g} nV/sqrtHz."
                ),
            )
        )

    observations.append(
        TutorObservation(
            id="noise_budget_boundary",
            label="Noise budget boundary",
            note=(
                "Noise values are starter estimates for teaching. They are not a full integrated noise, "
                "noise-gain, alias-noise, or datasheet-accurate design calculation."
            ),
        )
    )


def _build_ac_filter_observations(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> list[TutorObservation]:
    observations: list[TutorObservation] = []
    topology = circuit.topology_id or circuit.id
    title = circuit.title.lower()
    source_magnitude = _first_ac_source_magnitude(circuit)
    first_answer = _first_ac_answer(packet)

    if packet.frequency_hz is not None:
        observations.append(
            TutorObservation(
                id="analysis_frequency",
                label="Analysis frequency",
                value=float(packet.frequency_hz),
                unit="Hz",
            )
        )

    if first_answer is not None:
        observations.append(
            TutorObservation(
                id="requested_magnitude",
                label="Requested phasor magnitude",
                value=float(first_answer.magnitude),
                unit=first_answer.unit,
            )
        )
        observations.append(
            TutorObservation(
                id="requested_phase",
                label="Requested phasor phase",
                value=float(first_answer.phase_deg),
                unit="deg",
            )
        )

    if first_answer is not None and source_magnitude and source_magnitude > 0:
        observations.append(
            TutorObservation(
                id="transfer_magnitude_ratio",
                label="Output magnitude divided by source magnitude",
                value=float(first_answer.magnitude / source_magnitude),
                unit="V/V",
                note="For these voltage-source templates, the ratio is normalized to the source AC magnitude.",
            )
        )

    if "band_pass" in topology or "band-pass" in title or "band pass" in title:
        observations.append(
            TutorObservation(
                id="filter_behavior",
                label="Filter behavior",
                note="band-pass",
            )
        )
        _add_cutoff_observation(
            observations,
            "high_pass_cutoff_frequency",
            "High-pass corner frequency",
            _cutoff_frequency_hz(_component_by_id(circuit, "RHP"), _component_by_id(circuit, "CHP")),
        )
        _add_cutoff_observation(
            observations,
            "low_pass_cutoff_frequency",
            "Low-pass corner frequency",
            _cutoff_frequency_hz(_component_by_id(circuit, "RLP"), _component_by_id(circuit, "CLP")),
        )
    elif "low_pass" in topology or "low-pass" in title or "low pass" in title:
        observations.append(
            TutorObservation(
                id="filter_behavior",
                label="Filter behavior",
                note="low-pass",
            )
        )
        resistor = next((component for component in circuit.components if component.type == "resistor"), None)
        capacitor = next((component for component in circuit.components if component.type == "capacitor"), None)
        low_pass_cutoff_hz = _cutoff_frequency_hz(resistor, capacitor)
        _add_cutoff_observation(
            observations,
            "low_pass_cutoff_frequency",
            "Low-pass corner frequency",
            low_pass_cutoff_hz,
        )
        observations.append(
            TutorObservation(
                id="first_order_corner_ratio",
                label="First-order corner magnitude ratio",
                value=float(1.0 / math.sqrt(2.0)),
                unit="V/V",
                note="Canonical first-order RC marker included in the packet for tutor explanation.",
            )
        )
        _add_adc_sampling_observations(observations, circuit, low_pass_cutoff_hz)

    _add_noise_budget_observations(observations, circuit)
    return observations


def _build_rc_transient_observations(packet: SolutionPacket) -> list[TutorObservation]:
    response = packet.transient_response
    if response is None:
        return []

    observations = [
        TutorObservation(
            id="time_constant",
            label="Time constant",
            value=float(response.time_constant_s),
            unit="s",
        )
    ]
    tau_sample = next(
        (
            point
            for point in response.sample_points
            if abs(point.time_s - response.time_constant_s) <= max(1e-15, response.time_constant_s * 1e-9)
        ),
        None,
    )
    if tau_sample is not None:
        observations.append(
            TutorObservation(
                id="tau_marker_voltage",
                label="Capacitor voltage at one tau",
                value=float(tau_sample.voltage_v),
                unit="V",
            )
        )
    return observations


def _input_source_pair(
    circuit: CircuitProblem,
    positive_id: str,
    negative_id: str,
) -> tuple[Component, Component] | None:
    positive = _component_by_id(circuit, positive_id)
    negative = _component_by_id(circuit, negative_id)
    if positive is None or negative is None:
        return None
    if positive.type != "voltage_source" or negative.type != "voltage_source":
        return None
    return positive, negative


CMRR_MISMATCH_SCENARIOS = {
    "bme_ecg_front_end": {
        "positive_source_id": "VECGP",
        "negative_source_id": "VECGN",
        "default_mismatch_component_id": "RF",
        "output_node": "ecg_out",
        "reference_node": "0",
    },
    "bme_instrumentation_amplifier": {
        "positive_source_id": "VSENP",
        "negative_source_id": "VSENN",
        "default_mismatch_component_id": "R4",
        "output_node": "inst_out",
        "reference_node": "0",
    },
}


def _first_requested_voltage_answer(packet: SolutionPacket):
    return next(
        (answer for answer in packet.requested_answers.values() if answer.unit == "V"),
        None,
    )


def _add_differential_common_mode_observations(
    observations: list[TutorObservation],
    circuit: CircuitProblem,
) -> None:
    topology = circuit.topology_id or circuit.id
    pair = None
    if topology == "bme_ecg_front_end":
        pair = _input_source_pair(circuit, "VECGP", "VECGN")
    elif topology == "bme_instrumentation_amplifier":
        pair = _input_source_pair(circuit, "VSENP", "VSENN")
    if pair is None:
        return

    positive, negative = pair
    differential_v = positive.value - negative.value
    common_mode_v = 0.5 * (positive.value + negative.value)
    observations.extend(
        [
            TutorObservation(
                id="differential_input_voltage",
                label="Differential input voltage",
                value=float(differential_v),
                unit="V",
                note="Computed from the two input-source values in Circuit IR.",
            ),
            TutorObservation(
                id="common_mode_input_voltage",
                label="Common-mode input voltage",
                value=float(common_mode_v),
                unit="V",
                note="Average of the two input-source values in Circuit IR.",
            ),
        ]
    )
    if common_mode_v != 0:
        observations.append(
            TutorObservation(
                id="differential_to_common_mode_ratio",
                label="Differential/common-mode ratio",
                value=float(abs(differential_v / common_mode_v)),
                unit="V/V",
                note="Shows how small the desired biomedical signal is compared with common-mode level.",
            )
        )


def _add_cmrr_mismatch_observations(
    observations: list[TutorObservation],
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> None:
    topology = circuit.topology_id or circuit.id
    scenario = CMRR_MISMATCH_SCENARIOS.get(topology)
    if scenario is None:
        return

    pair = _input_source_pair(
        circuit,
        str(scenario["positive_source_id"]),
        str(scenario["negative_source_id"]),
    )
    if pair is None:
        return

    positive, negative = pair
    differential_v = positive.value - negative.value
    common_mode_v = 0.5 * (positive.value + negative.value)
    if abs(common_mode_v) <= 1e-15:
        return

    metadata = circuit.bme_metadata
    mismatch_percent = (
        float(metadata.cmrr_mismatch_percent)
        if metadata and metadata.cmrr_mismatch_percent is not None
        else 1.0
    )
    mismatch_component_id = (
        metadata.cmrr_mismatch_component_id
        if metadata and metadata.cmrr_mismatch_component_id
        else str(scenario["default_mismatch_component_id"])
    )
    mismatch_fraction = mismatch_percent / 100.0

    mismatch_problem = circuit.model_copy(deep=True)
    mismatch_pair = _input_source_pair(
        mismatch_problem,
        str(scenario["positive_source_id"]),
        str(scenario["negative_source_id"]),
    )
    mismatch_component = _component_by_id(mismatch_problem, mismatch_component_id)
    if mismatch_pair is None or mismatch_component is None or mismatch_component.type != "resistor":
        return
    if mismatch_component.value <= 0:
        return

    mismatch_pair[0].value = common_mode_v
    mismatch_pair[1].value = common_mode_v
    mismatch_component.value *= 1.0 + mismatch_fraction

    mismatch_result = solve_mna(mismatch_problem)
    if not mismatch_result.success:
        return

    output_node = str(scenario["output_node"])
    reference_node = str(scenario["reference_node"])
    if output_node not in mismatch_result.node_voltages or reference_node not in mismatch_result.node_voltages:
        return

    output_error_v = (
        mismatch_result.node_voltages[output_node]
        - mismatch_result.node_voltages[reference_node]
    )
    observations.extend(
        [
            TutorObservation(
                id="cmrr_mismatch_percent",
                label="CMRR resistor-ratio mismatch what-if",
                value=mismatch_percent,
                unit="%",
                note=f"{mismatch_component_id} is increased by this percentage in a common-mode-only what-if solve.",
            ),
            TutorObservation(
                id="cmrr_common_mode_leakage_output",
                label="Common-mode leakage output",
                value=float(output_error_v),
                unit="V",
                note=(
                    "Solved by setting both inputs to their common-mode value, forcing differential input to 0 V, "
                    f"and increasing {mismatch_component_id} by {mismatch_percent:.6g}%."
                ),
            ),
        ]
    )

    common_mode_gain = output_error_v / common_mode_v
    observations.append(
        TutorObservation(
            id="cmrr_common_mode_leakage_gain",
            label="Common-mode leakage gain",
            value=float(abs(common_mode_gain)),
            unit="V/V",
            note="Magnitude of common-mode-only output error divided by the common-mode input level.",
        )
    )

    requested_voltage = _first_requested_voltage_answer(packet)
    if requested_voltage is None or abs(differential_v) <= 1e-15 or abs(common_mode_gain) <= 1e-15:
        return

    ideal_differential_gain = abs(requested_voltage.value / differential_v)
    cmrr_estimate_db = 20.0 * math.log10(ideal_differential_gain / abs(common_mode_gain))
    observations.append(
        TutorObservation(
            id="cmrr_mismatch_estimate_db",
            label="CMRR mismatch estimate",
            value=float(cmrr_estimate_db),
            unit="dB",
            note=(
                "Teaching estimate from packet differential gain divided by the 1% mismatch common-mode gain; "
                "not a full finite-CMRR or frequency-dependent solver."
            ),
        )
    )


def _add_output_swing_observations(
    observations: list[TutorObservation],
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> None:
    if not any(
        component.type in {"ideal_op_amp", "op_amp_ideal"}
        for component in circuit.components
    ):
        return
    supply_window = _supply_window(circuit)
    if supply_window is None:
        return
    usable_lower, usable_upper, rail_lower, rail_upper, margin = supply_window
    for goal_id, answer in packet.requested_answers.items():
        if answer.unit != "V":
            continue
        if usable_lower <= answer.value <= usable_upper:
            continue
        margin_text = (
            f" with a {margin:.6g} V output-swing margin, so the usable output window is "
            f"{usable_lower:.6g} V to {usable_upper:.6g} V"
            if margin > 0
            else ""
        )
        observations.append(
            TutorObservation(
                id="real_op_amp_saturation_warning",
                label="Real op-amp output swing warning",
                value=float(answer.value),
                unit="V",
                note=(
                    f"The ideal result for {goal_id} is {answer.value:.6g} V; "
                    f"the template's nominal {rail_lower:.6g} V to {rail_upper:.6g} V op-amp rails"
                    f"{margin_text} "
                    "would saturate before reaching this output."
                ),
            )
        )
        return


def _build_bme_dc_observations(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> list[TutorObservation]:
    if circuit.bme_metadata is None:
        return []
    observations: list[TutorObservation] = []
    _add_differential_common_mode_observations(observations, circuit)
    _add_cmrr_mismatch_observations(observations, circuit, packet)
    _add_output_swing_observations(observations, circuit, packet)
    _add_noise_budget_observations(observations, circuit)
    return observations


def _build_tutor_observations(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorObservation]:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return []
    if packet.ac_requested_answers:
        return _build_ac_filter_observations(circuit, packet)
    if packet.transient_response:
        return _build_rc_transient_observations(packet)
    if circuit.bme_metadata is not None:
        return _build_bme_dc_observations(circuit, packet)
    return []


def _attach_tutor_context(circuit: CircuitProblem, packet: SolutionPacket) -> SolutionPacket:
    packet.bme_metadata = circuit.bme_metadata
    packet.tutor_observations = _build_tutor_observations(circuit, packet)
    packet.guided_steps = build_guided_steps(circuit, packet)
    packet.lesson_packet = build_lesson_packet(circuit, packet)
    return packet


def _failed_packet(
    circuit: CircuitProblem,
    status: str,
    message: str,
    checks: list[CheckResult],
    warnings: list[str] | None = None,
    calculation_trace: CalculationTrace | None = None,
) -> SolutionPacket:
    netlist = ""
    try:
        netlist = generate_netlist(circuit)
    except Exception as exc:  # pragma: no cover - defensive only
        warnings = [*(warnings or []), f"Could not generate netlist: {exc}"]

    badge_label = {
        "ambiguous": "AMBIGUOUS",
        "unsupported": "UNSUPPORTED",
    }.get(status, "FAIL")

    return SolutionPacket(
        circuit_id=circuit.id,
        status=status,  # type: ignore[arg-type]
        verification=VerificationReport(
            passed=False,
            checks=[
                *checks,
                CheckResult(name="pipeline", passed=False, message=message),
            ],
        ),
        verification_badge=VerificationBadge(
            label=badge_label,  # type: ignore[arg-type]
            message=message,
        ),
        calculation_trace=calculation_trace or CalculationTrace(),
        generated_netlist=netlist,
        warnings=warnings or [message],
        assumptions_used=circuit.assumptions,
        bme_metadata=circuit.bme_metadata,
    )


def solve_circuit(problem: CircuitProblem, parser_used: str | None = None) -> SolutionPacket:
    validation = validate_circuit(problem)
    circuit = validation.circuit or problem

    if not validation.valid:
        validation_message = "Circuit IR failed validation."
        if validation.errors:
            validation_message += " " + " ".join(validation.errors)
        return _failed_packet(
            circuit=circuit,
            status=validation.status,
            message=validation_message,
            checks=validation.checks,
            warnings=[*validation.warnings, *validation.errors],
            calculation_trace=CalculationTrace(parser_used=parser_used),
        )

    if circuit.analysis_type in {"ac_steady_state", "ac_single_frequency"}:
        solve_result = solve_ac(circuit)
        if not solve_result.success:
            return _failed_packet(
                circuit=circuit,
                status="invalid",
                message=solve_result.message or "AC circuit could not be solved.",
                checks=validation.checks,
                warnings=[
                    *validation.warnings,
                    solve_result.message or "AC circuit could not be solved.",
                ],
                calculation_trace=solve_result.calculation_trace.model_copy(
                    update={"parser_used": parser_used}
                ),
            )

        trace = solve_result.calculation_trace.model_copy(update={"parser_used": parser_used})
        packet = SolutionPacket(
            circuit_id=circuit.id,
            status="solved",
            ac_node_voltages=solve_result.node_voltages,
            ac_component_results=solve_result.component_results,
            ac_requested_answers=solve_result.requested_answers,
            frequency_hz=solve_result.frequency_hz,
            calculation_trace=trace,
            generated_netlist=generate_netlist(circuit),
            warnings=validation.warnings,
            assumptions_used=circuit.assumptions,
        )
        packet.verification = verify_ac_solution(circuit, packet)
        packet.verification_badge = VerificationBadge(
            label="PASS" if packet.verification.passed else "FAIL",
            message=(
                "AC phasor solver output passed validation, complex KCL, finite-value, "
                "and requested-answer checks."
                if packet.verification.passed
                else "AC solver output was produced, but one or more verification checks failed."
            ),
        )
        return _attach_tutor_context(circuit, packet)

    if circuit.analysis_type == "ac_sweep":
        points: list[ACFrequencyPoint] = []
        warnings = [*validation.warnings]
        max_kcl_residual = 0.0
        all_points_passed = True
        trace = CalculationTrace(
            parser_used=parser_used,
            solver_name="internal_ac_mna_v1",
            solver_method="Complex Modified Nodal Analysis sweep",
            answer_source="ac_solver",
            verification_source="ac_verifier.py",
        )

        for frequency in generate_sweep_frequencies(circuit):
            solve_result = solve_ac(circuit, frequency_hz=frequency)
            if not solve_result.success:
                all_points_passed = False
                message = solve_result.message or f"AC sweep point {frequency:g} Hz failed."
                warnings.append(f"{frequency:g} Hz: {message}")
                points.append(
                    ACFrequencyPoint(
                        frequency_hz=frequency,
                        verification=VerificationReport(
                            passed=False,
                            checks=[
                                CheckResult(
                                    name="ac_solve",
                                    passed=False,
                                    message=message,
                                    value=frequency,
                                )
                            ],
                        ),
                    )
                )
                continue

            point_packet = SolutionPacket(
                circuit_id=circuit.id,
                status="solved",
                ac_node_voltages=solve_result.node_voltages,
                ac_component_results=solve_result.component_results,
                ac_requested_answers=solve_result.requested_answers,
                frequency_hz=frequency,
            )
            verification = verify_ac_solution(circuit, point_packet)
            max_kcl_residual = max(max_kcl_residual, verification.max_kcl_residual_a)
            if not verification.passed:
                all_points_passed = False
            points.append(
                ACFrequencyPoint(
                    frequency_hz=frequency,
                    node_voltages=solve_result.node_voltages,
                    component_results=solve_result.component_results,
                    requested_answers=solve_result.requested_answers,
                    verification=verification,
                )
            )

        sweep_checks = [
            *validation.checks,
            CheckResult(
                name="ac_sweep_points_present",
                passed=bool(points),
                message="AC sweep produced frequency points."
                if points
                else "AC sweep produced no frequency points.",
                value=len(points),
            ),
            CheckResult(
                name="ac_sweep_points_passed",
                passed=all_points_passed and bool(points),
                message="Every AC sweep point passed verification."
                if all_points_passed and points
                else "One or more AC sweep points failed solving or verification.",
                value=max_kcl_residual,
            ),
        ]
        verification = VerificationReport(
            passed=all(check.passed for check in sweep_checks),
            max_kcl_residual_a=max_kcl_residual,
            power_balance_error_w=0.0,
            checks=sweep_checks,
        )
        status = "solved" if verification.passed else "invalid"
        packet = SolutionPacket(
            circuit_id=circuit.id,
            status=status,  # type: ignore[arg-type]
            ac_sweep=points,
            verification=verification,
            verification_badge=VerificationBadge(
                label="PASS" if verification.passed else "FAIL",
                message=(
                    "AC sweep passed validation and every frequency point passed AC verification."
                    if verification.passed
                    else "AC sweep was attempted, but one or more points failed."
                ),
            ),
            calculation_trace=trace,
            generated_netlist=generate_netlist(circuit),
            warnings=warnings,
            assumptions_used=circuit.assumptions,
        )
        return _attach_tutor_context(circuit, packet)

    if circuit.analysis_type == "rc_transient":
        solve_result = solve_rc_transient(circuit)
        if not solve_result.success:
            return _failed_packet(
                circuit=circuit,
                status="invalid",
                message=solve_result.message or "RC transient template could not be solved.",
                checks=validation.checks,
                warnings=[
                    *validation.warnings,
                    solve_result.message or "RC transient template could not be solved.",
                ],
                calculation_trace=solve_result.calculation_trace.model_copy(
                    update={"parser_used": parser_used}
                ),
            )

        checks = [
            *validation.checks,
            CheckResult(
                name="rc_transient_template",
                passed=True,
                message=(
                    "First-order RC transient template was generated from initial condition, "
                    "DC final value, and Thevenin resistance."
                ),
                value=solve_result.transient_response.time_constant_s
                if solve_result.transient_response
                else None,
            ),
        ]
        verification = VerificationReport(
            passed=all(check.passed for check in checks),
            checks=checks,
        )
        packet = SolutionPacket(
            circuit_id=circuit.id,
            status="solved" if verification.passed else "invalid",
            requested_answers=solve_result.requested_answers,
            transient_response=solve_result.transient_response,
            verification=verification,
            verification_badge=VerificationBadge(
                label="PASS" if verification.passed else "FAIL",
                message=(
                    "RC transient template passed validation and generated time constant, "
                    "initial/final conditions, and voltage samples."
                    if verification.passed
                    else "RC transient template was produced, but one or more checks failed."
                ),
            ),
            calculation_trace=solve_result.calculation_trace.model_copy(
                update={"parser_used": parser_used}
            ),
            generated_netlist=generate_netlist(circuit),
            warnings=validation.warnings,
            assumptions_used=circuit.assumptions,
        )
        return _attach_tutor_context(circuit, packet)

    if circuit.analysis_type != "dc_operating_point":
        return _failed_packet(
            circuit=circuit,
            status="unsupported",
            message=f"Unsupported analysis type {circuit.analysis_type!r}.",
            checks=validation.checks,
            warnings=[*validation.warnings, f"Unsupported analysis type {circuit.analysis_type!r}."],
            calculation_trace=CalculationTrace(parser_used=parser_used),
        )

    solve_result = solve_mna(circuit)
    if not solve_result.success:
        return _failed_packet(
            circuit=circuit,
            status="invalid",
            message=solve_result.message or "Circuit could not be solved.",
            checks=validation.checks,
            warnings=[*validation.warnings, solve_result.message or "Circuit could not be solved."],
            calculation_trace=solve_result.calculation_trace.model_copy(
                update={"parser_used": parser_used}
            ),
        )

    trace = solve_result.calculation_trace.model_copy(update={"parser_used": parser_used})
    packet = SolutionPacket(
        circuit_id=circuit.id,
        status="solved",
        node_voltages=solve_result.node_voltages,
        component_results=solve_result.component_results,
        requested_answers=solve_result.requested_answers,
        calculation_trace=trace,
        generated_netlist=generate_netlist(circuit),
        warnings=validation.warnings,
        assumptions_used=circuit.assumptions,
    )
    packet.verification = verify_solution(circuit, packet)
    packet.verification_badge = VerificationBadge(
        label="PASS" if packet.verification.passed else "FAIL",
        message=(
            "Solver output passed validation, KCL, power-balance, unit, and requested-answer checks."
            if packet.verification.passed
            else "Solver output was produced, but one or more verification checks failed."
        ),
    )
    return _attach_tutor_context(circuit, packet)
