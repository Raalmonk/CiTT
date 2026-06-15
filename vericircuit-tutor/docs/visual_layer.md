# Visual Layer

The current visual stack is incremental:

```text
Circuit IR -> VisualCircuit semantic layout -> SVG renderer and frontend overlays
```

`/schematic` remains the public SVG endpoint. SVG output preserves `data-component-id`, `data-node-id`, current-path metadata, a renderer `<desc>`, and a `data-vericircuit-renderer` root attribute.

`/visual_layout` exposes the semantic layout as JSON:

- `VisualNode`
- `VisualComponent`
- `VisualWire`
- `VisualAnnotation`
- `VisualOverlay`
- `VisualFocusRegion`

The frontend lesson mode still uses SVG metadata for focus and zoom. `VisualCircuit` gives future UI work a stable place for overlays such as KCL arrows, current paths, voltage polarity markers, phasor hints, and lesson focus regions.

## Current Scope

Named templates cover voltage divider, current divider, bridge networks, and common BME fallback layouts through the existing SVG renderer. The semantic visual layer also recognizes RC low-pass structure, op-amp pins, ground, input, output, and goal reference overlays.

Fallback visual layout is intentionally conservative and may not be publication-quality. It should remain valid, inspectable, and honest about being fallback.

## Not Implemented

- Arbitrary image or schematic recognition.
- Full automatic schematic placement for every topology.
- AC complex-power overlays.
- Medical safety diagrams or certification markings.
