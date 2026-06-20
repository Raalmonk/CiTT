import { create } from "zustand";
import type { SchematicRenderer } from "@/api/tutorApi";
import type {
  AnalysisView,
  CircuitProblem,
  EntityRef,
  InstructorDashboard,
  PracticeVariant,
  ScopeBoundary,
  SolutionPacket,
  StudentProfile,
  RuntimeDebugTrace,
  TutorFocus,
  TutorStep,
  VisualCircuit
} from "@/types/api";

export type ChatRole = "student" | "assistant" | "system";
export type ChatStatus = "complete" | "streaming" | "error";
export type StreamStatus = "idle" | "connecting" | "streaming" | "closed" | "error";

export type TutorMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: string;
  status: ChatStatus;
  references: EntityRef[];
};

export type TutorStreamEvent =
  | { type: "start"; messageId?: string; content?: string }
  | { type: "token"; token: string }
  | { type: "complete" }
  | { type: "error"; message: string };

type LoadCircuitPayload = {
  circuit: CircuitProblem;
  parserUsed?: string | null;
  problemText?: string | null;
  visualCircuit?: VisualCircuit | null;
  solutionPacket?: SolutionPacket | null;
  explanation?: string | null;
  variants?: PracticeVariant[];
  analysisView?: AnalysisView | null;
  debugTrace?: RuntimeDebugTrace | null;
  schematicRenderer?: SchematicRenderer;
  schematicSvg?: string | null;
};

type TutorState = {
  circuit: CircuitProblem | null;
  parserUsed: string | null;
  problemText: string | null;
  visualCircuit: VisualCircuit | null;
  solutionPacket: SolutionPacket | null;
  explanation: string | null;
  variants: PracticeVariant[];
  analysisView: AnalysisView | null;
  scopeBoundary: ScopeBoundary | null;
  studentProfile: StudentProfile | null;
  instructorDashboard: InstructorDashboard | null;
  debugTrace: RuntimeDebugTrace | null;
  schematicRenderer: SchematicRenderer;
  schematicSvg: string | null;
  activeStepId: string | null;
  activeStepIndex: number;
  chatHistory: TutorMessage[];
  hoveredEntity: EntityRef | null;
  selectedEntity: EntityRef | null;
  manualFocusEntities: EntityRef[];
  chatReferencedEntities: EntityRef[];
  highlightedEntities: EntityRef[];
  streamStatus: StreamStatus;
  streamingMessageId: string | null;
};

type TutorActions = {
  loadCircuit: (payload: LoadCircuitPayload) => void;
  setCircuit: (circuit: CircuitProblem) => void;
  setVisualCircuit: (visualCircuit: VisualCircuit | null) => void;
  setSolutionPacket: (solutionPacket: SolutionPacket | null) => void;
  setAnalysisView: (analysisView: AnalysisView | null) => void;
  setExplanation: (explanation: string | null) => void;
  setVariants: (variants: PracticeVariant[]) => void;
  setScopeBoundary: (scopeBoundary: ScopeBoundary | null) => void;
  setStudentProfile: (studentProfile: StudentProfile | null) => void;
  setInstructorDashboard: (dashboard: InstructorDashboard | null) => void;
  setSchematicSvg: (schematicSvg: string | null, renderer?: SchematicRenderer) => void;
  setActiveStep: (stepId: string | null) => void;
  setActiveStepByIndex: (stepIndex: number) => void;
  setHoveredEntity: (entity: EntityRef | null) => void;
  selectEntity: (entity: EntityRef | null) => void;
  setManualFocusEntities: (entities: EntityRef[]) => void;
  highlightFromTutorText: (text: string) => EntityRef[];
  clearChatHistory: () => void;
  clearChatHighlights: () => void;
  addStudentMessage: (content: string) => string;
  addAssistantMessage: (content: string, status?: ChatStatus) => string;
  beginAssistantStream: (messageId?: string, initialContent?: string) => string;
  appendAssistantToken: (token: string) => void;
  finishAssistantStream: () => void;
  failAssistantStream: (message: string) => void;
  receiveTutorEvent: (event: TutorStreamEvent) => void;
  resetTutorSession: () => void;
};

export type TutorStore = TutorState & TutorActions;

const initialState: TutorState = {
  circuit: null,
  parserUsed: null,
  problemText: null,
  visualCircuit: null,
  solutionPacket: null,
  explanation: null,
  variants: [],
  analysisView: null,
  scopeBoundary: null,
  studentProfile: null,
  instructorDashboard: null,
  debugTrace: null,
  schematicRenderer: "optcpv",
  schematicSvg: null,
  activeStepId: null,
  activeStepIndex: -1,
  chatHistory: [],
  hoveredEntity: null,
  selectedEntity: null,
  manualFocusEntities: [],
  chatReferencedEntities: [],
  highlightedEntities: [],
  streamStatus: "idle",
  streamingMessageId: null
};

export const useTutorStore = create<TutorStore>((set, get) => ({
  ...initialState,

  loadCircuit: ({
    circuit,
    parserUsed = null,
    problemText = null,
    visualCircuit = null,
    solutionPacket = null,
    explanation = null,
    variants = [],
    analysisView = null,
    debugTrace = null,
    schematicRenderer = "optcpv",
    schematicSvg = null
  }) => {
    const firstStep = getSteps(solutionPacket)[0] ?? null;
    set((state) => {
      const next = {
        ...state,
        circuit,
        parserUsed,
        problemText,
        visualCircuit,
        solutionPacket,
        explanation,
        variants,
        analysisView,
        debugTrace,
        schematicRenderer,
        schematicSvg,
        activeStepId: firstStep?.id ?? null,
        activeStepIndex: firstStep ? 0 : -1,
        chatReferencedEntities: [],
        hoveredEntity: null,
        selectedEntity: null,
        manualFocusEntities: []
      };

      return {
        ...next,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  setCircuit: (circuit) => {
    set({ circuit });
  },

  setVisualCircuit: (visualCircuit) => {
    set((state) => {
      const next = { ...state, visualCircuit };
      return {
        visualCircuit,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  setAnalysisView: (analysisView) => {
    set({ analysisView });
  },

  setExplanation: (explanation) => {
    set({ explanation });
  },

  setVariants: (variants) => {
    set({ variants });
  },

  setScopeBoundary: (scopeBoundary) => {
    set({ scopeBoundary });
  },

  setStudentProfile: (studentProfile) => {
    set({ studentProfile });
  },

  setInstructorDashboard: (dashboard) => {
    set({ instructorDashboard: dashboard });
  },

  setSchematicSvg: (schematicSvg, renderer) => {
    set((state) => ({
      schematicRenderer: renderer ?? state.schematicRenderer,
      schematicSvg
    }));
  },

  setSolutionPacket: (solutionPacket) => {
    const currentStepId = get().activeStepId;
    const steps = getSteps(solutionPacket);
    const matchingStepIndex = steps.findIndex((step) => step.id === currentStepId);
    const activeStepIndex = matchingStepIndex >= 0 ? matchingStepIndex : steps.length ? 0 : -1;
    const activeStepId = activeStepIndex >= 0 ? steps[activeStepIndex].id : null;

    set((state) => {
      const next = { ...state, solutionPacket, activeStepId, activeStepIndex };
      return {
        solutionPacket,
        activeStepId,
        activeStepIndex,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  setActiveStep: (stepId) => {
    const steps = getSteps(get().solutionPacket);
    const activeStepIndex = stepId ? steps.findIndex((step) => step.id === stepId) : -1;
    set((state) => {
      const next = {
        ...state,
        activeStepId: activeStepIndex >= 0 ? stepId : null,
        activeStepIndex
      };

      return {
        activeStepId: next.activeStepId,
        activeStepIndex,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  setActiveStepByIndex: (stepIndex) => {
    const steps = getSteps(get().solutionPacket);
    const boundedIndex = stepIndex >= 0 && stepIndex < steps.length ? stepIndex : -1;
    const activeStepId = boundedIndex >= 0 ? steps[boundedIndex].id : null;

    set((state) => {
      const next = { ...state, activeStepId, activeStepIndex: boundedIndex };
      return {
        activeStepId,
        activeStepIndex: boundedIndex,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  setHoveredEntity: (entity) => {
    set((state) => {
      const next = { ...state, hoveredEntity: entity };
      return {
        hoveredEntity: entity,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  selectEntity: (entity) => {
    set((state) => {
      const next = { ...state, selectedEntity: entity };
      return {
        selectedEntity: entity,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  setManualFocusEntities: (entities) => {
    set((state) => {
      const next = { ...state, manualFocusEntities: entities };
      return {
        manualFocusEntities: entities,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  highlightFromTutorText: (text) => {
    const references = extractCircuitReferences(text, collectKnownEntities(get()));
    set((state) => {
      const next = { ...state, chatReferencedEntities: references };
      return {
        chatReferencedEntities: references,
        highlightedEntities: composeHighlights(next)
      };
    });
    return references;
  },

  clearChatHistory: () => {
    set((state) => {
      const next = {
        ...state,
        chatHistory: [],
        chatReferencedEntities: [],
        streamStatus: "idle" as const,
        streamingMessageId: null
      };
      return {
        chatHistory: [],
        chatReferencedEntities: [],
        streamStatus: "idle",
        streamingMessageId: null,
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  clearChatHighlights: () => {
    set((state) => {
      const next = { ...state, chatReferencedEntities: [] };
      return {
        chatReferencedEntities: [],
        highlightedEntities: composeHighlights(next)
      };
    });
  },

  addStudentMessage: (content) => {
    const message = createMessage("student", content, "complete", []);
    set((state) => ({ chatHistory: [...state.chatHistory, message] }));
    return message.id;
  },

  addAssistantMessage: (content, status = "complete") => {
    const references = extractCircuitReferences(content, collectKnownEntities(get()));
    const message = createMessage("assistant", content, status, references);

    set((state) => {
      const next = {
        ...state,
        chatHistory: [...state.chatHistory, message],
        chatReferencedEntities: references
      };

      return {
        chatHistory: next.chatHistory,
        chatReferencedEntities: references,
        highlightedEntities: composeHighlights(next)
      };
    });

    return message.id;
  },

  beginAssistantStream: (messageId, initialContent = "") => {
    const id = messageId ?? createMessageId();
    const references = extractCircuitReferences(initialContent, collectKnownEntities(get()));
    const message = createMessage("assistant", initialContent, "streaming", references, id);

    set((state) => {
      const next = {
        ...state,
        chatHistory: [...state.chatHistory, message],
        chatReferencedEntities: references,
        streamStatus: "streaming" as const,
        streamingMessageId: id
      };

      return {
        chatHistory: next.chatHistory,
        chatReferencedEntities: references,
        highlightedEntities: composeHighlights(next),
        streamStatus: next.streamStatus,
        streamingMessageId: id
      };
    });

    return id;
  },

  appendAssistantToken: (token) => {
    const streamingMessageId = get().streamingMessageId;
    if (!streamingMessageId) {
      get().beginAssistantStream(undefined, token);
      return;
    }

    set((state) => {
      let streamedContent = "";
      const chatHistory = state.chatHistory.map((message) => {
        if (message.id !== streamingMessageId) {
          return message;
        }

        streamedContent = `${message.content}${token}`;
        return {
          ...message,
          content: streamedContent,
          references: extractCircuitReferences(streamedContent, collectKnownEntities(state))
        };
      });

      const references = extractCircuitReferences(streamedContent, collectKnownEntities(state));
      const next = {
        ...state,
        chatHistory,
        chatReferencedEntities: references,
        streamStatus: "streaming" as const
      };

      return {
        chatHistory,
        chatReferencedEntities: references,
        highlightedEntities: composeHighlights(next),
        streamStatus: next.streamStatus
      };
    });
  },

  finishAssistantStream: () => {
    const streamingMessageId = get().streamingMessageId;
    set((state) => ({
      chatHistory: state.chatHistory.map((message) =>
        message.id === streamingMessageId ? { ...message, status: "complete" } : message
      ),
      streamStatus: "closed",
      streamingMessageId: null
    }));
  },

  failAssistantStream: (message) => {
    const streamingMessageId = get().streamingMessageId;
    set((state) => ({
      chatHistory: state.chatHistory.map((chatMessage) =>
        chatMessage.id === streamingMessageId
          ? { ...chatMessage, content: message, status: "error" }
          : chatMessage
      ),
      streamStatus: "error",
      streamingMessageId: null
    }));
  },

  receiveTutorEvent: (event) => {
    if (event.type === "start") {
      get().beginAssistantStream(event.messageId, event.content);
      return;
    }

    if (event.type === "token") {
      get().appendAssistantToken(event.token);
      return;
    }

    if (event.type === "complete") {
      get().finishAssistantStream();
      return;
    }

    get().failAssistantStream(event.message);
  },

  resetTutorSession: () => {
    set(initialState);
  }
}));

export function extractCircuitReferences(text: string, knownEntities: EntityRef[]): EntityRef[] {
  const refs = knownEntities.filter((entity) => textMentionsEntity(text, entity));
  return uniqueRefs(refs);
}

function collectKnownEntities(state: Pick<TutorState, "circuit" | "visualCircuit">): EntityRef[] {
  const refs: EntityRef[] = [];

  for (const component of state.visualCircuit?.components ?? []) {
    refs.push({ kind: "component", id: component.id });
  }

  for (const node of state.visualCircuit?.nodes ?? []) {
    refs.push({ kind: "node", id: node.id });
  }

  for (const wire of state.visualCircuit?.wires ?? []) {
    refs.push({ kind: "wire", id: wire.id });
  }

  for (const component of state.circuit?.components ?? []) {
    refs.push({ kind: "component", id: component.id });
  }

  for (const nodeId of state.circuit?.nodes ?? []) {
    refs.push({ kind: "node", id: nodeId });
  }

  for (const goal of state.circuit?.goals ?? []) {
    refs.push({ kind: "goal", id: goal.id });
  }

  return uniqueRefs(refs);
}

function composeHighlights(state: Pick<
  TutorState,
  | "activeStepId"
  | "solutionPacket"
  | "hoveredEntity"
  | "selectedEntity"
  | "chatReferencedEntities"
  | "manualFocusEntities"
>): EntityRef[] {
  const refs: EntityRef[] = [];

  if (state.selectedEntity) {
    refs.push(state.selectedEntity);
  }

  if (state.hoveredEntity) {
    refs.push(state.hoveredEntity);
  }

  refs.push(...state.manualFocusEntities);
  refs.push(...state.chatReferencedEntities);

  const activeStep = getSteps(state.solutionPacket).find((step) => step.id === state.activeStepId);
  if (activeStep) {
    refs.push(...refsFromFocus(activeStep.focus));
  }

  return uniqueRefs(refs);
}

function refsFromFocus(focus: TutorFocus): EntityRef[] {
  return [
    ...focus.components.map((id) => ({ kind: "component" as const, id })),
    ...focus.nodes.map((id) => ({ kind: "node" as const, id })),
    ...focus.current_paths.map((id) => ({ kind: "wire" as const, id })),
    ...focus.goals.map((id) => ({ kind: "goal" as const, id }))
  ];
}

function getSteps(solutionPacket: SolutionPacket | null): TutorStep[] {
  return (
    solutionPacket?.guided_steps.length
      ? solutionPacket.guided_steps
      : solutionPacket?.lesson_packet?.step_by_step_derivation
  ) ?? [];
}

function textMentionsEntity(text: string, entity: EntityRef): boolean {
  if (!entity.id) {
    return false;
  }

  if (entity.kind === "node") {
    return textMentionsNode(text, entity.id);
  }

  return hasToken(text, entity.id);
}

function textMentionsNode(text: string, nodeId: string): boolean {
  if (nodeId === "0") {
    return /\b(?:ground|node\s+0|v\s*\(\s*0\s*\))/i.test(text);
  }

  if (nodeId.length <= 2 || COMMON_WORD_IDS.has(nodeId.toLowerCase())) {
    const escaped = escapeRegExp(nodeId);
    return new RegExp(
      String.raw`(?:\bnode\s+${escaped}\b|\bV\s*\(\s*${escaped}\s*\)|\b${escaped}\s+node\b)`,
      "i"
    ).test(text);
  }

  return hasToken(text, nodeId);
}

function hasToken(text: string, token: string): boolean {
  const escaped = escapeRegExp(token);
  return new RegExp(String.raw`(^|[^A-Za-z0-9_])${escaped}([^A-Za-z0-9_]|$)`, "i").test(text);
}

function uniqueRefs(refs: EntityRef[]): EntityRef[] {
  const seen = new Set<string>();
  const unique: EntityRef[] = [];

  for (const ref of refs) {
    const key = `${ref.kind}:${ref.id}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(ref);
    }
  }

  return unique;
}

function createMessage(
  role: ChatRole,
  content: string,
  status: ChatStatus,
  references: EntityRef[],
  id = createMessageId()
): TutorMessage {
  return {
    id,
    role,
    content,
    createdAt: new Date().toISOString(),
    status,
    references
  };
}

function createMessageId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `message_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const COMMON_WORD_IDS = new Set(["in", "out", "top", "left", "right", "a", "b"]);
