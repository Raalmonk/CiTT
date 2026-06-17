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
  topology_id?: string | null;
  layout_hint?: Record<string, unknown> | null;
  ground_node: string;
  nodes: string[];
  components: CircuitComponent[];
  goals: CircuitGoal[];
  assumptions: string[];
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
};

export type SolutionPacket = {
  circuit_id: string;
  status: "solved" | "invalid" | "unsupported" | "ambiguous";
  requested_answers: Record<string, QuantityValue>;
  verification_badge: {
    label: "PASS" | "FAIL" | "AMBIGUOUS" | "UNSUPPORTED";
    message: string;
  };
  warnings: string[];
  assumptions_used: string[];
  guided_steps: TutorStep[];
  lesson_packet?: LessonPacket | null;
};
