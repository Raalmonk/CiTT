# CiTT MATLAB Plugin

CiTT is now a MATLAB-native plugin shell around Gemini and Simulink Agentic Toolkit.

Run it from MATLAB:

```matlab
addpath("vericircuit-tutor/matlab")
citt
```

The app opens five tabs and shows a persistent stage bar in the header while longer steps also open a MATLAB progress dialog:

- Read Circuit: drag in or browse for a circuit image, optionally add a prompt, then parse with Gemini.
- Build Model: prepare the SATK task, generate MATLAB build code, and open a real Simscape model in Simulink.
- Model Lab: open, check, and simulate the generated Simulink/Simscape model.
- Teach: build a Socratic plan from the circuit spec and focus map, then highlight or zoom focus points.
- Probe & Compare: add guided probes and compare hand, simulation, and lab CSV values.

The Read Circuit tab shows a human-readable spec summary and next step. Use Open JSON only when you want the raw file.
Symbolic or omitted values such as `V_c` are kept as Simscape parameters. They do not block model drawing; they only need values before simulation/checking.

Required for the real flow:

- `GEMINI_API_KEY`
- Gemini model `gemini-3.5-flash` unless `GEMINI_MODEL` is explicitly set
- Simulink
- Simscape, preferably Simscape Electrical
- Simulink Agentic Toolkit initialized with `satk_initialize`
- MATLAB MCP Server

If MATLAB was opened from the Dock and cannot see shell environment variables, create a local untracked file:

```text
vericircuit-tutor/matlab/.env
```

with:

```text
GEMINI_API_KEY=your_key_here
```

Build Model writes `matlab/work/citt_build_simscape_model.m`, runs it in the current MATLAB session, saves `matlab/work/citt_generated_model.slx`, and opens the model. Unknown values are parameterized instead of invented. CiTT only stops before drawing when the spec has unclear or unsupported image/model regions.
