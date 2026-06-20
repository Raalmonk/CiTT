from __future__ import annotations

from app.models.circuit_ir import Component


def format_component_label(component: Component) -> str:
    return f"{component.id} = {_format_value(component.value, component.unit)}"


def _format_value(value: float, unit: str) -> str:
    if unit == "ohm":
        if abs(value) >= 1000:
            return f"{value / 1000:g} kΩ"
        return f"{value:g} Ω"
    if unit == "A" and 0 < abs(value) < 1:
        return f"{value * 1000:g} mA"
    if unit == "F" and 0 < abs(value) < 1:
        return f"{value * 1_000_000:g} uF"
    if unit == "H" and 0 < abs(value) < 1:
        return f"{value * 1000:g} mH"
    if unit == "ideal":
        return "ideal"
    return f"{value:g} {unit}"
