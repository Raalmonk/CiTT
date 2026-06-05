from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.parser_service import parse_problem  # noqa: E402
from app.services.pipeline import solve_circuit  # noqa: E402


SMOKE_PROBLEM = (
    "A 5 V voltage source is connected in series with R1 = 1 kOhm and "
    "R2 = 4 kOhm. Find the voltage across R2 and the current through the circuit."
)


def main() -> int:
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        print("GEMINI_API_KEY or GOOGLE_API_KEY is required for this smoke test.", file=sys.stderr)
        return 2

    parsed = parse_problem(SMOKE_PROBLEM, mode="gemini_strict")
    packet = solve_circuit(parsed.circuit, parser_used=parsed.parser_used)

    print(f"parser_used: {parsed.parser_used}")
    print("Circuit IR:")
    print(json.dumps(parsed.circuit.model_dump(), indent=2))
    print("\nGenerated netlist:")
    print(packet.generated_netlist)
    print(f"\nverification_badge: {packet.verification_badge.label}")
    print("requested_answers:")
    print(json.dumps({key: value.model_dump() for key, value in packet.requested_answers.items()}, indent=2))
    print(
        "calculation_trace.llm_used_for_numerical_answer: "
        f"{packet.calculation_trace.llm_used_for_numerical_answer}"
    )

    return 0 if packet.verification_badge.label == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
