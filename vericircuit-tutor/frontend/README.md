# VeriCircuit Tutor Frontend

This directory is the decoupled React workspace for the interactive tutor UI. The backend remains the source of truth for parsing, solving, verification, guided steps, and reasoning-coach nudges.

## Proposed Directory Structure

```text
frontend/
  src/
    api/                  # typed API clients for /parse, /solve, /visual_layout, /reasoning_coach
    components/
      circuit/            # interactive SVG or React Flow circuit renderers
      tutor/              # chat, stepper, hint ladder, equation surfaces
      ui/                 # shadcn/ui generated primitives
      TutorWorkspace.tsx  # split-pane workspace shell
    hooks/                # SSE/WebSocket and responsive workspace hooks
    lib/                  # formatting, math, reference parsing, class merging
    store/
      useTutorStore.ts    # centralized tutor/canvas/chat state
    types/
      api.ts              # TypeScript mirrors of backend Pydantic contracts
    App.tsx
    index.css
    main.tsx
  components.json         # shadcn/ui configuration
  tailwind.config.ts
  vite.config.ts
```

## Why This Shape

- `store/` owns cross-pane state: active step, hovered entity, selected entity, streamed chat, and highlight synchronization.
- `types/` mirrors backend response contracts so the UI does not drift from FastAPI/Pydantic payloads.
- `components/circuit/` can evolve from custom semantic SVG to React Flow while preserving the same `VisualCircuit` contract.
- `hooks/` is reserved for streaming transport and backend orchestration, keeping rendering components declarative.
