from app.models.solution_packet import VerificationBadge, VerificationReport
from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.demo_parser import (
    bridge_network_problem,
    current_divider_problem,
    rc_low_pass_problem,
    rc_transient_charging_problem,
    voltage_divider_problem,
)
from app.services.lesson_builder import lesson_has_unverified_numeric_claims
from app.models.solution_packet import LessonPacket, TutorFocus, TutorStep
from app.services.pipeline import solve_circuit


def _assert_lesson_basics(packet):
    lesson = packet.lesson_packet
    assert lesson is not None
    assert lesson.summary
    assert lesson.learning_objectives
    assert lesson.conceptual_overview
    assert lesson.step_by_step_derivation
    assert lesson.equation_steps
    assert lesson.checks
    assert lesson.verified_value_refs
    assert not lesson_has_unverified_numeric_claims(lesson)
    assert any(
        step.focus.components or step.focus.nodes or step.focus.goals
        for step in lesson.step_by_step_derivation
    )


def test_voltage_divider_detailed_lesson_packet():
    packet = solve_circuit(voltage_divider_problem())

    _assert_lesson_basics(packet)
    lesson = packet.lesson_packet
    assert lesson is not None
    assert [step.id for step in lesson.step_by_step_derivation][:3] == [
        "divider_reference",
        "divider_series_path",
        "divider_output",
    ]
    assert any(ref.id == "voltage_across_R2" for ref in lesson.verified_value_refs)
    assert any("series current" in item.lower() for item in lesson.learning_objectives)


def test_current_divider_detailed_lesson_packet():
    packet = solve_circuit(current_divider_problem())

    _assert_lesson_basics(packet)
    lesson = packet.lesson_packet
    assert lesson is not None
    assert [step.id for step in lesson.step_by_step_derivation][:3] == [
        "current_divider_source",
        "current_divider_parallel_branches",
        "current_divider_requested_values",
    ]
    assert any("parallel" in item.lower() for item in lesson.conceptual_overview)
    assert any(ref.id == "R1_current" for ref in lesson.verified_value_refs)


def test_bridge_nodal_lesson_packet():
    packet = solve_circuit(bridge_network_problem())

    _assert_lesson_basics(packet)
    lesson = packet.lesson_packet
    assert lesson is not None
    assert any("nodal" in step.title.lower() or "nodal" in step.explanation.lower() for step in lesson.equation_steps)
    assert any("shortcut" in item.lower() for item in lesson.conceptual_overview)
    assert any(ref.id == "R5_current" for ref in lesson.verified_value_refs)


def test_ac_low_pass_lesson_packet():
    packet = solve_circuit(rc_low_pass_problem())

    _assert_lesson_basics(packet)
    lesson = packet.lesson_packet
    assert lesson is not None
    assert any(step.id == "ac_low_pass_pole" for step in lesson.step_by_step_derivation)
    assert any("impedance" in step.explanation.lower() for step in lesson.equation_steps)
    assert any(ref.id == "vout_magnitude" for ref in lesson.verified_value_refs)


def test_rc_transient_lesson_packet():
    packet = solve_circuit(rc_transient_charging_problem())

    _assert_lesson_basics(packet)
    lesson = packet.lesson_packet
    assert lesson is not None
    assert any(step.id == "rc_time_constant" for step in lesson.step_by_step_derivation)
    assert any("exponential" in step.title.lower() for step in lesson.equation_steps)
    assert any(ref.id == "time_constant" for ref in lesson.verified_value_refs)


def test_bme_template_lesson_packet_keeps_context_cautious():
    circuit = BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem
    packet = solve_circuit(circuit)

    _assert_lesson_basics(packet)
    lesson = packet.lesson_packet
    assert lesson is not None
    assert any("biomedical" in item.lower() for item in lesson.conceptual_overview)
    assert any("not patient-safety certification" in item.lower() for item in lesson.limitations)
    assert any(step.id == "bme_context_boundary" for step in lesson.step_by_step_derivation)


def test_lesson_packet_not_generated_for_unverified_packet():
    circuit = voltage_divider_problem()
    packet = solve_circuit(circuit)
    packet.status = "invalid"
    packet.verification = VerificationReport(passed=False)
    packet.verification_badge = VerificationBadge(label="FAIL", message="forced failure")

    from app.services.lesson_builder import build_lesson_packet

    assert build_lesson_packet(circuit, packet) is None


def test_lesson_numeric_guard_ignores_digits_inside_ids():
    lesson = LessonPacket(
        summary="A verified lesson is available.",
        step_by_step_derivation=[
            TutorStep(
                id="id_digits",
                title="Inspect component R13",
                body="Look at V13, node sense_13, and R5b13 before reading values.",
                focus=TutorFocus(components=["R13", "R5b13"], nodes=["sense_13"]),
            )
        ],
    )

    assert not lesson_has_unverified_numeric_claims(lesson)
