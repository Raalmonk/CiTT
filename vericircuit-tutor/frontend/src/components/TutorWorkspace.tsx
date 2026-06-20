import {
  ChangeEvent,
  ClipboardEvent as ReactClipboardEvent,
  DragEvent,
  FormEvent,
  PointerEvent as ReactPointerEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import {
  Activity,
  BarChart3,
  BatteryCharging,
  Cable,
  CircuitBoard,
  CircleDot,
  Eye,
  GraduationCap,
  Gauge,
  Info,
  Lightbulb,
  type LucideIcon,
  Loader2,
  Move,
  MousePointer2,
  RefreshCw,
  Send,
  Settings2,
  Sparkles,
  Trash2,
  Upload,
  X,
  Zap
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import {
  explainSolution,
  fetchAnalysisView,
  fetchInstructorDashboard,
  fetchMatlabPlaygroundArtifacts,
  fetchMatlabPlaygroundFocusMap,
  fetchMatlabPlaygroundManifest,
  fetchMatlabPlaygroundProbePlans,
  fetchParserConfig,
  fetchSchematicSvg,
  fetchScopeBoundary,
  fetchVariants,
  fetchVisualLayout,
  fileToBase64,
  solveCircuit,
  simulateLab,
  updateResistorIncremental,
  compareMatlabPlaygroundLabDelta,
  runImagePipeline,
  runReasoningCoach,
  runTextPipeline,
  type FullPipelineResponse,
  type ParserConfig,
  type ReasoningCoachResponse,
  type RepresentationMode,
  type SchematicRenderer
} from "@/api/tutorApi";
import { katexOptions, normalizeTutorLatex } from "@/lib/latex";
import { cn } from "@/lib/utils";
import { useTutorStore, type TutorMessage } from "@/store/useTutorStore";
import type {
  AnalysisView,
  CircuitProblem,
  ComponentFlow,
  ComplexQuantityValue,
  EntityKind,
  EntityRef,
  NodeKclReport,
  LabComparison,
  LabSimulationResponse,
  MatlabPlaygroundArtifact,
  MatlabPlaygroundFocusMapEntry,
  MatlabPlaygroundLabDeltaResponse,
  MatlabPlaygroundManifest,
  MatlabPlaygroundProbePlan,
  PracticeVariant,
  PlaygroundLab,
  RuntimeDebugTrace,
  ScopeBoundary,
  SolutionPacket,
  TeachingPlot,
  TutorStep,
  VisualCircuit,
  VisualComponent,
  VisualNode
} from "@/types/api";

export function TutorWorkspace() {
  const circuit = useTutorStore((state) => state.circuit);
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const streamStatus = useTutorStore((state) => state.streamStatus);
  const [activePanel, setActivePanel] = useState<WorkspacePanel>("learn");

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <header className="border-b bg-card/95 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-[1600px] items-center justify-between gap-4 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="monk-glow flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <CircuitBoard className="size-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold tracking-normal">CiTT</h1>
              <p className="truncate text-sm text-muted-foreground">
                {circuit?.title ?? "Circuit reasoning workspace"}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 text-xs font-medium">
            {solutionPacket?.verification_badge ? (
              <span
                className={cn(
                  "rounded-full border px-2.5 py-1",
                  solutionPacket.verification_badge.label === "PASS"
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                    : "border-amber-200 bg-amber-50 text-amber-800"
                )}
              >
                {solutionPacket.verification_badge.label}
              </span>
            ) : null}
            <span className="rounded-full border bg-muted px-2.5 py-1 text-muted-foreground">
              {streamStatus === "streaming" ? "CiTT thinking" : "CiTT ready"}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1600px] gap-4 p-4 lg:h-[calc(100dvh-65px)] lg:grid-cols-[minmax(0,1.38fr)_minmax(390px,0.92fr)] lg:grid-rows-[auto_minmax(0,1fr)]">
        <section className="workspace-panel lg:col-span-2">
          <ProblemInputPanel />
        </section>

        <section className="workspace-panel flex min-h-[440px] flex-col lg:min-h-0">
          <CanvasHeader />
          <CircuitCanvas />
        </section>

        <aside className="workspace-panel flex min-h-[560px] flex-col lg:min-h-0">
          <WorkspaceTabs activePanel={activePanel} onPanelChange={setActivePanel} />
          <RightWorkspace activePanel={activePanel} />
        </aside>
      </main>
    </div>
  );
}

type WorkspacePanel = "learn" | "coach" | "inspect" | "lab" | "playground" | "scope";
type LoadStatus = "idle" | "loading" | "error";
type ProgressStep = "idle" | "reading_image" | "solving" | "rendering" | "organizing";
type LabPredictionDirection = "increase" | "decrease" | "about_same";
type LabPresetId = "resistor" | "bias" | "saturation" | "breadboard" | "readout";
type LabPredictionRecord = {
  direction: LabPredictionDirection;
  reason: string;
};

const DEFAULT_PROBLEM_TEXT = "";
const SUPPORTED_IMAGE_MIME_TYPES = new Set(["image/png", "image/jpeg", "image/jpg", "image/webp"]);
const SCHEMATIC_RENDERER: SchematicRenderer = "optcpv";
const LAB_PRESETS: Array<{ id: LabPresetId; title: string; detail: string }> = [
  { id: "resistor", title: "Resistor drift", detail: "5% value spread" },
  { id: "bias", title: "Bias current", detail: "50 nA plus balance" },
  { id: "saturation", title: "Output rail", detail: "plus/minus 5 V limit" },
  { id: "breadboard", title: "Breadboard", detail: "leakage and pF shunt" },
  { id: "readout", title: "Readout", detail: "meter gain and offset" }
];
const RUN_PROGRESS: Record<ProgressStep, { label: string; percent: number }> = {
  idle: { label: "Ready", percent: 0 },
  reading_image: { label: "Reading pasted image", percent: 18 },
  solving: { label: "Parsing circuit and verifying solution", percent: 64 },
  rendering: { label: "Rendering OptCPV schematic", percent: 84 },
  organizing: { label: "Building teaching workspace", percent: 94 }
};
const PLAYGROUND_DND_MIME = "application/x-citt-playground-tool";
const MATLAB_PLAYGROUND_DEFAULT_LAB_ID = "rc_antialias_adc";

type PlaygroundItemKind =
  | "resistor"
  | "capacitor"
  | "voltage_source"
  | "current_source"
  | "op_amp"
  | "diode"
  | "ground"
  | "node"
  | "probe"
  | "wire"
  | "note";
type PlaygroundItemOrigin = "circuit" | "manual";
type PlaygroundPoint = { x: number; y: number };
type PlaygroundItem = PlaygroundPoint & {
  id: string;
  kind: PlaygroundItemKind;
  label: string;
  value: string;
  origin: PlaygroundItemOrigin;
  sourceType?: string;
  width: number;
  height: number;
  sourceEntity?: EntityRef;
};
type PlaygroundTool = {
  kind: PlaygroundItemKind;
  label: string;
  defaultLabel: string;
  defaultValue: string;
  icon: LucideIcon;
};
type PlaygroundDragState = {
  itemId: string;
  pointerId: number;
  lastClientX: number;
  lastClientY: number;
};
type OptcpvViewport = { x: number; y: number; width: number; height: number };
type OptcpvComponentRegion = OptcpvViewport & {
  id: string;
  type: string;
};
type OptcpvTerminal = PlaygroundPoint & {
  componentId: string;
  netName: string;
  pinName: string;
};
type OptcpvModel = {
  renderer: string;
  circuitId: string;
  layoutMode: string;
  fallbackUsed: boolean;
  viewBox: OptcpvViewport;
  sanitizedSvg: string;
  components: OptcpvComponentRegion[];
  terminals: OptcpvTerminal[];
};

const PLAYGROUND_TOOLS: PlaygroundTool[] = [
  { kind: "resistor", label: "Resistor", defaultLabel: "R", defaultValue: "10 kOhm", icon: CircuitBoard },
  { kind: "capacitor", label: "Capacitor", defaultLabel: "C", defaultValue: "1 uF", icon: CircleDot },
  { kind: "voltage_source", label: "Voltage", defaultLabel: "V", defaultValue: "5 V", icon: BatteryCharging },
  { kind: "current_source", label: "Current", defaultLabel: "I", defaultValue: "1 mA", icon: Zap },
  { kind: "op_amp", label: "Op amp", defaultLabel: "U", defaultValue: "ideal", icon: Settings2 },
  { kind: "diode", label: "Diode", defaultLabel: "D", defaultValue: "0.7 V", icon: Zap },
  { kind: "ground", label: "Ground", defaultLabel: "GND", defaultValue: "0 V", icon: Cable },
  { kind: "node", label: "Node", defaultLabel: "N", defaultValue: "junction", icon: CircleDot },
  { kind: "probe", label: "Probe", defaultLabel: "Probe", defaultValue: "V?", icon: Gauge },
  { kind: "wire", label: "Wire", defaultLabel: "Wire", defaultValue: "link", icon: Cable },
  { kind: "note", label: "Note", defaultLabel: "Note", defaultValue: "check", icon: Info }
];
const PLAYGROUND_TOOL_BY_KIND = new Map(PLAYGROUND_TOOLS.map((tool) => [tool.kind, tool]));

function WorkspaceTabs({
  activePanel,
  onPanelChange
}: {
  activePanel: WorkspacePanel;
  onPanelChange: (panel: WorkspacePanel) => void;
}) {
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const analysisView = useTutorStore((state) => state.analysisView);
  const variants = useTutorStore((state) => state.variants);
  const scopeBoundary = useTutorStore((state) => state.scopeBoundary);

  const tabs: Array<{ id: WorkspacePanel; label: string; icon: LucideIcon; available: boolean }> = [
    { id: "learn", label: "Learn", icon: GraduationCap, available: Boolean(solutionPacket) },
    { id: "coach", label: "Coach", icon: Sparkles, available: Boolean(solutionPacket) },
    { id: "inspect", label: "Inspect", icon: Eye, available: Boolean(analysisView || solutionPacket) },
    { id: "lab", label: "Lab", icon: Activity, available: Boolean(solutionPacket || variants.length) },
    { id: "playground", label: "MATLAB", icon: CircuitBoard, available: true },
    { id: "scope", label: "Scope", icon: Info, available: Boolean(scopeBoundary) }
  ];

  return (
    <div className="flex min-h-14 items-center gap-1 overflow-x-auto border-b px-3">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            aria-label={`${tab.label} panel`}
            aria-pressed={activePanel === tab.id}
            className={cn("workspace-tab", activePanel === tab.id && "workspace-tab-active")}
            onClick={() => onPanelChange(tab.id)}
            type="button"
          >
            <Icon className="size-4 shrink-0" aria-hidden="true" />
            <span>{tab.label}</span>
            {!tab.available ? <span className="sr-only">not loaded</span> : null}
          </button>
        );
      })}
    </div>
  );
}

function RightWorkspace({ activePanel }: { activePanel: WorkspacePanel }) {
  return (
    <div className="min-h-0 flex-1">
      {activePanel === "learn" ? <StepPanel /> : null}
      {activePanel === "coach" ? <ChatPanel /> : null}
      {activePanel === "inspect" ? <InspectPanel /> : null}
      {activePanel === "lab" ? <LabPanel /> : null}
      {activePanel === "playground" ? <MatlabPlaygroundPanel /> : null}
      {activePanel === "scope" ? <ScopePanel /> : null}
    </div>
  );
}

function ProblemInputPanel() {
  const loadCircuit = useTutorStore((state) => state.loadCircuit);
  const addStudentMessage = useTutorStore((state) => state.addStudentMessage);
  const addAssistantMessage = useTutorStore((state) => state.addAssistantMessage);
  const clearChatHistory = useTutorStore((state) => state.clearChatHistory);
  const setScopeBoundary = useTutorStore((state) => state.setScopeBoundary);
  const [problemText, setProblemText] = useState(DEFAULT_PROBLEM_TEXT);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedImagePreviewUrl, setSelectedImagePreviewUrl] = useState<string | null>(null);
  const [isImageDragActive, setIsImageDragActive] = useState(false);
  const [parserConfig, setParserConfig] = useState<ParserConfig | null>(null);
  const [parserConfigError, setParserConfigError] = useState<string | null>(null);
  const [status, setStatus] = useState<LoadStatus>("idle");
  const [progressStep, setProgressStep] = useState<ProgressStep>("idle");
  const [loadingElapsedMs, setLoadingElapsedMs] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    status !== "loading" &&
    parserConfig?.gemini_configured !== false &&
    (Boolean(selectedFile) || Boolean(problemText.trim()));
  const statusIsProblem = status === "error" || parserConfig?.gemini_configured === false || Boolean(parserConfigError);

  useEffect(() => {
    let active = true;

    Promise.allSettled([fetchParserConfig(), fetchScopeBoundary()])
      .then(([configResult, scopeResult]) => {
        if (!active) {
          return;
        }

        if (configResult.status === "fulfilled") {
          setParserConfig(configResult.value);
          setParserConfigError(null);
        } else {
          setParserConfigError(errorMessage(configResult.reason));
        }

        if (scopeResult.status === "fulfilled") {
          setScopeBoundary(scopeResult.value);
        }
      })
      .catch((caughtError) => {
        if (!active) {
          return;
        }

        setParserConfigError(errorMessage(caughtError));
      });

    return () => {
      active = false;
    };
  }, [setScopeBoundary]);

  useEffect(() => {
    if (!selectedFile) {
      setSelectedImagePreviewUrl(null);
      return;
    }

    const previewUrl = URL.createObjectURL(selectedFile);
    setSelectedImagePreviewUrl(previewUrl);

    return () => {
      URL.revokeObjectURL(previewUrl);
    };
  }, [selectedFile]);

  useEffect(() => {
    if (status !== "loading") {
      setLoadingElapsedMs(0);
      return;
    }

    const startedAt = Date.now();
    const timer = window.setInterval(() => {
      setLoadingElapsedMs(Date.now() - startedAt);
    }, 600);

    return () => window.clearInterval(timer);
  }, [status]);

  useEffect(() => {
    function handleWindowPaste(event: globalThis.ClipboardEvent) {
      if (event.defaultPrevented || !event.clipboardData) {
        return;
      }

      const imageFile = imageFileFromClipboard(event.clipboardData);
      if (!imageFile) {
        return;
      }

      event.preventDefault();
      acceptImageFile(imageFile);
    }

    function handleWindowDragOver(event: globalThis.DragEvent) {
      if (event.defaultPrevented || !event.dataTransfer || !hasImageDragItem(event.dataTransfer)) {
        return;
      }

      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
      setIsImageDragActive(true);
    }

    function handleWindowDragLeave(event: globalThis.DragEvent) {
      const leftWindow =
        event.clientX <= 0 ||
        event.clientY <= 0 ||
        event.clientX >= window.innerWidth ||
        event.clientY >= window.innerHeight;

      if (leftWindow) {
        setIsImageDragActive(false);
      }
    }

    function handleWindowDrop(event: globalThis.DragEvent) {
      if (event.defaultPrevented || !event.dataTransfer) {
        return;
      }

      const imageFile = imageFileFromDataTransfer(event.dataTransfer);
      setIsImageDragActive(false);

      if (!imageFile) {
        return;
      }

      event.preventDefault();
      acceptImageFile(imageFile);
    }

    window.addEventListener("paste", handleWindowPaste);
    window.addEventListener("dragover", handleWindowDragOver);
    window.addEventListener("dragleave", handleWindowDragLeave);
    window.addEventListener("drop", handleWindowDrop);

    return () => {
      window.removeEventListener("paste", handleWindowPaste);
      window.removeEventListener("dragover", handleWindowDragOver);
      window.removeEventListener("dragleave", handleWindowDragLeave);
      window.removeEventListener("drop", handleWindowDrop);
    };
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    acceptImageFile(event.target.files?.[0] ?? null);
  }

  function handlePaste(event: ReactClipboardEvent<HTMLFormElement>) {
    const imageFile = imageFileFromClipboard(event.clipboardData);
    if (!imageFile) {
      return;
    }

    event.preventDefault();
    acceptImageFile(imageFile);
  }

  function handleDragEnter(event: DragEvent<HTMLFormElement>) {
    if (!hasImageDragItem(event.dataTransfer)) {
      return;
    }

    event.preventDefault();
    setIsImageDragActive(true);
  }

  function handleDragOver(event: DragEvent<HTMLFormElement>) {
    if (!hasImageDragItem(event.dataTransfer)) {
      return;
    }

    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setIsImageDragActive(true);
  }

  function handleDragLeave(event: DragEvent<HTMLFormElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setIsImageDragActive(false);
    }
  }

  function handleDrop(event: DragEvent<HTMLFormElement>) {
    const imageFile = imageFileFromDataTransfer(event.dataTransfer);
    setIsImageDragActive(false);

    if (!imageFile) {
      return;
    }

    event.preventDefault();
    acceptImageFile(imageFile);
  }

  function acceptImageFile(file: File | null) {
    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!isSupportedImageFile(file)) {
      setStatus("error");
      setError("Use a PNG, JPEG, or WebP image.");
      return;
    }

    setSelectedFile(file);
    setStatus("idle");
    setError(null);
  }

  function clearSelectedImage() {
    setSelectedFile(null);
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = problemText.trim();
    const fileForSubmit = selectedFile;

    if (!trimmed && !fileForSubmit) {
      setError("Paste a circuit question or image first.");
      setStatus("error");
      return;
    }

    setStatus("loading");
    setProgressStep(fileForSubmit ? "reading_image" : "solving");
    setError(null);

    try {
      let pipeline: FullPipelineResponse;
      if (fileForSubmit) {
        setProgressStep("reading_image");
        const imageBase64 = await fileToBase64(fileForSubmit);
        setProgressStep("solving");
        pipeline = await runImagePipeline({
          imageBase64,
          mimeType: normalizeImageMimeType(fileForSubmit.type),
          problemText: trimmed
        });
      } else {
        setProgressStep("solving");
        pipeline = await runTextPipeline(trimmed);
      }

      const renderable = shouldRenderSchematic(pipeline);
      if (renderable) {
        setProgressStep("rendering");
      }
      const [visualCircuit, schematicSvg, analysisView] = renderable
        ? await Promise.all([
            fetchVisualLayout(pipeline.circuit_ir, pipeline.parser_used),
            fetchSchematicSvg(pipeline.circuit_ir, SCHEMATIC_RENDERER, pipeline.parser_used),
            fetchAnalysisView(pipeline.circuit_ir, pipeline.solution_packet).catch(() => null)
          ])
        : [null, null, null];

      setProgressStep("organizing");

      loadCircuit({
        analysisView,
        circuit: pipeline.circuit_ir,
        explanation: pipeline.explanation,
        debugTrace: pipeline.debug_trace,
        parserUsed: pipeline.parser_used,
        problemText: trimmed || pipeline.circuit_ir.title,
        schematicRenderer: SCHEMATIC_RENDERER,
        schematicSvg,
        solutionPacket: pipeline.solution_packet,
        variants: pipeline.variants ?? [],
        visualCircuit
      });
      clearChatHistory();
      addStudentMessage(fileForSubmit ? imageSubmissionText(fileForSubmit, trimmed) : trimmed);
      addAssistantMessage(loadSocraticOpening(pipeline, renderable));
      setStatus("idle");
      setProgressStep("idle");
    } catch (caughtError) {
      setStatus("error");
      setProgressStep("idle");
      setError(errorMessage(caughtError));
    }
  }

  return (
    <form
      className={cn(
        "grid gap-3 p-3 transition",
        isImageDragActive && "bg-accent/60 ring-2 ring-inset ring-primary"
      )}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onPaste={handlePaste}
      onSubmit={handleSubmit}
    >
      <div className="grid min-w-0 gap-3 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
        <label className="grid min-w-0 gap-1 text-xs font-medium text-muted-foreground" htmlFor="problem-text">
          Problem
          <textarea
            id="problem-text"
            className="soft-field min-h-[72px] min-w-0 resize-none py-2 leading-5"
            onChange={(event) => setProblemText(event.target.value)}
            placeholder="Paste a circuit question here, or paste/drop a schematic image."
            value={problemText}
          />
        </label>
        <div className="flex min-w-0 items-center gap-2">
          <input
            accept="image/png,image/jpeg,image/webp"
            className="sr-only"
            id="circuit-image"
            onChange={handleFileChange}
            type="file"
          />
          <label
            aria-label="Attach schematic image"
            className={cn(
              "flex size-10 shrink-0 cursor-pointer items-center justify-center rounded-md border bg-background text-muted-foreground transition hover:bg-muted hover:text-foreground",
              selectedFile && "border-primary bg-accent text-accent-foreground"
            )}
            htmlFor="circuit-image"
            title="Attach schematic image"
          >
            <Upload className="size-4" aria-hidden="true" />
          </label>
        <button
          className="soft-button h-10 shrink-0 bg-primary px-4 text-primary-foreground hover:opacity-90"
          disabled={!canSubmit}
          type="submit"
        >
          {status === "loading" ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <Sparkles className="size-4" aria-hidden="true" />
          )}
          Run
        </button>
        </div>
      </div>
      {status !== "loading" ? (
        <p
          className={cn(
            "min-w-0 truncate text-xs",
            statusIsProblem ? "text-destructive" : "text-muted-foreground"
          )}
        >
          {inputStatusText({
            error,
            isImageDragActive,
            parserConfig,
            parserConfigError,
            progressStep,
            selectedFile,
            status,
            loadingElapsedMs
          })}
        </p>
      ) : null}

      {status === "loading" ? (
        <RunProgress hasImage={Boolean(selectedFile)} loadingElapsedMs={loadingElapsedMs} progressStep={progressStep} />
      ) : null}

      {selectedFile && selectedImagePreviewUrl ? (
        <div className="flex min-w-0 items-center gap-3 rounded-md border bg-background p-2">
          <img
            alt={selectedFile.name || "Selected schematic image"}
            className="h-16 w-24 shrink-0 rounded border bg-white object-contain"
            src={selectedImagePreviewUrl}
          />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{selectedFile.name || "pasted-schematic.png"}</p>
            <p className="text-xs text-muted-foreground">{formatFileSize(selectedFile.size)}</p>
          </div>
          <button
            aria-label="Remove selected image"
            className="flex size-9 shrink-0 items-center justify-center rounded-md border bg-card text-muted-foreground transition hover:bg-muted hover:text-foreground"
            onClick={clearSelectedImage}
            type="button"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
        </div>
      ) : null}
    </form>
  );
}

function RunProgress({
  hasImage,
  loadingElapsedMs,
  progressStep
}: {
  hasImage: boolean;
  loadingElapsedMs: number;
  progressStep: ProgressStep;
}) {
  const progress = RUN_PROGRESS[progressStep];
  const detail = progressDetail(progressStep, loadingElapsedMs, hasImage);

  return (
    <div className="grid gap-1.5" aria-live="polite">
      <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
        <span className="truncate">{detail}</span>
        <span className="shrink-0 tabular-nums">{progress.percent}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-[width] duration-300"
          style={{ width: `${progress.percent}%` }}
        />
      </div>
    </div>
  );
}

function progressDetail(progressStep: ProgressStep, elapsedMs: number, hasImage: boolean): string {
  if (progressStep === "solving") {
    const seconds = elapsedMs / 1000;
    if (seconds < 3) {
      return hasImage ? "Reading schematic image" : "Reading problem statement";
    }
    if (seconds < 8) {
      return "Building Circuit IR";
    }
    if (seconds < 14) {
      return "Running deterministic solver";
    }
    return "Verifying KCL, power, units, and requested answers";
  }

  return RUN_PROGRESS[progressStep].label;
}

function CanvasHeader() {
  const visualCircuit = useTutorStore((state) => state.visualCircuit);
  const schematicRenderer = useTutorStore((state) => state.schematicRenderer);
  const schematicSvg = useTutorStore((state) => state.schematicSvg);
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const selectedEntity = useTutorStore((state) => state.selectedEntity);

  return (
    <div className="flex min-h-14 items-center justify-between gap-3 border-b px-4">
      <div className="min-w-0">
        <h2 className="truncate text-sm font-semibold">Circuit Playground</h2>
        <p className="truncate text-xs text-muted-foreground">
          {schematicSvg
            ? `${schematicRenderer.toUpperCase()} preview layer`
            : solutionPacket
              ? `${solutionPacket.verification_badge.label} parse workspace`
              : visualCircuit?.layout_strategy ?? "semantic playground"}
        </p>
      </div>
      {selectedEntity ? (
        <span className="rounded-md border bg-accent px-2 py-1 text-xs font-medium text-accent-foreground">
          {selectedEntity.kind}: {selectedEntity.id}
        </span>
      ) : null}
    </div>
  );
}

function CircuitCanvas() {
  const circuit = useTutorStore((state) => state.circuit);
  const schematicSvg = useTutorStore((state) => state.schematicSvg);
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const visualCircuit = useTutorStore((state) => state.visualCircuit);
  const highlightedEntities = useTutorStore((state) => state.highlightedEntities);
  const setHoveredEntity = useTutorStore((state) => state.setHoveredEntity);
  const selectEntity = useTutorStore((state) => state.selectEntity);
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const dragStateRef = useRef<PlaygroundDragState | null>(null);
  const manualItemCounterRef = useRef(0);
  const [items, setItems] = useState<PlaygroundItem[]>([]);
  const [selectedPlaygroundItemId, setSelectedPlaygroundItemId] = useState<string | null>(null);
  const [isDropActive, setIsDropActive] = useState(false);

  const optcpvModel = useMemo(() => parseOptcpvModel(schematicSvg), [schematicSvg]);
  const playgroundFrame = optcpvModel?.viewBox ?? visualCircuitFrame(visualCircuit);
  const active = useMemo(() => toEntitySet(highlightedEntities), [highlightedEntities]);
  const playgroundSourceKey = useMemo(
    () =>
      [
        circuit?.id ?? "empty",
        optcpvModel?.circuitId ?? "no-optcpv",
        optcpvModel?.components.map((component) => component.id).join("|") ?? "no-optcpv-components",
        visualCircuit?.circuit_id ?? "no-visual",
        circuit?.components.map((component) => component.id).join("|") ?? "no-components",
        visualCircuit?.components.map((component) => component.id).join("|") ?? "no-visual-components",
        visualCircuit?.nodes.map((node) => node.id).join("|") ?? "no-visual-nodes"
      ].join(":"),
    [circuit, optcpvModel, visualCircuit]
  );
  const selectedItem = items.find((item) => item.id === selectedPlaygroundItemId) ?? null;
  const hasCircuitSource = Boolean(circuit?.components.length || visualCircuit || optcpvModel);

  useEffect(() => {
    const nextItems = buildInitialPlaygroundItems(optcpvModel, visualCircuit, circuit);
    manualItemCounterRef.current = 0;
    setItems(nextItems);
    setSelectedPlaygroundItemId(null);
  }, [optcpvModel, playgroundSourceKey, visualCircuit, circuit]);

  if (!hasCircuitSource && solutionPacket) {
    return <ParseStatusPanel solutionPacket={solutionPacket} />;
  }

  function clearPlaygroundSelection() {
    setSelectedPlaygroundItemId(null);
    selectEntity(null);
  }

  function selectPlaygroundItem(item: PlaygroundItem) {
    setSelectedPlaygroundItemId(item.id);
    selectEntity(item.sourceEntity ?? null);
  }

  function updateSelectedItem(updates: Partial<Pick<PlaygroundItem, "label" | "value">>) {
    if (!selectedPlaygroundItemId) {
      return;
    }

    setItems((currentItems) =>
      currentItems.map((item) => (item.id === selectedPlaygroundItemId ? { ...item, ...updates } : item))
    );
  }

  function addPlaygroundItem(kind: PlaygroundItemKind, point: PlaygroundPoint) {
    const tool = PLAYGROUND_TOOL_BY_KIND.get(kind);
    if (!tool) {
      return;
    }

    manualItemCounterRef.current += 1;
    const sequence = manualItemCounterRef.current;
    const nextItem: PlaygroundItem = {
      id: `manual-${kind}-${sequence}`,
      kind,
      label: tool.defaultLabel === "GND" ? `GND${sequence}` : `${tool.defaultLabel}${sequence}`,
      value: tool.defaultValue,
      origin: "manual",
      width: defaultPlaygroundItemSize(kind).width,
      height: defaultPlaygroundItemSize(kind).height,
      ...clampPlaygroundPoint(point, playgroundFrame)
    };

    setItems((currentItems) => [...currentItems, nextItem]);
    setSelectedPlaygroundItemId(nextItem.id);
    selectEntity(null);
  }

  function deleteSelectedItem() {
    if (!selectedPlaygroundItemId) {
      return;
    }

    setItems((currentItems) => currentItems.filter((item) => item.id !== selectedPlaygroundItemId));
    clearPlaygroundSelection();
  }

  function resetPlayground() {
    setItems(buildInitialPlaygroundItems(optcpvModel, visualCircuit, circuit));
    setSelectedPlaygroundItemId(null);
    selectEntity(null);
  }

  function handleToolClick(kind: PlaygroundItemKind) {
    const offset = manualItemCounterRef.current % 5;
    addPlaygroundItem(kind, {
      x: playgroundFrame.x + playgroundFrame.width * (0.46 + offset * 0.02),
      y: playgroundFrame.y + playgroundFrame.height * (0.44 + offset * 0.03)
    });
  }

  function handleToolDragStart(event: DragEvent<HTMLButtonElement>, kind: PlaygroundItemKind) {
    event.dataTransfer.setData(PLAYGROUND_DND_MIME, kind);
    event.dataTransfer.effectAllowed = "copy";
  }

  function handleStageDragOver(event: DragEvent<HTMLDivElement>) {
    if (!hasPlaygroundDragData(event)) {
      return;
    }

    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setIsDropActive(true);
  }

  function handleStageDragLeave(event: DragEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
      setIsDropActive(false);
    }
  }

  function handleStageDrop(event: DragEvent<HTMLDivElement>) {
    const kind = event.dataTransfer.getData(PLAYGROUND_DND_MIME);
    if (!isPlaygroundItemKind(kind)) {
      return;
    }

    event.preventDefault();
    setIsDropActive(false);
    addPlaygroundItem(kind, clientPointToPlaygroundPoint(event, canvasRef.current, playgroundFrame));
  }

  function handleItemPointerDown(event: ReactPointerEvent<SVGGElement>, item: PlaygroundItem) {
    if (event.button !== 0) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    selectPlaygroundItem(item);
    dragStateRef.current = {
      itemId: item.id,
      pointerId: event.pointerId,
      lastClientX: event.clientX,
      lastClientY: event.clientY
    };

    try {
      event.currentTarget.setPointerCapture(event.pointerId);
    } catch {
      // Pointer capture can fail if the browser has already cancelled the pointer.
    }
  }

  function handleItemPointerMove(event: ReactPointerEvent<SVGGElement>) {
    const dragState = dragStateRef.current;
    const canvas = canvasRef.current;
    if (!dragState || dragState.pointerId !== event.pointerId || !canvas) {
      return;
    }

    const rect = canvas.getBoundingClientRect();
    if (!rect.width || !rect.height) {
      return;
    }

    const scale = optcpvContainScale(rect, playgroundFrame);
    const deltaX = (event.clientX - dragState.lastClientX) / scale;
    const deltaY = (event.clientY - dragState.lastClientY) / scale;
    dragStateRef.current = {
      ...dragState,
      lastClientX: event.clientX,
      lastClientY: event.clientY
    };

    setItems((currentItems) =>
      currentItems.map((item) =>
        item.id === dragState.itemId
          ? { ...item, ...clampPlaygroundPoint({ x: item.x + deltaX, y: item.y + deltaY }, playgroundFrame) }
          : item
      )
    );
  }

  function handleItemPointerUp(event: ReactPointerEvent<SVGGElement>) {
    const dragState = dragStateRef.current;
    if (dragState?.pointerId !== event.pointerId) {
      return;
    }

    dragStateRef.current = null;
    try {
      event.currentTarget.releasePointerCapture(event.pointerId);
    } catch {
      // The pointer may already be released by the browser.
    }
  }

  return (
    <div className="grid min-h-0 flex-1 grid-rows-[auto_minmax(420px,1fr)_auto] bg-muted/40 xl:grid-cols-[176px_minmax(0,1fr)_220px] xl:grid-rows-1">
      <PlaygroundPalette
        onToolClick={handleToolClick}
        onToolDragStart={handleToolDragStart}
      />

      <div className="min-h-[420px] min-w-0 p-3 xl:min-h-0">
        <div
          ref={canvasRef}
          className={cn(
            "circuit-grid relative h-full min-h-[420px] overflow-hidden rounded-md border bg-white shadow-inner",
            isDropActive && "ring-2 ring-primary/45 ring-inset"
          )}
          onClick={(event) => {
            if ((event.target as Element).closest("[data-playground-item='true']")) {
              return;
            }
            clearPlaygroundSelection();
          }}
          onDragLeave={handleStageDragLeave}
          onDragOver={handleStageDragOver}
          onDrop={handleStageDrop}
        >
          <PlaygroundBackdrop active={active} optcpvModel={optcpvModel} visualCircuit={visualCircuit} />

          <div className="pointer-events-none absolute left-3 top-3 z-20 flex items-center gap-2 rounded-md border bg-card/90 px-2.5 py-1 text-xs font-medium text-muted-foreground shadow-sm backdrop-blur">
            <MousePointer2 className="size-3.5 text-primary" aria-hidden={true} />
            <span>{optcpvModel ? `${items.length} OptCPV items` : `${items.length} items`}</span>
          </div>

          <div className="absolute right-3 top-3 z-20 flex gap-1 rounded-md border bg-card/90 p-1 shadow-sm backdrop-blur">
            <button
              className="soft-button size-8 border bg-background text-muted-foreground hover:bg-muted"
              onClick={resetPlayground}
              title="Reset playground"
              type="button"
            >
              <RefreshCw className="size-4" aria-hidden={true} />
              <span className="sr-only">Reset playground</span>
            </button>
            <button
              className="soft-button size-8 border bg-background text-muted-foreground hover:bg-muted"
              disabled={!selectedItem}
              onClick={deleteSelectedItem}
              title="Delete selected item"
              type="button"
            >
              <Trash2 className="size-4" aria-hidden={true} />
              <span className="sr-only">Delete selected item</span>
            </button>
          </div>

          {optcpvModel ? (
            <div className="pointer-events-none absolute bottom-3 left-3 z-20 max-w-[calc(100%-1.5rem)] rounded-md border bg-card/90 px-2.5 py-1 text-xs text-muted-foreground shadow-sm backdrop-blur">
              {optcpvModel.renderer} · {optcpvModel.layoutMode}
              {optcpvModel.fallbackUsed ? " · fallback regions" : ""}
            </div>
          ) : null}

          {!items.length ? (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center p-6">
              <div className="rounded-md border border-dashed bg-card/95 p-4 text-center shadow-sm">
                <p className="text-sm font-semibold">Empty playground</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {optcpvModel ? "OptCPV canvas ready" : "Parts palette ready"}
                </p>
              </div>
            </div>
          ) : null}

          <svg
            className="absolute inset-0 z-10 h-full w-full overflow-visible"
            role="img"
            aria-label="OptCPV playground overlay"
            viewBox={`${playgroundFrame.x} ${playgroundFrame.y} ${playgroundFrame.width} ${playgroundFrame.height}`}
          >
            <g>
              {optcpvModel?.terminals.map((terminal) => (
                <circle
                  key={`${terminal.componentId}:${terminal.pinName}:${terminal.netName}:${terminal.x}:${terminal.y}`}
                  cx={terminal.x}
                  cy={terminal.y}
                  r="5"
                  className="fill-primary/20 stroke-primary/40"
                  strokeWidth="1.5"
                />
              ))}
            </g>
            {items.map((item) => (
              <PlaygroundSvgItem
                key={item.id}
                item={item}
                isHighlighted={Boolean(item.sourceEntity && active.has(entityKey(item.sourceEntity.kind, item.sourceEntity.id)))}
                isSelected={item.id === selectedPlaygroundItemId}
                onPointerDown={handleItemPointerDown}
                onPointerMove={handleItemPointerMove}
                onPointerUp={handleItemPointerUp}
                onPointerCancel={handleItemPointerUp}
                onPointerEnter={() => setHoveredEntity(item.sourceEntity ?? null)}
                onPointerLeave={() => setHoveredEntity(null)}
              />
            ))}
          </svg>
        </div>
      </div>

      <PlaygroundInspector
        selectedItem={selectedItem}
        onUpdateSelectedItem={updateSelectedItem}
      />
    </div>
  );
}

function PlaygroundPalette({
  onToolClick,
  onToolDragStart
}: {
  onToolClick: (kind: PlaygroundItemKind) => void;
  onToolDragStart: (event: DragEvent<HTMLButtonElement>, kind: PlaygroundItemKind) => void;
}) {
  return (
    <aside className="border-b bg-card/80 p-3 xl:border-b-0 xl:border-r">
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground">
        <Move className="size-3.5 text-primary" aria-hidden={true} />
        Parts
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1 xl:grid xl:grid-cols-1 xl:overflow-visible xl:pb-0">
        {PLAYGROUND_TOOLS.map((tool) => {
          const Icon = tool.icon;
          return (
            <button
              key={tool.kind}
              className="flex min-w-32 items-center gap-2 rounded-md border bg-background px-3 py-2 text-left text-sm transition hover:bg-muted active:translate-y-px xl:min-w-0"
              draggable
              onClick={() => onToolClick(tool.kind)}
              onDragStart={(event) => onToolDragStart(event, tool.kind)}
              title={tool.label}
              type="button"
            >
              <span className="flex size-8 shrink-0 items-center justify-center rounded-md bg-accent text-accent-foreground">
                <Icon className="size-4" aria-hidden={true} />
              </span>
              <span className="min-w-0">
                <span className="block truncate font-semibold">{tool.label}</span>
                <span className="block truncate text-xs text-muted-foreground">{tool.defaultValue}</span>
              </span>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

function PlaygroundBackdrop({
  active,
  optcpvModel,
  visualCircuit
}: {
  active: Set<string>;
  optcpvModel: OptcpvModel | null;
  visualCircuit: VisualCircuit | null;
}) {
  if (optcpvModel) {
    return (
      <div
        aria-label={`OptCPV schematic ${optcpvModel.circuitId}`}
        className="pointer-events-none absolute inset-0 z-0 [&>svg]:h-full [&>svg]:w-full [&>svg]:overflow-visible"
        dangerouslySetInnerHTML={{ __html: optcpvModel.sanitizedSvg }}
        role="img"
      />
    );
  }

  if (visualCircuit) {
    return <SemanticCircuitBackdrop active={active} visualCircuit={visualCircuit} />;
  }

  return null;
}

function SemanticCircuitBackdrop({ active, visualCircuit }: { active: Set<string>; visualCircuit: VisualCircuit }) {
  const nodeById = new Map(visualCircuit.nodes.map((node) => [node.id, node]));
  const bounds = getCircuitBounds(visualCircuit);

  return (
    <svg
      aria-label={`Circuit layout for ${visualCircuit.circuit_id}`}
      className="pointer-events-none absolute inset-0 h-full w-full opacity-35"
      role="img"
      viewBox={`${bounds.x} ${bounds.y} ${bounds.width} ${bounds.height}`}
    >
      <g>
        {visualCircuit.wires.map((wire) => {
          const isActive =
            active.has(entityKey("wire", wire.id)) ||
            Boolean(wire.component_id && active.has(entityKey("component", wire.component_id)));
          const fallbackPoints = [
            nodeById.get(wire.from_node)?.position,
            nodeById.get(wire.to_node)?.position
          ].filter(isDefined);
          const points = wire.points.length ? wire.points : fallbackPoints;

          return (
            <polyline
              key={wire.id}
              className={cn("fill-none transition-all", isActive ? "stroke-primary" : "stroke-slate-400")}
              data-wire-id={wire.id}
              points={points.map((point) => `${point.x},${point.y}`).join(" ")}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={isActive ? 5 : 3}
            />
          );
        })}
      </g>

      <g>
        {visualCircuit.components.map((component) => {
          const nodes = component.nodes.map((nodeId) => nodeById.get(nodeId)).filter(isDefined);
          if (!nodes.length) {
            return null;
          }

          return (
            <ComponentGlyph
              key={component.id}
              component={component}
              isActive={active.has(entityKey("component", component.id))}
              nodes={nodes}
              onClick={() => undefined}
              onPointerEnter={() => undefined}
              onPointerLeave={() => undefined}
            />
          );
        })}
      </g>

      <g>
        {visualCircuit.nodes.map((node) => {
          const isActive = active.has(entityKey("node", node.id));
          return (
            <g key={node.id} data-node-id={node.id}>
              <circle
                className={cn("transition-all", isActive ? "fill-primary stroke-primary" : "fill-white stroke-slate-700")}
                cx={node.position.x}
                cy={node.position.y}
                r={node.role === "ground" ? 9 : 7}
                strokeWidth={isActive ? 4 : 3}
              />
              <text
                className={cn("select-none fill-slate-700 text-[15px] font-semibold", isActive && "fill-primary")}
                textAnchor="middle"
                x={node.position.x}
                y={node.position.y - 16}
              >
                {node.role === "ground" ? "GND" : node.label}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
}

function PlaygroundSvgItem({
  isHighlighted,
  isSelected,
  item,
  onPointerCancel,
  onPointerDown,
  onPointerEnter,
  onPointerLeave,
  onPointerMove,
  onPointerUp
}: {
  isHighlighted: boolean;
  isSelected: boolean;
  item: PlaygroundItem;
  onPointerCancel: (event: ReactPointerEvent<SVGGElement>) => void;
  onPointerDown: (event: ReactPointerEvent<SVGGElement>, item: PlaygroundItem) => void;
  onPointerEnter: () => void;
  onPointerLeave: () => void;
  onPointerMove: (event: ReactPointerEvent<SVGGElement>) => void;
  onPointerUp: (event: ReactPointerEvent<SVGGElement>) => void;
}) {
  const stroke = isSelected || isHighlighted ? "hsl(var(--primary))" : "hsl(165 15% 36%)";
  const fill = item.origin === "circuit" ? "hsl(var(--accent) / 0.08)" : "hsl(var(--card) / 0.94)";
  const labelY = item.height / 2 + 18;

  return (
    <g
      className="cursor-grab touch-none select-none transition active:cursor-grabbing"
      data-playground-item="true"
      onPointerCancel={onPointerCancel}
      onPointerDown={(event) => onPointerDown(event, item)}
      onPointerEnter={onPointerEnter}
      onPointerLeave={onPointerLeave}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      tabIndex={0}
      transform={`translate(${item.x} ${item.y})`}
    >
      <rect
        x={-item.width / 2}
        y={-item.height / 2}
        width={item.width}
        height={item.height}
        rx={Math.min(10, item.width / 8)}
        fill={fill}
        stroke={stroke}
        strokeDasharray={item.origin === "circuit" ? "8 6" : undefined}
        strokeWidth={isSelected || isHighlighted ? 4 : 2.5}
      />
      {item.origin === "manual" ? <ManualOptcpvGlyph item={item} stroke={stroke} /> : null}
      <text
        y={item.origin === "manual" ? labelY : 5}
        textAnchor="middle"
        className="pointer-events-none fill-slate-900 text-[16px] font-bold"
      >
        {item.label}
      </text>
      <text
        y={item.origin === "manual" ? labelY + 18 : 23}
        textAnchor="middle"
        className="pointer-events-none fill-slate-600 text-[12px] font-semibold"
      >
        {shortenLabel(item.value)}
      </text>
    </g>
  );
}

function ManualOptcpvGlyph({ item, stroke }: { item: PlaygroundItem; stroke: string }) {
  const halfWidth = item.width / 2;
  const halfHeight = item.height / 2;

  if (item.kind === "capacitor") {
    return (
      <g stroke={stroke} strokeLinecap="round" strokeWidth="4">
        <line x1={-halfWidth + 12} y1="0" x2="-12" y2="0" />
        <line x1="12" y1="0" x2={halfWidth - 12} y2="0" />
        <line x1="-10" y1={-halfHeight + 10} x2="-10" y2={halfHeight - 10} />
        <line x1="10" y1={-halfHeight + 10} x2="10" y2={halfHeight - 10} />
      </g>
    );
  }

  if (item.kind === "voltage_source" || item.kind === "current_source") {
    return (
      <g stroke={stroke} strokeLinecap="round" strokeWidth="4">
        <line x1={-halfWidth + 10} y1="0" x2="-20" y2="0" />
        <line x1="20" y1="0" x2={halfWidth - 10} y2="0" />
        <circle cx="0" cy="0" r={Math.min(halfHeight - 9, 20)} fill="white" />
        {item.kind === "voltage_source" ? (
          <>
            <line x1="-7" y1="0" x2="7" y2="0" />
            <line x1="0" y1="-7" x2="0" y2="7" />
          </>
        ) : (
          <path d="M -7 6 L 0 -7 L 7 6" fill="none" />
        )}
      </g>
    );
  }

  if (item.kind === "ground") {
    return (
      <g stroke={stroke} strokeLinecap="round" strokeWidth="4">
        <line x1="0" y1={-halfHeight + 10} x2="0" y2="0" />
        <line x1="-24" y1="0" x2="24" y2="0" />
        <line x1="-16" y1="9" x2="16" y2="9" />
        <line x1="-7" y1="18" x2="7" y2="18" />
      </g>
    );
  }

  if (item.kind === "op_amp") {
    return <path d="M -28 -24 L -28 24 L 34 0 Z" fill="white" stroke={stroke} strokeLinejoin="round" strokeWidth="4" />;
  }

  if (item.kind === "probe" || item.kind === "node") {
    return <circle cx="0" cy="0" r={Math.min(halfWidth, halfHeight) * 0.38} fill="white" stroke={stroke} strokeWidth="4" />;
  }

  if (item.kind === "wire") {
    return (
      <g stroke={stroke} strokeLinecap="round" strokeWidth="4">
        <path d={`M ${-halfWidth + 12} ${halfHeight - 12} C -16 -18, 16 18, ${halfWidth - 12} ${-halfHeight + 12}`} fill="none" />
        <circle cx={-halfWidth + 12} cy={halfHeight - 12} r="4" fill={stroke} />
        <circle cx={halfWidth - 12} cy={-halfHeight + 12} r="4" fill={stroke} />
      </g>
    );
  }

  if (item.kind === "diode") {
    return (
      <g stroke={stroke} strokeLinecap="round" strokeLinejoin="round" strokeWidth="4">
        <line x1={-halfWidth + 12} y1="0" x2="-18" y2="0" />
        <line x1="18" y1="0" x2={halfWidth - 12} y2="0" />
        <path d="M -16 -16 L -16 16 L 12 0 Z" fill="white" />
        <line x1="16" y1="-16" x2="16" y2="16" />
      </g>
    );
  }

  if (item.kind === "note") {
    return <path d="M -26 -18 H 18 L 26 -10 V 22 H -26 Z M 18 -18 V -10 H 26" fill="white" stroke={stroke} strokeLinejoin="round" strokeWidth="4" />;
  }

  return (
    <g stroke={stroke} strokeLinecap="round" strokeLinejoin="round" strokeWidth="4">
      <line x1={-halfWidth + 12} y1="0" x2="-28" y2="0" />
      <polyline points="-28,0 -22,-14 -12,14 -2,-14 8,14 18,-14 28,0" fill="none" />
      <line x1="28" y1="0" x2={halfWidth - 12} y2="0" />
    </g>
  );
}

function PlaygroundInspector({
  onUpdateSelectedItem,
  selectedItem
}: {
  onUpdateSelectedItem: (updates: Partial<Pick<PlaygroundItem, "label" | "value">>) => void;
  selectedItem: PlaygroundItem | null;
}) {
  const tool = selectedItem ? PLAYGROUND_TOOL_BY_KIND.get(selectedItem.kind) : null;

  return (
    <aside className="border-t bg-card/80 p-3 xl:border-l xl:border-t-0">
      <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground">
        <MousePointer2 className="size-3.5 text-primary" aria-hidden={true} />
        Selection
      </div>
      {selectedItem ? (
        <div className="space-y-3">
          <label className="block text-xs font-medium text-muted-foreground">
            Label
            <input
              className="soft-field mt-1 h-9 w-full"
              onChange={(event) => onUpdateSelectedItem({ label: event.target.value })}
              value={selectedItem.label}
            />
          </label>
          <label className="block text-xs font-medium text-muted-foreground">
            Value
            <input
              className="soft-field mt-1 h-9 w-full"
              onChange={(event) => onUpdateSelectedItem({ value: event.target.value })}
              value={selectedItem.value}
            />
          </label>
          <div className="grid gap-2 rounded-md border bg-background p-3 text-xs">
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Kind</span>
              <span className="truncate font-semibold">{tool?.label ?? selectedItem.kind}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Origin</span>
              <span className="truncate font-semibold">{selectedItem.origin === "circuit" ? "Circuit parse" : "Manual"}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-muted-foreground">Position</span>
              <span className="font-mono text-[11px] font-semibold">
                {formatNumber(selectedItem.x)}, {formatNumber(selectedItem.y)}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-md border border-dashed bg-background p-3 text-sm text-muted-foreground">
          No selection
        </div>
      )}
    </aside>
  );
}

function ParseStatusPanel({ solutionPacket }: { solutionPacket: SolutionPacket }) {
  const symbolicLines = symbolicAnswerLines(solutionPacket);
  const details = [
    solutionPacket.verification_badge.message,
    ...solutionPacket.warnings
  ].filter(Boolean);

  if (symbolicLines.length) {
    return (
      <div className="circuit-grid flex flex-1 items-center justify-center bg-white p-8">
        <div className="max-w-xl rounded-md border bg-card p-5 text-card-foreground shadow-sm">
          <p className="text-sm font-semibold">Symbolic result</p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-muted-foreground">
            {symbolicLines.map((line) => (
              <li key={line}>
                <MarkdownInline>{line}</MarkdownInline>
              </li>
            ))}
          </ul>
          <MarkdownBlock className="mt-3 text-sm leading-6 text-muted-foreground">
            V_c is being treated as the command-voltage symbol, not as a missing numeric value.
          </MarkdownBlock>
        </div>
      </div>
    );
  }

  return (
    <div className="circuit-grid flex flex-1 items-center justify-center bg-white p-8">
      <div className="max-w-xl rounded-md border bg-card p-5 text-card-foreground shadow-sm">
        <p className="text-sm font-semibold">No schematic rendered</p>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          CiTT did not pass this parse to the OptCPV drawing module because the circuit is not verified yet.
        </p>
        {details.length ? (
          <ul className="mt-3 list-disc space-y-2 pl-5 text-sm leading-6 text-muted-foreground">
            {details.slice(0, 4).map((detail) => (
              <li key={detail}>{detail}</li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}

type ComponentGlyphProps = {
  component: VisualComponent;
  isActive: boolean;
  nodes: VisualNode[];
  onPointerEnter: () => void;
  onPointerLeave: () => void;
  onClick: () => void;
};

function ComponentGlyph({
  component,
  isActive,
  nodes,
  onPointerEnter,
  onPointerLeave,
  onClick
}: ComponentGlyphProps) {
  const [start, end] = nodes;
  const center = getComponentCenter(nodes);
  const angle = start && end ? radiansToDegrees(Math.atan2(end.position.y - start.position.y, end.position.x - start.position.x)) : 0;
  const strokeClass = isActive ? "stroke-primary" : "stroke-slate-800";
  const fillClass = isActive ? "fill-accent" : "fill-white";

  return (
    <g
      className="cursor-pointer"
      data-component-id={component.id}
      onClick={onClick}
      onPointerEnter={onPointerEnter}
      onPointerLeave={onPointerLeave}
      transform={`translate(${center.x} ${center.y}) rotate(${angle})`}
    >
      {component.role === "source" ? (
        <circle
          r="25"
          className={cn(fillClass, strokeClass, "transition-all")}
          strokeWidth={isActive ? 5 : 3}
        />
      ) : component.type.includes("capacitor") ? (
        <g className={cn(strokeClass, "transition-all")} strokeLinecap="round" strokeWidth={isActive ? 5 : 3}>
          <line x1="-12" y1="-25" x2="-12" y2="25" />
          <line x1="12" y1="-25" x2="12" y2="25" />
        </g>
      ) : component.role === "op_amp" ? (
        <path
          d="M -32 -28 L -32 28 L 36 0 Z"
          className={cn(fillClass, strokeClass, "transition-all")}
          strokeWidth={isActive ? 5 : 3}
        />
      ) : (
        <rect
          x="-34"
          y="-17"
          width="68"
          height="34"
          rx="7"
          className={cn(fillClass, strokeClass, "transition-all")}
          strokeWidth={isActive ? 5 : 3}
        />
      )}
      <text
        y={component.role === "source" ? 5 : -27}
        textAnchor="middle"
        className={cn("select-none fill-slate-900 text-[15px] font-bold", isActive && "fill-primary")}
      >
        {component.id}
      </text>
      <text
        y={component.role === "source" ? 44 : 33}
        textAnchor="middle"
        className="select-none fill-slate-600 text-[12px] font-medium"
      >
        {shortenLabel(component.label)}
      </text>
    </g>
  );
}

function StepPanel() {
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const activeStepIndex = useTutorStore((state) => state.activeStepIndex);
  const setActiveStepByIndex = useTutorStore((state) => state.setActiveStepByIndex);
  const setManualFocusEntities = useTutorStore((state) => state.setManualFocusEntities);

  const steps = solutionPacket?.guided_steps.length
    ? solutionPacket.guided_steps
    : solutionPacket?.lesson_packet?.step_by_step_derivation ?? [];
  const activeStep = activeStepIndex >= 0 ? steps[activeStepIndex] : null;
  const lesson = solutionPacket?.lesson_packet ?? null;
  const socraticLecture = solutionPacket?.socratic_lecture ?? null;
  const [activeLectureStage, setActiveLectureStage] = useState(0);
  const selectedLectureStage = socraticLecture?.stages[activeLectureStage] ?? socraticLecture?.stages[0] ?? null;

  useEffect(() => {
    setActiveLectureStage(0);
  }, [solutionPacket?.circuit_id]);

  function moveStep(direction: -1 | 1) {
    if (!steps.length) {
      return;
    }

    const nextIndex = Math.min(Math.max(activeStepIndex + direction, 0), steps.length - 1);
    setActiveStepByIndex(nextIndex);
  }

  return (
    <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)]">
      <PanelHeader
        icon={GraduationCap}
        title="Learn"
        subtitle={lesson?.summary ?? "Run a circuit to build a guided lesson."}
      />
      <ScrollArea.Root className="min-h-0">
        <ScrollArea.Viewport className="h-full">
          <div className="space-y-4 p-4">
            {!solutionPacket ? <EmptyPanel title="No lesson yet" body="Run a text prompt or image to create the guided lesson." /> : null}

            {socraticLecture ? (
              <SocraticLecturePanel
                activeStageIndex={activeLectureStage}
                lecture={socraticLecture}
                selectedStage={selectedLectureStage}
                setActiveStageIndex={setActiveLectureStage}
                setManualFocusEntities={setManualFocusEntities}
              />
            ) : null}

            {lesson?.learning_objectives.length ? (
              <section className="rounded-lg border bg-accent/55 p-3">
                <h3 className="text-sm font-semibold">Objectives</h3>
                <div className="mt-2 flex flex-wrap gap-2">
                  {lesson.learning_objectives.slice(0, 4).map((objective) => (
                    <span key={objective} className="rounded-full bg-background px-2.5 py-1 text-xs text-accent-foreground">
                      {objective}
                    </span>
                  ))}
                </div>
              </section>
            ) : null}

            {activeStep ? (
              <section className="rounded-lg border bg-card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-muted-foreground">
                      Move {Math.max(activeStepIndex, 0) + 1} of {steps.length}
                    </p>
                    <h3 className="mt-1 text-base font-semibold">
                      <MarkdownInline>{activeStep.title}</MarkdownInline>
                    </h3>
                  </div>
                  <div className="flex shrink-0 gap-1">
                    <button
                      className="soft-button h-8 border bg-background px-2 text-xs text-muted-foreground hover:bg-muted"
                      disabled={activeStepIndex <= 0}
                      onClick={() => moveStep(-1)}
                      type="button"
                    >
                      Prev
                    </button>
                    <button
                      className="soft-button h-8 border bg-background px-2 text-xs text-muted-foreground hover:bg-muted"
                      disabled={activeStepIndex >= steps.length - 1}
                      onClick={() => moveStep(1)}
                      type="button"
                    >
                      Next
                    </button>
                  </div>
                </div>
                <MarkdownBlock className="mt-3 text-sm text-muted-foreground">{activeStep.body}</MarkdownBlock>
                <StepDetail step={activeStep} />
              </section>
            ) : null}

            {steps.length ? (
              <section className="grid gap-2">
                {steps.map((step, index) => {
                  const isActive = index === activeStepIndex;
                  return (
                    <button
                      key={step.id}
                      className={cn(
                        "grid w-full grid-cols-[28px_minmax(0,1fr)] gap-3 rounded-md border p-3 text-left transition-colors active:translate-y-px",
                        isActive ? "border-primary bg-accent" : "bg-card hover:bg-muted"
                      )}
                      type="button"
                      onClick={() => setActiveStepByIndex(index)}
                    >
                      <span
                        className={cn(
                          "flex size-7 items-center justify-center rounded-full text-xs font-semibold",
                          isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                        )}
                      >
                        {index + 1}
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-semibold">
                          <MarkdownInline>{step.title}</MarkdownInline>
                        </span>
                        <span className="mt-1 line-clamp-2 block text-xs leading-5 text-muted-foreground">
                          <MarkdownInline>{step.body}</MarkdownInline>
                        </span>
                      </span>
                    </button>
                  );
                })}
              </section>
            ) : null}

            {lesson?.equation_steps.length ? (
              <Disclosure title="Equation path" icon={BarChart3}>
                <div className="space-y-3">
                  {lesson.equation_steps.map((equation) => (
                    <button
                      key={equation.id}
                      className="w-full rounded-md border bg-background p-3 text-left transition hover:bg-muted"
                      onClick={() => setManualFocusEntities(refsFromFocus(equation.focus))}
                      type="button"
                    >
                      <p className="text-sm font-semibold">
                        <MarkdownInline>{equation.title}</MarkdownInline>
                      </p>
                      <MarkdownBlock className="mt-2 text-sm">{`$$${equation.equation}$$`}</MarkdownBlock>
                      <MarkdownBlock className="mt-2 text-xs leading-5 text-muted-foreground">{equation.explanation}</MarkdownBlock>
                    </button>
                  ))}
                </div>
              </Disclosure>
            ) : null}

            {lesson ? <LessonExtras lesson={lesson} /> : null}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex w-2.5 touch-none select-none bg-muted p-0.5" orientation="vertical">
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-border" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </section>
  );
}

function SocraticLecturePanel({
  activeStageIndex,
  lecture,
  selectedStage,
  setActiveStageIndex,
  setManualFocusEntities
}: {
  activeStageIndex: number;
  lecture: NonNullable<SolutionPacket["socratic_lecture"]>;
  selectedStage: NonNullable<SolutionPacket["socratic_lecture"]>["stages"][number] | null;
  setActiveStageIndex: (index: number) => void;
  setManualFocusEntities: (entities: EntityRef[]) => void;
}) {
  if (!selectedStage) {
    return null;
  }

  const activePrompt = selectedStage.prompts[0] ?? null;
  const activeMode = lecture.mode_profiles.find((profile) => profile.mode === lecture.mode) ?? lecture.mode_profiles[0];

  return (
    <section className="rounded-lg border bg-card">
      <div className="border-b p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 text-primary" aria-hidden="true" />
              <h3 className="text-sm font-semibold">Socratic pace</h3>
            </div>
            <MarkdownBlock className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{lecture.opening_contract}</MarkdownBlock>
          </div>
          <span className="rounded-full border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground">
            {formatSocraticMode(lecture.mode)}
          </span>
        </div>
        {activeMode ? (
          <div className="mt-3 rounded-md bg-muted p-3 text-xs leading-5 text-muted-foreground">
            <span className="font-semibold text-foreground">
              <MarkdownInline>{activeMode.tutor_posture}</MarkdownInline>
            </span>
            <span className="ml-1">
              <MarkdownInline>{activeMode.reveal_rule}</MarkdownInline>
            </span>
          </div>
        ) : null}
      </div>

      <div className="grid gap-4 p-4">
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {lecture.stages.map((stage, index) => {
            const isActive = index === activeStageIndex;
            return (
              <button
                key={stage.id}
                className={cn(
                  "min-h-20 rounded-md border p-3 text-left transition-colors",
                  isActive ? "border-primary bg-accent" : "bg-background hover:bg-muted"
                )}
                onClick={() => {
                  setActiveStageIndex(index);
                  setManualFocusEntities(refsFromFocus(stage.prompts[0]?.focus ?? {
                    components: [],
                    current_paths: [],
                    goals: [],
                    nodes: []
                  }));
                }}
                type="button"
              >
                <span className="text-[11px] font-semibold uppercase text-muted-foreground">{stage.pace}</span>
                <span className="mt-1 block text-sm font-semibold">
                  <MarkdownInline>{stage.title}</MarkdownInline>
                </span>
                <span className="mt-1 line-clamp-2 block text-xs leading-5 text-muted-foreground">
                  <MarkdownInline>{stage.goal}</MarkdownInline>
                </span>
              </button>
            );
          })}
        </div>

        <div className="grid gap-3 lg:grid-cols-[1fr_1fr]">
          <div className="rounded-md border bg-background p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Stage {activeStageIndex + 1} of {lecture.stages.length}
                </p>
                <h4 className="mt-1 text-base font-semibold">
                  <MarkdownInline>{selectedStage.title}</MarkdownInline>
                </h4>
              </div>
              <StatusPill label={selectedStage.pace} tone="neutral" />
            </div>
            <MarkdownBlock className="mt-3 text-sm text-muted-foreground">{selectedStage.goal}</MarkdownBlock>
            <div className="mt-3 grid gap-2">
              <div className="rounded-md bg-muted p-3">
                <p className="text-xs font-semibold text-foreground">Advance when</p>
                  <MarkdownBlock className="mt-1 text-xs text-muted-foreground">{selectedStage.advance_when}</MarkdownBlock>
              </div>
              {selectedStage.common_failure ? (
                <div className="rounded-md bg-muted p-3">
                  <p className="text-xs font-semibold text-foreground">Common failure</p>
                  <MarkdownBlock className="mt-1 text-xs text-muted-foreground">{selectedStage.common_failure}</MarkdownBlock>
                </div>
              ) : null}
            </div>
          </div>

          {activePrompt ? (
            <div className="rounded-md border bg-background p-4">
              <div className="flex items-center justify-between gap-3">
                <h4 className="text-base font-semibold">Tutor question</h4>
                <span className="rounded-full bg-muted px-2.5 py-1 text-xs text-muted-foreground">
                  {activePrompt.reveal_policy.replaceAll("_", " ")}
                </span>
              </div>
              <div className="mt-3 space-y-3">
                <PromptLine label="Tutor move" value={activePrompt.tutor_move} />
                <PromptLine label="Student task" value={activePrompt.student_task} />
                <PromptLine label="Evidence" value={activePrompt.expected_student_evidence} />
                <PromptLine label="If stuck" value={activePrompt.if_stuck} />
              </div>
              {activePrompt.plot_ids.length || activePrompt.value_refs.length || activePrompt.unlocks.length ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {[...activePrompt.unlocks, ...activePrompt.plot_ids, ...activePrompt.value_refs].slice(0, 10).map((item) => (
                    <span key={item} className="rounded-full border bg-card px-2 py-1 text-[11px] text-muted-foreground">
                      {item}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function PromptLine({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold text-foreground">{label}</p>
      <MarkdownBlock className="mt-1 text-sm text-muted-foreground">{value}</MarkdownBlock>
    </div>
  );
}

function StepDetail({ step }: { step: TutorStep }) {
  const details = [
    step.look_at ? { label: "Look at", value: step.look_at } : null,
    step.why_it_matters ? { label: "Why", value: step.why_it_matters } : null,
    step.common_mistake ? { label: "Watch for", value: step.common_mistake } : null,
    step.next_action ? { label: "Next", value: step.next_action } : null,
    step.caution ? { label: "Caution", value: step.caution } : null
  ].filter(isDefined);

  return (
    <div className="mt-3 space-y-3">
      {details.length ? (
        <div className="grid gap-2">
          {details.map((detail) => (
            <div key={detail.label} className="rounded-md bg-muted p-3">
              <p className="text-xs font-semibold text-foreground">{detail.label}</p>
              <MarkdownBlock className="mt-1 text-xs text-muted-foreground">{detail.value}</MarkdownBlock>
            </div>
          ))}
        </div>
      ) : null}
      {step.verified_values.length ? (
        <div className="grid gap-2 sm:grid-cols-2">
            {step.verified_values.slice(0, 4).map((value) => (
              <div key={value.id} className="rounded-md border bg-background p-3">
              <p className="truncate text-xs font-medium text-muted-foreground">
                <MarkdownInline>{value.label}</MarkdownInline>
              </p>
              <p className="mt-1 text-sm font-semibold">
                {value.value === null || value.value === undefined ? (
                  value.note ? <MarkdownInline>{value.note}</MarkdownInline> : null
                ) : (
                  formatQuantity(value.value, value.unit)
                )}
              </p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function LessonExtras({ lesson }: { lesson: NonNullable<SolutionPacket["lesson_packet"]> }) {
  return (
    <div className="space-y-3">
      {lesson.checks.length ? (
        <Disclosure title="Checks" icon={Eye}>
          <div className="grid gap-2">
            {lesson.checks.map((check) => (
              <div key={check.id} className="rounded-md border bg-background p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold">
                    <MarkdownInline>{check.label}</MarkdownInline>
                  </p>
                  <StatusPill label={check.passed ? "PASS" : "CHECK"} tone={check.passed ? "pass" : "warn"} />
                </div>
                <MarkdownBlock className="mt-1 text-xs leading-5 text-muted-foreground">{check.explanation}</MarkdownBlock>
              </div>
            ))}
          </div>
        </Disclosure>
      ) : null}

      {lesson.common_mistakes.length || lesson.practice_prompts.length || lesson.limitations.length ? (
        <Disclosure title="Practice notes" icon={Lightbulb}>
          <div className="space-y-3">
            <CompactList title="Common mistakes" items={lesson.common_mistakes} />
            <CompactList title="Practice prompts" items={lesson.practice_prompts} />
            <CompactList title="Limits" items={lesson.limitations} />
          </div>
        </Disclosure>
      ) : null}
    </div>
  );
}

function ChatPanel() {
  const circuit = useTutorStore((state) => state.circuit);
  const chatHistory = useTutorStore((state) => state.chatHistory);
  const addStudentMessage = useTutorStore((state) => state.addStudentMessage);
  const addAssistantMessage = useTutorStore((state) => state.addAssistantMessage);
  const highlightFromTutorText = useTutorStore((state) => state.highlightFromTutorText);
  const parserUsed = useTutorStore((state) => state.parserUsed);
  const problemText = useTutorStore((state) => state.problemText);
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const studentProfile = useTutorStore((state) => state.studentProfile);
  const setStudentProfile = useTutorStore((state) => state.setStudentProfile);
  const setInstructorDashboard = useTutorStore((state) => state.setInstructorDashboard);
  const [draft, setDraft] = useState("");
  const [hintLevel, setHintLevel] = useState(1);
  const [representationMode, setRepresentationMode] = useState<RepresentationMode>("physical_intuition");
  const [confidencePercent, setConfidencePercent] = useState("");
  const [isCoaching, setIsCoaching] = useState(false);

  async function requestCoach(studentText: string, revealSolution = false) {
    if (!circuit || !solutionPacket) {
      addAssistantMessage("Load a verified circuit first, then I can coach your reasoning from the solution packet.", "error");
      return;
    }

    setIsCoaching(true);
    try {
      const confidence = Number(confidencePercent);
      const coach = await runReasoningCoach({
        circuit,
        confidencePercent: confidencePercent.trim() && Number.isFinite(confidence) ? confidence : null,
        parserUsed: parserUsed ?? undefined,
        problemText: problemText || circuit.title,
        representationMode,
        requestedHintLevel: revealSolution ? 5 : hintLevel,
        revealSolution,
        solutionPacket,
        studentProfile,
        studentText
      });
      setStudentProfile(coach.profile_update);
      if (coach.profile_update) {
        fetchInstructorDashboard([coach.profile_update])
          .then(setInstructorDashboard)
          .catch(() => setInstructorDashboard(null));
      }
      addAssistantMessage(formatCoachNudge(coach));
    } catch (caughtError) {
      addAssistantMessage(errorMessage(caughtError), "error");
    } finally {
      setIsCoaching(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || isCoaching) {
      return;
    }

    addStudentMessage(trimmed);
    highlightFromTutorText(trimmed);
    setDraft("");
    await requestCoach(trimmed);
  }

  async function handleReveal() {
    const commitment = draft.trim() || "I am ready to compare my reasoning with the verified solution.";
    if (isCoaching) {
      return;
    }

    if (draft.trim()) {
      addStudentMessage(commitment);
      highlightFromTutorText(commitment);
      setDraft("");
    }

    await requestCoach(commitment, true);
  }

  return (
    <section className="grid h-full min-h-0 grid-rows-[auto_auto_minmax(0,1fr)_auto]">
      <PanelHeader
        icon={Sparkles}
        title="Coach"
        subtitle="Commit to a move, get one nudge, reveal only when ready."
      />
      <div className="grid gap-2 border-b bg-muted/45 p-3">
        <div className="grid gap-2 sm:grid-cols-[0.8fr_1.2fr_0.7fr]">
          <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="hint-level">
            Hint
            <select
              id="hint-level"
              className="soft-field h-9"
              onChange={(event) => setHintLevel(Number(event.target.value))}
              value={hintLevel}
            >
              <option value={0}>Check only</option>
              <option value={1}>Nudge</option>
              <option value={2}>Stronger hint</option>
              <option value={3}>Equation cue</option>
              <option value={4}>Near reveal</option>
            </select>
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="representation-mode">
            Think by
            <select
              id="representation-mode"
              className="soft-field h-9"
              onChange={(event) => setRepresentationMode(event.target.value as RepresentationMode)}
              value={representationMode}
            >
              <option value="physical_intuition">Physical intuition</option>
              <option value="diagram">Diagram</option>
              <option value="kcl_equation">KCL equation</option>
              <option value="units_magnitude">Units</option>
              <option value="biomedical_context">BME context</option>
            </select>
          </label>
          <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="confidence">
            Confidence
            <input
              id="confidence"
              className="soft-field h-9"
              inputMode="numeric"
              max={100}
              min={0}
              onChange={(event) => setConfidencePercent(event.target.value)}
              placeholder="0-100"
              type="number"
              value={confidencePercent}
            />
          </label>
        </div>
        <div className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
          <span>{studentProfile ? `Independence: ${studentProfile.independence_level}` : "Student profile builds as you coach."}</span>
          <button
            className="soft-button h-8 border border-primary/30 bg-background px-3 text-primary hover:bg-accent"
            disabled={isCoaching || !solutionPacket}
            onClick={handleReveal}
            type="button"
          >
            Reveal verified
          </button>
        </div>
      </div>

      <ScrollArea.Root className="min-h-0">
        <ScrollArea.Viewport className="h-full">
          <div className="space-y-3 p-4">
            {chatHistory.length ? (
              chatHistory.map((message) => <ChatMessageBubble key={message.id} message={message} />)
            ) : (
              <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                Ask for a hint, a KCL check, or a next reasoning move.
              </p>
            )}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex w-2.5 touch-none select-none bg-muted p-0.5" orientation="vertical">
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-border" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>

      <form className="flex gap-2 border-t p-3" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="tutor-message">
          Message
        </label>
        <textarea
          id="tutor-message"
          className="min-h-10 flex-1 resize-none rounded-md border bg-background px-3 py-2 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring"
          onChange={(event) => setDraft(event.target.value)}
          placeholder="I think KCL at node n2 starts with..."
          rows={1}
          value={draft}
        />
        <button
          aria-label="Send message"
          className="flex size-10 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-55 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          disabled={isCoaching}
          type="submit"
        >
          {isCoaching ? (
            <Loader2 className="size-4 animate-spin" aria-hidden="true" />
          ) : (
            <Send className="size-4" aria-hidden="true" />
          )}
        </button>
      </form>
    </section>
  );
}

function ChatMessageBubble({ message }: { message: TutorMessage }) {
  const isStudent = message.role === "student";

  return (
    <article className={cn("flex", isStudent ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "min-w-0 max-w-[92%] overflow-hidden rounded-lg border px-3 py-2 text-sm leading-6",
          isStudent ? "bg-primary text-primary-foreground" : "bg-card",
          message.status === "error" && "border-destructive text-destructive"
        )}
      >
        <MarkdownBlock>{message.content}</MarkdownBlock>
        {message.status === "streaming" ? (
          <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded-sm bg-primary align-middle" />
        ) : null}
      </div>
    </article>
  );
}

function InspectPanel() {
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const analysisView = useTutorStore((state) => state.analysisView);
  const explanation = useTutorStore((state) => state.explanation);
  const circuit = useTutorStore((state) => state.circuit);

  if (!solutionPacket) {
    return (
      <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)]">
        <PanelHeader icon={Eye} title="Inspect" subtitle="Verified values and checks appear after a run." />
        <div className="p-4">
          <EmptyPanel title="Nothing to inspect yet" body="Run a problem to see answers, checks, and current directions." />
        </div>
      </section>
    );
  }

  const numericAnswers = Object.entries(solutionPacket.requested_answers ?? {});
  const symbolicAnswers = Object.entries(solutionPacket.symbolic_requested_answers ?? {});
  const acAnswers = Object.entries(solutionPacket.ac_requested_answers ?? {});
  const nodeVoltages = Object.entries(solutionPacket.node_voltages ?? {});
  const componentResults = Object.entries(solutionPacket.component_results ?? {});
  const bme = solutionPacket.bme_metadata ?? circuit?.bme_metadata ?? null;

  return (
    <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)]">
      <PanelHeader
        icon={Eye}
        title="Inspect"
        subtitle={solutionPacket.verification_badge.message}
        action={<StatusPill label={solutionPacket.verification_badge.label} tone={badgeTone(solutionPacket.verification_badge.label)} />}
      />
      <ScrollArea.Root className="min-h-0">
        <ScrollArea.Viewport className="h-full">
          <div className="space-y-4 p-4">
            <section className="grid gap-2 sm:grid-cols-2">
              {numericAnswers.map(([id, answer]) => (
                <MetricTile key={id} label={id} value={formatQuantity(answer.value, answer.unit)} />
              ))}
              {symbolicAnswers.map(([id, answer]) => (
                <MetricTile key={id} label={id} value={answer.expression} note={answer.unit} />
              ))}
              {acAnswers.map(([id, answer]) => (
                <MetricTile key={id} label={id} value={formatComplex(answer)} note={answer.unit} />
              ))}
              {!numericAnswers.length && !symbolicAnswers.length && !acAnswers.length ? (
                <EmptyPanel title="No requested answer" body="The packet did not include a requested output value." />
              ) : null}
            </section>

            {bme ? <BmeContextPanel metadata={bme} /> : null}

            {analysisView ? <AnalysisViewPanel analysisView={analysisView} /> : null}

            {nodeVoltages.length ? (
              <Disclosure title="Node voltages" icon={CircuitBoard}>
                <div className="grid gap-2 sm:grid-cols-2">
                  {nodeVoltages.map(([node, value]) => (
                    <MetricTile key={node} label={`Node ${node}`} value={formatQuantity(value, "V")} />
                  ))}
                </div>
              </Disclosure>
            ) : null}

            {componentResults.length ? (
              <Disclosure title="Component values" icon={Activity}>
                <div className="space-y-2">
                  {componentResults.map(([componentId, result]) => (
                    <div key={componentId} className="rounded-md border bg-background p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{componentId}</p>
                        <span className="text-xs text-muted-foreground">{result.sign_convention}</span>
                      </div>
                      <div className="mt-2 grid gap-2 sm:grid-cols-3">
                        <MiniValue label="V" value={formatQuantity(result.voltage.value, result.voltage.unit)} />
                        <MiniValue label="I" value={formatQuantity(result.current.value, result.current.unit)} />
                        <MiniValue label="P" value={formatQuantity(result.power.value, result.power.unit)} />
                      </div>
                    </div>
                  ))}
                </div>
              </Disclosure>
            ) : null}

            {solutionPacket.verification.checks.length ? (
              <Disclosure title="Verification" icon={Settings2}>
                <div className="space-y-2">
                  {solutionPacket.verification.checks.map((check) => (
                    <div key={check.name} className="rounded-md border bg-background p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold">{check.name}</p>
                        <StatusPill label={check.passed ? "PASS" : "CHECK"} tone={check.passed ? "pass" : "warn"} />
                      </div>
                      <p className="mt-1 text-xs leading-5 text-muted-foreground">{check.message}</p>
                    </div>
                  ))}
                </div>
              </Disclosure>
            ) : null}

            {explanation ? (
              <Disclosure title="Verified explanation" icon={Lightbulb}>
                <MarkdownBlock>{explanation}</MarkdownBlock>
              </Disclosure>
            ) : null}

            {solutionPacket.generated_netlist || solutionPacket.calculation_trace?.unknown_order.length ? (
              <Disclosure title="Provenance" icon={Info}>
                <div className="space-y-3">
                  {solutionPacket.calculation_trace ? (
                    <div className="grid gap-2 sm:grid-cols-2">
                      <MiniValue label="Solver" value={solutionPacket.calculation_trace.solver_name} />
                      <MiniValue label="Method" value={solutionPacket.calculation_trace.solver_method} />
                      <MiniValue label="Answer source" value={solutionPacket.calculation_trace.answer_source} />
                      <MiniValue label="Parser" value={solutionPacket.calculation_trace.parser_used ?? "unknown"} />
                    </div>
                  ) : null}
                  {solutionPacket.generated_netlist ? (
                    <pre className="max-h-52 overflow-auto rounded-md bg-muted p-3 text-xs leading-5">
                      {solutionPacket.generated_netlist}
                    </pre>
                  ) : null}
                </div>
              </Disclosure>
            ) : null}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex w-2.5 touch-none select-none bg-muted p-0.5" orientation="vertical">
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-border" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </section>
  );
}

function AnalysisViewPanel({ analysisView }: { analysisView: AnalysisView }) {
  const flows = Object.values(analysisView.component_flows ?? {});
  const kclReports = Object.values(analysisView.node_kcl ?? {});

  if (analysisView.status === "blocked") {
    return <EmptyPanel title="Analysis blocked" body={analysisView.reason ?? "The current packet is not ready for probes."} />;
  }

  return (
    <Disclosure title="Current and KCL" icon={BarChart3} defaultOpen>
      <div className="space-y-3">
        {flows.length ? (
          <div className="grid gap-2">
            {flows.slice(0, 8).map((flow) => (
              <ComponentFlowRow key={flow.component_id} flow={flow} />
            ))}
          </div>
        ) : null}
        {kclReports.length ? (
          <div className="grid gap-2">
            {kclReports.slice(0, 5).map((report) => (
              <KclReportCard key={report.node} report={report} />
            ))}
          </div>
        ) : null}
      </div>
    </Disclosure>
  );
}

function ComponentFlowRow({ flow }: { flow: ComponentFlow }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">{flow.component_id}</p>
        <span className="text-xs text-muted-foreground">
          {flow.direction_from} to {flow.direction_to}
        </span>
      </div>
      <div className="mt-2 grid gap-2 sm:grid-cols-3">
        <MiniValue label="Current" value={formatQuantity(flow.current_a, "A")} />
        <MiniValue label="Voltage" value={formatQuantity(flow.voltage_v, "V")} />
        <MiniValue label="Power" value={formatQuantity(flow.power_w, "W")} />
      </div>
    </div>
  );
}

function KclReportCard({ report }: { report: NodeKclReport }) {
  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">Node {report.node}</p>
        <StatusPill label={report.passed ? "KCL pass" : "Check KCL"} tone={report.passed ? "pass" : "warn"} />
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        Residual {formatQuantity(report.residual_a, "A")} at {formatQuantity(report.voltage_v, "V")}
      </p>
      {report.terms.length ? (
        <div className="mt-2 space-y-1">
          {report.terms.slice(0, 4).map((term) => (
            <p key={`${term.component_id}-${term.other_node}`} className="text-xs leading-5 text-muted-foreground">
              {term.description}
            </p>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function MatlabPlaygroundPanel() {
  const [manifest, setManifest] = useState<MatlabPlaygroundManifest | null>(null);
  const [selectedLabId, setSelectedLabId] = useState(MATLAB_PLAYGROUND_DEFAULT_LAB_ID);
  const [artifacts, setArtifacts] = useState<MatlabPlaygroundArtifact[]>([]);
  const [focusMap, setFocusMap] = useState<MatlabPlaygroundFocusMapEntry[]>([]);
  const [probePlan, setProbePlan] = useState<MatlabPlaygroundProbePlan[]>([]);
  const [labDelta, setLabDelta] = useState<MatlabPlaygroundLabDeltaResponse | null>(null);
  const [status, setStatus] = useState<LoadStatus>("loading");
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const selectedLab: PlaygroundLab | null = manifest?.labs.find((lab) => lab.id === selectedLabId) ?? manifest?.labs[0] ?? null;
  const scriptArtifact = artifacts.find((artifact) => artifact.kind === "matlab_script") ?? null;

  useEffect(() => {
    let active = true;

    fetchMatlabPlaygroundManifest()
      .then((nextManifest) => {
        if (!active) {
          return;
        }
        setManifest(nextManifest);
        if (!nextManifest.labs.some((lab) => lab.id === selectedLabId)) {
          setSelectedLabId(nextManifest.labs[0]?.id ?? MATLAB_PLAYGROUND_DEFAULT_LAB_ID);
        }
      })
      .catch((caughtError) => {
        if (!active) {
          return;
        }
        setStatus("error");
        setError(errorMessage(caughtError));
      });

    return () => {
      active = false;
    };
  }, [selectedLabId]);

  useEffect(() => {
    let active = true;

    setStatus("loading");
    setError(null);
    Promise.all([
      fetchMatlabPlaygroundArtifacts(selectedLabId, {
        kinds: [
          "matlab_script",
          "simscape_script",
          "simulink_script",
          "popup_app_script",
          "lab_delta_report"
        ]
      }),
      fetchMatlabPlaygroundFocusMap(selectedLabId),
      fetchMatlabPlaygroundProbePlans(selectedLabId),
      compareMatlabPlaygroundLabDelta(selectedLabId, {
        lab_id: selectedLabId,
        hand_values: { fc_hz: 40 },
        simulation_values: { fc_hz: 40.1 },
        measured_values: { fc_hz: 251.3 },
        notes: "Preview comparison for angular-frequency mismatch."
      })
    ])
      .then(([nextArtifacts, nextFocusMap, nextProbePlan, nextLabDelta]) => {
        if (!active) {
          return;
        }
        setArtifacts(nextArtifacts);
        setFocusMap(nextFocusMap);
        setProbePlan(nextProbePlan);
        setLabDelta(nextLabDelta);
        setStatus("idle");
      })
      .catch((caughtError) => {
        if (!active) {
          return;
        }
        setStatus("error");
        setError(errorMessage(caughtError));
      });

    return () => {
      active = false;
    };
  }, [selectedLabId, reloadKey]);

  return (
    <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)]">
      <PanelHeader
        icon={CircuitBoard}
        title="MATLAB/Simscape Playground"
        subtitle={selectedLab?.title ?? "Graphical popup tutor artifacts"}
        action={
          <button
            className="soft-button h-9 border bg-background px-3 text-muted-foreground hover:bg-muted"
            disabled={status === "loading"}
            onClick={() => setReloadKey((current) => current + 1)}
            type="button"
          >
            {status === "loading" ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <RefreshCw className="size-4" aria-hidden="true" />}
            Refresh
          </button>
        }
      />
      <ScrollArea.Root className="min-h-0">
        <ScrollArea.Viewport className="h-full">
          <div className="space-y-4 p-4">
            {error ? <EmptyPanel title="Playground preview unavailable" body={error} /> : null}

            {manifest ? (
              <section className="rounded-lg border bg-card p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold">{manifest.product_name}</h3>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {manifest.positioning}
                    </p>
                  </div>
                  <StatusPill label="Graphical UI" tone="pass" />
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {manifest.tabs.map((tab) => (
                    <span key={tab} className="rounded-md border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground">
                      {formatPluginTab(tab)}
                    </span>
                  ))}
                </div>
                <div className="mt-4 grid gap-2">
                  {manifest.labs.map((lab) => (
                    <button
                      key={lab.id}
                      aria-pressed={selectedLabId === lab.id}
                      className={cn(
                        "rounded-md border bg-background p-3 text-left transition hover:bg-muted active:translate-y-px",
                        selectedLabId === lab.id && "border-primary bg-primary/10"
                      )}
                      onClick={() => setSelectedLabId(lab.id)}
                      type="button"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <p className="truncate text-sm font-semibold">{lab.title}</p>
                        <StatusPill label={lab.id === MATLAB_PLAYGROUND_DEFAULT_LAB_ID ? "included" : "focus-ready"} tone="pass" />
                      </div>
                      <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">{lab.summary}</p>
                    </button>
                  ))}
                </div>
              </section>
            ) : status === "loading" ? (
              <EmptyPanel title="Loading playground preview" body="Fetching the MATLAB/Simscape tutor manifest." />
            ) : null}

            {selectedLab ? (
              <section className="rounded-lg border bg-card p-4">
                <div className="grid gap-2 sm:grid-cols-2">
                  {Object.entries(selectedLab.default_parameters).map(([key, value]) => (
                    <MiniValue key={key} label={key} value={String(value)} />
                  ))}
                </div>
                <div className="mt-3 grid gap-3 lg:grid-cols-2">
                  <CompactList title="Learning objectives" items={selectedLab.learning_objectives} />
                  <CompactList title="Assumptions" items={selectedLab.assumptions} />
                </div>
                <div className="mt-3 rounded-md bg-muted/55 p-3">
                  <p className="text-xs font-semibold text-foreground">BME context</p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">{selectedLab.bme_context}</p>
                </div>
              </section>
            ) : null}

            <Disclosure title="Four tutor modes" icon={GraduationCap} defaultOpen>
              <div className="grid gap-2 sm:grid-cols-2">
                {[
                  ["Overview", "Scope Boundary, BME Template Context, assumptions, and MATLAB/Simscape representation."],
                  ["Teach", "Guided Explanation plus Reasoning Coach focus targets and coach-before-reveal flow."],
                  ["Probe", "Probe Panel, KCL/current checks, local measurement plans, and signal logging names."],
                  ["Lab Delta", "What Changed, variants, and comparison of hand, simulation, and measured evidence."]
                ].map(([title, body]) => (
                  <div key={title} className="rounded-md border bg-background p-3">
                    <p className="text-sm font-semibold">{title}</p>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">{body}</p>
                  </div>
                ))}
              </div>
            </Disclosure>

            {artifacts.length ? (
              <Disclosure title="Artifacts" icon={Settings2} defaultOpen>
                <div className="space-y-2">
                  <button
                    className="soft-button h-9 border bg-background px-3 text-muted-foreground hover:bg-muted"
                    disabled={status === "loading"}
                    onClick={() => setReloadKey((current) => current + 1)}
                    type="button"
                  >
                    {status === "loading" ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <Settings2 className="size-4" aria-hidden="true" />}
                    Generate MATLAB/Simscape Artifact
                  </button>
                  {artifacts.map((artifact) => (
                    <div key={artifact.id} className="rounded-md border bg-background p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold">{artifact.filename}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{artifact.kind}</p>
                        </div>
                        <StatusPill label="generated" tone="pass" />
                      </div>
                    </div>
                  ))}
                  {scriptArtifact ? (
                    <pre className="max-h-44 overflow-auto rounded-md bg-muted p-3 text-[11px] leading-5 text-muted-foreground">
                      {scriptArtifact.content.split("\n").slice(0, 22).join("\n")}
                    </pre>
                  ) : null}
                </div>
              </Disclosure>
            ) : null}

            {focusMap.length ? (
              <Disclosure title="Focus map" icon={Eye} defaultOpen>
                <div className="grid gap-2">
                  {focusMap.slice(0, 7).map((entry) => (
                    <div key={entry.id} className="rounded-md border bg-background p-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold">{entry.label}</p>
                          <p className="mt-1 text-xs leading-5 text-muted-foreground">{entry.description}</p>
                        </div>
                        <span className="shrink-0 rounded-md bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
                          {formatPluginTab(entry.mode)}
                        </span>
                      </div>
                      {entry.targets.length ? (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Targets: {entry.targets.map((target) => target.id).join(", ")}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </Disclosure>
            ) : null}

            {probePlan.length ? (
              <Disclosure title="Probe plan" icon={Gauge}>
                <div className="space-y-2">
                  {probePlan.map((probe) => (
                    <div key={probe.id} className="rounded-md border bg-background p-3">
                      <div className="flex items-start justify-between gap-3">
                        <p className="text-sm font-semibold">{probe.label}</p>
                        <span className="shrink-0 rounded-md bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
                          {probe.measurement_type} · {probe.expected_unit}
                        </span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-muted-foreground">{probe.student_question}</p>
                      {probe.insertion_steps.length ? (
                        <p className="mt-2 text-xs text-muted-foreground">
                          Steps: {probe.insertion_steps.slice(0, 2).join(" ")}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              </Disclosure>
            ) : null}

            {labDelta ? <MatlabPlaygroundLabDeltaPreview response={labDelta} /> : null}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex w-2.5 touch-none select-none bg-muted p-0.5" orientation="vertical">
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-border" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </section>
  );
}

function MatlabPlaygroundLabDeltaPreview({ response }: { response: MatlabPlaygroundLabDeltaResponse }) {
  return (
    <Disclosure title="Lab Delta" icon={BarChart3}>
      <div className="space-y-3">
        <div className="grid gap-2 sm:grid-cols-2">
          {response.rows.slice(0, 2).map((row) => (
            <div key={row.quantity} className="rounded-md border bg-background p-3">
              <p className="text-sm font-semibold">{row.quantity}</p>
              <div className="mt-2 grid gap-2">
                {row.hand_value !== null && row.hand_value !== undefined ? (
                  <MiniValue label="Hand" value={formatQuantity(row.hand_value, row.unit ?? "")} />
                ) : null}
                {row.measured_value !== null && row.measured_value !== undefined ? (
                  <MiniValue label="Measured" value={formatQuantity(row.measured_value, row.unit ?? "")} />
                ) : null}
                <MiniValue
                  label="Difference"
                  value={
                    row.percent_error !== null && row.percent_error !== undefined
                      ? `${formatNumber(row.percent_error)}%`
                      : row.absolute_error !== null && row.absolute_error !== undefined
                        ? formatNumber(row.absolute_error)
                        : "n/a"
                  }
                />
              </div>
            </div>
          ))}
        </div>
        <div className="space-y-2">
          {response.likely_causes.slice(0, 3).map((cause) => (
            <div key={cause.id} className="rounded-md border bg-background p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold">{cause.label}</p>
                <StatusPill label={cause.severity} tone={cause.severity === "high" ? "warn" : cause.severity === "medium" ? "neutral" : "pass"} />
              </div>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{cause.check_to_run}</p>
            </div>
          ))}
        </div>
        <p className="rounded-md bg-muted/55 p-3 text-xs leading-5 text-muted-foreground">
          {response.reflection_question}
        </p>
      </div>
    </Disclosure>
  );
}

function LabPanel() {
  const circuit = useTutorStore((state) => state.circuit);
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const variants = useTutorStore((state) => state.variants);
  const parserUsed = useTutorStore((state) => state.parserUsed);
  const loadCircuit = useTutorStore((state) => state.loadCircuit);
  const setVariants = useTutorStore((state) => state.setVariants);
  const addAssistantMessage = useTutorStore((state) => state.addAssistantMessage);
  const [componentId, setComponentId] = useState("");
  const [componentValue, setComponentValue] = useState("");
  const [labStatus, setLabStatus] = useState<LoadStatus>("idle");
  const [labError, setLabError] = useState<string | null>(null);
  const [componentErrorPercent, setComponentErrorPercent] = useState("0");
  const [resistorTolerancePercent, setResistorTolerancePercent] = useState("0");
  const [sourceAmplitudeErrorPercent, setSourceAmplitudeErrorPercent] = useState("0");
  const [sourceOffsetMv, setSourceOffsetMv] = useState("0");
  const [biasEnabled, setBiasEnabled] = useState(true);
  const [biasCurrentNa, setBiasCurrentNa] = useState("50");
  const [biasCompensationEnabled, setBiasCompensationEnabled] = useState(false);
  const [opAmpOffsetMv, setOpAmpOffsetMv] = useState("0");
  const [railLimitEnabled, setRailLimitEnabled] = useState(true);
  const [railPositiveV, setRailPositiveV] = useState("5");
  const [railNegativeV, setRailNegativeV] = useState("-5");
  const [outputSwingMarginV, setOutputSwingMarginV] = useState("0.2");
  const [slewRateVPerUs, setSlewRateVPerUs] = useState("0");
  const [breadboardEnabled, setBreadboardEnabled] = useState(false);
  const [breadboardLeakageMOhm, setBreadboardLeakageMOhm] = useState("100");
  const [breadboardCapacitancePf, setBreadboardCapacitancePf] = useState("2");
  const [readoutGainErrorPercent, setReadoutGainErrorPercent] = useState("0");
  const [readoutOffsetMv, setReadoutOffsetMv] = useState("0");
  const [activeLabPreset, setActiveLabPreset] = useState<LabPresetId | null>(null);
  const [predictionDirection, setPredictionDirection] = useState<LabPredictionDirection>("increase");
  const [predictionReason, setPredictionReason] = useState("");
  const [lastPrediction, setLastPrediction] = useState<LabPredictionRecord | null>(null);
  const [labResult, setLabResult] = useState<LabSimulationResponse | null>(null);

  const selectedComponent = circuit?.components.find((component) => component.id === componentId) ?? null;
  const hasOpAmp = circuit?.components.some((component) => component.type.includes("op_amp")) ?? false;
  const labReady = Boolean(
    circuit &&
      solutionPacket &&
      solutionPacket.status === "solved" &&
      solutionPacket.verification_badge.label === "PASS"
  );

  useEffect(() => {
    const firstComponent = circuit?.components[0] ?? null;
    setComponentId(firstComponent?.id ?? "");
    setComponentValue(firstComponent ? String(firstComponent.value) : "");
    setActiveLabPreset(null);
    setLastPrediction(null);
    setLabResult(null);
  }, [circuit?.id]);

  function handleComponentSelect(nextComponentId: string) {
    const component = circuit?.components.find((item) => item.id === nextComponentId) ?? null;
    setComponentId(nextComponentId);
    setComponentValue(component ? String(component.value) : "");
  }

  function handleLabPreset(nextPreset: LabPresetId) {
    const resistor = circuit?.components.find((component) => component.type === "resistor") ?? null;
    setActiveLabPreset(nextPreset);
    setLabResult(null);
    setLastPrediction(null);
    setComponentErrorPercent("0");
    setResistorTolerancePercent("0");
    setSourceAmplitudeErrorPercent("0");
    setSourceOffsetMv("0");
    setBiasEnabled(false);
    setBiasCurrentNa("0");
    setBiasCompensationEnabled(false);
    setOpAmpOffsetMv("0");
    setRailLimitEnabled(false);
    setRailPositiveV("5");
    setRailNegativeV("-5");
    setOutputSwingMarginV("0.2");
    setSlewRateVPerUs("0");
    setBreadboardEnabled(false);
    setBreadboardLeakageMOhm("100");
    setBreadboardCapacitancePf("2");
    setReadoutGainErrorPercent("0");
    setReadoutOffsetMv("0");

    if (nextPreset === "resistor") {
      if (resistor) {
        handleComponentSelect(resistor.id);
      }
      setResistorTolerancePercent("5");
      setPredictionDirection("increase");
      setPredictionReason("The output should move in the direction set by the divider ratio change.");
    } else if (nextPreset === "bias") {
      setBiasEnabled(true);
      setBiasCurrentNa("50");
      setBiasCompensationEnabled(true);
      setPredictionDirection("about_same");
      setPredictionReason("Matched input resistances should make the bias-current voltage drops cancel more closely.");
    } else if (nextPreset === "saturation") {
      setRailLimitEnabled(true);
      setRailPositiveV("5");
      setRailNegativeV("-5");
      setOutputSwingMarginV("0.2");
      setPredictionDirection("decrease");
      setPredictionReason("If the ideal output asks for more than the rail window, the output should clamp.");
    } else if (nextPreset === "breadboard") {
      setBreadboardEnabled(true);
      setBreadboardLeakageMOhm("10");
      setBreadboardCapacitancePf("5");
      setPredictionDirection("decrease");
      setPredictionReason("Leakage adds an extra load path, so high-impedance nodes should sag.");
    } else if (nextPreset === "readout") {
      setReadoutGainErrorPercent("1");
      setReadoutOffsetMv("5");
      setPredictionDirection("increase");
      setPredictionReason("The solved circuit should stay fixed, but the displayed measurement should move upward.");
    }
  }

  async function refreshSolvedCircuit(nextCircuit: CircuitProblem, nextPacket?: SolutionPacket | null) {
    const packet = nextPacket ?? (await solveCircuit(nextCircuit, parserUsed ?? undefined));
    const renderable = packet.verification_badge.label === "PASS" && packet.status === "solved";
    const [visualCircuit, schematicSvg, analysisView, explanation, nextVariants] = await Promise.all([
      renderable ? fetchVisualLayout(nextCircuit, parserUsed ?? undefined).catch(() => null) : Promise.resolve(null),
      renderable ? fetchSchematicSvg(nextCircuit, SCHEMATIC_RENDERER, parserUsed ?? undefined).catch(() => null) : Promise.resolve(null),
      renderable ? fetchAnalysisView(nextCircuit, packet).catch(() => null) : Promise.resolve(null),
      explainSolution(packet).catch(() => null),
      renderable ? fetchVariants(nextCircuit).catch(() => []) : Promise.resolve([])
    ]);

    loadCircuit({
      analysisView,
      circuit: nextCircuit,
      explanation,
      parserUsed,
      problemText: nextCircuit.title,
      schematicRenderer: SCHEMATIC_RENDERER,
      schematicSvg,
      solutionPacket: packet,
      variants: nextVariants,
      visualCircuit
    });
  }

  async function handleApplyValue() {
    if (!circuit || !selectedComponent) {
      return;
    }

    const nextValue = Number(componentValue);
    if (!Number.isFinite(nextValue) || nextValue <= 0) {
      setLabError("Enter a positive numeric value.");
      setLabStatus("error");
      return;
    }

    setLabStatus("loading");
    setLabError(null);
    try {
      const nextCircuit = updateCircuitComponentValue(circuit, selectedComponent.id, nextValue);
      let packet: SolutionPacket | null | undefined = null;
      if (selectedComponent.type === "resistor" && circuit.analysis_type === "dc_operating_point") {
        const incremental = await updateResistorIncremental({
          circuit,
          componentId: selectedComponent.id,
          newValue: nextValue
        });
        packet = incremental.solution_packet ?? null;
        addAssistantMessage(incremental.message);
      }
      await refreshSolvedCircuit(nextCircuit, packet);
      setLabStatus("idle");
    } catch (caughtError) {
      setLabStatus("error");
      setLabError(errorMessage(caughtError));
    }
  }

  async function handleRunErrorLab() {
    if (!circuit || !solutionPacket || !labReady) {
      return;
    }

    setLabStatus("loading");
    setLabError(null);
    try {
      const componentPercent = activeNumber(componentErrorPercent);
      const resistorPercent = activeNumber(resistorTolerancePercent);
      const sourcePercent = activeNumber(sourceAmplitudeErrorPercent);
      const sourceOffset = activeNumber(sourceOffsetMv, 1e-3);
      const biasCurrent = biasEnabled && hasOpAmp ? activeNumber(biasCurrentNa, 1e-9) : null;
      const offsetVoltage = hasOpAmp ? activeNumber(opAmpOffsetMv, 1e-3) : null;
      const railLimitActive = railLimitEnabled && hasOpAmp;
      const positiveRail = railLimitActive ? numericField(railPositiveV) : null;
      const negativeRail = railLimitActive ? numericField(railNegativeV) : null;
      const swingMargin = railLimitActive ? numericField(outputSwingMarginV) : null;
      const slewRate = hasOpAmp ? activeNumber(slewRateVPerUs, 1e6) : null;
      const leakage = breadboardEnabled ? activeNumber(breadboardLeakageMOhm, 1_000_000) : null;
      const shuntCapacitance = breadboardEnabled ? activeNumber(breadboardCapacitancePf, 1e-12) : null;
      const readoutGain = activeNumber(readoutGainErrorPercent);
      const readoutOffset = activeNumber(readoutOffsetMv, 1e-3);
      const prediction = {
        direction: predictionDirection,
        reason: predictionReason.trim()
      };
      const componentErrors =
        selectedComponent && componentPercent !== null
          ? {
              [selectedComponent.id]: componentPercent
            }
          : undefined;

      const response = await simulateLab({
        baselinePacket: solutionPacket,
        circuit,
        parserUsed,
        scenario: {
          component_value_error_percent: componentErrors,
          resistor_tolerance_percent: resistorPercent,
          source_amplitude_error_percent: sourcePercent,
          source_dc_offset_v: sourceOffset,
          op_amp_input_bias_current_a: biasCurrent,
          op_amp_input_offset_voltage_v: offsetVoltage,
          op_amp_open_loop_gain: hasOpAmp && (biasCurrent !== null || offsetVoltage !== null || railLimitActive) ? 100_000 : null,
          supply_positive_v: positiveRail,
          supply_negative_v: negativeRail,
          output_swing_margin_v: swingMargin,
          slew_rate_v_per_s: slewRate,
          enable_bias_compensation: biasCompensationEnabled && hasOpAmp,
          breadboard_leakage_ohm: leakage,
          breadboard_shunt_capacitance_f: shuntCapacitance,
          readout_gain_error_percent: readoutGain,
          readout_offset_v: readoutOffset
        }
      });
      setLabResult(response);
      setLastPrediction(prediction);
      addAssistantMessage(formatLabAssistantSummary(response, prediction));
      setLabStatus("idle");
    } catch (caughtError) {
      setLabStatus("error");
      setLabError(errorMessage(caughtError));
    }
  }

  async function handleLoadLabResult() {
    if (!labResult) {
      return;
    }
    setLabStatus("loading");
    setLabError(null);
    try {
      await refreshSolvedCircuit(labResult.lab_circuit, labResult.lab_packet);
      addAssistantMessage("Loaded the nonideal lab circuit into the main workspace.");
      setLabStatus("idle");
    } catch (caughtError) {
      setLabStatus("error");
      setLabError(errorMessage(caughtError));
    }
  }

  async function handleRefreshVariants() {
    if (!circuit) {
      return;
    }

    setLabStatus("loading");
    setLabError(null);
    try {
      const nextVariants = await fetchVariants(circuit);
      setVariants(nextVariants);
      setLabStatus("idle");
    } catch (caughtError) {
      setLabStatus("error");
      setLabError(errorMessage(caughtError));
    }
  }

  async function handleLoadVariant(variant: PracticeVariant) {
    setLabStatus("loading");
    setLabError(null);
    try {
      await refreshSolvedCircuit(variant.circuit_ir);
      addAssistantMessage(`Loaded practice variant: ${variant.prompt}`);
      setLabStatus("idle");
    } catch (caughtError) {
      setLabStatus("error");
      setLabError(errorMessage(caughtError));
    }
  }

  return (
    <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)]">
      <PanelHeader
        icon={Activity}
        title="Lab"
        subtitle="Change values, load practice variants, and inspect sweep behavior."
      />
      <ScrollArea.Root className="min-h-0">
        <ScrollArea.Viewport className="h-full">
          <div className="space-y-4 p-4">
            {!labReady ? <EmptyPanel title="No lab yet" body="Run a verified circuit to unlock edits, error labs, and variants." /> : null}

            {labReady && circuit && solutionPacket ? (
              <section className="rounded-lg border bg-card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">Error lab</h3>
                    <p className="mt-1 text-xs text-muted-foreground">Perturb the real circuit model, then compare ideal, nonideal, and measured values.</p>
                  </div>
                  <StatusPill label={labStatus === "loading" ? "Running" : labResult ? "Simulated" : "Ready"} tone={labStatus === "error" ? "danger" : labResult ? "pass" : "neutral"} />
                </div>

                <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
                  {LAB_PRESETS.map((preset) => (
                    <button
                      key={preset.id}
                      aria-pressed={activeLabPreset === preset.id}
                      className={cn(
                        "rounded-md border bg-background p-3 text-left transition hover:bg-muted active:translate-y-px",
                        activeLabPreset === preset.id && "border-primary bg-primary/10"
                      )}
                      onClick={() => handleLabPreset(preset.id)}
                      type="button"
                    >
                      <p className="text-xs font-semibold text-foreground">{preset.title}</p>
                      <p className="mt-1 text-[11px] leading-4 text-muted-foreground">{preset.detail}</p>
                    </button>
                  ))}
                </div>

                <div className="mt-4 rounded-md bg-muted/55 p-3">
                  <div className="grid gap-3 sm:grid-cols-[180px_minmax(0,1fr)]">
                    <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="lab-prediction-direction">
                      Prediction
                      <select
                        id="lab-prediction-direction"
                        className="soft-field h-10"
                        onChange={(event) => setPredictionDirection(event.target.value as LabPredictionDirection)}
                        value={predictionDirection}
                      >
                        <option value="increase">output increases</option>
                        <option value="decrease">output decreases</option>
                        <option value="about_same">about the same</option>
                      </select>
                    </label>
                    <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="lab-prediction-reason">
                      Why
                      <textarea
                        id="lab-prediction-reason"
                        className="soft-field min-h-10 resize-none py-2 leading-5"
                        onChange={(event) => setPredictionReason(event.target.value)}
                        value={predictionReason}
                      />
                    </label>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="error-component">
                    Target component
                    <select
                      id="error-component"
                      className="soft-field h-10"
                      onChange={(event) => handleComponentSelect(event.target.value)}
                      value={componentId}
                    >
                      {circuit.components.map((component) => (
                        <option key={component.id} value={component.id}>
                          {component.id} ({component.type})
                        </option>
                      ))}
                    </select>
                  </label>
                  <NumberField
                    id="component-error-percent"
                    label="Selected value error (%)"
                    onChange={setComponentErrorPercent}
                    value={componentErrorPercent}
                  />
                  <NumberField
                    id="resistor-error-percent"
                    label="All resistor drift (%)"
                    onChange={setResistorTolerancePercent}
                    value={resistorTolerancePercent}
                  />
                  <NumberField
                    id="source-error-percent"
                    label="Signal source gain (%)"
                    onChange={setSourceAmplitudeErrorPercent}
                    value={sourceAmplitudeErrorPercent}
                  />
                  <NumberField
                    id="source-offset-mv"
                    label="Voltage source offset (mV)"
                    onChange={setSourceOffsetMv}
                    value={sourceOffsetMv}
                  />
                  <NumberField
                    id="readout-gain-percent"
                    label="Meter gain error (%)"
                    onChange={setReadoutGainErrorPercent}
                    value={readoutGainErrorPercent}
                  />
                  <NumberField
                    id="readout-offset-mv"
                    label="Meter offset (mV)"
                    onChange={setReadoutOffsetMv}
                    value={readoutOffsetMv}
                  />
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-2">
                  <div className="space-y-3 rounded-md bg-muted/55 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <label className="flex items-center gap-2 text-xs font-semibold text-foreground">
                        <input
                          checked={biasEnabled}
                          className="size-4 accent-primary"
                          onChange={(event) => setBiasEnabled(event.target.checked)}
                          type="checkbox"
                        />
                        Op-amp input bias
                      </label>
                      <StatusPill label={hasOpAmp ? "op amp found" : "no op amp"} tone={hasOpAmp ? "pass" : "neutral"} />
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <NumberField
                        disabled={!biasEnabled}
                        id="bias-current-na"
                        label="Bias current (nA)"
                        onChange={setBiasCurrentNa}
                        value={biasCurrentNa}
                      />
                      <NumberField
                        id="opamp-offset-mv"
                        label="Input offset (mV)"
                        onChange={setOpAmpOffsetMv}
                        value={opAmpOffsetMv}
                      />
                    </div>
                    <label className="flex items-start gap-2 text-xs leading-5 text-muted-foreground">
                      <input
                        checked={biasCompensationEnabled}
                        className="mt-0.5 size-4 accent-primary"
                        onChange={(event) => setBiasCompensationEnabled(event.target.checked)}
                        type="checkbox"
                      />
                      Add balance resistor for input-bias cancellation
                    </label>
                  </div>

                  <div className="space-y-3 rounded-md bg-muted/55 p-3">
                    <label className="flex items-center gap-2 text-xs font-semibold text-foreground">
                      <input
                        checked={railLimitEnabled}
                        className="size-4 accent-primary"
                        onChange={(event) => setRailLimitEnabled(event.target.checked)}
                        type="checkbox"
                      />
                      Op-amp rail and slew limits
                    </label>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <NumberField
                        disabled={!railLimitEnabled}
                        id="rail-positive-v"
                        label="+ rail (V)"
                        onChange={setRailPositiveV}
                        value={railPositiveV}
                      />
                      <NumberField
                        disabled={!railLimitEnabled}
                        id="rail-negative-v"
                        label="- rail (V)"
                        onChange={setRailNegativeV}
                        value={railNegativeV}
                      />
                      <NumberField
                        disabled={!railLimitEnabled}
                        id="swing-margin-v"
                        label="Swing margin (V)"
                        onChange={setOutputSwingMarginV}
                        value={outputSwingMarginV}
                      />
                      <NumberField
                        id="slew-rate-v-us"
                        label="Slew rate (V/us)"
                        onChange={setSlewRateVPerUs}
                        value={slewRateVPerUs}
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-4 rounded-md bg-muted/55 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <label className="flex items-center gap-2 text-xs font-semibold text-foreground">
                      <input
                        checked={breadboardEnabled}
                        className="size-4 accent-primary"
                        onChange={(event) => setBreadboardEnabled(event.target.checked)}
                        type="checkbox"
                      />
                      Breadboard parasitics
                    </label>
                    <span className="text-xs text-muted-foreground">{circuit.nodes.filter((node) => node !== circuit.ground_node).length} active nodes</span>
                  </div>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <NumberField
                      disabled={!breadboardEnabled}
                      id="breadboard-leakage-mohm"
                      label="Leakage to ground (MOhm)"
                      onChange={setBreadboardLeakageMOhm}
                      value={breadboardLeakageMOhm}
                    />
                    <NumberField
                      disabled={!breadboardEnabled}
                      id="breadboard-capacitance-pf"
                      label="Shunt capacitance (pF)"
                      onChange={setBreadboardCapacitancePf}
                      value={breadboardCapacitancePf}
                    />
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <button
                    className="soft-button h-10 bg-primary px-4 text-primary-foreground hover:opacity-90"
                    disabled={labStatus === "loading"}
                    onClick={handleRunErrorLab}
                    type="button"
                  >
                    {labStatus === "loading" ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <Activity className="size-4" aria-hidden="true" />}
                    Run lab
                  </button>
                  {labResult ? (
                    <button
                      className="soft-button h-10 border bg-background px-4 text-muted-foreground hover:bg-muted"
                      disabled={labStatus === "loading"}
                      onClick={handleLoadLabResult}
                      type="button"
                    >
                      <Settings2 className="size-4" aria-hidden="true" />
                      Load result circuit
                    </button>
                  ) : null}
                </div>
                {labError ? <p className="mt-2 text-xs text-destructive">{labError}</p> : null}
                {labResult ? <LabResultPanel prediction={lastPrediction} result={labResult} /> : null}
              </section>
            ) : null}

            {labReady && circuit ? (
              <section className="rounded-lg border bg-card p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">Value edit</h3>
                    <p className="mt-1 text-xs text-muted-foreground">Supported edits re-solve and refresh the lesson packet.</p>
                  </div>
                  <StatusPill label={labStatus === "loading" ? "Running" : "Ready"} tone={labStatus === "error" ? "danger" : "pass"} />
                </div>
                <div className="mt-3 grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                  <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="component-edit">
                    Component
                    <select
                      id="component-edit"
                      className="soft-field h-10"
                      onChange={(event) => handleComponentSelect(event.target.value)}
                      value={componentId}
                    >
                      {circuit.components.map((component) => (
                        <option key={component.id} value={component.id}>
                          {component.id} ({component.type})
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor="component-value">
                    Value {selectedComponent?.unit ? `(${selectedComponent.unit})` : ""}
                    <input
                      id="component-value"
                      className="soft-field h-10"
                      onChange={(event) => setComponentValue(event.target.value)}
                      type="number"
                      value={componentValue}
                    />
                  </label>
                  <button
                    className="soft-button h-10 self-end bg-primary px-4 text-primary-foreground hover:opacity-90"
                    disabled={labStatus === "loading" || !selectedComponent}
                    onClick={handleApplyValue}
                    type="button"
                  >
                    Apply
                  </button>
                </div>
                {labError ? <p className="mt-2 text-xs text-destructive">{labError}</p> : null}
              </section>
            ) : null}

            {labReady && solutionPacket ? <SweepAndTransientPanel solutionPacket={solutionPacket} /> : null}

            {labReady ? (
            <section className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold">Practice variants</h3>
                  <p className="mt-1 text-xs text-muted-foreground">Same idea, changed values or target.</p>
                </div>
                <button
                  className="soft-button h-9 border bg-background px-3 text-muted-foreground hover:bg-muted"
                  disabled={labStatus === "loading" || !circuit}
                  onClick={handleRefreshVariants}
                  type="button"
                >
                  <RefreshCw className="size-4" aria-hidden="true" />
                  Refresh
                </button>
              </div>
              <div className="mt-3 grid gap-2">
                {variants.length ? (
                  variants.map((variant) => (
                    <button
                      key={`${variant.kind}-${variant.circuit_ir.id}`}
                      className="rounded-md border bg-background p-3 text-left transition hover:bg-muted active:translate-y-px"
                      disabled={labStatus === "loading"}
                      onClick={() => handleLoadVariant(variant)}
                      type="button"
                    >
                      <p className="text-sm font-semibold">
                        <MarkdownInline>{variant.prompt}</MarkdownInline>
                      </p>
                      <MarkdownBlock className="mt-1 text-xs leading-5 text-muted-foreground">{variant.description}</MarkdownBlock>
                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        <MarkdownInline>{variant.circuit_ir.title}</MarkdownInline>
                      </p>
                    </button>
                  ))
                ) : (
                  <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">No variants yet.</p>
                )}
              </div>
            </section>
            ) : null}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex w-2.5 touch-none select-none bg-muted p-0.5" orientation="vertical">
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-border" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </section>
  );
}

function NumberField({
  disabled = false,
  id,
  label,
  onChange,
  value
}: {
  disabled?: boolean;
  id: string;
  label: string;
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <label className="grid gap-1 text-xs font-medium text-muted-foreground" htmlFor={id}>
      {label}
      <input
        id={id}
        className="soft-field h-10 disabled:cursor-not-allowed disabled:opacity-55"
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        step="any"
        type="number"
        value={value}
      />
    </label>
  );
}

function LabResultPanel({
  prediction,
  result
}: {
  prediction: LabPredictionRecord | null;
  result: LabSimulationResponse;
}) {
  const firstComparisons = result.comparisons.slice(0, 4);
  return (
    <div className="mt-4 space-y-4 border-t pt-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="size-4 text-primary" aria-hidden="true" />
          <h4 className="text-sm font-semibold">Lab result</h4>
        </div>
        <StatusPill label={result.lab_packet.verification_badge.label} tone={badgeTone(result.lab_packet.verification_badge.label)} />
      </div>

      {prediction ? <LabPredictionResult prediction={prediction} result={result} /> : null}

      {firstComparisons.length ? (
        <div className="grid gap-2 md:grid-cols-2">
          {firstComparisons.map((comparison) => (
            <div key={comparison.id} className="rounded-md bg-background p-3">
              <p className="truncate text-xs font-semibold text-foreground">
                <MarkdownInline>{comparison.label}</MarkdownInline>
              </p>
              <div className="mt-2 grid grid-cols-3 gap-2">
                <MiniValue label="Baseline" value={formatQuantity(comparison.baseline_value, comparison.unit)} />
                <MiniValue label="Lab truth" value={formatQuantity(comparison.lab_value, comparison.unit)} />
                <MiniValue label="Measured" value={formatQuantity(comparison.measured_value, comparison.unit)} />
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">
                Delta {formatQuantity(comparison.delta, comparison.unit)}
                {comparison.relative_error_percent !== null && comparison.relative_error_percent !== undefined
                  ? ` (${formatNumber(comparison.relative_error_percent)}%)`
                  : ""}
              </p>
              {comparison.note ? <MarkdownBlock className="mt-1 text-xs leading-5 text-muted-foreground">{comparison.note}</MarkdownBlock> : null}
            </div>
          ))}
        </div>
      ) : (
        <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">No shared scalar outputs were available for comparison.</p>
      )}

      {result.comparisons.length ? <LabDeltaPlot comparisons={result.comparisons} /> : null}

      {result.sensitivity_sweeps.length ? (
        <div className="space-y-2">
          {result.sensitivity_sweeps.slice(0, 2).map((sweep) => (
            <LabSensitivitySweepPlot key={sweep.id} sweep={sweep} />
          ))}
        </div>
      ) : null}

      {result.counterfactuals.length ? (
        <div className="space-y-2">
          {result.counterfactuals.map((counterfactual) => (
            <LabCounterfactualPanel
              key={counterfactual.id}
              counterfactual={counterfactual}
              currentComparisons={result.comparisons}
            />
          ))}
        </div>
      ) : null}

      {result.observations.length ? (
        <div className="space-y-2">
          {result.observations.slice(0, 6).map((observation) => (
            <div key={observation.id} className="rounded-md bg-muted/60 p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-semibold text-foreground">
                  <MarkdownInline>{observation.title}</MarkdownInline>
                </p>
                <StatusPill label={observation.severity} tone={labObservationTone(observation.severity)} />
              </div>
              <MarkdownBlock className="mt-2 text-xs leading-5 text-muted-foreground">{observation.body}</MarkdownBlock>
              {observation.value !== null && observation.value !== undefined ? (
                <p className="mt-1 text-xs font-medium text-muted-foreground">
                  {formatQuantity(observation.value, observation.unit)}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}

      {result.applied_modifications.length ? (
        <div>
          <p className="text-xs font-semibold text-foreground">Applied model changes</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {result.applied_modifications.slice(0, 8).map((item) => (
              <span key={item.id} className="rounded-full bg-muted px-2.5 py-1 text-xs leading-5 text-muted-foreground">
                {item.target}: {item.after_value !== null && item.after_value !== undefined ? formatQuantity(item.after_value, item.unit) : item.kind}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      {result.teaching_script.length ? (
        <div>
          <p className="text-xs font-semibold text-foreground">Next Socratic moves</p>
          <div className="mt-2 space-y-1">
            {result.teaching_script.slice(0, 4).map((step) => (
              <p key={step} className="text-xs leading-5 text-muted-foreground">
                {step}
              </p>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function LabPredictionResult({
  prediction,
  result
}: {
  prediction: LabPredictionRecord;
  result: LabSimulationResponse;
}) {
  const observed = labObservedDirection(result.comparisons);
  const matched = observed.direction === prediction.direction;
  return (
    <div className="rounded-md bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold text-foreground">Prediction check</p>
        <StatusPill label={matched ? "matched" : "revisit"} tone={matched ? "pass" : "warn"} />
      </div>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <MiniValue label="Predicted" value={formatPredictionDirection(prediction.direction)} />
        <MiniValue label="Observed" value={formatPredictionDirection(observed.direction)} />
      </div>
      {prediction.reason ? <p className="mt-2 text-xs leading-5 text-muted-foreground">{prediction.reason}</p> : null}
      {observed.comparison ? (
        <p className="mt-1 text-xs leading-5 text-muted-foreground">
          <MarkdownInline>{observed.comparison.label}</MarkdownInline>: measured shift {formatQuantity(observed.measuredDelta, observed.comparison.unit)}
        </p>
      ) : null}
    </div>
  );
}

function LabSensitivitySweepPlot({
  sweep
}: {
  sweep: LabSimulationResponse["sensitivity_sweeps"][number];
}) {
  const points = sweep.points.filter((point) => Number.isFinite(point.x_value) && Number.isFinite(point.lab_value));
  if (points.length < 2) {
    return null;
  }
  const width = 320;
  const height = 150;
  const left = 38;
  const right = 12;
  const top = 14;
  const bottom = 30;
  const xValues = points.map((point) => point.x_value).filter((value) => sweep.x_unit !== "ohm" || value > 0);
  const yValues = points.map((point) => point.lab_value);
  const [xMin, xMax] = paddedDomain(xValues, sweep.x_unit === "ohm" ? "log" : "linear");
  const [yMin, yMax] = paddedDomain(yValues, "linear");
  const xScale = sweep.x_unit === "ohm" ? "log" : "linear";
  const scaleX = (value: number) => scalePlotValue(value, xMin, xMax, left, width - right, xScale);
  const scaleY = (value: number) => scalePlotValue(value, yMin, yMax, height - bottom, top, "linear");
  const path = points
    .filter((point) => xScale === "linear" || point.x_value > 0)
    .map((point, index) => `${index === 0 ? "M" : "L"} ${scaleX(point.x_value).toFixed(2)} ${scaleY(point.lab_value).toFixed(2)}`)
    .join(" ");

  return (
    <div className="rounded-md bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold text-foreground">
          <MarkdownInline>{sweep.label}</MarkdownInline>
        </p>
        <span className="text-xs text-muted-foreground">{sweep.comparison_id}</span>
      </div>
      <svg className="mt-3 h-40 w-full overflow-visible" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${sweep.label} plot`}>
        <line x1={left} x2={width - right} y1={height - bottom} y2={height - bottom} stroke="hsl(var(--border))" />
        <line x1={left} x2={left} y1={top} y2={height - bottom} stroke="hsl(var(--border))" />
        <path d={path} fill="none" stroke="hsl(var(--primary))" strokeLinecap="round" strokeWidth={2.5} />
        {points.map((point) => (
          <circle
            key={`${point.x_value}-${point.lab_value}`}
            cx={scaleX(point.x_value)}
            cy={scaleY(point.lab_value)}
            fill="hsl(var(--primary))"
            r={2.6}
          />
        ))}
        <text x={left} y={height - 9} className="fill-muted-foreground text-[10px]">
          {sweep.x_label} ({sweep.x_unit})
        </text>
        <text x={left + 2} y={top - 4} className="fill-muted-foreground text-[10px]">
          {sweep.y_label} ({sweep.y_unit})
        </text>
      </svg>
      {sweep.insight ? <MarkdownBlock className="mt-2 text-xs leading-5 text-muted-foreground">{sweep.insight}</MarkdownBlock> : null}
    </div>
  );
}

function LabCounterfactualPanel({
  counterfactual,
  currentComparisons
}: {
  counterfactual: LabSimulationResponse["counterfactuals"][number];
  currentComparisons: LabComparison[];
}) {
  const rows = counterfactual.comparisons.slice(0, 3).map((comparison) => ({
    off: comparison,
    on: currentComparisons.find((item) => item.id === comparison.id) ?? null
  }));

  return (
    <div className="rounded-md bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold text-foreground">
          <MarkdownInline>{counterfactual.label}</MarkdownInline>
        </p>
        <StatusPill label="control" tone="neutral" />
      </div>
      <MarkdownBlock className="mt-2 text-xs leading-5 text-muted-foreground">{counterfactual.summary}</MarkdownBlock>
      <div className="mt-3 grid gap-2">
        {rows.map(({ off, on }) => (
          <div key={off.id} className="grid gap-2 rounded-md bg-muted/60 p-2 sm:grid-cols-[minmax(0,1fr)_96px_96px]">
            <p className="min-w-0 truncate text-xs font-medium text-foreground">
              <MarkdownInline>{off.label}</MarkdownInline>
            </p>
            <MiniValue label="Off shift" value={formatQuantity(off.delta, off.unit)} />
            <MiniValue label="On shift" value={on ? formatQuantity(on.delta, on.unit) : "n/a"} />
          </div>
        ))}
      </div>
    </div>
  );
}

function LabDeltaPlot({ comparisons }: { comparisons: LabComparison[] }) {
  const plotted = comparisons
    .filter((comparison) => Number.isFinite(comparison.relative_error_percent ?? Number.NaN))
    .slice(0, 6);
  if (!plotted.length) {
    return null;
  }
  const maxAbs = Math.max(...plotted.map((comparison) => Math.abs(comparison.relative_error_percent ?? 0)), 1);
  const rowHeight = 24;
  const width = 320;
  const height = 32 + plotted.length * rowHeight;
  const zeroX = 166;
  const usable = 128;

  return (
    <div className="rounded-md bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold text-foreground">Relative error plot</p>
        <span className="text-xs text-muted-foreground">max {formatNumber(maxAbs)}%</span>
      </div>
      <svg className="mt-3 h-auto w-full overflow-visible" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Lab relative error plot">
        <line x1={zeroX} x2={zeroX} y1={12} y2={height - 8} stroke="hsl(var(--border))" />
        {plotted.map((comparison, index) => {
          const value = comparison.relative_error_percent ?? 0;
          const barLength = (Math.abs(value) / maxAbs) * usable;
          const x = value >= 0 ? zeroX : zeroX - barLength;
          const y = 24 + index * rowHeight;
          return (
            <g key={comparison.id}>
              <text x={4} y={y + 8} className="fill-muted-foreground text-[10px]">
                {comparison.id.slice(0, 18)}
              </text>
              <rect
                x={x}
                y={y}
                width={Math.max(barLength, 1)}
                height={10}
                rx={2}
                fill={value >= 0 ? "hsl(var(--primary))" : "#dc2626"}
              />
              <text x={value >= 0 ? x + barLength + 4 : x - 4} y={y + 9} textAnchor={value >= 0 ? "start" : "end"} className="fill-muted-foreground text-[10px]">
                {formatNumber(value)}%
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function SweepAndTransientPanel({ solutionPacket }: { solutionPacket: SolutionPacket }) {
  const phasors = collectPhasors(solutionPacket);
  const teachingPlots = solutionPacket.teaching_plots ?? [];

  if (!teachingPlots.length && !solutionPacket.ac_sweep_plots.length && !solutionPacket.transient_response && !phasors.length) {
    return null;
  }

  return (
    <section className="rounded-lg border bg-card p-4">
      <div className="flex items-center gap-2">
        <BarChart3 className="size-4 text-primary" aria-hidden="true" />
        <h3 className="text-sm font-semibold">Teaching plots</h3>
      </div>
      <div className="mt-3 space-y-3">
        {teachingPlots.length ? (
          teachingPlots.map((plot) => <TeachingPlotCard key={plot.id} plot={plot} />)
        ) : (
          <>
            {solutionPacket.ac_sweep_plots[0] ? <SweepPlot series={solutionPacket.ac_sweep_plots[0]} /> : null}
            {solutionPacket.transient_response ? <TransientPlot response={solutionPacket.transient_response} /> : null}
            {phasors.length ? <PhasorPanel phasors={phasors} /> : null}
          </>
        )}
      </div>
    </section>
  );
}

const TEACHING_PLOT_WIDTH = 320;
const TEACHING_PLOT_HEIGHT = 150;
const TEACHING_PLOT_LEFT = 34;
const TEACHING_PLOT_RIGHT = 10;
const TEACHING_PLOT_TOP = 14;
const TEACHING_PLOT_BOTTOM = 30;
const TEACHING_PLOT_COLORS = [
  "hsl(var(--primary))",
  "#2563eb",
  "#b45309",
  "#7c3aed",
  "#dc2626",
  "#0891b2"
];

function TeachingPlotCard({ plot }: { plot: TeachingPlot }) {
  const pointCount = plot.series.reduce((count, series) => count + series.points.length, 0);
  if (!pointCount) {
    return null;
  }

  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">
            <MarkdownInline>{plot.title}</MarkdownInline>
          </p>
          {plot.subtitle ? <MarkdownBlock className="mt-1 text-xs leading-5 text-muted-foreground">{plot.subtitle}</MarkdownBlock> : null}
        </div>
        <span className="shrink-0 rounded-full border bg-muted px-2 py-1 text-[11px] font-medium text-muted-foreground">
          {plot.source.replaceAll("_", " ")}
        </span>
      </div>
      <div className="mt-3">
        {plot.plot_type === "bar" ? <TeachingBarPlot plot={plot} /> : <TeachingLinePlot plot={plot} />}
      </div>
      <PlotLegend plot={plot} />
      <PlotValuePreview plot={plot} />
      {plot.insight ? <MarkdownBlock className="mt-3 text-xs leading-5 text-muted-foreground">{plot.insight}</MarkdownBlock> : null}
    </div>
  );
}

function TeachingLinePlot({ plot }: { plot: TeachingPlot }) {
  const domain = plotDomain(plot, { includeZeroY: false });
  const scaleX = (value: number) => scalePlotValue(value, domain.xMin, domain.xMax, TEACHING_PLOT_LEFT, TEACHING_PLOT_WIDTH - TEACHING_PLOT_RIGHT, plot.x_scale);
  const scaleY = (value: number) => scalePlotValue(value, domain.yMin, domain.yMax, TEACHING_PLOT_HEIGHT - TEACHING_PLOT_BOTTOM, TEACHING_PLOT_TOP, plot.y_scale);

  return (
    <svg className="h-40 w-full overflow-visible" viewBox={`0 0 ${TEACHING_PLOT_WIDTH} ${TEACHING_PLOT_HEIGHT}`} role="img" aria-label={`${plot.title} plot`}>
      <PlotAxes plot={plot} domain={domain} scaleX={scaleX} scaleY={scaleY} />
      {plot.series.map((series, index) => (
        <path
          key={series.id}
          d={teachingLinePath(series.points, scaleX, scaleY, plot.x_scale)}
          fill="none"
          stroke={TEACHING_PLOT_COLORS[index % TEACHING_PLOT_COLORS.length]}
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.5"
        />
      ))}
      {plot.markers.map((marker) =>
        marker.axis === "x" ? (
          <line
            key={`${marker.axis}-${marker.value}-${marker.label}`}
            x1={scaleX(marker.value)}
            x2={scaleX(marker.value)}
            y1={TEACHING_PLOT_TOP}
            y2={TEACHING_PLOT_HEIGHT - TEACHING_PLOT_BOTTOM}
            stroke="hsl(var(--muted-foreground) / 0.55)"
            strokeDasharray="4 4"
            strokeWidth="1.2"
          />
        ) : (
          <line
            key={`${marker.axis}-${marker.value}-${marker.label}`}
            x1={TEACHING_PLOT_LEFT}
            x2={TEACHING_PLOT_WIDTH - TEACHING_PLOT_RIGHT}
            y1={scaleY(marker.value)}
            y2={scaleY(marker.value)}
            stroke="hsl(var(--muted-foreground) / 0.55)"
            strokeDasharray="4 4"
            strokeWidth="1.2"
          />
        )
      )}
    </svg>
  );
}

function TeachingBarPlot({ plot }: { plot: TeachingPlot }) {
  const domain = plotDomain(plot, { includeZeroY: true });
  const maxPoints = Math.max(...plot.series.map((series) => series.points.length));
  const plotWidth = TEACHING_PLOT_WIDTH - TEACHING_PLOT_LEFT - TEACHING_PLOT_RIGHT;
  const groupWidth = plotWidth / Math.max(maxPoints, 1);
  const barWidth = Math.max(5, Math.min(24, groupWidth / Math.max(plot.series.length + 0.55, 1)));
  const scaleY = (value: number) => scalePlotValue(value, domain.yMin, domain.yMax, TEACHING_PLOT_HEIGHT - TEACHING_PLOT_BOTTOM, TEACHING_PLOT_TOP, plot.y_scale);
  const zeroY = scaleY(0);

  return (
    <svg className="h-40 w-full overflow-visible" viewBox={`0 0 ${TEACHING_PLOT_WIDTH} ${TEACHING_PLOT_HEIGHT}`} role="img" aria-label={`${plot.title} bar plot`}>
      <PlotAxes plot={plot} domain={domain} scaleX={(value) => value} scaleY={scaleY} />
      <line
        x1={TEACHING_PLOT_LEFT}
        x2={TEACHING_PLOT_WIDTH - TEACHING_PLOT_RIGHT}
        y1={zeroY}
        y2={zeroY}
        stroke="hsl(var(--foreground) / 0.32)"
        strokeWidth="1"
      />
      {plot.series.map((series, seriesIndex) =>
        series.points.map((point, pointIndex) => {
          const center = TEACHING_PLOT_LEFT + groupWidth * pointIndex + groupWidth / 2;
          const x = center - (barWidth * plot.series.length) / 2 + seriesIndex * barWidth;
          const y = scaleY(point.y);
          return (
            <rect
              key={`${series.id}-${pointIndex}`}
              x={x}
              y={Math.min(y, zeroY)}
              width={barWidth * 0.78}
              height={Math.max(2, Math.abs(zeroY - y))}
              rx="2"
              fill={TEACHING_PLOT_COLORS[seriesIndex % TEACHING_PLOT_COLORS.length]}
            />
          );
        })
      )}
    </svg>
  );
}

function PlotAxes({
  domain,
  plot,
  scaleX,
  scaleY
}: {
  domain: PlotDomain;
  plot: TeachingPlot;
  scaleX: (value: number) => number;
  scaleY: (value: number) => number;
}) {
  const xTicks = plot.plot_type === "line" ? axisTicks(domain.xMin, domain.xMax, plot.x_scale) : [];
  const yTicks = axisTicks(domain.yMin, domain.yMax, plot.y_scale);

  return (
    <>
      <line x1={TEACHING_PLOT_LEFT} x2={TEACHING_PLOT_LEFT} y1={TEACHING_PLOT_TOP} y2={TEACHING_PLOT_HEIGHT - TEACHING_PLOT_BOTTOM} stroke="hsl(var(--border))" strokeWidth="1" />
      <line x1={TEACHING_PLOT_LEFT} x2={TEACHING_PLOT_WIDTH - TEACHING_PLOT_RIGHT} y1={TEACHING_PLOT_HEIGHT - TEACHING_PLOT_BOTTOM} y2={TEACHING_PLOT_HEIGHT - TEACHING_PLOT_BOTTOM} stroke="hsl(var(--border))" strokeWidth="1" />
      {yTicks.map((tick) => (
        <g key={`y-${tick}`}>
          <line x1={TEACHING_PLOT_LEFT} x2={TEACHING_PLOT_WIDTH - TEACHING_PLOT_RIGHT} y1={scaleY(tick)} y2={scaleY(tick)} stroke="hsl(var(--border) / 0.55)" strokeWidth="1" />
          <text x={TEACHING_PLOT_LEFT - 7} y={scaleY(tick) + 3} textAnchor="end" className="fill-muted-foreground text-[9px]">
            {compactAxisNumber(tick)}
          </text>
        </g>
      ))}
      {xTicks.map((tick) => (
        <g key={`x-${tick}`}>
          <line x1={scaleX(tick)} x2={scaleX(tick)} y1={TEACHING_PLOT_TOP} y2={TEACHING_PLOT_HEIGHT - TEACHING_PLOT_BOTTOM} stroke="hsl(var(--border) / 0.45)" strokeWidth="1" />
          <text x={scaleX(tick)} y={TEACHING_PLOT_HEIGHT - 9} textAnchor="middle" className="fill-muted-foreground text-[9px]">
            {compactAxisNumber(tick)}
          </text>
        </g>
      ))}
      <text x={TEACHING_PLOT_LEFT} y={TEACHING_PLOT_HEIGHT - 1} className="fill-muted-foreground text-[9px]">
        {plot.x_label}
      </text>
      <text x={TEACHING_PLOT_LEFT - 29} y={TEACHING_PLOT_TOP + 4} className="fill-muted-foreground text-[9px]">
        {plot.y_label}
      </text>
    </>
  );
}

function PlotLegend({ plot }: { plot: TeachingPlot }) {
  if (plot.series.length <= 1) {
    return null;
  }

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {plot.series.map((series, index) => (
        <span key={series.id} className="inline-flex max-w-full items-center gap-1 rounded-full border bg-muted px-2 py-1 text-[11px] text-muted-foreground">
          <span
            className="size-2 shrink-0 rounded-full"
            style={{ backgroundColor: TEACHING_PLOT_COLORS[index % TEACHING_PLOT_COLORS.length] }}
          />
          <span className="truncate">
            <MarkdownInline>{series.label}</MarkdownInline>
          </span>
        </span>
      ))}
    </div>
  );
}

function PlotValuePreview({ plot }: { plot: TeachingPlot }) {
  const previewPoints = plot.series.flatMap((series) =>
    series.points.slice(0, 4).map((point) => ({
      id: `${series.id}-${point.x_label ?? point.x}`,
      label: point.x_label ?? series.label,
      value: point.y_label ?? formatQuantity(point.y, series.unit ?? "")
    }))
  ).slice(0, 6);

  if (!previewPoints.length) {
    return null;
  }

  return (
    <div className="mt-2 grid gap-2 sm:grid-cols-2">
      {previewPoints.map((point) => (
        <MiniValue key={point.id} label={shortenLabel(point.label)} value={point.value} />
      ))}
    </div>
  );
}

function SweepPlot({ series }: { series: SolutionPacket["ac_sweep_plots"][number] }) {
  const points = series.points.slice(0, 120);
  const path = buildPlotPath(points.map((point) => point.magnitude_db));

  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">
          <MarkdownInline>{series.label}</MarkdownInline>
        </p>
        <span className="text-xs text-muted-foreground">{series.unit}</span>
      </div>
      <svg className="mt-3 h-32 w-full overflow-visible" viewBox="0 0 320 120" role="img" aria-label={`${series.label} sweep plot`}>
        <path d={path} fill="none" stroke="hsl(var(--primary))" strokeLinecap="round" strokeWidth="3" />
      </svg>
    </div>
  );
}

function TransientPlot({ response }: { response: NonNullable<SolutionPacket["transient_response"]> }) {
  const path = buildPlotPath(response.sample_points.map((point) => point.voltage_v));

  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">RC transient</p>
        <span className="text-xs text-muted-foreground">tau {formatQuantity(response.time_constant_s, "s")}</span>
      </div>
      <svg className="mt-3 h-32 w-full overflow-visible" viewBox="0 0 320 120" role="img" aria-label="Transient response plot">
        <path d={path} fill="none" stroke="hsl(var(--primary))" strokeLinecap="round" strokeWidth="3" />
      </svg>
      <MarkdownBlock className="mt-2 text-xs text-muted-foreground">{response.formula}</MarkdownBlock>
    </div>
  );
}

function PhasorPanel({ phasors }: { phasors: Array<{ id: string; value: ComplexQuantityValue }> }) {
  const selected = phasors[0];

  return (
    <div className="rounded-md border bg-background p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-semibold">Phasor probe</p>
        <span className="text-xs text-muted-foreground">
          <MarkdownInline>{selected.id}</MarkdownInline>
        </span>
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-[120px_1fr]">
        <svg className="h-28 w-28" viewBox="0 0 120 120" role="img" aria-label={`${selected.id} phasor`}>
          <circle cx="60" cy="60" r="46" className="fill-none stroke-border" strokeWidth="2" />
          <line x1="60" y1="60" x2={phasorEnd(selected.value).x} y2={phasorEnd(selected.value).y} stroke="hsl(var(--primary))" strokeLinecap="round" strokeWidth="4" />
          <circle cx="60" cy="60" r="3" fill="hsl(var(--primary))" />
        </svg>
        <div className="grid content-center gap-2">
          <MiniValue label="Magnitude" value={formatQuantity(selected.value.magnitude, selected.value.unit)} />
          <MiniValue label="Phase" value={`${formatNumber(selected.value.phase_deg)} deg`} />
        </div>
      </div>
    </div>
  );
}

function ScopePanel() {
  const scopeBoundary = useTutorStore((state) => state.scopeBoundary);
  const setScopeBoundary = useTutorStore((state) => state.setScopeBoundary);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (scopeBoundary) {
      return;
    }

    let active = true;
    fetchScopeBoundary()
      .then((scope) => {
        if (active) {
          setScopeBoundary(scope);
        }
      })
      .catch((caughtError) => {
        if (active) {
          setError(errorMessage(caughtError));
        }
      });

    return () => {
      active = false;
    };
  }, [scopeBoundary, setScopeBoundary]);

  return (
    <section className="grid h-full min-h-0 grid-rows-[auto_minmax(0,1fr)]">
      <PanelHeader
        icon={Info}
        title="Scope"
        subtitle={scopeBoundary?.source_of_truth_rule ?? "CiTT keeps unsupported cases explicit."}
      />
      <ScrollArea.Root className="min-h-0">
        <ScrollArea.Viewport className="h-full">
          <div className="space-y-4 p-4">
            {error ? <EmptyPanel title="Scope unavailable" body={error} /> : null}
            {!scopeBoundary && !error ? <EmptyPanel title="Loading scope" body="Fetching the shared product boundary." /> : null}
            {scopeBoundary ? <ScopeContent scope={scopeBoundary} /> : null}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex w-2.5 touch-none select-none bg-muted p-0.5" orientation="vertical">
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-border" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </section>
  );
}

function ScopeContent({ scope }: { scope: ScopeBoundary }) {
  const circuit = useTutorStore((state) => state.circuit);
  const parserUsed = useTutorStore((state) => state.parserUsed);
  const problemText = useTutorStore((state) => state.problemText);
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const visualCircuit = useTutorStore((state) => state.visualCircuit);
  const analysisView = useTutorStore((state) => state.analysisView);
  const variants = useTutorStore((state) => state.variants);
  const debugTrace = useTutorStore((state) => state.debugTrace);

  return (
    <div className="space-y-4">
      <section className="rounded-lg border bg-accent/55 p-4">
        <h3 className="text-sm font-semibold">Product boundary</h3>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{scope.product_positioning}</p>
      </section>
      <Disclosure title="Supported modes" icon={CircuitBoard} defaultOpen>
        <div className="flex flex-wrap gap-2">
          {scope.supported_analysis_modes.map((mode) => (
            <span key={mode.label} className="rounded-full border bg-background px-2.5 py-1 text-xs" title={mode.detail}>
              {mode.label}
            </span>
          ))}
        </div>
      </Disclosure>
      <Disclosure title="BME teaching layer" icon={Lightbulb}>
        <CompactList title="Templates" items={scope.bme_templates} />
        <CompactList title="Boundary" items={scope.bme_boundary} />
      </Disclosure>
      <Disclosure title="Unsupported" icon={Info}>
        <div className="space-y-2">
          {scope.unsupported_features.map((item) => (
            <div key={item.label} className="rounded-md border bg-background p-3">
              <p className="text-sm font-semibold">{item.label}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{item.detail}</p>
            </div>
          ))}
        </div>
      </Disclosure>
      <Disclosure title="Verification rule" icon={Eye}>
        <CompactList title="PASS means" items={scope.verification_boundary} />
      </Disclosure>
      <Disclosure title="Debug" icon={Activity}>
        <RuntimeDebugPanel
          analysisView={analysisView}
          circuit={circuit}
          debugBoundary={scope.debug_boundary}
          debugTrace={debugTrace}
          parserUsed={parserUsed}
          problemText={problemText}
          solutionPacket={solutionPacket}
          variants={variants}
          visualCircuit={visualCircuit}
        />
      </Disclosure>
    </div>
  );
}

function RuntimeDebugPanel({
  analysisView,
  circuit,
  debugBoundary,
  debugTrace,
  parserUsed,
  problemText,
  solutionPacket,
  variants,
  visualCircuit
}: {
  analysisView: AnalysisView | null;
  circuit: CircuitProblem | null;
  debugBoundary: string[];
  debugTrace: RuntimeDebugTrace | null;
  parserUsed: string | null;
  problemText: string | null;
  solutionPacket: SolutionPacket | null;
  variants: PracticeVariant[];
  visualCircuit: VisualCircuit | null;
}) {
  const runtimeSummary = {
    problem_text: problemText,
    parser_used: parserUsed,
    circuit: circuit
      ? {
          id: circuit.id,
          title: circuit.title,
          analysis_type: circuit.analysis_type,
          component_count: circuit.components.length,
          goal_count: circuit.goals.length,
          ambiguity_count: circuit.ambiguities.length,
          nonblocking_ambiguity_count: circuit.nonblocking_ambiguities.length
        }
      : null,
    solution: solutionPacket
      ? {
          status: solutionPacket.status,
          verification_badge: solutionPacket.verification_badge,
          solver_name: solutionPacket.calculation_trace.solver_name,
          answer_source: solutionPacket.calculation_trace.answer_source,
          warning_count: solutionPacket.warnings.length,
          requested_answer_count: Object.keys(solutionPacket.requested_answers ?? {}).length,
          symbolic_answer_count: Object.keys(solutionPacket.symbolic_requested_answers ?? {}).length,
          ac_answer_count: Object.keys(solutionPacket.ac_requested_answers ?? {}).length
        }
      : null,
    frontend: {
      visual_circuit_loaded: Boolean(visualCircuit),
      schematic_nodes: visualCircuit?.nodes.length ?? 0,
      schematic_components: visualCircuit?.components.length ?? 0,
      analysis_view_loaded: Boolean(analysisView),
      variant_count: variants.length
    }
  };

  return (
    <div className="space-y-3">
      <CompactList title="Debug boundary" items={debugBoundary} />
      {debugTrace?.redaction_notes.length ? (
        <CompactList title="Redaction" items={debugTrace.redaction_notes} />
      ) : null}
      <DebugJsonBlock title="Runtime summary" value={runtimeSummary} />
      {debugTrace?.events.length ? <DebugEventList trace={debugTrace} /> : <EmptyPanel title="No backend trace" body="Run a text or image problem to populate Gemini and solver debug events." />}
      {circuit ? <DebugJsonBlock title="Circuit IR" value={circuit} /> : null}
      {solutionPacket ? <DebugJsonBlock title="Solution Packet" value={solutionPacket} /> : null}
      {visualCircuit || analysisView ? (
        <DebugJsonBlock
          title="Visual and analysis state"
          value={{ visual_circuit: visualCircuit, analysis_view: analysisView, variants }}
        />
      ) : null}
    </div>
  );
}

function DebugEventList({ trace }: { trace: RuntimeDebugTrace }) {
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-foreground">Backend events</p>
      {trace.events.map((event, index) => (
        <details key={`${event.stage}:${event.label}:${index}`} className="rounded-md border bg-background p-3">
          <summary className="cursor-pointer text-xs font-semibold">
            {index + 1}. {event.stage} / {event.label}
            {event.elapsed_ms !== null && event.elapsed_ms !== undefined ? ` (${formatNumber(event.elapsed_ms)} ms)` : ""}
          </summary>
          {event.message ? <p className="mt-2 text-xs leading-5 text-muted-foreground">{event.message}</p> : null}
          <DebugPre value={event.data} />
        </details>
      ))}
    </div>
  );
}

function DebugJsonBlock({ title, value }: { title: string; value: unknown }) {
  return (
    <details className="rounded-md border bg-background p-3">
      <summary className="cursor-pointer text-xs font-semibold">{title}</summary>
      <DebugPre value={value} />
    </details>
  );
}

function DebugPre({ value }: { value: unknown }) {
  return (
    <pre className="mt-2 max-h-96 overflow-auto rounded-md border bg-muted/40 p-3 text-[11px] leading-5 text-muted-foreground">
      {JSON.stringify(value, null, 2)}
    </pre>
  );
}

function PanelHeader({
  action,
  icon: Icon,
  subtitle,
  title
}: {
  action?: ReactNode;
  icon: LucideIcon;
  subtitle: string;
  title: string;
}) {
  return (
    <div className="flex min-h-14 items-center justify-between gap-3 border-b px-4">
      <div className="flex min-w-0 items-center gap-2">
        <Icon className="size-4 shrink-0 text-primary" aria-hidden={true} />
        <div className="min-w-0">
          <h2 className="truncate text-sm font-semibold">{title}</h2>
          <p className="truncate text-xs text-muted-foreground">
            <MarkdownInline>{subtitle}</MarkdownInline>
          </p>
        </div>
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

function Disclosure({
  children,
  defaultOpen = false,
  icon: Icon,
  title
}: {
  children: ReactNode;
  defaultOpen?: boolean;
  icon: LucideIcon;
  title: string;
}) {
  return (
    <details className="rounded-lg border bg-card p-3" open={defaultOpen}>
      <summary className="flex cursor-pointer list-none items-center gap-2 text-sm font-semibold">
        <Icon className="size-4 text-primary" aria-hidden={true} />
        {title}
      </summary>
      <div className="mt-3">{children}</div>
    </details>
  );
}

function EmptyPanel({ body, title }: { body: string; title: string }) {
  return (
    <div className="rounded-lg border border-dashed bg-card p-4">
      <p className="text-sm font-semibold">{title}</p>
      <MarkdownBlock className="mt-1 text-sm leading-6 text-muted-foreground">{body}</MarkdownBlock>
    </div>
  );
}

function MarkdownBlock({ children, className }: { children: string; className?: string }) {
  const markdown = useMemo(() => normalizeTutorLatex(children), [children]);

  return (
    <ReactMarkdown
      className={cn("tutor-markdown", className)}
      rehypePlugins={[[rehypeKatex, katexOptions]]}
      remarkPlugins={[remarkGfm, remarkMath]}
    >
      {markdown}
    </ReactMarkdown>
  );
}

function MarkdownInline({ children, className }: { children: string; className?: string }) {
  const markdown = useMemo(() => normalizeTutorLatex(children), [children]);

  return (
    <span className={cn("tutor-markdown tutor-markdown-inline", className)}>
      <ReactMarkdown
        rehypePlugins={[[rehypeKatex, katexOptions]]}
        remarkPlugins={[remarkGfm, remarkMath]}
        components={{
          p: ({ children: paragraphChildren }) => <>{paragraphChildren}</>
        }}
      >
        {markdown}
      </ReactMarkdown>
    </span>
  );
}

function CompactList({ items, title }: { items: string[]; title: string }) {
  if (!items.length) {
    return null;
  }

  return (
    <div>
      <p className="text-xs font-semibold text-foreground">{title}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.slice(0, 8).map((item) => (
          <span key={item} className="rounded-full border bg-background px-2.5 py-1 text-xs leading-5 text-muted-foreground">
            <MarkdownInline>{item}</MarkdownInline>
          </span>
        ))}
      </div>
    </div>
  );
}

function StatusPill({
  label,
  tone
}: {
  label: string;
  tone: "pass" | "warn" | "danger" | "neutral";
}) {
  return (
    <span
      className={cn(
        "rounded-full border px-2.5 py-1 text-xs font-medium",
        tone === "pass" && "border-emerald-200 bg-emerald-50 text-emerald-800",
        tone === "warn" && "border-amber-200 bg-amber-50 text-amber-800",
        tone === "danger" && "border-red-200 bg-red-50 text-red-700",
        tone === "neutral" && "bg-muted text-muted-foreground"
      )}
    >
      {label}
    </span>
  );
}

function MetricTile({ label, note, value }: { label: string; note?: string; value: string }) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <p className="truncate text-xs font-medium text-muted-foreground">
        <MarkdownInline>{label}</MarkdownInline>
      </p>
      <p className="mt-1 break-words text-lg font-semibold">
        <MarkdownInline>{value}</MarkdownInline>
      </p>
      {note ? <MarkdownBlock className="mt-1 text-xs text-muted-foreground">{note}</MarkdownBlock> : null}
    </div>
  );
}

function MiniValue({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-muted p-2">
      <p className="text-[11px] font-medium text-muted-foreground">
        <MarkdownInline>{label}</MarkdownInline>
      </p>
      <p className="mt-1 break-words text-xs font-semibold">
        <MarkdownInline>{value}</MarkdownInline>
      </p>
    </div>
  );
}

function BmeContextPanel({ metadata }: { metadata: NonNullable<SolutionPacket["bme_metadata"]> }) {
  return (
    <section className="rounded-lg border bg-accent/55 p-4">
      <h3 className="text-sm font-semibold">BME context</h3>
      <MarkdownBlock className="mt-2 text-sm leading-6 text-muted-foreground">{metadata.biomedical_context}</MarkdownBlock>
      <p className="mt-2 text-xs font-medium text-accent-foreground">
        <MarkdownInline>{metadata.signal_chain_role}</MarkdownInline>
      </p>
      <div className="mt-3 space-y-3">
        <CompactList title="Students should learn" items={metadata.what_students_should_learn} />
        <CompactList title="Lab mistakes" items={metadata.common_lab_mistakes} />
        <CompactList title="Noise sources" items={metadata.noise_sources} />
      </div>
      {metadata.safety_note ? <MarkdownBlock className="mt-3 text-xs leading-5 text-muted-foreground">{metadata.safety_note}</MarkdownBlock> : null}
    </section>
  );
}

function badgeTone(label: SolutionPacket["verification_badge"]["label"]): "pass" | "warn" | "danger" | "neutral" {
  if (label === "PASS") {
    return "pass";
  }

  if (label === "FAIL") {
    return "danger";
  }

  if (label === "AMBIGUOUS") {
    return "warn";
  }

  return "neutral";
}

function labObservationTone(severity: LabSimulationResponse["observations"][number]["severity"]): "pass" | "warn" | "danger" | "neutral" {
  if (severity === "success") {
    return "pass";
  }
  if (severity === "failure") {
    return "danger";
  }
  if (severity === "watch") {
    return "warn";
  }
  return "neutral";
}

function labObservedDirection(comparisons: LabComparison[]): {
  comparison: LabComparison | null;
  direction: LabPredictionDirection;
  measuredDelta: number;
} {
  const comparison =
    comparisons.reduce<LabComparison | null>((current, item) => {
      const itemShift = Math.abs(item.measured_value - item.baseline_value);
      if (!current || itemShift > Math.abs(current.measured_value - current.baseline_value)) {
        return item;
      }
      return current;
    }, null) ?? null;
  if (!comparison) {
    return { comparison: null, direction: "about_same", measuredDelta: 0 };
  }
  const measuredDelta = comparison.measured_value - comparison.baseline_value;
  const tolerance = Math.max(Math.abs(comparison.baseline_value) * 0.001, 1e-12);
  if (Math.abs(measuredDelta) <= tolerance) {
    return { comparison, direction: "about_same", measuredDelta };
  }
  return { comparison, direction: measuredDelta > 0 ? "increase" : "decrease", measuredDelta };
}

function formatPredictionDirection(direction: LabPredictionDirection): string {
  if (direction === "increase") {
    return "increase";
  }
  if (direction === "decrease") {
    return "decrease";
  }
  return "about same";
}

function numericField(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isFinite(parsed) ? parsed : null;
}

function activeNumber(value: string, scale = 1): number | null {
  const parsed = numericField(value);
  if (parsed === null || Math.abs(parsed) < 1e-15) {
    return null;
  }
  return parsed * scale;
}

function formatLabAssistantSummary(
  result: LabSimulationResponse,
  prediction?: LabPredictionRecord
): string {
  const largest = result.comparisons.reduce<LabComparison | null>((current, comparison) => {
    if (!current || Math.abs(comparison.delta) > Math.abs(current.delta)) {
      return comparison;
    }
    return current;
  }, null);
  const firstObservation = result.observations[0]?.title ?? "Lab scenario completed";
  const shift = largest
    ? `${largest.label} shifted by ${formatQuantity(largest.delta, largest.unit)}`
    : "No shared scalar output shifted";
  const predictionLine = prediction
    ? ` Prediction ${labObservedDirection(result.comparisons).direction === prediction.direction ? "matched" : "needs revisiting"}.`
    : "";
  return `Lab run complete. ${shift}.${predictionLine} First observation: ${firstObservation}.`;
}

function updateCircuitComponentValue(
  circuit: CircuitProblem,
  componentId: string,
  nextValue: number
): CircuitProblem {
  return {
    ...circuit,
    components: circuit.components.map((component) =>
      component.id === componentId ? { ...component, value: nextValue } : component
    )
  };
}

function collectPhasors(solutionPacket: SolutionPacket): Array<{ id: string; value: ComplexQuantityValue }> {
  const requested = Object.entries(solutionPacket.ac_requested_answers ?? {}).map(([id, value]) => ({ id, value }));
  if (requested.length) {
    return requested;
  }

  return Object.entries(solutionPacket.ac_node_voltages ?? {}).map(([id, value]) => ({ id: `Node ${id}`, value }));
}

function phasorEnd(value: ComplexQuantityValue) {
  const angle = (value.phase_deg * Math.PI) / 180;
  const radius = 42;
  return {
    x: 60 + radius * Math.cos(angle),
    y: 60 - radius * Math.sin(angle)
  };
}

function buildPlotPath(values: number[]): string {
  const finiteValues = values.filter(Number.isFinite);
  if (finiteValues.length < 2) {
    return "";
  }

  const min = Math.min(...finiteValues);
  const max = Math.max(...finiteValues);
  const span = max - min || 1;
  const points = finiteValues.map((value, index) => {
    const x = (index / Math.max(finiteValues.length - 1, 1)) * 320;
    const y = 110 - ((value - min) / span) * 100;
    return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
  });

  return points.join(" ");
}

type PlotDomain = {
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
};

function plotDomain(plot: TeachingPlot, { includeZeroY }: { includeZeroY: boolean }): PlotDomain {
  const rawX = plot.series.flatMap((series) => series.points.map((point) => point.x)).filter(Number.isFinite);
  const rawY = plot.series.flatMap((series) => series.points.map((point) => point.y)).filter(Number.isFinite);
  const xValues = plot.x_scale === "log" ? rawX.filter((value) => value > 0) : rawX;
  const yValues = plot.y_scale === "log" ? rawY.filter((value) => value > 0) : rawY;
  const yWithZero = includeZeroY && plot.y_scale !== "log" ? [...yValues, 0] : yValues;
  const [xMin, xMax] = paddedDomain(xValues, plot.x_scale);
  const [yMin, yMax] = paddedDomain(yWithZero, plot.y_scale);

  return { xMin, xMax, yMin, yMax };
}

function paddedDomain(values: number[], scale: "linear" | "log"): [number, number] {
  const finite = values.filter((value) => Number.isFinite(value) && (scale === "linear" || value > 0));
  if (!finite.length) {
    return scale === "log" ? [1, 10] : [0, 1];
  }

  let min = Math.min(...finite);
  let max = Math.max(...finite);
  if (min === max) {
    if (scale === "log") {
      return [min / 10, min * 10];
    }
    const pad = Math.abs(min) || 1;
    return [min - pad, max + pad];
  }

  if (scale === "log") {
    return [min, max];
  }

  const pad = (max - min) * 0.08;
  return [min - pad, max + pad];
}

function scalePlotValue(
  value: number,
  min: number,
  max: number,
  outputMin: number,
  outputMax: number,
  scale: "linear" | "log"
): number {
  if (!Number.isFinite(value)) {
    return outputMin;
  }

  if (scale === "log") {
    const safeValue = Math.max(value, min);
    const logMin = Math.log10(Math.max(min, Number.MIN_VALUE));
    const logMax = Math.log10(Math.max(max, min * 10, Number.MIN_VALUE));
    const logValue = Math.log10(Math.max(safeValue, Number.MIN_VALUE));
    const ratio = (logValue - logMin) / (logMax - logMin || 1);
    return outputMin + clamp01(ratio) * (outputMax - outputMin);
  }

  const ratio = (value - min) / (max - min || 1);
  return outputMin + clamp01(ratio) * (outputMax - outputMin);
}

function teachingLinePath(
  points: TeachingPlot["series"][number]["points"],
  scaleX: (value: number) => number,
  scaleY: (value: number) => number,
  xScale: "linear" | "log"
): string {
  const commands = points
    .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y) && (xScale === "linear" || point.x > 0))
    .map((point, index) => {
      const x = scaleX(point.x);
      const y = scaleY(point.y);
      return `${index === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`;
    });
  return commands.join(" ");
}

function axisTicks(min: number, max: number, scale: "linear" | "log"): number[] {
  if (scale === "log") {
    const start = Math.ceil(Math.log10(Math.max(min, Number.MIN_VALUE)));
    const stop = Math.floor(Math.log10(Math.max(max, min, Number.MIN_VALUE)));
    const ticks: number[] = [];
    for (let power = start; power <= stop; power += 1) {
      ticks.push(10 ** power);
    }
    if (ticks.length >= 2) {
      return ticks.slice(0, 5);
    }
  }

  const span = max - min || 1;
  return [min, min + span / 2, max];
}

function compactAxisNumber(value: number): string {
  if (!Number.isFinite(value)) {
    return "";
  }

  if (Math.abs(value) >= 1000 || (Math.abs(value) > 0 && Math.abs(value) < 0.01)) {
    return value.toExponential(1);
  }

  return Number(value.toPrecision(3)).toString();
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value));
}

function refsFromFocus(focus: TutorStep["focus"]): EntityRef[] {
  return [
    ...focus.components.map((id) => ({ kind: "component" as const, id })),
    ...focus.nodes.map((id) => ({ kind: "node" as const, id })),
    ...focus.current_paths.map((id) => ({ kind: "wire" as const, id })),
    ...focus.goals.map((id) => ({ kind: "goal" as const, id }))
  ];
}

function formatComplex(value: ComplexQuantityValue): string {
  return `${formatQuantity(value.magnitude, value.unit)} at ${formatNumber(value.phase_deg)} deg`;
}

function formatQuantity(value: number, unit: string | null | undefined): string {
  const normalizedUnit = unit ?? "";
  const abs = Math.abs(value);
  const scale = engineeringScale(abs, normalizedUnit);
  return `${formatNumber(value / scale.factor)} ${scale.unit}`.trim();
}

function formatSocraticMode(mode: NonNullable<SolutionPacket["socratic_lecture"]>["mode"]): string {
  return mode
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function engineeringScale(abs: number, unit: string): { factor: number; unit: string } {
  const normalized = unit.toLowerCase();
  if (normalized === "ohm" || normalized === "ohms") {
    if (abs >= 1_000_000) {
      return { factor: 1_000_000, unit: "MOhm" };
    }
    if (abs >= 1_000) {
      return { factor: 1_000, unit: "kOhm" };
    }
    return { factor: 1, unit: "Ohm" };
  }

  if (unit === "A") {
    if (abs && abs < 1e-6) {
      return { factor: 1e-9, unit: "nA" };
    }
    if (abs && abs < 1e-3) {
      return { factor: 1e-6, unit: "uA" };
    }
    if (abs && abs < 1) {
      return { factor: 1e-3, unit: "mA" };
    }
  }

  if (unit === "V") {
    if (abs && abs < 1e-3) {
      return { factor: 1e-6, unit: "uV" };
    }
    if (abs && abs < 1) {
      return { factor: 1e-3, unit: "mV" };
    }
  }

  if (unit === "W") {
    if (abs && abs < 1e-6) {
      return { factor: 1e-9, unit: "nW" };
    }
    if (abs && abs < 1e-3) {
      return { factor: 1e-6, unit: "uW" };
    }
    if (abs && abs < 1) {
      return { factor: 1e-3, unit: "mW" };
    }
  }

  if (unit === "s") {
    if (abs && abs < 1e-6) {
      return { factor: 1e-9, unit: "ns" };
    }
    if (abs && abs < 1e-3) {
      return { factor: 1e-6, unit: "us" };
    }
    if (abs && abs < 1) {
      return { factor: 1e-3, unit: "ms" };
    }
  }

  return { factor: 1, unit };
}

function formatNumber(value: number): string {
  if (!Number.isFinite(value)) {
    return String(value);
  }

  if (Math.abs(value) >= 1000 || (Math.abs(value) > 0 && Math.abs(value) < 0.001)) {
    return value.toExponential(3);
  }

  return Number(value.toPrecision(4)).toString();
}

function parseOptcpvModel(svg: string | null): OptcpvModel | null {
  if (!svg || typeof DOMParser === "undefined" || typeof XMLSerializer === "undefined") {
    return null;
  }

  const document = new DOMParser().parseFromString(svg, "image/svg+xml");
  const root = document.documentElement;
  if (!root || !root.tagName.toLowerCase().endsWith("svg") || root.querySelector("parsererror")) {
    return null;
  }

  const viewBox = parseOptcpvViewBox(root);
  const components = Array.from(root.querySelectorAll<SVGRectElement>("rect[data-component-id]")).map((element) => ({
    id: element.getAttribute("data-component-id") ?? "component",
    type: element.getAttribute("data-component-type") ?? "component",
    x: numberAttr(element, "x"),
    y: numberAttr(element, "y"),
    width: Math.max(numberAttr(element, "width"), 24),
    height: Math.max(numberAttr(element, "height"), 24)
  }));
  const terminals = Array.from(root.querySelectorAll<SVGCircleElement>("circle[data-component-id][data-net-name]")).map((element) => ({
    componentId: element.getAttribute("data-component-id") ?? "component",
    netName: element.getAttribute("data-net-name") ?? "",
    pinName: element.getAttribute("data-pin-name") ?? "",
    x: numberAttr(element, "cx"),
    y: numberAttr(element, "cy")
  }));

  return {
    renderer: root.getAttribute("data-renderer") ?? "optcpv",
    circuitId: root.getAttribute("data-optcpv-circuit-id") ?? "optcpv-circuit",
    layoutMode: root.getAttribute("data-optcpv-layout-mode") ?? "layout",
    fallbackUsed: root.getAttribute("data-optcpv-fallback-used") === "true",
    viewBox,
    sanitizedSvg: sanitizeOptcpvSvg(root),
    components,
    terminals
  };
}

function sanitizeOptcpvSvg(root: Element): string {
  const clone = root.cloneNode(true) as Element;
  clone.setAttribute("preserveAspectRatio", "xMidYMid meet");
  clone.setAttribute("focusable", "false");
  clone.setAttribute("aria-hidden", "true");
  clone.querySelectorAll("script, foreignObject").forEach((element) => element.remove());
  clone.querySelectorAll("*").forEach((element) => {
    Array.from(element.attributes).forEach((attribute) => {
      if (attribute.name.toLowerCase().startsWith("on")) {
        element.removeAttribute(attribute.name);
      }
    });
  });
  return new XMLSerializer().serializeToString(clone);
}

function parseOptcpvViewBox(root: Element): OptcpvViewport {
  const viewBox = root.getAttribute("viewBox")?.trim().split(/\s+/).map(Number) ?? [];
  if (viewBox.length === 4 && viewBox.every(Number.isFinite)) {
    const [x, y, width, height] = viewBox;
    return { x, y, width, height };
  }

  return {
    x: 0,
    y: 0,
    width: Number(root.getAttribute("width")) || 1100,
    height: Number(root.getAttribute("height")) || 800
  };
}

function numberAttr(element: Element, name: string): number {
  const value = Number(element.getAttribute(name));
  return Number.isFinite(value) ? value : 0;
}

function visualCircuitFrame(visualCircuit: VisualCircuit | null): OptcpvViewport {
  if (!visualCircuit) {
    return { x: 0, y: 0, width: 1100, height: 800 };
  }

  return getCircuitBounds(visualCircuit);
}

function optcpvContainScale(rect: DOMRect, frame: OptcpvViewport): number {
  return Math.max(Math.min(rect.width / frame.width, rect.height / frame.height), 0.001);
}

function buildInitialPlaygroundItems(
  optcpvModel: OptcpvModel | null,
  visualCircuit: VisualCircuit | null,
  circuit: CircuitProblem | null
): PlaygroundItem[] {
  const items: PlaygroundItem[] = [];
  const circuitComponentById = new Map((circuit?.components ?? []).map((component) => [component.id, component]));

  if (optcpvModel?.components.length) {
    optcpvModel.components.forEach((component) => {
      const circuitComponent = circuitComponentById.get(component.id);
      const size = defaultPlaygroundItemSize(playgroundKindFromComponent(circuitComponent?.type ?? component.type));

      items.push({
        id: `optcpv-component-${component.id}`,
        kind: playgroundKindFromComponent(circuitComponent?.type ?? component.type),
        label: component.id,
        value: circuitComponent ? formatCircuitComponentValue(circuitComponent) : component.type,
        origin: "circuit",
        sourceEntity: { kind: "component", id: component.id },
        sourceType: component.type,
        width: Math.max(component.width, size.width),
        height: Math.max(component.height, size.height),
        x: component.x + component.width / 2,
        y: component.y + component.height / 2
      });
    });

    return items;
  }

  if (visualCircuit?.components.length) {
    const nodeById = new Map(visualCircuit.nodes.map((node) => [node.id, node]));
    const bounds = getCircuitBounds(visualCircuit);
    const frame = visualCircuitFrame(visualCircuit);

    visualCircuit.components.forEach((component, index) => {
      const nodes = component.nodes.map((nodeId) => nodeById.get(nodeId)).filter(isDefined);
      const point = nodes.length
        ? mapVisualPointToPlaygroundPoint(getComponentCenter(nodes), bounds, frame)
        : fallbackPlaygroundPoint(index, visualCircuit.components.length, frame);
      const circuitComponent = circuitComponentById.get(component.id);
      const kind = playgroundKindFromComponent(component.type, component.role);
      const size = defaultPlaygroundItemSize(kind);

      items.push({
        id: `circuit-component-${component.id}`,
        kind,
        label: component.id,
        value: circuitComponent ? formatCircuitComponentValue(circuitComponent) : shortenLabel(component.label),
        origin: "circuit",
        sourceType: component.type,
        sourceEntity: { kind: "component", id: component.id },
        width: size.width,
        height: size.height,
        ...point
      });
    });

    const visibleNodes = visualCircuit.nodes.filter((node) => node.role !== "internal" || visualCircuit.nodes.length <= 6);
    visibleNodes.forEach((node) => {
      items.push({
        id: `circuit-node-${node.id}`,
        kind: node.role === "ground" ? "ground" : "node",
        label: node.role === "ground" ? "GND" : node.label,
        value: node.role,
        origin: "circuit",
        sourceEntity: { kind: "node", id: node.id },
        sourceType: node.role,
        width: 70,
        height: 46,
        ...mapVisualPointToPlaygroundPoint(node.position, bounds, frame)
      });
    });

    return items;
  }

  if (circuit?.components.length) {
    const frame = visualCircuitFrame(null);
    circuit.components.forEach((component, index) => {
      const kind = playgroundKindFromComponent(component.type);
      const size = defaultPlaygroundItemSize(kind);
      items.push({
        id: `circuit-component-${component.id}`,
        kind,
        label: component.id,
        value: formatCircuitComponentValue(component),
        origin: "circuit",
        sourceType: component.type,
        sourceEntity: { kind: "component", id: component.id },
        width: size.width,
        height: size.height,
        ...fallbackPlaygroundPoint(index, circuit.components.length, frame)
      });
    });

    if (circuit.ground_node) {
      items.push({
        id: `circuit-node-${circuit.ground_node}`,
        kind: "ground",
        label: "GND",
        value: "ground",
        origin: "circuit",
        sourceEntity: { kind: "node", id: circuit.ground_node },
        sourceType: "ground",
        width: 70,
        height: 46,
        x: frame.x + frame.width * 0.5,
        y: frame.y + frame.height * 0.82
      });
    }
  }

  return items;
}

function playgroundKindFromComponent(type: string, role?: string | null): PlaygroundItemKind {
  const normalized = `${type} ${role ?? ""}`.toLowerCase();

  if (normalized.includes("op") && normalized.includes("amp")) {
    return "op_amp";
  }

  if (normalized.includes("capacitor") || normalized === "c") {
    return "capacitor";
  }

  if (normalized.includes("current")) {
    return "current_source";
  }

  if (normalized.includes("voltage") || normalized.includes("battery") || normalized.includes("source")) {
    return "voltage_source";
  }

  if (normalized.includes("diode")) {
    return "diode";
  }

  return "resistor";
}

function formatCircuitComponentValue(component: CircuitProblem["components"][number]): string {
  if (Number.isFinite(component.value) && component.unit) {
    return formatQuantity(component.value, component.unit);
  }

  return component.label ?? component.type;
}

function defaultPlaygroundItemSize(kind: PlaygroundItemKind): { width: number; height: number } {
  if (kind === "op_amp") {
    return { width: 92, height: 68 };
  }

  if (kind === "node" || kind === "ground" || kind === "probe") {
    return { width: 70, height: 54 };
  }

  if (kind === "wire" || kind === "note") {
    return { width: 104, height: 64 };
  }

  return { width: 96, height: 58 };
}

function fallbackPlaygroundPoint(index: number, total: number, frame: OptcpvViewport): PlaygroundPoint {
  const count = Math.max(total, 1);
  const columns = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(count))));
  const rows = Math.max(1, Math.ceil(count / columns));
  const column = index % columns;
  const row = Math.floor(index / columns);
  const xRatio = columns === 1 ? 0.5 : 0.2 + (column / (columns - 1)) * 0.6;
  const yRatio = rows === 1 ? 0.46 : 0.24 + (row / (rows - 1)) * 0.48;

  return clampPlaygroundPoint(
    {
      x: frame.x + frame.width * xRatio,
      y: frame.y + frame.height * yRatio
    },
    frame
  );
}

function mapVisualPointToPlaygroundPoint(
  point: { x: number; y: number },
  bounds: { x: number; y: number; width: number; height: number },
  frame: OptcpvViewport
): PlaygroundPoint {
  return clampPlaygroundPoint(
    {
      x: frame.x + ((point.x - bounds.x) / bounds.width) * frame.width,
      y: frame.y + ((point.y - bounds.y) / bounds.height) * frame.height
    },
    frame
  );
}

function clampPlaygroundPoint(point: PlaygroundPoint, frame: OptcpvViewport): PlaygroundPoint {
  const marginX = Math.min(48, frame.width / 8);
  const marginY = Math.min(48, frame.height / 8);
  return {
    x: Math.min(frame.x + frame.width - marginX, Math.max(frame.x + marginX, point.x)),
    y: Math.min(frame.y + frame.height - marginY, Math.max(frame.y + marginY, point.y))
  };
}

function clientPointToPlaygroundPoint(
  point: { clientX: number; clientY: number },
  element: HTMLElement | null,
  frame: OptcpvViewport
): PlaygroundPoint {
  if (!element) {
    return {
      x: frame.x + frame.width / 2,
      y: frame.y + frame.height / 2
    };
  }

  const rect = element.getBoundingClientRect();
  if (!rect.width || !rect.height) {
    return {
      x: frame.x + frame.width / 2,
      y: frame.y + frame.height / 2
    };
  }

  const scale = optcpvContainScale(rect, frame);
  const renderedWidth = frame.width * scale;
  const renderedHeight = frame.height * scale;
  const offsetX = (rect.width - renderedWidth) / 2;
  const offsetY = (rect.height - renderedHeight) / 2;

  return clampPlaygroundPoint(
    {
      x: frame.x + (point.clientX - rect.left - offsetX) / scale,
      y: frame.y + (point.clientY - rect.top - offsetY) / scale
    },
    frame
  );
}

function hasPlaygroundDragData(event: DragEvent<HTMLElement>): boolean {
  return Array.from(event.dataTransfer.types).includes(PLAYGROUND_DND_MIME);
}

function isPlaygroundItemKind(value: string): value is PlaygroundItemKind {
  return PLAYGROUND_TOOL_BY_KIND.has(value as PlaygroundItemKind);
}

function getCircuitBounds(visualCircuit: VisualCircuit) {
  const points = [
    ...visualCircuit.nodes.map((node) => node.position),
    ...visualCircuit.wires.flatMap((wire) => wire.points)
  ];

  if (!points.length) {
    return { x: 0, y: 0, width: 900, height: 560 };
  }

  const minX = Math.min(...points.map((point) => point.x)) - 100;
  const minY = Math.min(...points.map((point) => point.y)) - 100;
  const maxX = Math.max(...points.map((point) => point.x)) + 100;
  const maxY = Math.max(...points.map((point) => point.y)) + 100;

  return {
    x: minX,
    y: minY,
    width: Math.max(maxX - minX, 600),
    height: Math.max(maxY - minY, 420)
  };
}

function getComponentCenter(nodes: VisualNode[]) {
  const total = nodes.reduce(
    (sum, node) => ({
      x: sum.x + node.position.x,
      y: sum.y + node.position.y
    }),
    { x: 0, y: 0 }
  );

  return {
    x: total.x / nodes.length,
    y: total.y / nodes.length
  };
}

function radiansToDegrees(radians: number) {
  return (radians * 180) / Math.PI;
}

function shortenLabel(label: string) {
  return label.length > 18 ? `${label.slice(0, 17)}...` : label;
}

function toEntitySet(refs: EntityRef[]) {
  return new Set(refs.map((ref) => entityKey(ref.kind, ref.id)));
}

function entityKey(kind: EntityKind, id: string) {
  return `${kind}:${id}`;
}

function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined;
}

function normalizeImageMimeType(mimeType: string): "image/png" | "image/jpeg" | "image/webp" {
  if (mimeType === "image/webp") {
    return "image/webp";
  }

  if (mimeType === "image/jpeg" || mimeType === "image/jpg") {
    return "image/jpeg";
  }

  return "image/png";
}

function imageSubmissionText(selectedFile: File | null, problemText: string): string {
  const fileName = selectedFile?.name ?? "schematic image";
  return problemText ? `Uploaded ${fileName}: ${problemText}` : `Uploaded ${fileName}`;
}

function shouldRenderSchematic(response: FullPipelineResponse): boolean {
  return (
    response.solution_packet.verification_badge.label === "PASS" &&
    response.solution_packet.status === "solved" &&
    response.circuit_ir.components.length > 0
  );
}

function loadSocraticOpening(response: FullPipelineResponse, rendered: boolean): string {
  const badge = response.solution_packet.verification_badge.label;
  const symbolicText = symbolicAnswerLines(response.solution_packet);
  const warningText = response.warnings.length
    ? `\n\nWarnings:\n${response.warnings.map((warning) => `- ${warning}`).join("\n")}`
    : "";
  const firstStep = response.solution_packet.guided_steps[0] ?? response.solution_packet.lesson_packet?.step_by_step_derivation[0];
  const renderText = rendered ? "OptCPV preview is ready." : "No schematic preview was rendered.";

  if (badge !== "PASS") {
    return `CiTT parsed ${response.circuit_ir.title} with ${response.parser_used}, but Socratic coaching is blocked until verification passes. Verification: ${badge}.${warningText}`;
  }

  const prompt = firstStep
    ? `Start here: **${firstStep.title}**. ${firstStep.body}`
    : symbolicText.length
      ? "Start by deciding what role V_c plays: is it a number to substitute, or an input symbol?"
      : "Start by naming the unknown and the first law or equation you would write.";

  return `Socratic mode is ready for **${response.circuit_ir.title}**. ${renderText} Verification: ${badge}.\n\n${prompt}\n\nYour turn: what is your first unknown, assumption, or equation?`;
}

function symbolicAnswerLines(solutionPacket: SolutionPacket): string[] {
  return Object.entries(solutionPacket.symbolic_requested_answers ?? {}).map(([answerId, answer]) => {
    const approximate =
      answer.numeric_coefficient === null || answer.numeric_coefficient === undefined
        ? ""
        : ` (~ ${answer.numeric_coefficient.toPrecision(6)} V_c)`;
    return `${answerId}: ${answer.expression}${approximate}`;
  });
}

function formatCoachNudge(response: ReasoningCoachResponse): string {
  const parts = [
    `**Socratic nudge**\n${response.nudge.message}`,
    `**Question**\n${response.nudge.question}`
  ];

  if (response.nudge.representation_prompt) {
    parts.push(`**Try this representation**\n${response.nudge.representation_prompt}`);
  }

  if (response.nudge.choices.length) {
    parts.push(`**Good next moves**\n${response.nudge.choices.map((choice) => `- ${choice}`).join("\n")}`);
  }

  if (response.metrics.confidence_calibration) {
    parts.push(`**Calibration**\n${response.metrics.confidence_calibration}`);
  }

  if (response.nudge.answer_revealed && response.explanation) {
    parts.push(`**Verified reveal**\n${response.explanation}`);
  }

  return parts.join("\n\n");
}

function formatPluginTab(tab: string): string {
  return tab
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function errorMessage(caughtError: unknown): string {
  return caughtError instanceof Error ? caughtError.message : "Request failed.";
}

function inputStatusText({
  error,
  isImageDragActive,
  loadingElapsedMs,
  parserConfig,
  parserConfigError,
  progressStep,
  selectedFile,
  status
}: {
  error: string | null;
  isImageDragActive: boolean;
  loadingElapsedMs: number;
  parserConfig: ParserConfig | null;
  parserConfigError: string | null;
  progressStep: ProgressStep;
  selectedFile: File | null;
  status: LoadStatus;
}): string {
  if (status === "loading") {
    return progressDetail(progressStep, loadingElapsedMs, Boolean(selectedFile));
  }

  if (error) {
    return error;
  }

  if (parserConfig?.gemini_configured === false) {
    return "Backend parser key missing";
  }

  if (parserConfigError) {
    return parserConfigError;
  }

  if (isImageDragActive) {
    return "Drop image";
  }

  if (selectedFile) {
    return "Schematic attached";
  }

  return "Ready";
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function imageFileFromClipboard(dataTransfer: DataTransfer): File | null {
  return imageFileFromDataTransfer(dataTransfer);
}

function imageFileFromDataTransfer(dataTransfer: DataTransfer): File | null {
  const fileFromFiles = firstSupportedImageFile(Array.from(dataTransfer.files));
  if (fileFromFiles) {
    return normalizeImageFile(fileFromFiles);
  }

  const fileFromItems = firstSupportedImageItem(dataTransfer.items);
  return fileFromItems ? normalizeImageFile(fileFromItems) : null;
}

function hasImageDragItem(dataTransfer: DataTransfer): boolean {
  return (
    Array.from(dataTransfer.items).some((item) => item.kind === "file" && isSupportedImageMimeType(item.type)) ||
    Array.from(dataTransfer.files).some(isSupportedImageFile)
  );
}

function firstSupportedImageItem(items: DataTransferItemList): File | null {
  for (const item of Array.from(items)) {
    if (item.kind !== "file" || !isSupportedImageMimeType(item.type)) {
      continue;
    }

    const file = item.getAsFile();
    if (file && isSupportedImageFile(file)) {
      return file;
    }
  }

  return null;
}

function firstSupportedImageFile(files: File[]): File | null {
  return files.find(isSupportedImageFile) ?? null;
}

function isSupportedImageFile(file: File): boolean {
  return isSupportedImageMimeType(file.type) || /\.(png|jpe?g|webp)$/i.test(file.name);
}

function isSupportedImageMimeType(mimeType: string): boolean {
  return SUPPORTED_IMAGE_MIME_TYPES.has(mimeType.toLowerCase());
}

function normalizeImageFile(file: File): File {
  if (file.name) {
    return file;
  }

  return new File([file], `pasted-schematic.${imageExtension(file.type)}`, {
    lastModified: file.lastModified,
    type: file.type || "image/png"
  });
}

function imageExtension(mimeType: string): "png" | "jpg" | "webp" {
  if (mimeType === "image/webp") {
    return "webp";
  }

  if (mimeType === "image/jpeg" || mimeType === "image/jpg") {
    return "jpg";
  }

  return "png";
}
