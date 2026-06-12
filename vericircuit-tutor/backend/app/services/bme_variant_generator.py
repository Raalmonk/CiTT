from __future__ import annotations

from dataclasses import dataclass

from app.models.circuit_ir import CircuitProblem, Component


@dataclass(frozen=True)
class BMEPracticeVariant:
    kind: str
    prompt: str
    description: str
    circuit: CircuitProblem


def _component(problem: CircuitProblem, component_id: str) -> Component:
    component = next((item for item in problem.components if item.id == component_id), None)
    if component is None:
        raise KeyError(f"BME variant expected component {component_id!r}.")
    return component


def _set_assumptions(variant: CircuitProblem, assumptions: list[str]) -> None:
    variant.assumptions = assumptions
    if variant.bme_metadata is not None:
        variant.bme_metadata.assumptions = list(assumptions)


def _base_variant(
    problem: CircuitProblem,
    slug: str,
    title_suffix: str,
    assumptions: list[str],
) -> CircuitProblem:
    variant = problem.model_copy(deep=True)
    variant.id = f"{problem.id}_{slug}"
    variant.title = f"{problem.title} - {title_suffix}"
    variant.topology_id = problem.topology_id
    variant.layout_hint = problem.layout_hint.copy() if problem.layout_hint else None
    _set_assumptions(
        variant,
        [
            *assumptions,
            "Practice variant: biomedical parameter changed while the Circuit IR topology stays controlled.",
        ],
    )
    return variant


def _practice(
    problem: CircuitProblem,
    slug: str,
    title_suffix: str,
    prompt: str,
    description: str,
    assumptions: list[str],
) -> BMEPracticeVariant:
    return BMEPracticeVariant(
        kind="bme_what_if",
        prompt=prompt,
        description=description,
        circuit=_base_variant(problem, slug, title_suffix, assumptions),
    )


def _ecg_front_end_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    larger_signal = _practice(
        problem,
        "larger_differential_signal",
        "Larger ECG Differential Signal",
        "What if the ECG differential signal doubles?",
        "Increase the electrode differential signal from 1 mV to 2 mV while keeping common-mode level and gain fixed.",
        [
            "The electrode model is simplified to two ideal DC sources with a 2 mV differential signal.",
            "The common-mode level remains 1 V.",
            "The op-amp is ideal and the matched resistor ratios set a gain of 10.",
        ],
    )
    _component(larger_signal.circuit, "VECGP").value = 1.002

    common_mode_shift = _practice(
        problem,
        "higher_common_mode",
        "Higher ECG Common-Mode Level",
        "What if both electrodes ride on a higher common-mode voltage?",
        "Raise both electrode voltages by 500 mV while preserving the 1 mV differential signal.",
        [
            "The electrode model is simplified to two ideal DC sources with a 1 mV differential signal.",
            "Both electrodes ride on a 1.5 V common-mode level.",
            "The op-amp is ideal and the matched resistor ratios set a gain of 10.",
        ],
    )
    _component(common_mode_shift.circuit, "VECGP").value = 1.501
    _component(common_mode_shift.circuit, "VECGN").value = 1.5

    return [larger_signal, common_mode_shift]


def _emg_band_pass_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    high_pass_shift = _practice(
        problem,
        "higher_high_pass_corner",
        "Higher EMG High-Pass Corner",
        "What if the high-pass corner moves up?",
        "Reduce RHP so slow drift is rejected more aggressively, at the risk of attenuating low-frequency EMG content.",
        [
            "The EMG chain is a passive first-order high-pass followed by a first-order low-pass.",
            "The high-pass corner is shifted upward by reducing RHP.",
            "The source AC magnitude is 1 V so Vout is also the transfer magnitude at the analysis frequency.",
        ],
    )
    _component(high_pass_shift.circuit, "RHP").value = 6800.0

    low_pass_shift = _practice(
        problem,
        "higher_low_pass_corner",
        "Higher EMG Low-Pass Corner",
        "What if the low-pass corner moves up?",
        "Reduce RLP so more high-frequency EMG content passes before downstream filtering.",
        [
            "The EMG chain is a passive first-order high-pass followed by a first-order low-pass.",
            "The low-pass corner is shifted upward by reducing RLP.",
            "The source AC magnitude is 1 V so Vout is also the transfer magnitude at the analysis frequency.",
        ],
    )
    _component(low_pass_shift.circuit, "RLP").value = 2200.0

    return [high_pass_shift, low_pass_shift]


def _pressure_divider_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    higher_pressure = _practice(
        problem,
        "sensor_resistance_increases",
        "Higher Pressure Resistance",
        "What if sensor resistance increases?",
        "Raise RPRESS to model a different pressure operating point in the divider.",
        [
            "The pressure sensor is represented by a resistance of 14 kOhm at this operating point.",
            "The bias resistor and excitation voltage are unchanged.",
        ],
    )
    _component(higher_pressure.circuit, "RPRESS").value = 14_000.0
    return [higher_pressure]


def _pressure_bridge_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    larger_imbalance = _practice(
        problem,
        "active_arm_increases",
        "Larger Bridge Imbalance",
        "What if the pressure-active bridge arm increases more?",
        "Increase R4 to make the bridge differential output larger and reinforce polarity tracking.",
        [
            "The active pressure-sensor arm is modeled as 3.7 kOhm while the other arms are 3.5 kOhm.",
            "The bridge output is still read differentially between the midpoint nodes.",
        ],
    )
    _component(larger_imbalance.circuit, "R4").value = 3700.0
    return [larger_imbalance]


def _strain_gauge_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    higher_strain = _practice(
        problem,
        "gauge_resistance_increases",
        "Higher Strain Gauge Resistance",
        "What if strain makes RG increase more?",
        "Increase the active gauge arm to show how a tiny resistance change becomes a bridge voltage.",
        [
            "Only one bridge arm changes with strain; the gauge arm is now 1005 ohm.",
            "Lead resistance and excitation noise are ignored.",
        ],
    )
    _component(higher_strain.circuit, "RG").value = 1005.0
    return [higher_strain]


def _thermistor_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    warmer = _practice(
        problem,
        "warmer_ntc_point",
        "Warmer NTC Thermistor Point",
        "What if the thermistor gets warmer?",
        "Lower RTH to model an NTC thermistor at a warmer operating point.",
        [
            "The thermistor is represented by an 8 kOhm resistance at a warmer operating point.",
            "The fixed resistor and excitation voltage are unchanged.",
        ],
    )
    _component(warmer.circuit, "RTH").value = 8000.0
    return [warmer]


def _photodiode_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    doubled = _practice(
        problem,
        "photocurrent_doubles",
        "Doubled Photocurrent",
        "What if photocurrent doubles?",
        "Double IPD to model higher light intensity and expose transimpedance output swing limits.",
        [
            "The photodiode is modeled as an ideal 20 uA current source.",
            "The op-amp is ideal and unsaturated in the mathematical model.",
        ],
    )
    _component(doubled.circuit, "IPD").value = 20e-6
    return [doubled]


def _instrumentation_amplifier_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    smaller_rg = _practice(
        problem,
        "rg_gets_smaller",
        "Higher Instrumentation Gain",
        "What if RG gets smaller?",
        "Reduce RG to increase the first-stage instrumentation-amplifier gain.",
        [
            "The three-op-amp instrumentation amplifier is ideal.",
            "The first-stage gain is increased by changing RG to 1 kOhm.",
        ],
    )
    _component(smaller_rg.circuit, "RG").value = 1000.0
    return [smaller_rg]


def _anti_aliasing_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    higher_cutoff = _practice(
        problem,
        "higher_cutoff",
        "Higher Anti-Aliasing Cutoff",
        "What if cutoff frequency increases?",
        "Reduce R1 to raise the RC cutoff for a faster sampling target.",
        [
            "The 1 V AC source makes Vout equal to the low-pass transfer value at 1 kHz.",
            "R1 is reduced to target a higher RC cutoff for a faster sampling setup.",
        ],
    )
    _component(higher_cutoff.circuit, "R1").value = 1590.0

    lower_cutoff = _practice(
        problem,
        "lower_cutoff",
        "Lower Anti-Aliasing Cutoff",
        "What if cutoff frequency decreases?",
        "Increase C1 to lower the cutoff and attenuate more high-frequency content before the ADC.",
        [
            "The 1 V AC source makes Vout equal to the low-pass transfer value at 1 kHz.",
            "C1 is increased to target a lower RC cutoff for stronger anti-aliasing before a slower ADC.",
        ],
    )
    _component(lower_cutoff.circuit, "C1").value = 220e-9

    return [higher_cutoff, lower_cutoff]


BME_VARIANT_FACTORIES = {
    "bme_ecg_front_end": _ecg_front_end_variants,
    "bme_emg_band_pass_chain": _emg_band_pass_variants,
    "bme_pressure_sensor_divider": _pressure_divider_variants,
    "bme_pressure_sensor_bridge": _pressure_bridge_variants,
    "bme_strain_gauge_wheatstone": _strain_gauge_variants,
    "bme_thermistor_divider": _thermistor_variants,
    "bme_photodiode_tia": _photodiode_variants,
    "bme_instrumentation_amplifier": _instrumentation_amplifier_variants,
    "bme_anti_aliasing_low_pass": _anti_aliasing_variants,
}


def generate_bme_practice_variants(problem: CircuitProblem) -> list[BMEPracticeVariant]:
    key = problem.topology_id or problem.id
    factory = BME_VARIANT_FACTORIES.get(key)
    if factory is None:
        return []
    return factory(problem)


def generate_bme_value_variant(problem: CircuitProblem) -> CircuitProblem | None:
    variants = generate_bme_practice_variants(problem)
    return variants[0].circuit if variants else None

