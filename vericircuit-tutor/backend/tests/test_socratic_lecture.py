from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.demo_parser import rc_low_pass_sweep_problem, rc_transient_charging_problem, voltage_divider_problem
from app.services.pipeline import solve_circuit


def _stage_ids(packet):
    assert packet.socratic_lecture is not None
    return [stage.id for stage in packet.socratic_lecture.stages]


def test_socratic_lecture_has_gated_textbook_pace_for_dc_problem():
    packet = solve_circuit(voltage_divider_problem())

    lecture = packet.socratic_lecture
    assert lecture is not None
    assert lecture.opening_contract
    assert lecture.gemini_prompt
    assert "Do not invent numeric values" in lecture.gemini_prompt
    assert "first_exposure" in {profile.mode for profile in lecture.mode_profiles}
    assert "end_of_chapter_practice" in {profile.mode for profile in lecture.mode_profiles}

    assert _stage_ids(packet)[:6] == [
        "orient_measurand",
        "represent_system",
        "choose_model",
        "predict_before_calculating",
        "commit_minimal_equation",
        "compare_verified_view",
    ]
    assert lecture.stages[0].prompts[0].reveal_policy == "no_numeric_reveal"
    assert lecture.stages[4].prompts[0].reveal_policy == "value_refs_only"
    assert lecture.stages[5].prompts[0].reveal_policy == "allow_verified_reveal"


def test_socratic_lecture_adapts_to_frequency_and_transient_views():
    sweep_packet = solve_circuit(rc_low_pass_sweep_problem())
    transient_packet = solve_circuit(rc_transient_charging_problem())

    assert sweep_packet.socratic_lecture is not None
    sweep_prediction = next(
        stage for stage in sweep_packet.socratic_lecture.stages if stage.id == "predict_before_calculating"
    )
    assert "low frequency" in sweep_prediction.prompts[0].tutor_move
    assert any("ac_sweep" in plot_id for plot_id in sweep_prediction.prompts[0].plot_ids)

    assert transient_packet.socratic_lecture is not None
    transient_model = next(
        stage for stage in transient_packet.socratic_lecture.stages if stage.id == "choose_model"
    )
    assert "storage element" in transient_model.prompts[0].tutor_move


def test_socratic_lecture_requires_bme_nonideality_boundary():
    packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem)

    lecture = packet.socratic_lecture
    assert lecture is not None
    assert "nonideality_and_safety" in _stage_ids(packet)
    assert any("not medical-device certification" in note for note in lecture.safety_notes)

    nonideality = next(stage for stage in lecture.stages if stage.id == "nonideality_and_safety")
    prompt = nonideality.prompts[0]
    assert "loading" in prompt.student_task
    assert prompt.value_refs
    assert any("bme_sampling" in plot_id for plot_id in prompt.plot_ids)
