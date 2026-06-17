import { FormEvent, useMemo, useState } from "react";
import * as ScrollArea from "@radix-ui/react-scroll-area";
import { CircuitBoard, GraduationCap, Send, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import { katexOptions, normalizeTutorLatex } from "@/lib/latex";
import { cn } from "@/lib/utils";
import { useTutorStore, type TutorMessage } from "@/store/useTutorStore";
import type {
  EntityKind,
  EntityRef,
  VisualCircuit,
  VisualComponent,
  VisualNode
} from "@/types/api";

export function TutorWorkspace() {
  const circuit = useTutorStore((state) => state.circuit);
  const solutionPacket = useTutorStore((state) => state.solutionPacket);
  const streamStatus = useTutorStore((state) => state.streamStatus);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <header className="border-b bg-card/95">
        <div className="mx-auto flex min-h-16 max-w-[1600px] items-center justify-between gap-4 px-4 py-3">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <CircuitBoard className="size-5" aria-hidden="true" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold tracking-normal">VeriCircuit Tutor</h1>
              <p className="truncate text-sm text-muted-foreground">
                {circuit?.title ?? "Interactive circuit reasoning workspace"}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 text-xs font-medium">
            {solutionPacket?.verification_badge ? (
              <span
                className={cn(
                  "rounded-full border px-2.5 py-1",
                  solutionPacket.verification_badge.label === "PASS"
                    ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                    : "border-amber-200 bg-amber-50 text-amber-800"
                )}
              >
                {solutionPacket.verification_badge.label}
              </span>
            ) : null}
            <span className="rounded-full border bg-muted px-2.5 py-1 text-muted-foreground">
              {streamStatus === "streaming" ? "Tutor typing" : "Tutor ready"}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1600px] gap-4 p-4 lg:h-[calc(100dvh-65px)] lg:grid-cols-[minmax(0,1.42fr)_minmax(360px,0.88fr)]">
        <section className="workspace-panel flex min-h-[440px] flex-col lg:min-h-0">
          <CanvasHeader />
          <CircuitCanvas />
        </section>

        <aside className="workspace-panel grid min-h-[560px] grid-rows-[minmax(180px,0.9fr)_minmax(280px,1.1fr)] lg:min-h-0">
          <StepPanel />
          <ChatPanel />
        </aside>
      </main>
    </div>
  );
}

function CanvasHeader() {
  const visualCircuit = useTutorStore((state) => state.visualCircuit);
  const selectedEntity = useTutorStore((state) => state.selectedEntity);

  return (
    <div className="flex min-h-14 items-center justify-between gap-3 border-b px-4">
      <div className="min-w-0">
        <h2 className="truncate text-sm font-semibold">Circuit Canvas</h2>
        <p className="truncate text-xs text-muted-foreground">
          {visualCircuit?.layout_strategy ?? "semantic visual layout"}
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
  const visualCircuit = useTutorStore((state) => state.visualCircuit);
  const highlightedEntities = useTutorStore((state) => state.highlightedEntities);
  const setHoveredEntity = useTutorStore((state) => state.setHoveredEntity);
  const selectEntity = useTutorStore((state) => state.selectEntity);

  const active = useMemo(() => toEntitySet(highlightedEntities), [highlightedEntities]);

  if (!visualCircuit) {
    return (
      <div className="circuit-grid flex flex-1 items-center justify-center bg-white p-8 text-sm text-muted-foreground">
        No circuit loaded
      </div>
    );
  }

  const nodeById = new Map(visualCircuit.nodes.map((node) => [node.id, node]));
  const bounds = getCircuitBounds(visualCircuit);

  return (
    <div className="circuit-grid min-h-0 flex-1 bg-white">
      <svg
        className="h-full min-h-[380px] w-full"
        role="img"
        aria-label={`Circuit layout for ${visualCircuit.circuit_id}`}
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
            const points = wire.points.length
              ? wire.points
              : fallbackPoints;

            return (
              <polyline
                key={wire.id}
                data-wire-id={wire.id}
                points={points.map((point) => `${point.x},${point.y}`).join(" ")}
                className={cn(
                  "fill-none transition-all",
                  isActive ? "stroke-amber-500" : "stroke-slate-400"
                )}
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
                onPointerEnter={() => setHoveredEntity({ kind: "component", id: component.id })}
                onPointerLeave={() => setHoveredEntity(null)}
                onClick={() => selectEntity({ kind: "component", id: component.id })}
              />
            );
          })}
        </g>

        <g>
          {visualCircuit.nodes.map((node) => {
            const isActive = active.has(entityKey("node", node.id));
            return (
              <g
                key={node.id}
                className="cursor-pointer"
                data-node-id={node.id}
                onClick={() => selectEntity({ kind: "node", id: node.id })}
                onPointerEnter={() => setHoveredEntity({ kind: "node", id: node.id })}
                onPointerLeave={() => setHoveredEntity(null)}
              >
                <circle
                  cx={node.position.x}
                  cy={node.position.y}
                  r={node.role === "ground" ? 9 : 7}
                  className={cn(
                    "transition-all",
                    isActive ? "fill-amber-500 stroke-amber-800" : "fill-white stroke-slate-700"
                  )}
                  strokeWidth={isActive ? 4 : 3}
                />
                <text
                  x={node.position.x}
                  y={node.position.y - 16}
                  textAnchor="middle"
                  className={cn(
                    "select-none fill-slate-700 text-[15px] font-semibold",
                    isActive && "fill-amber-800"
                  )}
                >
                  {node.role === "ground" ? "GND" : node.label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>
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
  const strokeClass = isActive ? "stroke-amber-600" : "stroke-slate-800";
  const fillClass = isActive ? "fill-amber-50" : "fill-white";

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
        className={cn("select-none fill-slate-900 text-[15px] font-bold", isActive && "fill-amber-900")}
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

  const steps = solutionPacket?.guided_steps.length
    ? solutionPacket.guided_steps
    : solutionPacket?.lesson_packet?.step_by_step_derivation ?? [];

  return (
    <section className="min-h-0 border-b">
      <div className="flex min-h-12 items-center gap-2 border-b px-4">
        <GraduationCap className="size-4 text-primary" aria-hidden="true" />
        <h2 className="text-sm font-semibold">Guided Steps</h2>
      </div>
      <ScrollArea.Root className="h-[calc(100%-3rem)]">
        <ScrollArea.Viewport className="h-full">
          <div className="space-y-2 p-3">
            {steps.length ? (
              steps.map((step, index) => {
                const isActive = index === activeStepIndex;
                return (
                  <button
                    key={step.id}
                    className={cn(
                      "grid w-full grid-cols-[28px_minmax(0,1fr)] gap-3 rounded-md border p-3 text-left transition-colors",
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
                      <span className="block truncate text-sm font-semibold">{step.title}</span>
                      <span className="mt-1 line-clamp-2 block text-xs leading-5 text-muted-foreground">
                        {step.body}
                      </span>
                    </span>
                  </button>
                );
              })
            ) : (
              <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
                No guided steps available
              </p>
            )}
          </div>
        </ScrollArea.Viewport>
        <ScrollArea.Scrollbar className="flex w-2.5 touch-none select-none bg-muted p-0.5" orientation="vertical">
          <ScrollArea.Thumb className="relative flex-1 rounded-full bg-border" />
        </ScrollArea.Scrollbar>
      </ScrollArea.Root>
    </section>
  );
}

function ChatPanel() {
  const chatHistory = useTutorStore((state) => state.chatHistory);
  const addStudentMessage = useTutorStore((state) => state.addStudentMessage);
  const highlightFromTutorText = useTutorStore((state) => state.highlightFromTutorText);
  const [draft, setDraft] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed) {
      return;
    }

    addStudentMessage(trimmed);
    highlightFromTutorText(trimmed);
    setDraft("");
  }

  return (
    <section className="grid min-h-0 grid-rows-[3rem_minmax(0,1fr)_auto]">
      <div className="flex items-center gap-2 border-b px-4">
        <Sparkles className="size-4 text-primary" aria-hidden="true" />
        <h2 className="text-sm font-semibold">Tutor Chat</h2>
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
          className="flex size-10 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground transition hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          type="submit"
        >
          <Send className="size-4" aria-hidden="true" />
        </button>
      </form>
    </section>
  );
}

function ChatMessageBubble({ message }: { message: TutorMessage }) {
  const isStudent = message.role === "student";
  const markdown = useMemo(() => normalizeTutorLatex(message.content), [message.content]);

  return (
    <article className={cn("flex", isStudent ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "min-w-0 max-w-[92%] overflow-hidden rounded-lg border px-3 py-2 text-sm leading-6",
          isStudent ? "bg-primary text-primary-foreground" : "bg-card",
          message.status === "error" && "border-destructive text-destructive"
        )}
      >
        <ReactMarkdown
          className="tutor-markdown"
          rehypePlugins={[[rehypeKatex, katexOptions]]}
          remarkPlugins={[remarkGfm, remarkMath]}
        >
          {markdown}
        </ReactMarkdown>
        {message.status === "streaming" ? (
          <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded-sm bg-primary align-middle" />
        ) : null}
      </div>
    </article>
  );
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
