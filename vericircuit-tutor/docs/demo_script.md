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

## 3:45-4:30 - Show A Harder MNA Example

Select **Bridge Network** or **Second Bridge Network** and run the pipeline.

Say:

> This is where the architecture starts to matter more than a hand-coded voltage-divider formula. The same MNA path solves a multi-node bridge network, then KCL and power balance verify the result.

Point out node voltages and R5 current, then show the PASS badge.

## 4:30-5:00 - Close With Honest Limits

Close with:

> The MVP scope is intentionally narrow: linear DC circuits with resistors and independent sources. It does not handle op-amps, capacitors, inductors, diodes, transistors, dependent sources, AC, transient analysis, or schematic/image parsing yet. Unsupported or ambiguous problems are marked as such instead of being guessed.

End on the research point:

> The interesting part is not that an AI can talk about circuits. The interesting part is that the tutoring text is downstream of a formal circuit representation, a numerical solver, and verification checks. That is what makes this more than prompt engineering.

