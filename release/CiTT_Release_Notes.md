# CiTT BMES 2026 Release Notes

Version: `0.9.0-bmes2026-rc1`

Date: 2026-06-22

Commit: `388f14a783e0e47c55521769eeb816fe85367a83`

## What CiTT Is

CiTT is a MATLAB-native circuit tutor that connects agent-assisted circuit interpretation with Simulink/Simscape model evidence, focus-map teaching, natural-language probes, and exportable review artifacts.

The release entry point remains:

```matlab
addpath("matlab")
citt
```

After installing the toolbox package, `citt` resolves directly from the installed MATLAB Add-On path.

## What This Release Demonstrates

- A reproducible MATLAB plugin package for BMES/Medtronic review.
- Live GUI evidence for three benchmarks under `submission_assets/live_gui_evidence/`.
- Model-grounded evidence that goes beyond text-only LLM reasoning: generated Simulink/Simscape artifacts, focus maps, probe maps, highlights, plots, metrics, and explicit limitation reporting.
- A clean installed-toolbox launch path that uses a writable MATLAB preference work directory if the Add-Ons install folder is read-only.

## Artifacts

- MATLAB toolbox: `release/CiTT_BMES_2026.mltbx`
- Source fallback: `release/CiTT_BMES_2026_Source.zip`
- Setup docs: `docs/release_setup.md`
- Live evidence map: `docs/demo_live_gui_evidence.md`
- BMES answer scaffold: `paper_orchestra/bmes_application/application_answers_draft.md`

## Install

Toolbox install:

```matlab
matlab.addons.toolbox.installToolbox("release/CiTT_BMES_2026.mltbx")
citt.checkSetup
citt
```

Source fallback:

```matlab
addpath("CiTT_BMES_2026_Source/matlab")
citt.checkSetup
citt
```

## Included

- `matlab/citt.m`
- `matlab/+citt/`
- `matlab/resources/ui/`
- `matlab/resources/prompts/`
- `matlab/resources/schemas/`
- `matlab/README.md`
- `README.md`
- selected setup/demo docs

## Excluded

- `.env` files and API keys
- `matlab/work/`
- `slprj/`
- `*.slxc`
- frontend/backend caches
- `node_modules/`
- old offline evidence drafts as final proof

## Evidence Package

Final evidence entry point:

```text
submission_assets/live_gui_evidence/
```

Do not use older offline draft reports as final proof.

## Known Limitations

- Full flow requires MATLAB, Simulink, Simscape, preferably Simscape Electrical, SATK/MCP-compatible model tooling, a configured LLM/agent backend, and an agent CLI. Gemini is one supported provider.
- Benchmark 3 is educational scaled benchmark evidence, not medical-use validation.
- Lab Delta CSV comparison is not completed without an external lab CSV.
- Gemini-only baseline is a no-tools comparison artifact, not an exhaustive evaluation.
- The release smoke tests verify setup, resources, launch, close, and installed-toolbox path behavior; they do not rerun all live benchmark generation.
