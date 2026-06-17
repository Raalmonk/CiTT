# Gemini-Style Tutor Strategy

This note describes the tutor behavior we want once OptCPV is responsible for polished schematic rendering. The tutor should generate semantic teaching moves, not pixel coordinates and not unverified final answers.

## Contract

Inputs:

- `CircuitProblem`: components, nodes, goals, references, analysis type, assumptions.
- `SolutionPacket`: verified solver values, badge, checks, calculation trace.
- Optional visual artifact: OptCPV SVG/artifact with component bboxes, net metadata, labels, and viewBox.

Outputs:

- A step sequence that can drive real-time zoom and highlight.
- Each step focuses by component, node, current-path, or goal IDs.
- Each step teaches one relationship, asks one student-facing question, and reveals verified values only when pedagogically appropriate.
- Each step carries a lightweight self-evaluation so the planner can revise weak steps before the UI shows them.

The LLM must not invent numerical values. It may refer to symbolic laws and verified value references, but final numbers are rendered from `SolutionPacket`, `TutorObservation`, `AnalysisView`, or deterministic metadata.

## Proposed Tutor Move Shape

The current `TutorStep` already has most playback fields. Gemini-style planning should conceptually produce:

```json
{
  "id": "dc_coupled_node_map",
  "title": "Map the coupled interior nodes",
  "focus": {
    "components": ["R1", "R2", "R5", "R3", "R4"],
    "nodes": ["n2", "n3"],
    "current_paths": ["R5"],
    "goals": []
  },
  "look_at": "Look at the interior nodes and the branch that ties them together.",
  "student_prompt": "Before seeing numbers, which node voltages must be solved together?",
  "hint_ladder": [
    "Find every branch touching the highlighted nodes.",
    "If a branch connects the two highlighted nodes, neither side is an independent divider.",
    "Use KCL at the interior nodes."
  ],
  "reveal_policy": "reveal_verified_values_after_student_attempt",
  "verified_value_refs": [],
  "self_evaluation": {
    "visual_grounding": 2,
    "socratic_quality": 2,
    "answer_leakage": 0,
    "risk": "May focus many branches on dense circuits; split into smaller neighborhoods if bbox is too wide."
  }
}
```

The UI does not have to render every field immediately. The important point is that planning is a sequence of tutor moves, not a prose template.

## Planning Algorithm

1. Anchor references.
   Identify ground, source terminals, and requested references before discussing any formula.

2. Build the relation graph.
   Nodes are circuit nodes. Edges are components. Mark source-constrained nodes, unknown interior nodes, goal targets, coupling branches, and storage/reactive elements.

3. Choose the teaching lens.
   Use a motif only when the motif is structurally isolated. A voltage divider is a simple divider only if the midpoint has exactly the upper and lower divider branches. If an extra branch touches the midpoint, switch to nodal or graph-cut teaching.

4. Cut the circuit into teachable regions.
   Prefer these cuts: source/reference anchor, unknown-node set, target neighborhood, verification boundary. For dense circuits, split by articulation nodes or by one-hop neighborhoods around goals.

5. Use Socratic reveal.
   Each step asks for a prediction or relationship first. Verified numbers are revealed only after the student has seen the relevant reference, polarity, and law.

6. Self-check and repair.
   Reject or rewrite steps that leak final answers early, lack focus IDs, cite unsupported laws, or use a shortcut contradicted by the graph.

## Example: Simple Voltage Divider

Goal: explain output voltage or current without immediately giving both final values.

Steps:

1. `divider_reference`
   Focus `V1`, top node, ground.
   Prompt: "Which node is fixed by the source, and relative to what?"
   Reveal: top-node verified value may be shown.
   Self-eval: strong visual grounding; no final-goal leakage.

2. `divider_series_path`
   Focus `R1`, `R2`, top/mid/ground nodes.
   Prompt: "Is there only one path for current through the two resistors?"
   Hint: "If no branch leaves the midpoint except the lower resistor, the same current flows through both."
   Reveal: series current only if it is a requested or supporting verified value.
   Self-eval: safe only if midpoint has no extra branch.

3. `divider_output`
   Focus lower resistor, output node, goal.
   Prompt: "Which two nodes define the requested output?"
   Reveal: requested verified value.
   Self-eval: good tutor step because polarity is checked before value.

## Example: Current Divider

Steps:

1. `current_divider_source`
   Focus current source, common top node, ground.
   Prompt: "Where does the total current enter the branch network?"
   Reveal: common node voltage only after the shared node is identified.

2. `current_divider_parallel_branches`
   Focus all branch resistors.
   Prompt: "Which branch should carry more current: larger resistance or smaller resistance?"
   Hint: "Parallel branches share voltage; current follows conductance."
   Reveal: branch currents one at a time, not all at once.

3. `current_divider_requested_values`
   Focus requested branch goals.
   Prompt: "Check the requested current direction before reading the sign."
   Reveal: verified requested answers.

Self-QA: The plan does not say current splits equally; every value is tied to a branch direction.

## Example: Bridge Network

Problem shape: source to two divider-like sides, plus a resistor between the midpoints.

Steps:

1. `dc_sources_and_ground`
   Focus source, source node, ground.
   Prompt: "Which node is known before solving KCL?"

2. `dc_coupled_node_map`
   Focus interior nodes and all branches touching them, especially the bridge resistor.
   Prompt: "Can the two midpoint voltages be solved independently?"
   Hint: "The bridge resistor carries current based on the difference between the two midpoint voltages."
   Reveal: no numerical values yet.

3. `dc_target_kcl_neighborhood`
   Focus requested nodes and bridge branch.
   Prompt: "For the bridge current, which node is the from-node and which is the to-node?"
   Hint: "Write KCL at the interior nodes before reading the current sign."
   Reveal: no final value until polarity is checked.

4. `dc_requested_answer`
   Focus all requested goals.
   Prompt: "Now read the verified values and compare signs with the requested references."
   Reveal: requested verified values.

Self-QA: This avoids the false divider shortcut. Visual focus may be wide, so OptCPV bbox feedback can split the coupling step into left midpoint and right midpoint if needed.

## Example: RC Low-Pass AC

Steps:

1. `ac_source_frequency`
   Focus AC source and input node.
   Prompt: "What changes when the same circuit is analyzed at a frequency instead of DC?"
   Reveal: analysis frequency.

2. `ac_low_pass_pole`
   Focus series resistor and shunt capacitor.
   Prompt: "As frequency rises, does the capacitor look more open or more like a path to ground?"
   Hint: "Use capacitor impedance, then locate the output node."
   Reveal: corner-frequency observation if available.

3. `ac_output_phasor`
   Focus output node and goal.
   Prompt: "Do we need magnitude only, or magnitude plus phase?"
   Reveal: verified phasor magnitude and phase.

Self-QA: Does not treat AC as a DC scalar; output reference is visible before reveal.

## Example: Transimpedance Amplifier

Steps:

1. `tia_input_current`
   Focus current source/sensor branch.
   Prompt: "Is the input signal a current or a voltage?"

2. `tia_summing_node`
   Focus op-amp input node and feedback meeting point.
   Prompt: "If feedback holds the input node near reference in the ideal model, where must the input current go?"

3. `tia_feedback_conversion`
   Focus feedback resistor and output.
   Prompt: "How does current through feedback become an output voltage, and what sets the polarity?"
   Reveal: verified output only after polarity is discussed.

Self-QA: Keeps ideal-op-amp assumptions explicit and avoids pretending this is a real hardware rail/noise model.

## Example: Unknown General DC Network

When no safe motif is detected:

1. `dc_sources_and_ground`
   Focus sources and ground.
   Prompt: "What is known before solving?"

2. `dc_node_relationships`
   Focus non-reference nodes and their incident branches.
   Prompt: "Which node voltages are unknown, and which components connect them?"
   Hint: "Every highlighted branch contributes one current term to a KCL equation."

3. `dc_target_neighborhood`
   Focus the requested branch or node plus one-hop neighbors.
   Prompt: "Which local KCL terms directly control the requested value?"

4. `dc_requested_answer`
   Focus goals.
   Prompt: "Check reference and sign, then read the verified value."

5. `verification_boundary`
   Focus goals/checks.
   Prompt: "Which checks passed, and what does internal verification not prove?"

Self-QA: This is less elegant than a named motif, but it scales to arbitrary supported linear networks because it follows the graph rather than a template.

## Self-QA Checklist

Before returning a lesson packet:

- Does every major step have focus IDs that exist in the circuit and can map to OptCPV artifact metadata?
- Did the tutor ask at least one question before revealing requested final values?
- Are all numerical values references to verified packet fields or deterministic observations?
- Did motif detection check structural preconditions, not only component names or topology IDs?
- For complex circuits, is there a node-relationship or graph-cut step before readout?
- Are current directions and voltage references named before values are shown?
- Does the verification step explain the difference between internal consistency and independent correctness?
- If focus is visually too broad, can the step be split into source, left neighborhood, right neighborhood, coupling branch, and target?

## UI Playback Notes

OptCPV should stay semantic:

- Convert `focus.components` to component bboxes.
- Convert `focus.nodes` to net pin clusters or node markers.
- Convert `focus.current_paths` to wire/path highlights.
- Compute zoom from the union of selected bboxes with padding.
- Keep the active step label visible beside the diagram.

The tutor should never depend on absolute pixels. If OptCPV improves layout, the same lesson steps should still play correctly.
