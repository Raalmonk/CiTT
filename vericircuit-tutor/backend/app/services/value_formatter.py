from __future__ import annotations

from app.models.solution_packet import ComplexQuantityValue, QuantityValue, TutorObservation


def format_value(value: float, unit: str) -> str:
    abs_value = abs(value)
    if unit == "%":
        return f"{value:.6g}%"
    if unit == "ohm":
        if abs_value >= 1_000_000:
            return f"{value / 1_000_000:.6g} Mohm"
        if abs_value >= 1000:
            return f"{value / 1000:.6g} kohm"
        return f"{value:.6g} ohm"
    if unit == "F":
        if 0 < abs_value < 1e-9:
            return f"{value * 1e12:.6g} pF"
        if 0 < abs_value < 1e-6:
            return f"{value * 1e9:.6g} nF"
        if 0 < abs_value < 1:
            return f"{value * 1e6:.6g} uF"
    if unit == "H" and 0 < abs_value < 1:
        return f"{value * 1000:.6g} mH"
    if unit in {"Hz", "hz"}:
        if abs_value >= 1_000_000:
            return f"{value / 1_000_000:.6g} MHz"
        if abs_value >= 1000:
            return f"{value / 1000:.6g} kHz"
        return f"{value:.6g} Hz"
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
    if unit == "deg":
        return f"{value:.6g} deg"
    return f"{value:.6g} {unit}".strip()


def format_quantity(quantity: QuantityValue) -> str:
    return format_value(quantity.value, quantity.unit)


def format_complex_quantity(quantity: ComplexQuantityValue) -> str:
    return (
        f"{format_value(quantity.magnitude, quantity.unit)} angle "
        f"{format_value(quantity.phase_deg, 'deg')}"
    )


def format_observation(observation: TutorObservation) -> str | None:
    if observation.value is None:
        return None
    return format_value(observation.value, observation.unit or "")
