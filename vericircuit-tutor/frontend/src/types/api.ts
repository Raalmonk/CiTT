export type AnalysisType =
  | "dc_operating_point"
  | "ac_steady_state"
  | "ac_single_frequency"
  | "ac_sweep"
  | "rc_transient";

export type GoalQuantity =
  | "node_voltage"
  | "component_voltage"
  | "component_current"
  | "component_power"
  | "source_power";

export type ComponentRole =
  | "source"
  | "load"
  | "filter"
  | "feedback"
  | "op_amp"
  | "bridge"
  | "generic";

export type EntityKind = "component" | "node" | "goal" | "wire";

export type EntityRef = {
  kind: EntityKind;
  id: string;
};

export type ACSweepConfig = {
  start_hz: number;
  stop_hz: number;
  points_per_decade: number;
  scale: "log" | "linear";
};

export type RCTransientConfig = {
  capacitor_id?: string | null;
  initial_voltage_v: number;
  time_points_s: number[];
};

export type BMETemplateMetadata = {
  biomedical_context: string;
  signal_chain_role: string;
  assumptions: string[];
  what_students_should_learn: string[];
  common_lab_mistakes: string[];
  typical_signal_range?: string | null;
  safety_note?: string | null;
  noise_sources: string[];
  real_world_nonidealities: string[];
  recommended_next_block?: string | null;
  nominal_supply_rails_v?: Record<string, number> | null;
  supply_positive_v?: number | null;
  supply_negative_v?: number | null;
  output_swing_margin_v: number;
  adc_sampling_frequency_hz?: number | null;
  adc_target_cutoff_hz?: number | null;
  adc_resolution_bits?: number | null;
  adc_full_scale_voltage_v?: number | null;
  adc_input_impedance_ohm?: number | null;
  noise_bandwidth_hz?: number | null;
  thermal_noise_temperature_k: number;
  thermal_noise_resistor_ids: string[];
  photodiode_shot_noise_current_id?: string | null;
  op_amp_input_noise_nv_per_sqrt_hz?: number | null;
  flicker_noise_corner_hz?: number | null;
  flicker_noise_component_ids: string[];
  cmrr_mismatch_percent?: number | null;
  cmrr_mismatch_component_id?: string | null;
};

export type CircuitComponent = {
  id: string;
  type: string;
  nodes: string[];
  value: number;
  unit: string;
  label?: string | null;
  current_reference?: Record<string, unknown> | null;
  voltage_reference?: Record<string, unknown> | null;
  ac_magnitude?: number | null;
  ac_phase_deg?: number | null;
  open_loop_gain?: number | null;
  gain_bandwidth_hz?: number | null;
  bandwidth_hz?: number | null;
  supply_positive_v?: number | null;
  supply_negative_v?: number | null;
  output_swing_margin_v?: number | null;
  input_bias_current_a?: number | null;
  slew_rate_v_per_s?: number | null;
  clipping_recovery_s?: number | null;
  output_current_limit_a?: number | null;
  input_offset_voltage_v?: number | null;
  input_resistance_ohm?: number | null;
  output_resistance_ohm?: number | null;
  compensation_capacitance_f?: number | null;
  clamp_diode_saturation_current_a?: number | null;
  saturation_current_a?: number | null;
  emission_coefficient?: number | null;
  thermal_voltage_v?: number | null;
};

export type CircuitGoal = {
  id: string;
  quantity: GoalQuantity;
  target: string;
  reference?: Record<string, unknown> | null;
};

export type CircuitProblem = {
  id: string;
  title: string;
  analysis_type: AnalysisType;
  frequency_hz?: number | null;
  sweep?: ACSweepConfig | null;
  transient?: RCTransientConfig | null;
  topology_id?: string | null;
  layout_hint?: Record<string, unknown> | null;
  ground_node: string;
  nodes: string[];
  components: CircuitComponent[];
  goals: CircuitGoal[];
  assumptions: string[];
  bme_metadata?: BMETemplateMetadata | null;
  nonblocking_ambiguities: string[];
  ambiguities: string[];
  unsupported_features: string[];
};

export type VisualPoint = {
  x: number;
  y: number;
};

export type VisualNode = {
  id: string;
  label: string;
  position: VisualPoint;
  role: "ground" | "input" | "output" | "internal";
};

export type VisualComponent = {
  id: string;
  type: string;
  label: string;
  nodes: string[];
  role: ComponentRole;
  orientation: "horizontal" | "vertical" | "triangle" | "auto";
};

export type VisualWire = {
  id: string;
  from_node: string;
  to_node: string;
  component_id?: string | null;
  points: VisualPoint[];
};

export type VisualFocusRegion = {
  id: string;
  label: string;
  components: string[];
  nodes: string[];
  goals: string[];
};

export type VisualOverlay = {
  id: string;
  kind:
    | "goal_reference"
    | "kcl_node"
    | "current_path"
    | "phasor_hint"
    | "lesson_focus";
  label: string;
  focus_region_id?: string | null;
  enabled_by_default: boolean;
};

export type VisualCircuit = {
  circuit_id: string;
  renderer: string;
  layout_strategy: string;
  nodes: VisualNode[];
  components: VisualComponent[];
  wires: VisualWire[];
  annotations: Array<Record<string, unknown>>;
  overlays: VisualOverlay[];
  focus_regions: VisualFocusRegion[];
  warnings: string[];
};

export type QuantityValue = {
  value: number;
  unit: string;
  explanation_key?: string | null;
  reference?: Record<string, string> | null;
};

export type SymbolicQuantityValue = {
  expression: string;
  unit: string;
  explanation_key?: string | null;
  reference?: Record<string, string> | null;
  numeric_coefficient?: number | null;
};

export type ComplexQuantityValue = {
  real: number;
  imag: number;
  magnitude: number;
  phase_deg: number;
  unit: string;
  explanation_key?: string | null;
  reference?: Record<string, string> | null;
};

export type ComponentResult = {
  voltage: QuantityValue;
  current: QuantityValue;
  power: QuantityValue;
  sign_convention: string;
};

export type ACComponentResult = {
  voltage: ComplexQuantityValue;
  current: ComplexQuantityValue;
  complex_power?: ComplexQuantityValue | null;
  power_note: string;
};

export type CheckResult = {
  name: string;
  passed: boolean;
  message: string;
  value?: number | string | null;
};

export type VerificationReport = {
  passed: boolean;
  max_kcl_residual_a: number;
  power_balance_error_w: number;
  checks: CheckResult[];
};

export type CalculationTrace = {
  parser_used?: string | null;
  llm_used_for_numerical_answer: boolean;
  solver_name: string;
  solver_method: string;
  solver_backend: string;
  answer_source: string;
  verification_source: string;
  unknown_order: string[];
  mna_matrix: number[][];
  rhs_vector: number[];
  solution_vector: number[];
};

export type ACFrequencyPoint = {
  frequency_hz: number;
  node_voltages: Record<string, ComplexQuantityValue>;
  component_results: Record<string, ACComponentResult>;
  requested_answers: Record<string, ComplexQuantityValue>;
  verification: VerificationReport;
};

export type ACSweepPlotPoint = {
  frequency_hz: number;
  real: number;
  imag: number;
  magnitude: number;
  magnitude_db: number;
  phase_deg: number;
};

export type ACSweepPlotSeries = {
  id: string;
  label: string;
  source: "requested_answer" | "node_voltage" | "component_voltage" | "component_current";
  unit: string;
  points: ACSweepPlotPoint[];
};

export type TransientPoint = {
  time_s: number;
  voltage_v: number;
};

export type RCTransientResponse = {
  capacitor_id: string;
  positive_node: string;
  negative_node: string;
  initial_voltage_v: number;
  final_voltage_v: number;
  resistance_ohm: number;
  capacitance_f: number;
  time_constant_s: number;
  formula: string;
  sample_points: TransientPoint[];
  analysis_method: string;
  is_first_order: boolean;
};

export type TeachingPlotPoint = {
  x: number;
  y: number;
  x_label?: string | null;
  y_label?: string | null;
  note?: string | null;
};

export type TeachingPlotSeries = {
  id: string;
  label: string;
  unit?: string | null;
  points: TeachingPlotPoint[];
};

export type TeachingPlotMarker = {
  axis: "x" | "y";
  value: number;
  label: string;
};

export type TeachingPlot = {
  id: string;
  title: string;
  subtitle?: string | null;
  plot_type: "line" | "bar";
  source:
    | "dc_operating_point"
    | "ac_single_frequency"
    | "ac_sweep"
    | "rc_transient"
    | "biomedical_context"
    | "verification";
  x_label: string;
  y_label: string;
  x_scale: "linear" | "log";
  y_scale: "linear" | "log";
  series: TeachingPlotSeries[];
  markers: TeachingPlotMarker[];
  insight?: string | null;
};

export type TutorFocus = {
  components: string[];
  nodes: string[];
  current_paths: string[];
  goals: string[];
};

export type TutorObservation = {
  id: string;
  label: string;
  value?: number | null;
  unit?: string | null;
  note: string;
};

export type TutorStep = {
  id: string;
  title: string;
  body: string;
  look_at?: string | null;
  why_it_matters?: string | null;
  common_mistake?: string | null;
  focus: TutorFocus;
  verified_values: TutorObservation[];
  caution?: string | null;
  next_action?: string | null;
};

export type LessonPacket = {
  summary: string;
  learning_objectives: string[];
  conceptual_overview: string[];
  step_by_step_derivation: TutorStep[];
  equation_steps: Array<{
    id: string;
    title: string;
    equation: string;
    explanation: string;
    focus: TutorFocus;
    value_refs: string[];
  }>;
  visual_cues: string[];
  common_mistakes: string[];
  checks: Array<{
    id: string;
    label: string;
    passed: boolean;
    explanation: string;
    value_ref?: string | null;
  }>;
  practice_prompts: string[];
  verified_value_refs: Array<{
    id: string;
    label: string;
    formatted_value?: string | null;
    source: "solution_packet" | "tutor_observation" | "analysis_view" | "deterministic_metadata";
    note?: string | null;
  }>;
  limitations: string[];
};

export type SocraticMode =
  | "first_exposure"
  | "worked_example"
  | "end_of_chapter_practice"
  | "review_debug";

export type SocraticModeProfile = {
  mode: SocraticMode;
  tutor_posture: string;
  reveal_rule: string;
  pace_notes: string[];
};

export type SocraticLecturePrompt = {
  id: string;
  phase:
    | "orient"
    | "represent"
    | "model"
    | "predict"
    | "commit"
    | "compare"
    | "check"
    | "transfer";
  tutor_move: string;
  student_task: string;
  expected_student_evidence: string;
  if_correct: string;
  if_stuck: string;
  reveal_policy: "no_numeric_reveal" | "value_refs_only" | "allow_verified_reveal";
  unlocks: string[];
  plot_ids: string[];
  value_refs: string[];
  focus: TutorFocus;
};

export type SocraticLectureStage = {
  id: string;
  title: string;
  goal: string;
  pace: "observe" | "predict" | "commit" | "calculate" | "interpret" | "transfer";
  prompts: SocraticLecturePrompt[];
  advance_when: string;
  common_failure?: string | null;
  instructor_note?: string | null;
};

export type SocraticLecturePacket = {
  mode: SocraticMode;
  source_pattern: string;
  opening_contract: string;
  textbook_pacing_summary: string[];
  mode_profiles: SocraticModeProfile[];
  stages: SocraticLectureStage[];
  gemini_prompt: string;
  safety_notes: string[];
};

export type SolutionPacket = {
  circuit_id: string;
  status: "solved" | "invalid" | "unsupported" | "ambiguous";
  node_voltages: Record<string, number>;
  component_results: Record<string, ComponentResult>;
  requested_answers: Record<string, QuantityValue>;
  symbolic_requested_answers: Record<string, SymbolicQuantityValue>;
  ac_node_voltages: Record<string, ComplexQuantityValue>;
  ac_component_results: Record<string, ACComponentResult>;
  ac_requested_answers: Record<string, ComplexQuantityValue>;
  frequency_hz?: number | null;
  ac_sweep: ACFrequencyPoint[];
  ac_sweep_plots: ACSweepPlotSeries[];
  transient_response?: RCTransientResponse | null;
  verification: VerificationReport;
  verification_badge: {
    label: "PASS" | "FAIL" | "AMBIGUOUS" | "UNSUPPORTED";
    message: string;
  };
  calculation_trace: CalculationTrace;
  generated_netlist: string;
  warnings: string[];
  assumptions_used: string[];
  bme_metadata?: BMETemplateMetadata | null;
  tutor_observations: TutorObservation[];
  teaching_plots: TeachingPlot[];
  guided_steps: TutorStep[];
  lesson_packet?: LessonPacket | null;
  socratic_lecture?: SocraticLecturePacket | null;
};

export type LabScenario = {
  component_value_error_percent?: Record<string, number>;
  resistor_tolerance_percent?: number | null;
  capacitor_tolerance_percent?: number | null;
  inductor_tolerance_percent?: number | null;
  source_amplitude_error_percent?: number | null;
  source_dc_offset_v?: number | null;
  op_amp_input_bias_current_a?: number | null;
  op_amp_input_offset_voltage_v?: number | null;
  op_amp_open_loop_gain?: number | null;
  supply_positive_v?: number | null;
  supply_negative_v?: number | null;
  output_swing_margin_v?: number | null;
  slew_rate_v_per_s?: number | null;
  enable_bias_compensation?: boolean;
  breadboard_leakage_ohm?: number | null;
  breadboard_shunt_capacitance_f?: number | null;
  readout_gain_error_percent?: number | null;
  readout_offset_v?: number | null;
};

export type LabAppliedModification = {
  id: string;
  kind:
    | "component_value"
    | "source_generation"
    | "op_amp_nonideality"
    | "bias_compensation"
    | "breadboard_parasitic"
    | "measurement_readout";
  target: string;
  before_value?: number | null;
  after_value?: number | null;
  unit?: string | null;
  note: string;
};

export type LabComparison = {
  id: string;
  label: string;
  source:
    | "requested_answer"
    | "node_voltage"
    | "ac_requested_answer"
    | "ac_node_voltage"
    | "transient";
  unit: string;
  baseline_value: number;
  lab_value: number;
  measured_value: number;
  delta: number;
  relative_error_percent?: number | null;
  note: string;
};

export type LabObservation = {
  id: string;
  severity: "notice" | "watch" | "failure" | "success";
  title: string;
  body: string;
  value?: number | null;
  unit?: string | null;
  focus_component_ids: string[];
  focus_node_ids: string[];
};

export type LabSensitivityPoint = {
  x_value: number;
  lab_value: number;
  measured_value: number;
  delta: number;
  relative_error_percent?: number | null;
};

export type LabSensitivitySweep = {
  id: string;
  label: string;
  x_label: string;
  x_unit: string;
  y_label: string;
  y_unit: string;
  comparison_id: string;
  points: LabSensitivityPoint[];
  insight?: string | null;
};

export type LabCounterfactual = {
  id: string;
  label: string;
  summary: string;
  comparisons: LabComparison[];
  applied_modifications: LabAppliedModification[];
};

export type LabSimulationResponse = {
  baseline_packet: SolutionPacket;
  lab_packet: SolutionPacket;
  lab_circuit: CircuitProblem;
  applied_modifications: LabAppliedModification[];
  comparisons: LabComparison[];
  observations: LabObservation[];
  sensitivity_sweeps: LabSensitivitySweep[];
  counterfactuals: LabCounterfactual[];
  teaching_script: string[];
  warnings: string[];
};

export type MatlabPluginTab = "overview" | "teach" | "probe" | "lab_delta";

export type MatlabArtifactKind =
  | "matlab_script"
  | "simulink_build_script"
  | "live_script_plan"
  | "app_designer_plan"
  | "toolbox_manifest"
  | "focus_map_json"
  | "probe_plan_json";

export type HighlightTargetType =
  | "block"
  | "line"
  | "port"
  | "annotation"
  | "svg_component"
  | "svg_node"
  | "conceptual_path";

export type HighlightSurface =
  | "web_svg"
  | "matlab_script"
  | "simulink"
  | "simscape"
  | "conceptual";

export type HighlightTarget = {
  id: string;
  label: string;
  target_type: HighlightTargetType;
  target_path?: string | null;
  simulink_path?: string | null;
  svg_id?: string | null;
  port?: string | null;
  description: string;
};

export type FocusMapEntry = {
  id: string;
  tab: MatlabPluginTab;
  title: string;
  teaching_step_id?: string | null;
  target: HighlightTarget;
  reason: string;
  surfaces: HighlightSurface[];
  current_svg_components: string[];
  current_svg_nodes: string[];
  current_svg_goals: string[];
  future_simulink_actions: string[];
  student_prompt?: string | null;
};

export type ProbePlan = {
  id: string;
  title: string;
  student_goal: string;
  target: HighlightTarget;
  quantity: string;
  unit: string;
  expected_behavior: string;
  student_question: string;
  measurement_explanation: string;
  suggested_logging: string[];
  suggested_sensor_insertion: string[];
  future_matlab_steps: string[];
  matlab_comment_lines: string[];
};

export type MatlabTeachStep = {
  id: string;
  title: string;
  tab: MatlabPluginTab;
  prompt_before_reveal: string;
  focus_entry_ids: string[];
  verified_value_refs: string[];
  explanation: string;
  common_mistakes: string[];
  reveal_policy: "prompt_first" | "show_hand_check" | "show_simulation_evidence";
};

export type LabDeltaRequest = {
  hand_values?: Record<string, number>;
  simulation_values?: Record<string, number>;
  measured_values?: Record<string, number>;
  value_units?: Record<string, string>;
  notes?: string | null;
};

export type LabDeltaComparisonRow = {
  id: string;
  label: string;
  unit?: string | null;
  hand_value?: number | null;
  simulation_value?: number | null;
  measured_value?: number | null;
  reference_source: "hand" | "simulation" | "measured";
  compared_source: "hand" | "simulation" | "measured";
  absolute_difference: number;
  percent_difference?: number | null;
  note: string;
};

export type LabDeltaCause = {
  id: string;
  title: string;
  explanation: string;
  confidence: "low" | "medium" | "high";
  related_keys: string[];
  next_check: string;
};

export type LabDeltaResponse = {
  lab_id: string;
  comparison_rows: LabDeltaComparisonRow[];
  likely_causes: LabDeltaCause[];
  next_probe_suggestion: string;
  next_check: string;
  reflection_question: string;
  notes: string[];
};

export type MatlabLabDeltaUploadRequest = {
  content: string;
  format?: "auto" | "csv" | "tsv" | "json";
  notes?: string | null;
};

export type MatlabLabDeltaUploadResponse = {
  lab_id: string;
  parsed_request: LabDeltaRequest;
  lab_delta_response: LabDeltaResponse;
  warnings: string[];
};

export type MatlabAgentActionKind =
  | "fetch_manifest"
  | "render_tab"
  | "open_artifact"
  | "highlight_target"
  | "insert_probe"
  | "run_simulation"
  | "compare_lab_delta"
  | "refuse_unsupported";

export type MatlabAgentActionStep = {
  id: string;
  tab?: MatlabPluginTab | null;
  label: string;
  action_kind: MatlabAgentActionKind;
  inputs: string[];
  expected_output: string;
  requires_matlab_runtime: boolean;
  dry_run_note: string;
};

export type MatlabAdapterPlan = {
  lab_id: string;
  adapter_id: string;
  launch_command: string;
  mode: "dry_run_contract" | "future_matlab_runtime";
  required_matlab_products: string[];
  supported_now: string[];
  future_runtime_hooks: string[];
  agent_actions: MatlabAgentActionStep[];
  refusal_rules: string[];
  ci_validation: string[];
};

export type MatlabPluginArtifact = {
  id: string;
  lab_id: string;
  kind: MatlabArtifactKind;
  filename: string;
  title: string;
  description: string;
  content: string;
  mime_type: string;
  generated_by: string;
  requires_matlab_runtime: boolean;
};

export type MatlabLabSummary = {
  id: string;
  title: string;
  objective: string;
  tabs: MatlabPluginTab[];
  inputs: string[];
  outputs: string[];
  key_parameters: Record<string, string>;
  assumptions: string[];
  idealizations: string[];
  bme_safety_boundary: string;
  generated_artifact_kinds: MatlabArtifactKind[];
  evidence_to_collect: string[];
  status: "implemented" | "stub";
};

export type MatlabPluginManifest = {
  plugin_id: string;
  title: string;
  version: string;
  description: string;
  tabs: MatlabPluginTab[];
  labs: MatlabLabSummary[];
  api_prefix: string;
  matlab_entrypoint: string;
  default_deployment_mode: "offline_toolbox" | "optional_api" | "web_preview";
  deployment_modes: Array<"offline_toolbox" | "optional_api" | "web_preview">;
  local_server_required: boolean;
  ci_boundary: string;
  source_of_truth_rule: string;
};

export type MatlabLabPlan = {
  lab: MatlabLabSummary;
  overview: Record<string, unknown>;
  teach_steps: MatlabTeachStep[];
  focus_map: FocusMapEntry[];
  probe_plan: ProbePlan[];
  lab_delta_seed_request: LabDeltaRequest;
  expected_artifact_kinds: MatlabArtifactKind[];
  adapter_plan: MatlabAdapterPlan;
};

export type MatlabOfflineBundle = {
  bundle_id: string;
  lab_id: string;
  manifest: MatlabPluginManifest;
  lab_plan: MatlabLabPlan;
  artifacts: MatlabPluginArtifact[];
  files: Array<{
    path: string;
    content: string;
    mime_type: string;
    description: string;
  }>;
  lab_delta_example: LabDeltaResponse;
  file_tree: string[];
  integrity_checks: string[];
  requires_matlab_runtime: boolean;
};

export type MatlabArtifactRequest = {
  kinds?: MatlabArtifactKind[] | null;
  include_focus_map?: boolean;
  include_probe_plan?: boolean;
  include_app_designer_plan?: boolean;
};

export type MatlabPlaygroundTab = "overview" | "teach" | "probe" | "lab_delta";

export type MatlabPlaygroundArtifactKind =
  | "matlab_script"
  | "simulink_script"
  | "simscape_script"
  | "popup_app_script"
  | "focus_map"
  | "probe_plan"
  | "lab_delta_report";

export type PlaygroundLab = {
  id: string;
  title: string;
  summary: string;
  bme_context: string;
  required_products: string[];
  optional_products: string[];
  default_parameters: Record<string, number | string>;
  learning_objectives: string[];
  assumptions: string[];
};

export type MatlabPlaygroundHighlightTarget = {
  id: string;
  label: string;
  target_type:
    | "block"
    | "line"
    | "port"
    | "annotation"
    | "simscape_component"
    | "simscape_connection"
    | "svg_component"
    | "svg_node"
    | "conceptual_path";
  component_id?: string | null;
  node_id?: string | null;
  model_path?: string | null;
  signal_name?: string | null;
  style: string;
  reason: string;
};

export type MatlabPlaygroundFocusMapEntry = {
  id: string;
  label: string;
  mode: MatlabPlaygroundTab;
  description: string;
  targets: MatlabPlaygroundHighlightTarget[];
  teaching_step_id?: string | null;
  student_prompt?: string | null;
};

export type MatlabPlaygroundProbePlan = {
  id: string;
  label: string;
  target: MatlabPlaygroundHighlightTarget;
  measurement_type: string;
  expected_unit: string;
  why_probe_here: string;
  insertion_steps: string[];
  matlab_variable_name: string;
  student_question: string;
};

export type MatlabPlaygroundLabDeltaRequest = {
  lab_id?: string | null;
  hand_values?: Record<string, number>;
  simulation_values?: Record<string, number>;
  measured_values?: Record<string, number>;
  notes?: string | null;
};

export type MatlabPlaygroundLabDeltaRow = {
  quantity: string;
  hand_value?: number | null;
  simulation_value?: number | null;
  measured_value?: number | null;
  unit?: string | null;
  absolute_error?: number | null;
  percent_error?: number | null;
  interpretation: string;
};

export type MatlabPlaygroundLabDeltaCause = {
  id: string;
  label: string;
  explanation: string;
  check_to_run: string;
  severity: "low" | "medium" | "high";
};

export type MatlabPlaygroundLabDeltaResponse = {
  lab_id: string;
  rows: MatlabPlaygroundLabDeltaRow[];
  likely_causes: MatlabPlaygroundLabDeltaCause[];
  recommended_probe: string;
  reflection_question: string;
  notes: string[];
};

export type MatlabPlaygroundArtifact = {
  id: string;
  lab_id: string;
  title: string;
  kind: MatlabPlaygroundArtifactKind;
  filename: string;
  content: string;
  instructions: string;
};

export type MatlabPlaygroundManifest = {
  product_name: string;
  version: string;
  positioning: string;
  tabs: MatlabPlaygroundTab[];
  labs: PlaygroundLab[];
  artifacts: MatlabPlaygroundArtifact[];
  focus_map: MatlabPlaygroundFocusMapEntry[];
  probe_plans: MatlabPlaygroundProbePlan[];
  lab_delta_causes: MatlabPlaygroundLabDeltaCause[];
  notes: string[];
};

export type MatlabPlaygroundArtifactRequest = {
  kinds?: MatlabPlaygroundArtifactKind[] | null;
};

export type ScopeItem = {
  label: string;
  detail: string;
};

export type ProductCapability = {
  capability: string;
  user_value: string;
  current_evidence: string;
  boundary: string;
};

export type RuntimeDebugEvent = {
  stage: string;
  label: string;
  message: string;
  data: Record<string, unknown>;
  elapsed_ms?: number | null;
};

export type RuntimeDebugTrace = {
  enabled: boolean;
  events: RuntimeDebugEvent[];
  redaction_notes: string[];
};

export type ScopeBoundary = {
  product_positioning: string;
  source_of_truth_rule: string;
  product_capabilities: ProductCapability[];
  supported_analysis_modes: ScopeItem[];
  supported_components: string[];
  supported_workflows: string[];
  unsupported_features: ScopeItem[];
  verification_boundary: string[];
  bme_boundary: string[];
  bme_templates: string[];
  debug_boundary: string[];
};

export type PracticeVariant = {
  kind: string;
  prompt: string;
  description: string;
  circuit_ir: CircuitProblem;
};

export type ComponentFlow = {
  component_id: string;
  component_type: string;
  nodes: string[];
  current_a: number;
  abs_current_a: number;
  direction_from: string;
  direction_to: string;
  voltage_v: number;
  power_w: number;
  is_zero_current: boolean;
  sign_convention: string;
};

export type NodeKclTerm = {
  component_id: string;
  other_node: string;
  signed_current_leaving_a: number;
  abs_current_a: number;
  direction: "entering" | "leaving" | "zero";
  description: string;
};

export type NodeKclReport = {
  node: string;
  voltage_v: number;
  terms: NodeKclTerm[];
  sum_leaving_a: number;
  residual_a: number;
  passed: boolean;
};

export type AnalysisView = {
  status: "available" | "blocked";
  badge: string;
  reason?: string | null;
  component_flows: Record<string, ComponentFlow>;
  node_kcl: Record<string, NodeKclReport>;
};

export type KnowledgeState = {
  mastery: number;
  opportunities: number;
  last_evidence?: string | null;
};

export type StudentProfile = {
  strengths: string[];
  recurring_misconceptions: Record<string, number>;
  knowledge_state: Record<string, KnowledgeState>;
  hint_preference: string;
  independence_level: "high" | "medium" | "low";
  hint_budget_used: number;
  completed_attempts: number;
};

export type InstructorDashboard = {
  student_count: number;
  cohort_independence: Record<string, number>;
  misconception_summary: Array<{
    misconception: string;
    label: string;
    affected_students: number;
    total_occurrences: number;
    affected_percent: number;
    suggested_intervention: string;
  }>;
  guardrails: string[];
};
