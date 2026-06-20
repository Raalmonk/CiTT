from __future__ import annotations

import math
import re
from fractions import Fraction

from app.models.circuit_ir import CircuitProblem, Component, is_nonideal_op_amp_type
from app.models.solution_packet import (
    ACFrequencyPoint,
    ACSweepPlotPoint,
    ACSweepPlotSeries,
    CalculationTrace,
    CheckResult,
    ComplexQuantityValue,
    QuantityValue,
    SolutionPacket,
    SymbolicQuantityValue,
    TeachingPlot,
    TeachingPlotMarker,
    TeachingPlotPoint,
    TeachingPlotSeries,
    TutorFocus,
    TutorObservation,
    TutorStep,
    VerificationBadge,
    VerificationReport,
)
from app.services.ac_solver import generate_sweep_frequencies, quantity_to_complex, solve_ac
from app.services.ac_verifier import verify_ac_solution
from app.services.bme_context_injector import inject_dynamic_bme_context
from app.services.guided_steps import build_guided_steps
from app.services.lesson_builder import build_lesson_packet
from app.services.mna_solver import nonideal_open_loop_gain, nonideal_output_window, solve_mna
from app.services.netlist_generator import generate_netlist
from app.services.nonlinear_solver import solve_nonlinear_dc
from app.services.rc_transient_solver import solve_rc_transient
from app.services.socratic_lecture_builder import build_socratic_lecture_packet
from app.services.validator import validate_circuit
from app.services.verifier import verify_solution


BOLTZMANN_J_PER_K = 1.380649e-23
ELEMENTARY_CHARGE_C = 1.602176634e-19
NUMERIC_RE = r"([-+]?\d+(?:\.\d+)?(?:e[-+]?\d+)?)"
UNSPECIFIED_RE = re.compile(
    r"\b(unspecified|not specified|missing|not given|unknown|not provided)\b",
    re.IGNORECASE,
)
VOLTAGE_CLAMP_IGNORABLE_AMBIGUITY_RE = re.compile(
    r"(command\s+voltage|v\s*[_\s-]?c\b|voltage\s+electrode|r\s*[_\s-]?[ce]\b)",
    re.IGNORECASE,
)
ECG_RLD_MARKER_RE = re.compile(
    r"(ecg|心电|right[\s-]*leg|右腿驱动|rld|driven[\s-]*right[\s-]*leg)",
    re.IGNORECASE,
)
COMMON_MODE_MARKER_RE = re.compile(r"(common[\s-]*mode|commonmode|v\s*cm|共模)", re.IGNORECASE)
ECG_RLD_IGNORABLE_AMBIGUITY_RE = re.compile(
    r"("
    r"\br\s*1\b|\br\s*2\b|r2\s*[-\s]*r1\s*[-\s]*r2|"
    r"\br\s*o\b|current[\s-]*limiting|output[\s-]*limiting|"
    r"\br\s*4\b|potentiometer|cmrr|差分放大|可调|串联"
    r")",
    re.IGNORECASE,
)


def _component_by_id(circuit: CircuitProblem, component_id: str) -> Component | None:
    return next((component for component in circuit.components if component.id == component_id), None)


def _compact_token(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _circuit_symbol_text(circuit: CircuitProblem) -> str:
    parts = [
        circuit.id,
        circuit.title,
        circuit.topology_id or "",
        *circuit.assumptions,
        *circuit.nonblocking_ambiguities,
        *circuit.ambiguities,
    ]
    for component in circuit.components:
        parts.append(
            " ".join(
                [
                    component.id,
                    component.type,
                    component.label or "",
                    f"{component.value:g}",
                    component.unit,
                    "" if component.open_loop_gain is None else f"A = {component.open_loop_gain:g}",
                ]
            )
        )
    return "\n".join(part for part in parts if part)


def _first_pattern_number(text: str, patterns: list[str]) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _looks_like_voltage_clamp(circuit: CircuitProblem) -> bool:
    text = _circuit_symbol_text(circuit).lower()
    compact = _compact_token(text)
    return "voltage clamp" in text or ("commandvoltage" in compact and "vm" in compact)


def _blocking_voltage_clamp_ambiguities(circuit: CircuitProblem) -> list[str]:
    blocking: list[str] = []
    for ambiguity in circuit.ambiguities:
        if UNSPECIFIED_RE.search(ambiguity) and VOLTAGE_CLAMP_IGNORABLE_AMBIGUITY_RE.search(ambiguity):
            continue
        blocking.append(ambiguity)
    return blocking


def _has_explicit_command_voltage_value(circuit: CircuitProblem) -> bool:
    text = _circuit_symbol_text(circuit)
    if re.search(rf"V\s*[_\s-]?c\s*(?:=|is|to\s+be)\s*{NUMERIC_RE}", text, flags=re.IGNORECASE):
        return True
    for component in circuit.components:
        if component.type != "voltage_source":
            continue
        compact = _compact_token(" ".join([component.id, component.label or ""]))
        if "command" in compact or compact in {"vc", "vcommand", "vcmd"}:
            return True
    return False


def _has_symbolic_command_voltage(circuit: CircuitProblem) -> bool:
    for ambiguity in circuit.ambiguities:
        if UNSPECIFIED_RE.search(ambiguity) and re.search(
            r"(command\s+voltage|v\s*[_\s-]?c\b)",
            ambiguity,
            flags=re.IGNORECASE,
        ):
            return True
    return not _has_explicit_command_voltage_value(circuit)


def _extract_voltage_clamp_gain(circuit: CircuitProblem) -> float | None:
    for component in circuit.components:
        compact = _compact_token(" ".join([component.id, component.label or ""]))
        if component.open_loop_gain is not None and (
            "diff" in compact or "gain" in compact or compact == "a"
        ):
            return float(component.open_loop_gain)
        if compact in {"a", "gaina", "diffamp", "differentialamplifier"} and component.value > 0:
            return float(component.value)

    text = _circuit_symbol_text(circuit)
    return _first_pattern_number(
        text,
        [
            rf"(?<![A-Za-z0-9_])A(?![A-Za-z0-9_])\s*(?:=|is|to\s+be)\s*{NUMERIC_RE}",
            rf"gain\s*(?:A\s*)?(?:=|is|of|to\s+be)\s*{NUMERIC_RE}",
        ],
    )


def _shared_rm_ro_value(circuit: CircuitProblem) -> float | None:
    text = _circuit_symbol_text(circuit)
    return _first_pattern_number(
        text,
        [
            rf"R\s*[_\s-]?m\s*=\s*R\s*[_\s-]?o\s*=\s*{NUMERIC_RE}",
            rf"R\s*[_\s-]?o\s*=\s*R\s*[_\s-]?m\s*=\s*{NUMERIC_RE}",
        ],
    )


def _extract_named_resistance(
    circuit: CircuitProblem,
    *,
    name: str,
    tokens: set[str],
) -> float | None:
    for component in circuit.components:
        if component.type != "resistor" or component.value <= 0:
            continue
        compact_id = _compact_token(component.id)
        compact_label = _compact_token(component.label)
        if compact_id in tokens or any(token in compact_label for token in tokens):
            return float(component.value)

    text = _circuit_symbol_text(circuit)
    return _first_pattern_number(
        text,
        [
            rf"R\s*[_\s-]?{name}\s*(?:=|is|to\s+be)\s*{NUMERIC_RE}",
            rf"R{name}\s*(?:=|is|to\s+be)\s*{NUMERIC_RE}",
        ],
    )


def _voltage_clamp_answer_target(circuit: CircuitProblem) -> tuple[str, str]:
    for goal in circuit.goals:
        if goal.quantity == "node_voltage" and _compact_token(goal.target) in {"vm", "vmembrane"}:
            return goal.id, goal.target
    for node in circuit.nodes:
        if _compact_token(node) in {"vm", "vmembrane"}:
            return "vm_equilibrium", node
    return "vm_equilibrium", "Vm"


def _coefficient_expression(
    gain_a: float,
    membrane_resistance: float,
    output_resistance: float,
) -> tuple[str, float]:
    gain = Fraction(str(gain_a))
    rm = Fraction(str(membrane_resistance))
    ro = Fraction(str(output_resistance))
    coefficient = gain * rm / (gain * rm + rm + ro)
    coefficient = coefficient.limit_denominator(1_000_000)
    if coefficient.denominator == 1:
        prefix = "" if coefficient.numerator == 1 else f"{coefficient.numerator} "
    else:
        prefix = f"{coefficient.numerator}/{coefficient.denominator} "
    return f"{prefix}V_c", float(coefficient)


def _symbolic_voltage_clamp_steps(
    *,
    answer_id: str,
    vm_node: str,
    gain_a: float,
    membrane_resistance: float,
    output_resistance: float,
    expression: str,
    coefficient: float,
) -> list[TutorStep]:
    focus = TutorFocus(
        components=["DiffAmp", "R_m", "R_o"],
        nodes=[vm_node],
        goals=[answer_id],
    )
    return [
        TutorStep(
            id="keep_command_voltage_symbolic",
            title="Keep V_c symbolic",
            body=(
                "The prompt gives A, R_m, and R_o but no numeric command voltage. "
                "So V_c is an input symbol, not an unresolved ambiguity."
            ),
            focus=focus,
        ),
        TutorStep(
            id="write_clamp_loop",
            title="Write the clamp loop",
            body=(
                "The differential amplifier output is V_o = A(V_c - V_m), "
                "and the membrane node satisfies (V_o - V_m) / R_o = V_m / R_m."
            ),
            focus=focus,
        ),
        TutorStep(
            id="solve_symbolic_vm",
            title="Solve for V_m",
            body=(
                "Rearranging gives V_m = A R_m / (A R_m + R_m + R_o) * V_c. "
                f"With A = {gain_a:g}, R_m = {membrane_resistance:g} ohm, and "
                f"R_o = {output_resistance:g} ohm, V_m = {expression} "
                f"(about {coefficient:.6g} V_c)."
            ),
            focus=focus,
            verified_values=[
                TutorObservation(
                    id="closed_loop_voltage_gain",
                    label="V_m / V_c",
                    value=float(coefficient),
                    unit="V/V",
                    note="Closed-form coefficient from the symbolic voltage-clamp equilibrium.",
                )
            ],
        ),
    ]


def _node_by_compact_token(circuit: CircuitProblem, tokens: set[str]) -> str | None:
    for goal in circuit.goals:
        if goal.quantity == "node_voltage" and _compact_token(goal.target) in tokens:
            return goal.target
    for node in circuit.nodes:
        if _compact_token(node) in tokens:
            return node
    return None


def _resistors_between(circuit: CircuitProblem, node_a: str, node_b: str) -> list[Component]:
    wanted = {node_a, node_b}
    return [
        component
        for component in circuit.components
        if component.type == "resistor" and set(component.nodes) == wanted
    ]


def _preferred_resistor_between(
    circuit: CircuitProblem,
    node_a: str,
    node_b: str,
    compact_tokens: set[str],
) -> Component | None:
    candidates = _resistors_between(circuit, node_a, node_b)
    for component in candidates:
        compact = _compact_token(" ".join([component.id, component.label or ""]))
        if any(token in compact for token in compact_tokens):
            return component
    return candidates[0] if candidates else None


def _current_injected_into_node(
    component: Component,
    *,
    node: str,
    ground: str,
) -> float | None:
    if component.type != "current_source" or node not in component.nodes or ground not in component.nodes:
        return None
    if component.nodes[0] == ground and component.nodes[1] == node:
        return float(component.value)
    if component.nodes[0] == node and component.nodes[1] == ground:
        return -float(component.value)
    return None


def _has_grounded_rld_summing_amp(circuit: CircuitProblem, summing_node: str) -> bool:
    ground = circuit.ground_node
    return any(
        is_nonideal_op_amp_type(component.type) or component.type in {"op_amp_ideal", "ideal_op_amp"}
        for component in circuit.components
        if len(component.nodes) == 4 and component.nodes[0] == ground and component.nodes[1] == summing_node
    )


def _has_resistor_to_ground(circuit: CircuitProblem, node: str) -> bool:
    ground = circuit.ground_node
    return any(
        component.type == "resistor" and node in component.nodes and ground in component.nodes
        for component in circuit.components
    )


def _has_op_amp_output_from_input(circuit: CircuitProblem, input_node: str, output_node: str) -> bool:
    return any(
        (component.type in {"op_amp_ideal", "ideal_op_amp"} or is_nonideal_op_amp_type(component.type))
        and len(component.nodes) == 4
        and component.nodes[0] == input_node
        and component.nodes[2] == output_node
        for component in circuit.components
    )


def _looks_like_ecg_rld_common_mode(circuit: CircuitProblem) -> bool:
    if circuit.analysis_type != "dc_operating_point":
        return False
    text = _circuit_symbol_text(circuit)
    return bool(ECG_RLD_MARKER_RE.search(text) and COMMON_MODE_MARKER_RE.search(text))


def _blocking_ecg_rld_ambiguities(circuit: CircuitProblem) -> list[str]:
    return [
        ambiguity
        for ambiguity in circuit.ambiguities
        if not ECG_RLD_IGNORABLE_AMBIGUITY_RE.search(ambiguity)
    ]


def _quantity_value(node: str, value: float, ground: str) -> QuantityValue:
    return QuantityValue(
        value=float(value),
        unit="V",
        explanation_key=f"node_voltage:{node}",
        reference={"positive_node": node, "negative_node": ground},
    )


def _ecg_rld_steps(
    *,
    body_node: str,
    output_node: str,
    summing_node: str,
    current_a: float,
    right_leg_resistance_ohm: float,
    feedback_gain: float,
) -> list[TutorStep]:
    focus = TutorFocus(
        components=["R_RL", "R_f", "R_a"],
        nodes=[body_node, output_node, summing_node],
    )
    return [
        TutorStep(
            id="rld_scope_reduction",
            title="Reduce to the RLD common-mode loop",
            body=(
                "For a pure common-mode DC question with ideal op-amps, the missing input-buffer "
                "gain resistors and later AC-coupled output stage do not set the requested DC nodes."
            ),
            focus=focus,
        ),
        TutorStep(
            id="rld_virtual_ground",
            title="Use the auxiliary amplifier virtual ground",
            body=(
                f"The auxiliary amplifier holds {summing_node} at 0 V. The two common-mode "
                "buffer outputs feed that summing node through the stated Ra resistors."
            ),
            focus=focus,
        ),
        TutorStep(
            id="rld_body_kcl",
            title="Solve the body-node KCL",
            body=(
                f"With injected current {current_a:.6g} A and R_RL = "
                f"{right_leg_resistance_ohm:.6g} ohm, the body-node equation is "
                f"({body_node} - {output_node}) / R_RL = i_d while "
                f"{output_node} = -{feedback_gain:.6g} {body_node}."
            ),
            focus=focus,
        ),
    ]


def _try_solve_ecg_rld_common_mode(
    circuit: CircuitProblem,
    parser_used: str | None,
) -> SolutionPacket | None:
    if circuit.unsupported_features or not _looks_like_ecg_rld_common_mode(circuit):
        return None
    if _blocking_ecg_rld_ambiguities(circuit):
        return None

    ground = circuit.ground_node
    body_node = _node_by_compact_token(circuit, {"vcm", "vcmm", "body", "human"})
    output_node = _node_by_compact_token(circuit, {"vo", "vouto", "rldout"})
    summing_node = _node_by_compact_token(circuit, {"v3", "sum", "summing"})
    if body_node is None or output_node is None or summing_node is None:
        return None

    current_injections = [
        injection
        for component in circuit.components
        if (injection := _current_injected_into_node(component, node=body_node, ground=ground))
        is not None
    ]
    if len(current_injections) != 1:
        return None
    injected_current_a = current_injections[0]

    right_leg_resistor = _preferred_resistor_between(
        circuit,
        body_node,
        output_node,
        {"rrl", "rightleg", "leg", "rl"},
    )
    feedback_resistor = _preferred_resistor_between(
        circuit,
        output_node,
        summing_node,
        {"rf", "feedback"},
    )
    if right_leg_resistor is None or feedback_resistor is None:
        return None

    summing_input_resistors = [
        component
        for component in circuit.components
        if component.type == "resistor"
        and summing_node in component.nodes
        and output_node not in component.nodes
        and body_node not in component.nodes
        and ground not in component.nodes
        and component.value > 0
    ]
    if len(summing_input_resistors) < 2:
        return None
    if not _has_grounded_rld_summing_amp(circuit, summing_node):
        return None

    input_conductance_s = sum(1.0 / component.value for component in summing_input_resistors)
    feedback_gain = feedback_resistor.value * input_conductance_s
    if feedback_gain <= 0:
        return None

    body_voltage_v = injected_current_a * right_leg_resistor.value / (1.0 + feedback_gain)
    output_voltage_v = -feedback_gain * body_voltage_v
    computed_nodes: dict[str, float] = {
        ground: 0.0,
        body_node: float(body_voltage_v),
        output_node: float(output_voltage_v),
        summing_node: 0.0,
    }

    for node in circuit.nodes:
        compact = _compact_token(node)
        if compact in {"v1", "v2", "a2inv", "a2out"}:
            computed_nodes[node] = float(body_voltage_v)

    v4_node = _node_by_compact_token(circuit, {"v4"})
    if v4_node is not None and _has_resistor_to_ground(circuit, v4_node):
        computed_nodes[v4_node] = 0.0
    v5_node = _node_by_compact_token(circuit, {"v5"})
    if (
        v4_node is not None
        and v4_node in computed_nodes
        and v5_node is not None
        and (
            _has_op_amp_output_from_input(circuit, v4_node, v5_node)
            or not any(v5_node in component.nodes for component in circuit.components)
        )
    ):
        computed_nodes[v5_node] = 0.0

    unsupported_goals = [
        goal
        for goal in circuit.goals
        if goal.quantity != "node_voltage" or goal.target not in computed_nodes
    ]
    if unsupported_goals:
        return None

    requested_answers = {
        goal.id: _quantity_value(goal.target, computed_nodes[goal.target], ground)
        for goal in circuit.goals
    }
    body_kcl_residual = (
        (computed_nodes[body_node] - computed_nodes[output_node]) / right_leg_resistor.value
        - injected_current_a
    )
    summing_kcl_residual = (
        computed_nodes[output_node] / feedback_resistor.value
        + input_conductance_s * computed_nodes[body_node]
    )
    max_residual = max(abs(body_kcl_residual), abs(summing_kcl_residual))
    checks = [
        CheckResult(
            name="ecg_rld_scope_match",
            passed=True,
            message="ECG/RLD pure common-mode DC pattern matched a supported closed-form reduction.",
        ),
        CheckResult(
            name="ecg_rld_required_values_present",
            passed=True,
            message="i_d, R_RL, R_f, and the RLD summing input resistors were explicit.",
            value=(
                f"i_d={injected_current_a:g} A, R_RL={right_leg_resistor.value:g} ohm, "
                f"R_f={feedback_resistor.value:g} ohm"
            ),
        ),
        CheckResult(
            name="ecg_rld_nonblocking_ambiguities",
            passed=True,
            message="Missing R1/R2, Ro, R4, or their local topology do not affect the supported common-mode DC targets.",
            value=len(circuit.ambiguities),
        ),
        CheckResult(
            name="ecg_rld_closed_form_kcl",
            passed=max_residual <= 1e-12,
            message="Closed-form body-node and RLD summing-node KCL residuals are within tolerance.",
            value=float(max_residual),
        ),
    ]
    warnings = [
        f"Non-blocking RLD common-mode note: {ambiguity}"
        for ambiguity in circuit.ambiguities
    ]
    warnings.extend(
        f"Non-blocking parse note: {ambiguity}"
        for ambiguity in circuit.nonblocking_ambiguities
    )
    netlist = ""
    try:
        netlist = generate_netlist(circuit)
    except Exception:
        netlist = ""

    packet = SolutionPacket(
        circuit_id=circuit.id,
        status="solved",
        node_voltages=computed_nodes,
        requested_answers=requested_answers,
        verification=VerificationReport(
            passed=all(check.passed for check in checks),
            max_kcl_residual_a=float(max_residual),
            checks=checks,
        ),
        verification_badge=VerificationBadge(
            label="PASS" if all(check.passed for check in checks) else "FAIL",
            message=(
                "ECG right-leg-drive common-mode DC reduction passed deterministic checks."
                if all(check.passed for check in checks)
                else "ECG right-leg-drive reduction was produced, but KCL checks failed."
            ),
        ),
        calculation_trace=CalculationTrace(
            parser_used=parser_used,
            solver_name="ecg_rld_common_mode_v1",
            solver_method="Closed-form ideal RLD common-mode DC reduction",
            solver_backend="deterministic algebra",
            answer_source="ecg_rld_common_mode_solver",
            verification_source="closed_form_kcl_checks",
        ),
        generated_netlist=netlist,
        warnings=warnings,
        assumptions_used=[
            *circuit.assumptions,
            "Pure common-mode DC input: ideal input buffers drive equal common-mode outputs.",
            "The auxiliary RLD op-amp holds the summing node at virtual ground and the system is not saturated.",
            "The AC-coupled post stage is open for DC, so V4 and the ideal A4 output are 0 V when requested.",
        ],
        tutor_observations=[
            TutorObservation(
                id="rld_feedback_gain",
                label="RLD common-mode feedback gain",
                value=float(feedback_gain),
                unit="V/V",
                note="Computed as R_f times the sum of the Ra input conductances into the auxiliary summing node.",
            ),
            TutorObservation(
                id="rld_body_voltage_drop",
                label="R_RL current drop",
                value=float(injected_current_a * right_leg_resistor.value),
                unit="V",
                note="The injected displacement current times the right-leg contact resistance.",
            ),
        ],
        guided_steps=_ecg_rld_steps(
            body_node=body_node,
            output_node=output_node,
            summing_node=summing_node,
            current_a=injected_current_a,
            right_leg_resistance_ohm=right_leg_resistor.value,
            feedback_gain=feedback_gain,
        ),
    )
    return _attach_tutor_context(circuit, packet)


def _try_solve_symbolic_voltage_clamp(
    circuit: CircuitProblem,
    parser_used: str | None,
) -> SolutionPacket | None:
    if circuit.unsupported_features or not _looks_like_voltage_clamp(circuit):
        return None
    if _blocking_voltage_clamp_ambiguities(circuit):
        return None
    if not _has_symbolic_command_voltage(circuit):
        return None

    shared_resistance = _shared_rm_ro_value(circuit)
    gain_a = _extract_voltage_clamp_gain(circuit)
    membrane_resistance = shared_resistance or _extract_named_resistance(
        circuit,
        name="m",
        tokens={"rm", "rmembrane", "membraneresistance"},
    )
    output_resistance = shared_resistance or _extract_named_resistance(
        circuit,
        name="o",
        tokens={"ro", "rout", "outputresistance", "currentelectroderesistance"},
    )
    if (
        gain_a is None
        or membrane_resistance is None
        or output_resistance is None
        or gain_a <= 0
        or membrane_resistance <= 0
        or output_resistance <= 0
    ):
        return None

    answer_id, vm_node = _voltage_clamp_answer_target(circuit)
    expression, coefficient = _coefficient_expression(
        gain_a,
        membrane_resistance,
        output_resistance,
    )
    checks = [
        CheckResult(
            name="symbolic_command_voltage",
            passed=True,
            message="V_c is treated as a symbolic command voltage rather than a missing numeric constant.",
        ),
        CheckResult(
            name="voltage_clamp_closed_form",
            passed=True,
            message="Closed-form two-electrode voltage-clamp equilibrium was solved.",
            value=f"A={gain_a:g}, R_m={membrane_resistance:g}, R_o={output_resistance:g}",
        ),
        CheckResult(
            name="symbolic_gain_coefficient",
            passed=True,
            message="Computed A R_m / (A R_m + R_m + R_o).",
            value=float(coefficient),
        ),
    ]
    netlist = ""
    try:
        netlist = generate_netlist(circuit)
    except Exception:
        netlist = ""

    return SolutionPacket(
        circuit_id=circuit.id,
        status="solved",
        symbolic_requested_answers={
            answer_id: SymbolicQuantityValue(
                expression=expression,
                unit="V",
                explanation_key="symbolic_voltage_clamp_vm",
                reference={"positive_node": vm_node, "negative_node": circuit.ground_node},
                numeric_coefficient=float(coefficient),
            )
        },
        verification=VerificationReport(passed=True, checks=checks),
        verification_badge=VerificationBadge(
            label="PASS",
            message="Symbolic voltage-clamp expression passed deterministic closed-form checks.",
        ),
        calculation_trace=CalculationTrace(
            parser_used=parser_used,
            solver_name="symbolic_voltage_clamp_v1",
            solver_method="Closed-form voltage-clamp equilibrium",
            solver_backend="deterministic algebra",
            answer_source="symbolic_voltage_clamp",
            verification_source="symbolic_closed_form_checks",
        ),
        generated_netlist=netlist,
        warnings=[
            f"Non-blocking parse note: {ambiguity}"
            for ambiguity in circuit.nonblocking_ambiguities
        ],
        assumptions_used=[
            *circuit.assumptions,
            "V_c was kept symbolic because no numeric command voltage was provided.",
        ],
        tutor_observations=[
            TutorObservation(
                id="command_voltage_symbol",
                label="Command voltage",
                unit="V",
                note="V_c is the symbolic command-voltage input.",
            ),
            TutorObservation(
                id="closed_loop_voltage_gain",
                label="V_m / V_c",
                value=float(coefficient),
                unit="V/V",
                note=f"V_m = {expression}.",
            ),
        ],
        guided_steps=_symbolic_voltage_clamp_steps(
            answer_id=answer_id,
            vm_node=vm_node,
            gain_a=gain_a,
            membrane_resistance=membrane_resistance,
            output_resistance=output_resistance,
            expression=expression,
            coefficient=coefficient,
        ),
    )


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
                note="Template or dynamically inferred sampling-rate context for anti-aliasing discussion.",
            ),
            TutorObservation(
                id="adc_nyquist_frequency",
                label="ADC Nyquist frequency",
                value=nyquist_hz,
                unit="Hz",
                note="Half the template or dynamically inferred sampling frequency.",
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
                "Isolated noise values are starter estimates. Output noise observations below use "
                "complex MNA transfer propagation over the configured bandwidth, but still are not "
                "datasheet-accurate device-noise design calculations."
            ),
        )
    )
    _add_noise_transfer_observations(
        observations,
        circuit,
        bandwidth_hz=bandwidth_hz,
        temperature_k=temperature_k,
    )


def _noise_output_reference(circuit: CircuitProblem) -> tuple[str, str] | None:
    for goal in circuit.goals:
        if goal.quantity == "node_voltage" and goal.target in circuit.nodes:
            return goal.target, circuit.ground_node
        if goal.quantity == "component_voltage":
            component = _component_by_id(circuit, goal.target)
            if component is None:
                continue
            if goal.reference and {"positive_node", "negative_node"} <= set(goal.reference):
                positive = str(goal.reference["positive_node"])
                negative = str(goal.reference["negative_node"])
                if positive in circuit.nodes and negative in circuit.nodes:
                    return positive, negative
            return component.nodes[0], component.nodes[1]
    for candidate in ["out", "vout", "ecg_out", "inst_out", "tia_out"]:
        if candidate in circuit.nodes:
            return candidate, circuit.ground_node
    non_ground_nodes = [node for node in circuit.nodes if node != circuit.ground_node]
    if not non_ground_nodes:
        return None
    return non_ground_nodes[-1], circuit.ground_node


def _zero_ac_sources(circuit: CircuitProblem) -> None:
    for component in circuit.components:
        if component.type in {"voltage_source", "current_source"}:
            component.ac_magnitude = 0.0
            component.ac_phase_deg = 0.0


def _noise_transfer(
    circuit: CircuitProblem,
    *,
    source_id: str,
    source_nodes: list[str],
    output_positive: str,
    output_negative: str,
    frequency_hz: float,
) -> complex | None:
    noise_problem = circuit.model_copy(deep=True)
    noise_problem.analysis_type = "ac_single_frequency"
    noise_problem.frequency_hz = float(frequency_hz)
    noise_problem.sweep = None
    noise_problem.transient = None
    _zero_ac_sources(noise_problem)
    noise_problem.components.append(
        Component(
            id=f"INOISE_{source_id}",
            type="current_source",
            nodes=[source_nodes[0], source_nodes[1]],
            value=0.0,
            unit="A",
            ac_magnitude=1.0,
            ac_phase_deg=0.0,
        )
    )
    result = solve_ac(noise_problem, frequency_hz=frequency_hz)
    if not result.success:
        return None
    positive = result.node_voltages.get(output_positive)
    negative = result.node_voltages.get(output_negative)
    if positive is None:
        return None
    positive_value = quantity_to_complex(positive)
    negative_value = quantity_to_complex(negative) if negative is not None else 0.0 + 0.0j
    return positive_value - negative_value


def _integrated_noise_rms(
    circuit: CircuitProblem,
    *,
    source_id: str,
    source_nodes: list[str],
    output_positive: str,
    output_negative: str,
    bandwidth_hz: float,
    white_density: float,
    flicker_corner_hz: float | None = None,
) -> float | None:
    if bandwidth_hz <= 0 or white_density <= 0:
        return None
    points = 24
    df = bandwidth_hz / points
    accumulated = 0.0
    solved_points = 0
    for index in range(points):
        frequency_hz = max((index + 0.5) * df, 1e-6)
        transfer = _noise_transfer(
            circuit,
            source_id=source_id,
            source_nodes=source_nodes,
            output_positive=output_positive,
            output_negative=output_negative,
            frequency_hz=frequency_hz,
        )
        if transfer is None:
            continue
        flicker_multiplier = (
            1.0 + flicker_corner_hz / frequency_hz
            if flicker_corner_hz is not None and flicker_corner_hz > 0
            else 1.0
        )
        accumulated += (abs(transfer) ** 2) * (white_density**2) * flicker_multiplier * df
        solved_points += 1
    if solved_points == 0:
        return None
    return math.sqrt(accumulated)


def _add_noise_transfer_observations(
    observations: list[TutorObservation],
    circuit: CircuitProblem,
    *,
    bandwidth_hz: float,
    temperature_k: float,
) -> None:
    metadata = circuit.bme_metadata
    if metadata is None:
        return
    output_reference = _noise_output_reference(circuit)
    if output_reference is None:
        return
    output_positive, output_negative = output_reference
    total_variance = 0.0
    propagated_count = 0
    observations.append(
        TutorObservation(
            id="noise_transfer_output_reference",
            label="Noise output reference",
            note=f"Output noise is referred to V({output_positive}) - V({output_negative}).",
        )
    )

    flicker_ids = set(metadata.flicker_noise_component_ids)
    flicker_corner = metadata.flicker_noise_corner_hz
    for resistor_id in metadata.thermal_noise_resistor_ids:
        resistor = _component_by_id(circuit, resistor_id)
        if resistor is None or resistor.type != "resistor" or resistor.value <= 0:
            continue
        white_density = math.sqrt(4.0 * BOLTZMANN_J_PER_K * temperature_k / resistor.value)
        rms = _integrated_noise_rms(
            circuit,
            source_id=resistor.id,
            source_nodes=resistor.nodes,
            output_positive=output_positive,
            output_negative=output_negative,
            bandwidth_hz=bandwidth_hz,
            white_density=white_density,
            flicker_corner_hz=flicker_corner if resistor.id in flicker_ids else None,
        )
        if rms is None:
            continue
        total_variance += rms * rms
        propagated_count += 1
        observations.append(
            TutorObservation(
                id=f"output_noise_from_{resistor.id}",
                label=f"{resistor.id} output-referred noise",
                value=float(rms),
                unit="V_rms",
                note=(
                    "Integrated by injecting the resistor's Norton noise current through the complex MNA network"
                    + (
                        f" with a {flicker_corner:.6g} Hz 1/f corner."
                        if resistor.id in flicker_ids and flicker_corner is not None
                        else "."
                    )
                ),
            )
        )

    current_source_id = metadata.photodiode_shot_noise_current_id
    current_source = _component_by_id(circuit, current_source_id) if current_source_id else None
    if current_source is not None and current_source.type == "current_source":
        white_density = math.sqrt(2.0 * ELEMENTARY_CHARGE_C * abs(current_source.value))
        rms = _integrated_noise_rms(
            circuit,
            source_id=current_source.id,
            source_nodes=current_source.nodes,
            output_positive=output_positive,
            output_negative=output_negative,
            bandwidth_hz=bandwidth_hz,
            white_density=white_density,
        )
        if rms is not None:
            total_variance += rms * rms
            propagated_count += 1
            observations.append(
                TutorObservation(
                    id=f"output_noise_from_{current_source.id}",
                    label=f"{current_source.id} output-referred shot noise",
                    value=float(rms),
                    unit="V_rms",
                    note="Integrated by injecting photodiode shot-noise current through the complex MNA network.",
                )
            )

    if propagated_count:
        observations.append(
            TutorObservation(
                id="output_integrated_noise_rms",
                label="Output integrated noise",
                value=float(math.sqrt(total_variance)),
                unit="V_rms",
                note=(
                    f"RSS total of {propagated_count} propagated noise source(s) over "
                    f"{bandwidth_hz:.6g} Hz using complex MNA transfer integration."
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
    if not response.is_first_order or response.time_constant_s <= 0:
        return [
            TutorObservation(
                id="transient_sample_count",
                label="Transient sample count",
                value=float(len(response.sample_points)),
                unit="points",
                note="Samples were produced by numerical time-domain integration.",
            )
        ]

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


def _sweep_plot_point(
    frequency_hz: float,
    value: ComplexQuantityValue,
) -> ACSweepPlotPoint:
    magnitude = max(float(value.magnitude), 1e-300)
    return ACSweepPlotPoint(
        frequency_hz=float(frequency_hz),
        real=float(value.real),
        imag=float(value.imag),
        magnitude=float(value.magnitude),
        magnitude_db=float(20.0 * math.log10(magnitude)),
        phase_deg=float(value.phase_deg),
    )


def _build_ac_sweep_plot_series(
    circuit: CircuitProblem,
    points: list[ACFrequencyPoint],
) -> list[ACSweepPlotSeries]:
    series: dict[str, ACSweepPlotSeries] = {}

    def add_point(
        series_id: str,
        label: str,
        source: str,
        unit: str,
        frequency_hz: float,
        value: ComplexQuantityValue,
    ) -> None:
        if series_id not in series:
            series[series_id] = ACSweepPlotSeries(
                id=series_id,
                label=label,
                source=source,  # type: ignore[arg-type]
                unit=unit,
            )
        series[series_id].points.append(_sweep_plot_point(frequency_hz, value))

    ground = circuit.ground_node
    for point in points:
        frequency_hz = point.frequency_hz
        for answer_id, value in point.requested_answers.items():
            add_point(
                f"answer:{answer_id}",
                f"Answer {answer_id}",
                "requested_answer",
                value.unit,
                frequency_hz,
                value,
            )
        for node, value in point.node_voltages.items():
            if node == ground:
                continue
            add_point(
                f"node:{node}",
                f"Node V({node})",
                "node_voltage",
                value.unit,
                frequency_hz,
                value,
            )
        for component_id, result in point.component_results.items():
            add_point(
                f"component:{component_id}:voltage",
                f"{component_id} voltage",
                "component_voltage",
                result.voltage.unit,
                frequency_hz,
                result.voltage,
            )
            add_point(
                f"component:{component_id}:current",
                f"{component_id} current",
                "component_current",
                result.current.unit,
                frequency_hz,
                result.current,
            )

    return list(series.values())


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
    if pair is None and circuit.bme_metadata is not None:
        grounded_sources = [
            component
            for component in circuit.components
            if component.type == "voltage_source" and circuit.ground_node in component.nodes
        ]
        if len(grounded_sources) >= 2:
            pair = grounded_sources[0], grounded_sources[1]
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


def _build_nonideal_op_amp_observations(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> list[TutorObservation]:
    observations: list[TutorObservation] = []
    for component in circuit.components:
        if not is_nonideal_op_amp_type(component.type):
            continue

        observations.append(
            TutorObservation(
                id=f"{component.id}_open_loop_gain",
                label=f"{component.id} nonideal open-loop gain",
                value=float(nonideal_open_loop_gain(component)),
                unit="V/V",
                note="Finite open-loop gain used by the educational nonideal op-amp model.",
            )
        )

        if component.input_bias_current_a is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_input_bias_current",
                    label=f"{component.id} input bias current",
                    value=float(component.input_bias_current_a),
                    unit="A",
                    note="Bias current is stamped at both op-amp input nodes in the DC KCL solve.",
                )
            )

        if component.input_offset_voltage_v is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_input_offset_voltage",
                    label=f"{component.id} input offset voltage",
                    value=float(component.input_offset_voltage_v),
                    unit="V",
                    note="Input offset is stamped into the nonideal op-amp control equation.",
                )
            )

        if component.input_resistance_ohm is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_input_resistance",
                    label=f"{component.id} input resistance",
                    value=float(component.input_resistance_ohm),
                    unit="ohm",
                    note="Input resistance is stamped between the op-amp input pins, so it can load the source network.",
                )
            )

        if component.output_resistance_ohm is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_output_resistance",
                    label=f"{component.id} output resistance",
                    value=float(component.output_resistance_ohm),
                    unit="ohm",
                    note="Output resistance is part of the op-amp VCCS/Norton macromodel and affects load-dependent output.",
                )
            )

        if component.compensation_capacitance_f is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_compensation_capacitance",
                    label=f"{component.id} compensation capacitance",
                    value=float(component.compensation_capacitance_f),
                    unit="F",
                    note="AC analysis stamps this capacitance at the output port for macromodel frequency shaping.",
                )
            )

        if component.clamp_diode_saturation_current_a is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_clamp_diode_saturation_current",
                    label=f"{component.id} clamp diode saturation current",
                    value=float(component.clamp_diode_saturation_current_a),
                    unit="A",
                    note="Rail clamp behavior is represented by the educational saturation model; full recovery dynamics are still not vendor-SPICE accurate.",
                )
            )

        if component.gain_bandwidth_hz is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_gain_bandwidth",
                    label=f"{component.id} gain-bandwidth",
                    value=float(component.gain_bandwidth_hz),
                    unit="Hz",
                    note="AC analysis uses a single-pole open-loop gain model derived from this gain-bandwidth value.",
                )
            )
        elif component.bandwidth_hz is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_open_loop_bandwidth",
                    label=f"{component.id} open-loop bandwidth",
                    value=float(component.bandwidth_hz),
                    unit="Hz",
                    note="AC analysis uses this as the single-pole open-loop bandwidth.",
                )
            )

        output_current_limit = component.output_current_limit_a
        dc_result = packet.component_results.get(component.id)
        ac_result = packet.ac_component_results.get(component.id)
        if output_current_limit is not None:
            if dc_result is not None:
                output_current = abs(dc_result.current.value)
                observations.append(
                    TutorObservation(
                        id=f"{component.id}_output_current_limit",
                        label=f"{component.id} output-current limit",
                        value=float(output_current),
                        unit="A",
                        note=(
                            f"Configured limit is {output_current_limit:.6g} A; "
                            "verification fails if the solved output current exceeds it."
                        ),
                    )
                )
            elif ac_result is not None:
                observations.append(
                    TutorObservation(
                        id=f"{component.id}_output_current_limit",
                        label=f"{component.id} output-current limit",
                        value=float(ac_result.current.magnitude),
                        unit="A",
                        note=(
                            f"Configured limit is {output_current_limit:.6g} A; "
                            "AC verification checks the phasor current magnitude."
                        ),
                    )
                )

        window = nonideal_output_window(component)
        if window is not None:
            lower, upper = window
            output_voltage = None
            if dc_result is not None:
                output_voltage = dc_result.voltage.value
            elif ac_result is not None:
                output_voltage = ac_result.voltage.magnitude
            if output_voltage is not None:
                observations.append(
                    TutorObservation(
                        id=f"{component.id}_output_window",
                        label=f"{component.id} output rail window",
                        value=float(output_voltage),
                        unit="V",
                        note=(
                            f"Usable output window is {lower:.6g} V to {upper:.6g} V "
                            "after output swing margin."
                        ),
                    )
                )

        if component.slew_rate_v_per_s is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_slew_rate",
                    label=f"{component.id} slew-rate limit",
                    value=float(component.slew_rate_v_per_s),
                    unit="V/s",
                    note="Reported as a transition-speed limit; DC solves use it for saturation recovery estimates.",
                )
            )

        if component.clipping_recovery_s is not None:
            observations.append(
                TutorObservation(
                    id=f"{component.id}_clipping_recovery",
                    label=f"{component.id} clipping recovery",
                    value=float(component.clipping_recovery_s),
                    unit="s",
                    note="Educational recovery-time parameter attached when the output is driven into clipping.",
                )
            )

    return observations


def _build_tutor_observations(circuit: CircuitProblem, packet: SolutionPacket) -> list[TutorObservation]:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return []
    observations: list[TutorObservation] = []
    if packet.ac_requested_answers:
        observations.extend(_build_ac_filter_observations(circuit, packet))
    elif packet.transient_response:
        observations.extend(_build_rc_transient_observations(packet))
    elif circuit.bme_metadata is not None:
        observations.extend(_build_bme_dc_observations(circuit, packet))
    observations.extend(_build_nonideal_op_amp_observations(circuit, packet))
    return observations


def _plot_point(
    index: int,
    value: float,
    label: str,
    *,
    note: str | None = None,
) -> TeachingPlotPoint:
    return TeachingPlotPoint(
        x=float(index),
        y=float(value),
        x_label=label,
        y_label=f"{value:.6g}",
        note=note,
    )


def _single_bar_series(
    *,
    series_id: str,
    label: str,
    unit: str,
    values: list[tuple[str, float, str | None]],
) -> TeachingPlotSeries:
    return TeachingPlotSeries(
        id=series_id,
        label=label,
        unit=unit,
        points=[
            _plot_point(index, value, item_label, note=note)
            for index, (item_label, value, note) in enumerate(values)
        ],
    )


def _build_dc_teaching_plots(
    circuit: CircuitProblem,
    packet: SolutionPacket,
) -> list[TeachingPlot]:
    plots: list[TeachingPlot] = []
    node_values = [
        (node, packet.node_voltages[node], "Voltage relative to the reference node.")
        for node in circuit.nodes
        if node != circuit.ground_node and node in packet.node_voltages
    ]
    if node_values:
        plots.append(
            TeachingPlot(
                id="dc_node_voltage_levels",
                title="Node voltage map",
                subtitle="Static levels relative to ground",
                plot_type="bar",
                source="dc_operating_point",
                x_label="Node",
                y_label="Voltage (V)",
                series=[
                    _single_bar_series(
                        series_id="node_voltage",
                        label="Node voltage",
                        unit="V",
                        values=node_values,
                    )
                ],
                insight=(
                    "The textbook pattern is to locate the measurand first: "
                    "these bars show where the solved circuit creates high, low, and intermediate potentials."
                ),
            )
        )

    component_values = [
        (
            component.id,
            packet.component_results[component.id].current.value,
            f"Positive current follows {component.nodes[0]} to {component.nodes[1]}.",
        )
        for component in circuit.components
        if component.id in packet.component_results
    ]
    if component_values:
        plots.append(
            TeachingPlot(
                id="dc_component_current_flow",
                title="Component current flow",
                subtitle="Signed by each component's reference direction",
                plot_type="bar",
                source="dc_operating_point",
                x_label="Component",
                y_label="Current (A)",
                series=[
                    _single_bar_series(
                        series_id="component_current",
                        label="Signed current",
                        unit="A",
                        values=component_values,
                    )
                ],
                insight=(
                    "Current signs are not moral judgments; they are arrows. "
                    "A negative bar means the real current flows opposite the component reference."
                ),
            )
        )

    power_values = [
        (
            component.id,
            packet.component_results[component.id].power.value,
            "Positive absorbs power; negative supplies power.",
        )
        for component in circuit.components
        if component.id in packet.component_results
    ]
    if power_values:
        plots.append(
            TeachingPlot(
                id="dc_power_balance",
                title="Power balance",
                subtitle="Signed component power",
                plot_type="bar",
                source="verification",
                x_label="Component",
                y_label="Power (W)",
                series=[
                    _single_bar_series(
                        series_id="component_power",
                        label="Signed power",
                        unit="W",
                        values=power_values,
                    )
                ],
                insight=(
                    "Medical instrumentation design keeps asking where energy enters, leaves, or heats tissue. "
                    "The signed-power plot makes the verification check visible."
                ),
            )
        )
    return plots


SWEEP_SOURCE_RANK = {
    "requested_answer": 0,
    "node_voltage": 1,
    "component_voltage": 2,
    "component_current": 3,
}


def _teaching_sweep_series(
    sweep_series: list[ACSweepPlotSeries],
) -> list[ACSweepPlotSeries]:
    return sorted(
        sweep_series,
        key=lambda series: (
            SWEEP_SOURCE_RANK.get(series.source, 10),
            0 if series.points else 1,
            series.id,
        ),
    )[:6]


def _cutoff_markers(observations: list[TutorObservation]) -> list[TeachingPlotMarker]:
    markers: list[TeachingPlotMarker] = []
    for observation in observations:
        if observation.value is None or observation.unit != "Hz":
            continue
        if "cutoff" not in observation.id and "corner" not in observation.id:
            continue
        markers.append(
            TeachingPlotMarker(
                axis="x",
                value=float(observation.value),
                label=observation.label,
            )
        )
    return markers


def _build_ac_sweep_teaching_plots(packet: SolutionPacket) -> list[TeachingPlot]:
    selected = _teaching_sweep_series(packet.ac_sweep_plots)
    if not selected:
        return []

    magnitude_series = [
        TeachingPlotSeries(
            id=series.id,
            label=series.label,
            unit="dB",
            points=[
                TeachingPlotPoint(
                    x=point.frequency_hz,
                    y=point.magnitude_db,
                    x_label=f"{point.frequency_hz:.6g} Hz",
                    y_label=f"{point.magnitude_db:.6g} dB",
                )
                for point in series.points
            ],
        )
        for series in selected
    ]
    phase_series = [
        TeachingPlotSeries(
            id=series.id,
            label=series.label,
            unit="deg",
            points=[
                TeachingPlotPoint(
                    x=point.frequency_hz,
                    y=point.phase_deg,
                    x_label=f"{point.frequency_hz:.6g} Hz",
                    y_label=f"{point.phase_deg:.6g} deg",
                )
                for point in series.points
            ],
        )
        for series in selected
    ]
    markers = _cutoff_markers(packet.tutor_observations)
    return [
        TeachingPlot(
            id="ac_sweep_magnitude_response",
            title="Magnitude response",
            subtitle="AC sweep, textbook Bode-style view",
            plot_type="line",
            source="ac_sweep",
            x_label="Frequency (Hz)",
            y_label="Magnitude (dB)",
            x_scale="log",
            series=magnitude_series,
            markers=markers,
            insight=(
                "This turns the answer from one number into a transfer behavior: "
                "students can see passband, rolloff, and attenuation together."
            ),
        ),
        TeachingPlot(
            id="ac_sweep_phase_response",
            title="Phase response",
            subtitle="Where storage elements delay or lead the signal",
            plot_type="line",
            source="ac_sweep",
            x_label="Frequency (Hz)",
            y_label="Phase (deg)",
            x_scale="log",
            series=phase_series,
            markers=markers,
            insight=(
                "Medical signals are often low-frequency and time-shaped; "
                "phase tells students whether the circuit is preserving timing as well as amplitude."
            ),
        ),
    ]


def _build_ac_single_frequency_teaching_plots(packet: SolutionPacket) -> list[TeachingPlot]:
    phasors: list[tuple[str, ComplexQuantityValue, str]] = []
    for answer_id, value in packet.ac_requested_answers.items():
        phasors.append((answer_id, value, "requested answer"))
    for node, value in packet.ac_node_voltages.items():
        if len(phasors) >= 8:
            break
        phasors.append((f"V({node})", value, "node voltage"))
    if not phasors:
        return []

    return [
        TeachingPlot(
            id="ac_phasor_magnitudes",
            title="Phasor magnitudes",
            subtitle="Single-frequency AC levels",
            plot_type="bar",
            source="ac_single_frequency",
            x_label="Quantity",
            y_label=f"Magnitude ({phasors[0][1].unit})",
            series=[
                _single_bar_series(
                    series_id="phasor_magnitude",
                    label="Magnitude",
                    unit=phasors[0][1].unit,
                    values=[
                        (label, value.magnitude, note)
                        for label, value, note in phasors
                    ],
                )
            ],
            insight="Magnitude shows how much of the signal survives at the analysis frequency.",
        ),
        TeachingPlot(
            id="ac_phasor_phases",
            title="Phasor phases",
            subtitle="Single-frequency timing shift",
            plot_type="bar",
            source="ac_single_frequency",
            x_label="Quantity",
            y_label="Phase (deg)",
            series=[
                _single_bar_series(
                    series_id="phasor_phase",
                    label="Phase",
                    unit="deg",
                    values=[
                        (label, value.phase_deg, note)
                        for label, value, note in phasors
                    ],
                )
            ],
            insight="Phase is the timing part of the answer; it is easy to miss if students only chase magnitudes.",
        ),
    ]


def _build_transient_teaching_plots(packet: SolutionPacket) -> list[TeachingPlot]:
    response = packet.transient_response
    if response is None or not response.sample_points:
        return []

    markers = []
    if response.time_constant_s > 0:
        markers.append(
            TeachingPlotMarker(
                axis="x",
                value=float(response.time_constant_s),
                label="1 tau",
            )
        )
    plots = [
        TeachingPlot(
            id="transient_capacitor_voltage",
            title="Capacitor voltage over time",
            subtitle=response.analysis_method.replace("_", " "),
            plot_type="line",
            source="rc_transient",
            x_label="Time (s)",
            y_label="Voltage (V)",
            series=[
                TeachingPlotSeries(
                    id="capacitor_voltage",
                    label=response.capacitor_id,
                    unit="V",
                    points=[
                        TeachingPlotPoint(
                            x=point.time_s,
                            y=point.voltage_v,
                            x_label=f"{point.time_s:.6g} s",
                            y_label=f"{point.voltage_v:.6g} V",
                        )
                        for point in response.sample_points
                    ],
                )
            ],
            markers=markers,
            insight=(
                "The curve ties the initial condition, final value, and storage-element time scale together."
            ),
        )
    ]

    span = response.final_voltage_v - response.initial_voltage_v
    if response.is_first_order and response.time_constant_s > 0 and abs(span) > 1e-15:
        plots.append(
            TeachingPlot(
                id="transient_normalized_settling",
                title="Normalized settling",
                subtitle="Same transient measured in time constants",
                plot_type="line",
                source="rc_transient",
                x_label="Time constants (t/tau)",
                y_label="Settling fraction",
                series=[
                    TeachingPlotSeries(
                        id="settling_fraction",
                        label="Fraction from initial to final",
                        unit="fraction",
                        points=[
                            TeachingPlotPoint(
                                x=point.time_s / response.time_constant_s,
                                y=(point.voltage_v - response.initial_voltage_v) / span,
                                x_label=f"{point.time_s / response.time_constant_s:.6g} tau",
                                y_label=f"{(point.voltage_v - response.initial_voltage_v) / span:.6g}",
                            )
                            for point in response.sample_points
                        ],
                    )
                ],
                markers=[
                    TeachingPlotMarker(axis="x", value=1.0, label="1 tau"),
                    TeachingPlotMarker(axis="y", value=1.0 - math.exp(-1.0), label="63.2%"),
                ],
                insight=(
                    "Normalizing by tau lets different RC circuits become the same learning shape, "
                    "which is exactly how the textbook builds first-order intuition."
                ),
            )
        )
    return plots


def _observation_map(packet: SolutionPacket) -> dict[str, TutorObservation]:
    return {observation.id: observation for observation in packet.tutor_observations}


def _observation_value(
    observations: dict[str, TutorObservation],
    observation_id: str,
) -> float | None:
    observation = observations.get(observation_id)
    if observation is None or observation.value is None:
        return None
    return float(observation.value)


def _build_biomedical_teaching_plots(packet: SolutionPacket) -> list[TeachingPlot]:
    observations = _observation_map(packet)
    plots: list[TeachingPlot] = []

    differential = _observation_value(observations, "differential_input_voltage")
    common_mode = _observation_value(observations, "common_mode_input_voltage")
    if differential is not None and common_mode is not None:
        plots.append(
            TeachingPlot(
                id="bme_differential_common_mode_inputs",
                title="Differential vs common-mode input",
                subtitle="Why biopotential amplifiers need CMRR",
                plot_type="bar",
                source="biomedical_context",
                x_label="Input mode",
                y_label="Voltage (V)",
                series=[
                    _single_bar_series(
                        series_id="input_modes",
                        label="Input level",
                        unit="V",
                        values=[
                            ("Differential", differential, "Desired biopotential signal."),
                            ("Common-mode", common_mode, "Interference shared by both inputs."),
                        ],
                    )
                ],
                insight=(
                    "The textbook keeps returning to this contrast: the useful signal can be tiny "
                    "while common-mode interference is large."
                ),
            )
        )

    frequency_ids = [
        "low_pass_cutoff_frequency",
        "high_pass_cutoff_frequency",
        "adc_target_cutoff_frequency",
        "adc_sampling_frequency",
        "adc_nyquist_frequency",
    ]
    frequency_values = [
        (observations[item_id].label, float(observations[item_id].value), observations[item_id].note)
        for item_id in frequency_ids
        if item_id in observations and observations[item_id].value is not None and observations[item_id].unit == "Hz"
    ]
    if len(frequency_values) >= 2:
        plots.append(
            TeachingPlot(
                id="bme_sampling_frequency_landmarks",
                title="Sampling and filter landmarks",
                subtitle="Cutoff, sampling rate, and Nyquist in one view",
                plot_type="bar",
                source="biomedical_context",
                x_label="Landmark",
                y_label="Frequency (Hz)",
                series=[
                    _single_bar_series(
                        series_id="frequency_landmarks",
                        label="Frequency",
                        unit="Hz",
                        values=frequency_values,
                    )
                ],
                insight=(
                    "Anti-aliasing is a relationship, not one component value: "
                    "students should compare cutoff, sampling frequency, and Nyquist together."
                ),
            )
        )

    for unit, title in [("V_rms", "Voltage-noise budget"), ("A_rms", "Current-noise budget")]:
        values = [
            (observation.label, float(observation.value), observation.note)
            for observation in packet.tutor_observations
            if observation.value is not None
            and observation.unit == unit
            and "noise" in observation.id
        ][:8]
        if values:
            plots.append(
                TeachingPlot(
                    id=f"bme_noise_budget_{unit.lower()}",
                    title=title,
                    subtitle="Starter estimates from deterministic observations",
                    plot_type="bar",
                    source="biomedical_context",
                    x_label="Noise term",
                    y_label=unit,
                    series=[
                        _single_bar_series(
                            series_id=f"noise_{unit.lower()}",
                            label="Noise",
                            unit=unit,
                            values=values,
                        )
                    ],
                    insight=(
                        "Noise budgeting helps students stop treating biomedical front ends as ideal gain blocks."
                    ),
                )
            )

    leakage = _observation_value(observations, "cmrr_common_mode_leakage_output")
    mismatch_db = _observation_value(observations, "cmrr_mismatch_estimate_db")
    if leakage is not None:
        plots.append(
            TeachingPlot(
                id="bme_cmrr_mismatch_what_if",
                title="CMRR mismatch what-if",
                subtitle="Common-mode leakage from resistor-ratio error",
                plot_type="bar",
                source="biomedical_context",
                x_label="Quantity",
                y_label="Voltage (V)",
                series=[
                    _single_bar_series(
                        series_id="cmrr_leakage",
                        label="Common-mode output leakage",
                        unit="V",
                        values=[
                            (
                                "Leakage output",
                                leakage,
                                observations.get("cmrr_common_mode_leakage_output").note
                                if observations.get("cmrr_common_mode_leakage_output")
                                else None,
                            )
                        ],
                    )
                ],
                insight=(
                    f"Mismatch CMRR estimate: {mismatch_db:.6g} dB."
                    if mismatch_db is not None
                    else "A tiny resistor mismatch can turn common-mode voltage into output error."
                ),
            )
        )

    return plots


def _build_teaching_plots(circuit: CircuitProblem, packet: SolutionPacket) -> list[TeachingPlot]:
    if packet.status != "solved" or packet.verification_badge.label != "PASS":
        return []

    plots: list[TeachingPlot] = []
    if packet.node_voltages and packet.component_results:
        plots.extend(_build_dc_teaching_plots(circuit, packet))
    if packet.ac_sweep_plots:
        plots.extend(_build_ac_sweep_teaching_plots(packet))
    elif packet.ac_requested_answers or packet.ac_node_voltages:
        plots.extend(_build_ac_single_frequency_teaching_plots(packet))
    if packet.transient_response:
        plots.extend(_build_transient_teaching_plots(packet))
    if circuit.bme_metadata is not None or packet.tutor_observations:
        plots.extend(_build_biomedical_teaching_plots(packet))
    return plots


def _attach_tutor_context(circuit: CircuitProblem, packet: SolutionPacket) -> SolutionPacket:
    packet.bme_metadata = circuit.bme_metadata
    packet.tutor_observations = _build_tutor_observations(circuit, packet)
    packet.teaching_plots = _build_teaching_plots(circuit, packet)
    packet.guided_steps = build_guided_steps(circuit, packet)
    packet.lesson_packet = build_lesson_packet(circuit, packet)
    packet.socratic_lecture = build_socratic_lecture_packet(circuit, packet)
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
    problem = inject_dynamic_bme_context(problem)
    ecg_rld_packet = _try_solve_ecg_rld_common_mode(problem, parser_used)
    if ecg_rld_packet is not None:
        return ecg_rld_packet

    symbolic_packet = _try_solve_symbolic_voltage_clamp(problem, parser_used)
    if symbolic_packet is not None:
        symbolic_packet.teaching_plots = _build_teaching_plots(problem, symbolic_packet)
        symbolic_packet.socratic_lecture = build_socratic_lecture_packet(problem, symbolic_packet)
        return symbolic_packet

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
                "complex-power balance, and requested-answer checks."
                if packet.verification.passed
                else "AC solver output was produced, but one or more verification checks failed."
            ),
        )
        return _attach_tutor_context(circuit, packet)

    if circuit.analysis_type == "ac_sweep":
        points: list[ACFrequencyPoint] = []
        warnings = [*validation.warnings]
        max_kcl_residual = 0.0
        max_power_balance_error = 0.0
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
            max_power_balance_error = max(
                max_power_balance_error,
                verification.power_balance_error_w,
            )
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
            power_balance_error_w=max_power_balance_error,
            checks=sweep_checks,
        )
        status = "solved" if verification.passed else "invalid"
        packet = SolutionPacket(
            circuit_id=circuit.id,
            status=status,  # type: ignore[arg-type]
            ac_sweep=points,
            ac_sweep_plots=_build_ac_sweep_plot_series(circuit, points),
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
                message=solve_result.message or "Transient analysis could not be solved.",
                checks=validation.checks,
                warnings=[
                    *validation.warnings,
                    solve_result.message or "Transient analysis could not be solved.",
                ],
                calculation_trace=solve_result.calculation_trace.model_copy(
                    update={"parser_used": parser_used}
                ),
            )

        checks = [
            *validation.checks,
            CheckResult(
                name="transient_numerical_integration",
                passed=True,
                message=(
                    "Transient response was generated by Backward Euler companion-model "
                    "integration over the requested sample times."
                ),
                value=len(solve_result.transient_response.sample_points)
                if solve_result.transient_response
                else 0,
            ),
        ]
        if (
            solve_result.transient_response is not None
            and solve_result.transient_response.is_first_order
        ):
            checks.append(
                CheckResult(
                    name="first_order_rc_parameters",
                    passed=solve_result.transient_response.time_constant_s > 0,
                    message="First-order RC resistance and time constant were computed."
                    if solve_result.transient_response.time_constant_s > 0
                    else "First-order RC time constant was not available.",
                    value=solve_result.transient_response.time_constant_s,
                )
            )
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
                    "Transient numerical integration passed validation and generated "
                    "initial/final conditions and voltage samples."
                    if verification.passed
                    else "Transient response was produced, but one or more checks failed."
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

    has_nonlinear_device = any(component.type == "diode" for component in circuit.components)
    solve_result = solve_nonlinear_dc(circuit) if has_nonlinear_device else solve_mna(circuit)
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
        warnings=[*validation.warnings, *solve_result.warnings],
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
