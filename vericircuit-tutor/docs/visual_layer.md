# Visual Layer

The current visual stack is incremental:

```text
Circuit IR -> VisualCircuit semantic layout -> SVG renderer and frontend overlays
```

`/schematic` remains the public SVG endpoint, but CiTT now delegates schematic drawing to OptCPV through `app.services.optcpv_bridge`. SVG output preserves OptCPV renderer metadata plus `data-component-id`, net, and pin metadata for tutor focus.

`/visual_layout` exposes the semantic layout as JSON:

- `VisualNode`
- `VisualComponent`
- `VisualWire`
- `VisualAnnotation`
- `VisualOverlay`
- `VisualFocusRegion`

The frontend lesson mode still uses SVG metadata for focus and zoom. `VisualCircuit` gives future UI work a stable place for overlays such as KCL arrows, current paths, voltage polarity markers, phasor hints, and lesson focus regions without becoming the schematic drawing source of truth.

## Current Scope

OptCPV covers the public schematic SVG path for named examples, BME templates, and supported custom circuits. The semantic visual layer recognizes RC low-pass structure, op-amp pins, ground, input, output, and goal reference overlays for interaction anchors.

Fallback semantic visual layout is intentionally conservative and may not be publication-quality. For unsupported interaction templates it layers nodes outward from the ground/reference side of the circuit graph instead of placing every unknown topology in a circle. It should remain valid, inspectable, and honest about being fallback, while `/schematic` remains OptCPV-owned.

## Not Implemented

- Guaranteed arbitrary image or schematic recognition.
- Full automatic schematic placement for every topology.
- Full WYSIWYG schematic editing with drag/drop component creation.
- AC complex-power overlays.
- Medical safety diagrams or certification markings.
