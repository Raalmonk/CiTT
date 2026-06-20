# Lab-Guided Teaching Structure

This note defines how CiTT should turn the error lab into a guided lecture, not just a simulator panel.

## Core Pace

1. Establish the nominal claim.
   - Ask what the ideal answer represents.
   - Ask which output or node should be watched before any error is introduced.

2. Activate one physical error source.
   - Prefer one family at a time: component value, source generation, op-amp input, saturation, breadboard, or readout.
   - Ask for a sign prediction before running the lab.

3. Run baseline versus lab truth versus measured readout.
   - Baseline is the ideal or previously verified circuit.
   - Lab truth is the solved circuit after nonidealities are stamped into the circuit model.
   - Measured readout is what the instrument would display after meter gain/offset.

4. Use the sensitivity sweep.
   - Ask whether the curve is monotonic, flat, clipped, or unexpectedly curved.
   - Ask which physical path gives the sign of the slope.

5. Use a counterfactual.
   - For input bias current, compare bias compensation off versus on.
   - For saturation, compare the desired linear output with the allowed rail window.
   - For breadboard leakage, compare low-impedance and high-impedance nodes.

6. Transfer.
   - Ask what design change would reduce the error.
   - Ask what measurement change would only hide the error instead of fixing the circuit.

## Preset Lab Scripts

### Resistor Drift

Tutor move:
"Before calculating, decide whether this resistor drifting upward should raise or lower the watched output."

Student evidence:
- Names the watched quantity.
- Identifies whether the resistor is in the top leg, bottom leg, feedback leg, or load path.
- Predicts the sign.

Reveal policy:
- Run the lab only after the sign prediction.
- Show the sensitivity plot before the final numeric explanation.

### Op-Amp Input Bias Current

Tutor move:
"Where does the bias current flow, and what resistance turns that tiny current into a voltage?"

Student evidence:
- Identifies both input terminals.
- Computes or estimates the resistance seen by the inverting input.
- Explains why matching that resistance at the non-inverting input can cancel bias-current voltage drops.

Counterfactual:
- Run with compensation off.
- Run with compensation on.
- Compare output shift magnitudes, not only final output values.

### Op-Amp Saturation

Tutor move:
"First calculate what the linear closed-loop model wants. Then ask whether the real output stage can produce it."

Student evidence:
- Gives the desired linear output.
- States the rail window after swing margin.
- Predicts clipping before seeing the result.

Reveal policy:
- If saturation occurs, emphasize that feedback cannot force impossible output voltage.

### Source And Readout Error

Tutor move:
"Is this error upstream of the circuit, or only in the displayed measurement?"

Student evidence:
- Separates generated source value from solved circuit response.
- Separates lab truth from measured readout.

Key distinction:
- Source error changes the stimulus and therefore the circuit truth.
- Readout error changes the display without changing the solved circuit.

### Breadboard Parasitics

Tutor move:
"Which node has high enough impedance that leakage or pF-level capacitance can matter?"

Student evidence:
- Names a high-impedance node.
- Predicts extra loading or an extra pole.
- Explains why DC ignores capacitance but AC/transient does not.

## Gemini Prompt Fragment

Use this fragment when asking Gemini to drive the lab as a Socratic lecture:

```text
You are CiTT's lab tutor. Use the verified SolutionPacket, LabSimulationResponse, and circuit IR.

Rules:
- Do not reveal the final numeric result until the student makes a sign prediction.
- Treat baseline, lab truth, and measured readout as three separate claims.
- When sensitivity_sweeps exists, ask about the shape and sign of the curve before explaining the number.
- When counterfactuals exists, compare the control case against the current lab case before giving design advice.
- For op-amp input bias current, always ask which resistance converts input bias current into voltage error.
- For saturation, always ask for the desired linear output and the rail window.
- For breadboard parasitics, always ask whether the watched node is high impedance.
- For readout error, explicitly say that the meter changed, not the circuit truth.

Recommended response pace:
1. Ask one prediction question.
2. Wait for the student's commitment.
3. Run or cite the lab result.
4. Ask the student to explain the sign.
5. Only then summarize the verified numeric comparison.
```
