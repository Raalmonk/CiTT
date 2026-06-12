from __future__ import annotations

from collections.abc import Iterable

from app.models.circuit_ir import CircuitProblem
from app.models.solution_packet import SolutionPacket, TutorFocus, TutorObservation, TutorStep


def _topology(circuit: CircuitProblem) -> str:
    return circuit.topology_id or circuit.id


def _focus(
    circuit: CircuitProblem,
    components: Iterable[str] = (),
    nodes: Iterable[str] = (),
    current_paths: Iterable[str] = (),
    goals: Iterable[str] = (),
) -> TutorFocus:
    component_ids = {component.id for component in circuit.components}
    node_ids = set(circuit.nodes)
    goal_ids = {goal.id for goal in circuit.goals}
    return TutorFocus(
        components=[item for item in components if item in component_ids],
        nodes=[item for item in nodes if item in node_ids],
        current_paths=[item for item in current_paths if item in component_ids],
        goals=[item for item in goals if item in goal_ids],
    )


def _observations(packet: SolutionPacket) -> dict[str, TutorObservation]:
    return {observation.id: observation for observation in packet.tutor_observations}


def _observation(packet: SolutionPacket, observation_id: str) -> TutorObservation | None:
    return _observations(packet).get(observation_id)


def _only_present(values: Iterable[TutorObservation | None]) -> list[TutorObservation]:
    return [value for value in values if value is not None]


def _node_voltage(packet: SolutionPacket, node_id: str, label: str | None = None) -> TutorObservation | None:
    if node_id not in packet.node_voltages:
        return None
    return TutorObservation(
        id=f"node_voltage_{node_id}",
        label=label or f"Node {node_id} voltage",
        value=float(packet.node_voltages[node_id]),
        unit="V",
        note="Verified node voltage from the Solution Packet.",
    )


def _requested_answer(packet: SolutionPacket, answer_id: str, label: str | None = None) -> TutorObservation | None:
    answer = packet.requested_answers.get(answer_id)
    if answer is None:
        return None
    return TutorObservation(
        id=answer_id,
        label=label or answer_id.replace("_", " "),
        value=float(answer.value),
        unit=answer.unit,
        note="Requested answer from the verified Solution Packet.",
    )


def _ac_answer_magnitude(
    packet: SolutionPacket,
    answer_id: str,
    label: str | None = None,
) -> TutorObservation | None:
    answer = packet.ac_requested_answers.get(answer_id)
    if answer is None:
        return None
    return TutorObservation(
        id=f"{answer_id}_magnitude",
        label=label or f"{answer_id.replace('_', ' ')} magnitude",
        value=float(answer.magnitude),
        unit=answer.unit,
        note="Requested AC answer magnitude from the verified Solution Packet.",
    )


def _ac_answer_phase(packet: SolutionPacket, answer_id: str) -> TutorObservation | None:
    answer = packet.ac_requested_answers.get(answer_id)
    if answer is None:
        return None
    return TutorObservation(
        id=f"{answer_id}_phase",
        label=f"{answer_id.replace('_', ' ')} phase",
        value=float(answer.phase_deg),
        unit="deg",
        note="Requested AC answer phase from the verified Solution Packet.",
    )


def _verification_observations(packet: SolutionPacket) -> list[TutorObservation]:
    label = packet.verification_badge.label
    values = [
        TutorObservation(
            id="internal_verification_status",
            label="Internal verification",
            note=label,
        ),
        TutorObservation(
            id="reference_cross_check_status",
            label="Reference cross-check",
            note="not available",
        ),
    ]
    if packet.verification.max_kcl_residual_a is not None:
        values.append(
            TutorObservation(
                id="max_kcl_residual",
                label="Max KCL residual",
                value=float(packet.verification.max_kcl_residual_a),
                unit="A",
                note="Internal circuit-law residual check.",
            )
        )
    if packet.verification.power_balance_error_w is not None:
        values.append(
            TutorObservation(
                id="power_balance_error",
                label="Power-balance error",
                value=float(packet.verification.power_balance_error_w),
                unit="W",
                note="Internal power-balance check when applicable.",
            )
        )
    return values


def _first_source(circuit: CircuitProblem) -> str | None:
    for component in circuit.components:
        if component.type in {"voltage_source", "current_source"}:
            return component.id
    return None


def _first_component_of_type(circuit: CircuitProblem, component_type: str) -> str | None:
    for component in circuit.components:
        if component.type == component_type:
            return component.id
    return None


def _voltage_divider_steps(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorStep]:
    return [
        TutorStep(
            id="voltage_divider_reference",
            title="Anchor the source and reference node",
            body=(
                "The source fixes the top node relative to ground. That gives the divider a clear voltage "
                "reference before any resistor math starts."
            ),
            focus=_focus(circuit, components=["V1"], nodes=["n1", "0"], current_paths=["V1"]),
            verified_values=_only_present([_node_voltage(packet, "n1", "Top node voltage")]),
            next_action="Follow the same series current through R1 and R2.",
        ),
        TutorStep(
            id="voltage_divider_series_current",
            title="Follow the series current",
            body=(
                "R1 and R2 are in one path, so the solved current through R1 is the same divider current "
                "that continues through R2."
            ),
            focus=_focus(circuit, components=["R1", "R2"], nodes=["n1", "n2", "0"], current_paths=["R1", "R2"]),
            verified_values=_only_present(
                [_requested_answer(packet, "circuit_current", "Circuit current")]
            ),
            next_action="Use the current and R2 reference to read the requested output.",
        ),
        TutorStep(
            id="voltage_divider_output",
            title="Read the divider output",
            body=(
                "The requested voltage across R2 is measured from node n2 to ground. The highlighted node is "
                "the output of this divider."
            ),
            focus=_focus(circuit, components=["R2"], nodes=["n2", "0"], current_paths=["R2"], goals=["voltage_across_R2"]),
            verified_values=_only_present(
                [
                    _requested_answer(packet, "voltage_across_R2", "Voltage across R2"),
                    _node_voltage(packet, "n2", "Output node voltage"),
                ]
            ),
            next_action="Check what the PASS badge does and does not mean.",
        ),
        TutorStep(
            id="voltage_divider_verification_boundary",
            title="Inspect the verification boundary",
            body=(
                "This result is internally verified and inspectable: the solver, KCL residual, power balance, "
                "and requested answers agree. It is not claiming an independent external oracle yet."
            ),
            focus=_focus(circuit, components=["R1", "R2"], nodes=["n2"], goals=["voltage_across_R2", "circuit_current"]),
            verified_values=_verification_observations(packet),
            caution="Reference cross-check is reported separately from internal verification.",
        ),
    ]


def _ecg_front_end_steps(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorStep]:
    return [
        TutorStep(
            id="ecg_signal_sources",
            title="Identify the biomedical signal",
            body=(
                "The ECG information is not either electrode voltage by itself. It is the difference between "
                "the two electrode source potentials."
            ),
            focus=_focus(circuit, components=["VECGP", "VECGN"], nodes=["ecg_p", "ecg_n"]),
            verified_values=_only_present(
                [
                    _observation(packet, "differential_input_voltage"),
                    _observation(packet, "common_mode_input_voltage"),
                ]
            ),
            next_action="Separate the tiny differential signal from the larger common-mode level.",
        ),
        TutorStep(
            id="ecg_diff_common_mode",
            title="Separate differential and common-mode input",
            body=(
                "The desired ECG signal is the input difference, while the common-mode level is the average "
                "of the two electrode sources."
            ),
            focus=_focus(circuit, components=["VECGP", "VECGN"], nodes=["ecg_p", "ecg_n"]),
            verified_values=_only_present(
                [
                    _observation(packet, "differential_input_voltage"),
                    _observation(packet, "common_mode_input_voltage"),
                    _observation(packet, "differential_to_common_mode_ratio"),
                ]
            ),
            next_action="Trace the amplifier network that scales the differential input.",
        ),
        TutorStep(
            id="ecg_feedback_network",
            title="Follow the differential amplifier",
            body=(
                "The matched input and feedback resistors set the ideal differential gain. The op-amp model "
                "is ideal, so the lesson is about the topology and verified packet values."
            ),
            focus=_focus(
                circuit,
                components=["RINP", "RINN", "RF", "RREF", "U1"],
                nodes=["amp_plus", "amp_minus", "ecg_out"],
                current_paths=["RINP", "RINN", "RF", "RREF"],
            ),
            verified_values=[],
            next_action="Read the verified output node.",
        ),
        TutorStep(
            id="ecg_output",
            title="Read the verified output",
            body=(
                "The output node is the solver-backed answer for this ideal front-end. This is the number to "
                "connect back to the ECG gain story."
            ),
            focus=_focus(circuit, components=["U1", "RF"], nodes=["ecg_out"], current_paths=["RF"], goals=["ecg_front_end_output"]),
            verified_values=_only_present(
                [_requested_answer(packet, "ecg_front_end_output", "ECG front-end output")]
            ),
            next_action="Keep the ideal result separate from real patient-connected hardware constraints.",
        ),
        TutorStep(
            id="ecg_real_world_warning",
            title="Add the real-world warning",
            body=(
                "The ideal circuit demonstrates differential gain. Real ECG front ends also need isolation, "
                "input protection, finite-CMRR analysis, and resistor-ratio tolerance checks."
            ),
            focus=_focus(circuit, components=["U1", "RF"], nodes=["ecg_out"]),
            verified_values=_only_present(
                [
                    _observation(packet, "cmrr_mismatch_percent"),
                    _observation(packet, "cmrr_common_mode_leakage_output"),
                    _observation(packet, "cmrr_mismatch_estimate_db"),
                ]
            ),
            caution="Patient-connected ECG circuits require medical-safety isolation and leakage-current controls.",
        ),
    ]


def _low_pass_steps(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorStep]:
    topology = _topology(circuit)
    source_id = "VADC" if topology == "bme_anti_aliasing_low_pass" else (_first_source(circuit) or "V1")
    output_answer = "anti_aliasing_output" if topology == "bme_anti_aliasing_low_pass" else "vout"
    values_for_output = _only_present(
        [
            _ac_answer_magnitude(packet, output_answer, "Output magnitude"),
            _ac_answer_phase(packet, output_answer),
            _observation(packet, "requested_magnitude"),
            _observation(packet, "requested_phase"),
        ]
    )
    adc_values = _only_present(
        [
            _observation(packet, "adc_sampling_frequency"),
            _observation(packet, "adc_nyquist_frequency"),
            _observation(packet, "adc_attenuation_at_nyquist"),
            _observation(packet, "adc_input_loading_ratio"),
        ]
    )

    steps = [
        TutorStep(
            id="low_pass_signal_path",
            title="Start with the signal path",
            body=(
                "The source drives R1, and the output is read at the node shared by R1 and C1."
            ),
            focus=_focus(circuit, components=[source_id, "R1"], nodes=["in", "out"], current_paths=[source_id, "R1"]),
            verified_values=_only_present([_observation(packet, "analysis_frequency")]),
            next_action="Look at how the capacitor creates the low-pass behavior.",
        ),
        TutorStep(
            id="low_pass_pole",
            title="Locate the RC pole",
            body=(
                "R1 and C1 set the first-order corner. Above the corner, more signal is shunted through the "
                "capacitor instead of appearing at the output node."
            ),
            focus=_focus(circuit, components=["R1", "C1"], nodes=["out", "0"], current_paths=["R1", "C1"]),
            verified_values=_only_present(
                [
                    _observation(packet, "low_pass_cutoff_frequency"),
                    _observation(packet, "first_order_corner_ratio"),
                ]
            ),
            next_action="Read the phasor output at the requested frequency.",
        ),
        TutorStep(
            id="low_pass_output",
            title="Read the verified output phasor",
            body=(
                "The output is a magnitude and phase at the analysis frequency, not a DC voltage."
            ),
            focus=_focus(circuit, components=["R1", "C1"], nodes=["out", "0"], current_paths=["C1"], goals=[output_answer]),
            verified_values=values_for_output,
            next_action="Connect the filter result to the surrounding measurement system.",
        ),
    ]
    if topology == "bme_anti_aliasing_low_pass":
        steps.append(
            TutorStep(
                id="anti_aliasing_adc_context",
                title="Connect the pole to ADC sampling",
                body=(
                    "The RC pole helps reduce high-frequency content before sampling, but a single pole does "
                    "not prove alias-free measurement."
                ),
                focus=_focus(circuit, components=["R1", "C1"], nodes=["out", "0"]),
                verified_values=adc_values,
                caution="ADC input impedance, sampling capacitance, and required stop-band attenuation still need hardware checks.",
            )
        )
    return steps


def _photodiode_tia_steps(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorStep]:
    return [
        TutorStep(
            id="tia_photodiode_current",
            title="Start from photocurrent",
            body=(
                "The photodiode is modeled as a current source. That current is the signal before the circuit "
                "turns it into a voltage."
            ),
            focus=_focus(circuit, components=["IPD"], nodes=["sum", "0"], current_paths=["IPD"], goals=["photodiode_current"]),
            verified_values=_only_present(
                [_requested_answer(packet, "photodiode_current", "Photodiode current")]
            ),
            next_action="Move to the summing node at the op-amp input.",
        ),
        TutorStep(
            id="tia_summing_node",
            title="Inspect the summing node",
            body=(
                "In the ideal op-amp model, feedback holds the inverting input near the reference input. "
                "This makes the summing node the place where current balance matters."
            ),
            focus=_focus(circuit, components=["U1", "IPD", "RF"], nodes=["sum", "0"], current_paths=["IPD", "RF"]),
            verified_values=_only_present([_node_voltage(packet, "sum", "Summing-node voltage")]),
            next_action="Follow that current through the feedback resistor.",
        ),
        TutorStep(
            id="tia_feedback_conversion",
            title="Convert current through feedback",
            body=(
                "RF turns input current into output voltage. The larger RF is, the larger the ideal "
                "transimpedance gain and the more important offsets and noise become."
            ),
            focus=_focus(circuit, components=["RF", "U1"], nodes=["sum", "out"], current_paths=["RF"]),
            verified_values=_only_present([_requested_answer(packet, "tia_output", "TIA output")]),
            next_action="Check whether the ideal output fits real rails.",
        ),
        TutorStep(
            id="tia_real_world_limits",
            title="Check real amplifier limits",
            body=(
                "The ideal solver can report a large output. A real single-supply op-amp may saturate before "
                "reaching that value."
            ),
            focus=_focus(circuit, components=["U1", "RF"], nodes=["out"]),
            verified_values=_only_present(
                [
                    _observation(packet, "real_op_amp_saturation_warning"),
                    _observation(packet, "noise_budget_bandwidth"),
                    _observation(packet, "photodiode_shot_noise_IPD"),
                    _observation(packet, "thermal_noise_RF"),
                ]
            ),
            caution="The ideal op-amp result is a teaching calculation, not a rail-to-rail hardware guarantee.",
        ),
    ]


def _generic_steps(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorStep]:
    component_focus: list[str] = []
    node_focus: list[str] = []
    goal_ids: list[str] = []
    for goal in circuit.goals:
        goal_ids.append(goal.id)
        if goal.quantity == "node_voltage":
            node_focus.append(goal.target)
        else:
            component_focus.append(goal.target)

    requested_values = [
        TutorObservation(
            id=answer_id,
            label=answer_id.replace("_", " "),
            value=float(answer.value),
            unit=answer.unit,
            note="Requested answer from the verified Solution Packet.",
        )
        for answer_id, answer in packet.requested_answers.items()
    ]
    requested_values.extend(
        TutorObservation(
            id=f"{answer_id}_magnitude",
            label=f"{answer_id.replace('_', ' ')} magnitude",
            value=float(answer.magnitude),
            unit=answer.unit,
            note="Requested AC answer magnitude from the verified Solution Packet.",
        )
        for answer_id, answer in packet.ac_requested_answers.items()
    )

    return [
        TutorStep(
            id="generic_focus_requested_goal",
            title="Focus on the requested goal",
            body=(
                "This circuit does not have a specialized lesson template yet, so the guided view starts with "
                "the requested target and the verified answer."
            ),
            focus=_focus(circuit, components=component_focus, nodes=node_focus, current_paths=component_focus, goals=goal_ids),
            verified_values=requested_values,
            next_action="Use the advanced panels if you need full solver trace details.",
        ),
        TutorStep(
            id="generic_verification_boundary",
            title="Inspect the verification boundary",
            body=(
                "The packet is internally verified and inspectable. Independent reference cross-checking is "
                "reported separately when available."
            ),
            focus=_focus(circuit, components=component_focus, nodes=node_focus, goals=goal_ids),
            verified_values=_verification_observations(packet),
        ),
    ]


def build_guided_steps(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorStep]:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return []

    topology = _topology(circuit)
    if topology == "voltage_divider":
        return _voltage_divider_steps(circuit, packet)
    if topology == "bme_ecg_front_end":
        return _ecg_front_end_steps(circuit, packet)
    if topology in {"rc_low_pass", "bme_anti_aliasing_low_pass"}:
        return _low_pass_steps(circuit, packet)
    if topology == "bme_photodiode_tia":
        return _photodiode_tia_steps(circuit, packet)
    return _generic_steps(circuit, packet)
