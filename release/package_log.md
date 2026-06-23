# CiTT Package Log

Date: 2026-06-22

Version: `0.9.0-bmes2026-rc1`

Commit: `388f14a783e0e47c55521769eeb816fe85367a83`

## Environment

- MATLAB: R2026b Prerelease, Version 26.2.0.3271355
- Simulink: detected
- Simscape: detected
- Simscape Electrical: detected
- MATLAB MCP Server Toolbox: detected
- Branch: `bmes-2026-release-candidate`

## Staging Include List

The package was assembled under `/tmp/citt_bmes_release_stage/CiTT_BMES_2026_Source` from these approved paths:

- `README.md`
- `matlab/citt.m`
- `matlab/+citt/`
- `matlab/resources/ui/`
- `matlab/resources/prompts/`
- `matlab/resources/schemas/`
- `matlab/README.md`
- `docs/matlab_agentic_plugin_demo.md`
- `docs/release_setup.md`
- `docs/demo_live_gui_evidence.md`
- `docs/bmes_application_answers_draft.md`

## MATLAB Toolbox Packaging

Tool used:

```matlab
opts = matlab.addons.toolbox.ToolboxOptions(packageRoot, "3f5672d7-3c0d-4e5d-87e9-a4927e278f9b");
matlab.addons.toolbox.packageToolbox(opts);
```

Final output:

```text
release/CiTT_BMES_2026.mltbx
```

Size:

```text
241225 bytes
```

SHA-256:

```text
3aaf14f05f7be699db2825a7f751e0eb00b0190fa7e11496291c6fb9d6c42d8d
```

Notes from packaging attempts:

- Reverse-DNS identifier was rejected; R2026b requires a UUID identifier.
- Markdown cannot be assigned to `ToolboxGettingStartedGuide`; Markdown docs are packaged as files instead.
- `packageToolbox` returns no output in this MATLAB release; artifact verification uses `dir`.
- macOS `/tmp` needed canonical `/private/...` resolution for package-root path checks.

## Source Zip

Final output:

```text
release/CiTT_BMES_2026_Source.zip
```

Size:

```text
200377 bytes
```

SHA-256:

```text
37e4eda8b208ab46ef759754e396e948e54a64b75acff7bbd4ad3cb7ffdb4237
```

Zip entry count:

```text
68
```

Late UI rendering fix:

```text
Rebuilt after adding Benchmark 3 symbol rendering rules for V_m, A_ol, C_m, T_s, N_bits, K_ctrl, I_leak, and related node labels in matlab/resources/ui/citt_app.html.
```

## Smoke Results

Repository-path smoke:

```text
CiTT release smoke test status: passed
which citt: matlab/citt.m
citt.checkSetup: passed
resources: passed
launch/close: passed
```

MATLAB plugin regression suite:

```text
Running test_real_config...
Running test_agent_task_generation...
Running test_simscape_model_generation...
Running test_teaching_plan_contract...
Running test_lab_delta...
Running test_evidence_pack_export...
Running test_competition_feature_pack...
CiTT MATLAB tests passed: 7
run_all completed with 7 result entries.
```

Notes:

- `test_simscape_model_generation` emitted model-name shadowing warnings from stale local `matlab/work/` model names, but completed successfully.
Installed-toolbox smoke:

```text
Installed toolbox Name: CiTT BMES 2026
Installed toolbox Version: 0.9.0
Installed toolbox Guid: 3f5672d7-3c0d-4e5d-87e9-a4927e278f9b
which citt after install: /Users/Raalm/Library/Application Support/MathWorks/MATLAB Add-Ons/CiTT_BMES_2026@0.9.0(4)/matlab/citt.m
checkSetup work dir after install: /Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work
checkSetup guidance after install: Setup looks ready for the MATLAB-native SATK agent flow.
Installed toolbox launch/close smoke passed.
Uninstalled test toolbox.
Remaining CiTT BMES 2026 toolbox installs: 0
```

## Installed Examples Verification

Command:

```matlab
run("release/verify_installed_examples.m")
```

Result:

```text
Installed CiTT examples verification: passed
Summary: release/example_repro/verification_summary.md
GUI screenshot: release/example_repro/installed_gui_smoke.png
Remaining CiTT BMES 2026 toolbox installs: 0
```

Example reproduction outputs:

- `release/example_repro/installed_gui_smoke.png`
- `release/example_repro/benchmark_01_textbook_rc/`
- `release/example_repro/benchmark_02_tevc_equilibrium/`
- `release/example_repro/benchmark_03_mixed_signal/`

Installed path used:

```text
/Users/Raalm/Library/Application Support/MathWorks/MATLAB Add-Ons/CiTT_BMES_2026@0.9.0(4)/matlab/citt.m
```

Summary:

- Benchmark 1 RC: reproduced a deterministic installed-plugin Simscape model, model check report, Bode report/plot, teaching plan, and evidence pack.
- Benchmark 2 TEVC: opened and checked the live evidence model, then reproduced teaching plan and evidence pack from the installed plugin.
- Benchmark 3 mixed-signal: opened and checked the live evidence model, loaded educational parameters/metrics, then reproduced teaching plan and evidence pack from the installed plugin.

Warnings observed but non-blocking:

- Package-folder path-order warning from the generated RC fallback script.
- Simscape/To Workspace logging-format warnings during model checksum/update.
- Benchmark 3 algebraic-loop/discontinuity warnings, consistent with the live evidence limitations.
- A local `matlab/work/citt_generated_model.slx` shadowing warning during Benchmark 3 model open/check; the requested evidence model path still opened and checked successfully.

## Release Blocker Fixed

The first installed-toolbox smoke found that `citt.checkSetup` tried to create `matlab/work/` inside the MATLAB Add-Ons install folder and failed with permission denied. `matlab/+citt/loadConfig.m` now keeps source checkout behavior but falls back to `prefdir/CiTT/work` when the plugin install folder is not writable.

## Test Hardening

MATLAB can return `4` for Simulink model files when using `exist(path, "file")`. The release prep updated the evidence exporter and affected tests to use `isfile` for filesystem artifact checks, and isolated the evidence-pack export test from stale ambient `matlab/work/` requirement reports.
