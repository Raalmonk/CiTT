# CiTT Simscape Model Build Report

## 1. Executive Summary & SATK/MCP Diagnostic Failure

This report documents an attempt by the autonomous engineering agent to construct the Simscape model for the **Series RC AC Circuit** from the supplied structured circuit specification.

During the execution of the modeling workflow, the dedicated MATLAB Model-Based Design Model Tool Suite (SATK) encountered a critical system-level issue:
- **Error Status:** `failed to attach to MATLAB session` across all MCP tool interfaces (`mcp_matlab_model_edit`, `mcp_matlab_model_overview`, `mcp_matlab_model_read`, and `mcp_matlab_evaluate_matlab_code`).
- **Root Cause:** In the current headless running environment, either no local MATLAB desktop or shared session was accessible, or the MATLAB engine interface was unable to establish the IPC channel needed for the Model Agentic Toolkit.
- **Strict Compliance Guardrails Applied:** 
  - In accordance with the prompt's explicit directives, the agent **did not** invoke local model-construction helpers or raw generated build scripts.
  - The agent **did not** generate or execute any temporary build scripts like `citt_build_simscape_model.m`.
  - Instead of using non-compliant local model builders or unguided raw files, this engineering report serves as the official artifact documenting the SATK/MCP failure while defining the complete, build-ready architectural schematic and focus/probe map definitions.

---

## 2. Structured Circuit Specification Analysis

The structured JSON circuit specification defines a standard series RC circuit operating under an AC voltage source:
- **AC Voltage Source (V1):** Amplitude = $1.5\text{ V (peak)}$ ($3\text{ V}_{pp}$), Frequency = $50\text{ Hz}$.
- **Resistor (R1):** Resistance = $100\ \Omega$.
- **Capacitor (C1):** Capacitance = $1\text{ F}$ (as per the specification, mathematically treated literally).

### Mathematical Analysis & Learning Challenges:
1. **Capacitive Reactance ($X_C$):**
   $$X_C = \frac{1}{2\pi f C} = \frac{1}{2\pi \cdot 50 \cdot 1} \approx 0.003183\ \Omega$$
2. **Circuit Impedance ($Z$):**
   $$Z = \sqrt{R^2 + X_C^2} = \sqrt{100^2 + 0.003183^2} \approx 100\ \Omega$$
3. **Phase Angle ($\theta$):**
   $$\theta = -\arctan\left(\frac{X_C}{R}\right) = -\arctan\left(\frac{0.003183}{100}\right) \approx -0.00182^\circ$$
4. **Current ($\text{I}_{\text{peak}}$):**
   $$\text{I}_{\text{peak}} = \frac{\text{V}_{\text{peak}}}{Z} \approx \frac{1.5}{100} = 15\text{ mA}$$

*Teaching Insight:* A capacitance of $1\text{ F}$ at $50\text{ Hz}$ makes the circuit's impedance almost purely resistive. The phase shift between voltage and current is extremely close to zero degrees, which is an excellent starting topic for teaching students how extremely large capacitance acts practically as an AC short circuit.

---

## 3. Simscape-First Model Architecture Plan

Once the MATLAB session attachment is restored, the model should be built strictly using the following Simscape Electrical library components and connections.

### 3.1 Component Registry
The table below specifies the blocks to be added to the blank model `citt_generated_model.slx`:

| Block ID (Ref) | Display Name / Type | Parameter Name | Target Parameter Value | Simscape Library Source Path |
| :--- | :--- | :--- | :--- | :--- |
| `v1` | `AC Voltage Source` | `Amplitude`, `Frequency` | `1.5` V, `50` Hz | `ee_lib/Sources/AC Voltage Source` |
| `r1` | `Resistor` | `R` | `100` Ohm | `ee_lib/Passive Devices/Resistor` |
| `c1` | `Capacitor` | `C` | `1` F | `ee_lib/Passive Devices/Capacitor` |
| `gnd` | `Electrical Reference` | N/A | Reference node (0V) | `ee_lib/Passive Devices/Electrical Reference` |
| `sc` | `Solver Configuration`| N/A | Standard settings | `nesl_utility/Solver Configuration` |
| `isens` | `Current Sensor` | N/A | Series current monitor | `ee_lib/Sensors/Current Sensor` |
| `vsens` | `Voltage Sensor` | N/A | Voltage probe across V1 | `ee_lib/Sensors/Voltage Sensor` |
| `ps_i` | `PS-Simulink Converter`| N/A | Sensor signal output | `nesl_utility/PS-Simulink Converter` |
| `ps_v` | `PS-Simulink Converter`| N/A | Sensor signal output | `nesl_utility/PS-Simulink Converter` |

### 3.2 Connectivity Schema (using `<->` Physical Connection Syntax)
The physical electrical nodes map to specific Simscape connections:
```text
  [ V1 (pos) ]  <----------------->  [ Current Sensor (p) ]
  [ Current Sensor (n) ]  <--------->  [ Resistor R1 (t1) ]
  [ Resistor R1 (t2) ]  <----------->  [ Capacitor C1 (t1) ]
  [ Capacitor C1 (t2) ]  <----------->  [ V1 (neg) ]
  [ Electrical Reference ]  <-------->  [ V1 (neg) ] (Reference Node N0)
  [ Solver Configuration (f) ]  <---->  [ V1 (neg) ]
```

### 3.3 Target Signal Logging / Sensing Ports
To monitor and measure the outputs requested by the spec:
- **Current Measurement:**
  - Connect a physical current sensor `isens` in series.
  - S-port of `isens` connects to `ps_i` (PS-Simulink Converter) to expose the raw current signal to Simulink.
- **Voltage Measurement:**
  - Connect a voltage sensor `vsens` in parallel with `V1` (positive to terminal `pos`, negative to `neg`).
  - S-port of `vsens` connects to `ps_v` to expose the raw voltage signal.

---

## 4. Focus Map Definitions

The pedagogical focus map identifies learning targets mapped to structural model blocks and lines:

1. **Focus ID: `impedance_calculation`**
   - *Label:* Capacitive Reactance
   - *Explanation:* At $50\text{ Hz}$, a $1\text{ F}$ capacitor has an extremely low reactance ($X_C \approx 0.00318\ \Omega$), making the circuit highly resistive.
   - *Model Paths:* `citt_generated_model/C1`
   - *Block Paths:* `citt_generated_model/C1`
   - *Related Components:* `C1`
   - *Related Nodes:* `N2`, `N0`
   - *Teaching Question:* What is the capacitive reactance of a 1 Farad capacitor at 50 Hz, and how does it compare to the 100 Ohm resistor?

2. **Focus ID: `phase_angle`**
   - *Label:* Phase Difference
   - *Explanation:* Since R is much larger than $X_C$, the phase shift is very close to $0$ degrees (current and voltage almost in phase).
   - *Model Paths:* `citt_generated_model/R1`, `citt_generated_model/C1`
   - *Block Paths:* `citt_generated_model/R1`, `citt_generated_model/C1`
   - *Related Components:* `R1`, `C1`
   - *Related Nodes:* `N1`, `N2`, `N0`
   - *Teaching Question:* How does the massive difference between resistance and reactance affect the phase angle between total voltage and current?

---

## 5. Probe Map Definitions

To verify student measurements, the following virtual diagnostic probes should be bound to the simulation output:

1. **Probe ID: `probe_i_rms`**
   - *Focus ID:* `impedance_calculation`
   - *Label:* RMS Current ($I_{rms}$)
   - *Target Type:* block
   - *Model Paths:* `citt_generated_model/Current Sensor`
   - *Block Paths:* `citt_generated_model/Current Sensor`
   - *Quantity:* RMS Current
   - *Unit:* `A`
   - *Suggested Sensor:* Simscape Current Sensor connected in series with R1 and C1.
   - *Instructions:* Measure the current flowing through the series RC circuit. Use an RMS block to calculate the RMS value of the current signal.

2. **Probe ID: `probe_i_peak`**
   - *Focus ID:* `impedance_calculation`
   - *Label:* Peak Current ($I_{peak}$)
   - *Target Type:* block
   - *Model Paths:* `citt_generated_model/Current Sensor`
   - *Block Paths:* `citt_generated_model/Current Sensor`
   - *Quantity:* Peak Current
   - *Unit:* `A`
   - *Suggested Sensor:* Simscape Current Sensor connected in series with R1 and C1.
   - *Instructions:* Determine the peak value of the current waveform from the current sensor output.

3. **Probe ID: `probe_i_pp`**
   - *Focus ID:* `impedance_calculation`
   - *Label:* Peak-to-Peak Current ($I_{pp}$)
   - *Target Type:* block
   - *Model Paths:* `citt_generated_model/Current Sensor`
   - *Block Paths:* `citt_generated_model/Current Sensor`
   - *Quantity:* Peak-to-Peak Current
   - *Unit:* `A`
   - *Suggested Sensor:* Simscape Current Sensor connected in series with R1 and C1.
   - *Instructions:* Calculate peak-to-peak current by measuring the difference between the maximum and minimum values of the current waveform.

4. **Probe ID: `probe_phase`**
   - *Focus ID:* `phase_angle`
   - *Label:* Phase Relationship between Voltage and Current
   - *Target Type:* block
   - *Model Paths:* `citt_generated_model/Current Sensor`, `citt_generated_model/Voltage Sensor`
   - *Block Paths:* `citt_generated_model/Current Sensor`, `citt_generated_model/Voltage Sensor`
   - *Quantity:* Phase Difference
   - *Unit:* `degrees`
   - *Suggested Sensor:* Simscape Current Sensor and Voltage Sensor logged simultaneously.
   - *Instructions:* Compare the zero-crossing times or peak times of the source voltage and the series current to find the phase angle shift.

---

## 6. Verification and Validation Plan

Once the local MATLAB session becomes attachable, the following verification process should be executed:
1. **Structural Audit (`model_check`):**
   - Run connectivity audits to verify there are no unconnected ports or dangling signal lines.
   - Ensure the solver is correctly configured and the solver configuration block is tied to the electrical reference node.
2. **Behavioral Audit:**
   - Run a short simulation transient run (e.g. StopTime = $0.1$ seconds to capture $5$ complete cycles of a $50\text{ Hz}$ sine wave).
   - Verify that the simulated peak current is approximately $15\text{ mA}$ and the phase difference is effectively $0^\circ$, matching our analytical bounds.
