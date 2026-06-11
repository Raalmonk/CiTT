# VeriCircuit Tutor: 5-Minute Professor Demo

## 0:00-0:30 - Frame The Problem

Open with the core claim:

> VeriCircuit Tutor is not a generic AI homework solver. It is a small verified circuit-learning environment. The LLM may help parse or explain, but the final numbers come from circuit validation, Modified Nodal Analysis, and deterministic verification.

Start the backend:

```powershell
cd vericircuit-tutor\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## 0:30-1:30 - Run The Voltage Divider

Select **Voltage Divider** and click **Run pipeline**.

Point to the source-of-truth note in the left panel. Say:

> This is the key architectural boundary. The parser turns the text into Circuit IR. The answer is not accepted until the solver and verifier produce a Solution Packet.

Show the **Parsed Circuit IR** panel:

- Nodes are explicit: `0`, `n1`, `n2`.
- Values are normalized: `10 V`, `2000 ohm`, `3000 ohm`.
- Goals are explicit: voltage across R2 and current through the series path.

## 1:30-2:15 - Show Transparency And Results

Show the **Generated Netlist** panel:

> This netlist is here for transparency. The MVP does not require ngspice, but the circuit representation is inspectable.

Show **Verification Badge**:

> PASS means this packet passed validation, KCL, power balance, unit checks, and requested-answer checks.

Show **Requested Answers**:

- R2 voltage should be about `6 V`.
- Circuit current should be about `2 mA`.

Say clearly:

> These numbers came from the MNA solver, not from direct language-model generation.

## 2:15-3:00 - Show Verification

Open the **Verification** panel and point to:

- Ground exists.
- Component nodes are valid.
- Graph is ground-connected.
- KCL residual is near zero.
- Signed power balance is near zero.
- Requested answers are present.

Then show **Tutor Explanation**:

> The explanation is deliberately boring in the best way: it only cites values already present in the verified Solution Packet. If verification fails, the tutor withholds the numerical explanation.

## 3:00-3:45 - Generate Practice Variants

Click **Value variant**.

> This keeps the topology but changes component values, which is useful for quick practice generation.

Click **Goal variant**.

> This keeps the same circuit but asks for a different quantity, such as another voltage, current, or power.

Emphasize that variants are still Circuit IR and must go through the same solve-and-verify path.

## Optional 2-Minute What-If Demo

Use this when the next demo should emphasize simulation-grounded editing instead of broader component coverage.

1. Select **Voltage Divider**, choose **Gemini strict** if an API key is configured, and click **Run pipeline**.
2. Show the PASS badge, requested answers, and Answer Provenance.
3. In **Circuit Editor**, select `R2`.
4. Change `R2` from `3000` ohm / `3 kOhm` to `6 kOhm`.
5. Click **Update value and re-solve**.
6. Show that `V_R2` changes from `6 V` to `7.5 V`, and current changes from `2 mA` to `1.25 mA`.
7. Show that verification still reports PASS.
8. Explain that the edit updates Circuit IR and the deterministic solver recomputes the answer. The LLM does not calculate the new numerical answer.

Then use **Requested Goals** to select `R1_power`, click **Update goals and re-solve**, and show that R1 power appears as a verified requested answer.

## Optional Probe Mode Demo

Use this to show that the diagram is not just decoration: probes are derived from the verified Solution Packet.

1. Parse and solve the voltage divider.
2. Turn on **Show current pulse**.
3. Click `R2` in the circuit diagram and show current, voltage, power, actual direction, and sign convention.
4. Click node `n2` and show KCL:
   - `R1` entering
   - `R2` leaving
   - residual approximately zero
5. Parse the balanced bridge network.
6. Turn on **Show current pulse**.
7. Click `R5` and show that it has zero or near-zero current.
8. Click `n2` and `n3` and show KCL PASS for both.
9. Run an ambiguous prompt and confirm probe mode is blocked.

Say:

> This is a visual verification overlay, not transient simulation. The moving current marks are animated from DC solution values already verified by the solver and KCL/power checks.

## 3:45-4:30 - Show A Harder MNA Example

Select **Bridge Network** or **Second Bridge Network** and run the pipeline.

Say:

> This is where the architecture starts to matter more than a hand-coded voltage-divider formula. The same MNA path solves a multi-node bridge network, then KCL and power balance verify the result.

Point out node voltages and R5 current, then show the PASS badge.

## Optional AC / Op-Amp Demo

Use this when the demo should show the expanded scope beyond resistor-only DC.

1. Select **RC Low-Pass AC** and run the pipeline.
2. Show that the requested answer is reported as magnitude and phase, not a direct LLM number.
3. Point to AC verification: complex KCL and finite phasor values pass; AC power balance is intentionally not verified in this MVP.
4. Select **Ideal Non-Inverting Op-Amp** and run the pipeline.
5. Show that `Vout` is about `10 V` and the inverting input is held near `1 V`.
6. Emphasize that this is ideal closed-loop DC behavior only.

## 4:30-5:00 - Close With Honest Limits

Close with:

> The MVP scope is intentionally controlled: DC operating point, first-order RC transient templates, AC steady-state phasors for linear R/L/C/source circuits, AC sweep data, and ideal closed-loop op-amp DC. It does not handle general transient analysis, DC inductor behavior, diodes, transistors, nonlinear solving, or nonideal op-amp effects such as rails, saturation, slew rate, bias current, or frequency response. Unsupported or ambiguous problems are marked as such instead of being guessed.

End on the research point:

> The interesting part is not that an AI can talk about circuits. The interesting part is that the tutoring text is downstream of a formal circuit representation, a numerical solver, and verification checks. That is what makes this more than prompt engineering.
