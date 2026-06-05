# Local Debugging And Visual QA

## Circuit Diagram Checks

Run the app:

```powershell
cd vericircuit-tutor\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

Check these demo paths:

1. Run **Bridge Network**.
2. Run **Second Bridge Network**.
3. Generate and load a **Goal variant**.
4. Generate and load a **Value variant**.

In the Circuit Diagram panel, verify:

- R1, R2, R3, R4, and R5 labels are readable.
- n1/src, n2/a, n3/b, and 0 node labels are separated from component labels.
- V1 label does not collide with the source or ground symbol.
- The bridge resistor R5 label is above the horizontal resistor.
- The diagram remains full-width and is not squeezed in the two-column UI.

Diagram generation is deterministic and based only on Circuit IR. It does not affect solver output, MNA verification, or tutor answers.

## Export SVGs For Direct Inspection

You can export the demo schematics without running the web UI:

```powershell
cd vericircuit-tutor\backend
.\.venv\Scripts\python.exe scripts\export_schematics.py
```

This writes SVG files to:

```text
backend/schematic_exports/
```

Open these files directly in a browser:

- `voltage_divider.svg`
- `current_divider.svg`
- `bridge_network.svg`
- `bridge_network_alt.svg`
- `bridge_network_goal_variant.svg`
- `bridge_network_alt_value_variant.svg`

For bridge diagrams, inspect the SVG source or browser dev tools and confirm the renderer descriptor contains:

```text
manual_svg_bridge_network
```

Pytest can confirm that the endpoint returns SVG, the correct renderer is selected, and required labels are present. It cannot fully prove that no visual label overlap exists, so the exported SVGs are the final local visual QA step.

## Progress UI QA

Run the app, open `http://127.0.0.1:8000`, and use the **Run pipeline** button.

Check these paths:

1. Run a Gemini strict voltage divider, if `GEMINI_API_KEY` is configured.
2. Watch progress move through parse, diagram, solve, verify, explain, variants, and done.
3. Confirm the voltage divider with `R1 = 2 kOhm`, `R2 = 3 kOhm`, and `V = 10 V` reports `V_R2 = 6 V` and circuit current `2 mA`.
4. Run an ambiguous topology prompt.
5. Confirm badge `AMBIGUOUS`, no answers are displayed, and variants are skipped.
6. Run an unsupported capacitor or transient-analysis prompt.
7. Confirm badge `UNSUPPORTED`, no answers are displayed, and variants are skipped.
8. Confirm **Answer Provenance** still says `LLM numerical answer allowed: NO`.

OCR and image/PDF recognition are not implemented in this MVP. Current input is text only.
