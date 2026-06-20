import math

import pytest

from app.services.bme_templates import BME_TEMPLATE_FACTORIES
from app.services.demo_parser import (
    rc_low_pass_problem,
    rc_low_pass_sweep_problem,
    rc_transient_charging_problem,
    voltage_divider_problem,
)
from app.services.pipeline import solve_circuit


def _plots_by_id(packet):
    return {plot.id: plot for plot in packet.teaching_plots}


def _points_by_label(plot):
    return {point.x_label: point for point in plot.series[0].points}


def test_dc_solution_exposes_node_current_and_power_teaching_plots():
    packet = solve_circuit(voltage_divider_problem())
    plots = _plots_by_id(packet)

    assert {
        "dc_node_voltage_levels",
        "dc_component_current_flow",
        "dc_power_balance",
    }.issubset(plots)

    node_points = _points_by_label(plots["dc_node_voltage_levels"])
    assert node_points["n1"].y == pytest.approx(10.0)
    assert node_points["n2"].y == pytest.approx(6.0)

    current_points = _points_by_label(plots["dc_component_current_flow"])
    assert current_points["R1"].y == pytest.approx(0.002)
    assert current_points["R2"].y == pytest.approx(0.002)

    power_plot = plots["dc_power_balance"]
    assert power_plot.source == "verification"
    assert sum(point.y for point in power_plot.series[0].points) == pytest.approx(0.0)


def test_ac_sweep_exposes_bode_style_teaching_plots():
    packet = solve_circuit(rc_low_pass_sweep_problem())
    plots = _plots_by_id(packet)

    magnitude_plot = plots["ac_sweep_magnitude_response"]
    phase_plot = plots["ac_sweep_phase_response"]

    assert magnitude_plot.x_scale == "log"
    assert phase_plot.x_scale == "log"
    assert magnitude_plot.y_label == "Magnitude (dB)"
    assert phase_plot.y_label == "Phase (deg)"

    answer_series = next(series for series in magnitude_plot.series if series.id == "answer:vout")
    assert len(answer_series.points) == len(packet.ac_sweep)
    assert answer_series.points[0].x == pytest.approx(packet.ac_sweep[0].frequency_hz)
    assert answer_series.points[0].y > answer_series.points[-1].y


def test_ac_single_frequency_exposes_phasor_teaching_plots():
    packet = solve_circuit(rc_low_pass_problem())
    plots = _plots_by_id(packet)

    magnitude_points = _points_by_label(plots["ac_phasor_magnitudes"])
    phase_points = _points_by_label(plots["ac_phasor_phases"])

    assert magnitude_points["vout"].y == pytest.approx(0.7071, rel=1e-3)
    assert phase_points["vout"].y == pytest.approx(-45.0, abs=1e-2)


def test_rc_transient_exposes_time_and_normalized_settling_teaching_plots():
    packet = solve_circuit(rc_transient_charging_problem())
    plots = _plots_by_id(packet)

    voltage_plot = plots["transient_capacitor_voltage"]
    normalized_plot = plots["transient_normalized_settling"]

    assert voltage_plot.markers[0].label == "1 tau"
    assert voltage_plot.series[0].points[0].y == pytest.approx(0.0)
    assert voltage_plot.series[0].points[-1].y == pytest.approx(
        5.0 * (1.0 - math.exp(-5.0)),
        rel=2e-3,
    )

    assert normalized_plot.x_label == "Time constants (t/tau)"
    assert {marker.label for marker in normalized_plot.markers} == {"1 tau", "63.2%"}
    assert normalized_plot.series[0].points[-1].y == pytest.approx(
        1.0 - math.exp(-5.0),
        rel=2e-3,
    )


def test_bme_context_exposes_sampling_cmrr_and_noise_teaching_plots():
    anti_alias_packet = solve_circuit(
        BME_TEMPLATE_FACTORIES["bme_anti_aliasing_low_pass"]().circuit_problem
    )
    anti_alias_plots = _plots_by_id(anti_alias_packet)
    sampling_points = _points_by_label(anti_alias_plots["bme_sampling_frequency_landmarks"])

    assert sampling_points["ADC sampling frequency"].y == pytest.approx(4000.0)
    assert sampling_points["ADC Nyquist frequency"].y == pytest.approx(2000.0)

    ecg_packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_ecg_front_end"]().circuit_problem)
    ecg_plots = _plots_by_id(ecg_packet)
    input_mode_points = _points_by_label(ecg_plots["bme_differential_common_mode_inputs"])

    assert input_mode_points["Differential"].y == pytest.approx(0.001)
    assert input_mode_points["Common-mode"].y == pytest.approx(1.0005)
    assert ecg_plots["bme_cmrr_mismatch_what_if"].series[0].points[0].y == pytest.approx(
        -0.009095454545455775
    )

    tia_packet = solve_circuit(BME_TEMPLATE_FACTORIES["bme_photodiode_tia"]().circuit_problem)
    tia_plots = _plots_by_id(tia_packet)
    assert "bme_noise_budget_v_rms" in tia_plots
    assert "bme_noise_budget_a_rms" in tia_plots
    assert tia_plots["bme_noise_budget_v_rms"].series[0].points
    assert tia_plots["bme_noise_budget_a_rms"].series[0].points
