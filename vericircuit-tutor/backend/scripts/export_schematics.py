from __future__ import annotations

from pathlib import Path

from app.services.demo_parser import (
    bridge_network_alt_problem,
    bridge_network_problem,
    current_divider_problem,
    voltage_divider_problem,
)
from app.services.optcpv_bridge import render_optcpv_schematic_svg
from app.services.variant_generator import generate_goal_variant, generate_value_variant


EXPORT_DIR = Path(__file__).resolve().parents[1] / "schematic_exports"


def export_svg(filename: str, circuit) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / filename
    path.write_text(render_optcpv_schematic_svg(circuit), encoding="utf-8")
    print(path)


def main() -> None:
    bridge = bridge_network_problem()
    bridge_alt = bridge_network_alt_problem()

    exports = {
        "voltage_divider.svg": voltage_divider_problem(),
        "current_divider.svg": current_divider_problem(),
        "bridge_network.svg": bridge,
        "bridge_network_alt.svg": bridge_alt,
        "bridge_network_goal_variant.svg": generate_goal_variant(bridge),
        "bridge_network_alt_value_variant.svg": generate_value_variant(bridge_alt),
    }
    for filename, circuit in exports.items():
        export_svg(filename, circuit)


if __name__ == "__main__":
    main()
