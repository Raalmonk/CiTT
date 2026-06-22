# CiTT Reproducibility Checklist

Date: 2026-06-22

Version: `0.9.0-bmes2026-rc1`

## Package Artifacts

- [x] MATLAB toolbox package created: `release/CiTT_BMES_2026.mltbx`
- [x] Source fallback package created: `release/CiTT_BMES_2026_Source.zip`
- [x] Toolbox package is non-empty: 241193 bytes
- [x] Source zip is non-empty: 203974 bytes
- [x] SHA-256 recorded for both artifacts in `package_log.md`

## Archive Hygiene

- [x] Package assembled from an explicit staging include list.
- [x] No `.env` files found in `.mltbx` or source zip.
- [x] No `matlab/work/` files found in `.mltbx` or source zip.
- [x] No `slprj/` folders found in `.mltbx` or source zip.
- [x] No `*.slxc` files found in `.mltbx` or source zip.
- [x] No `node_modules/`, `__pycache__`, or `.pytest_cache` files found in `.mltbx` or source zip.

## MATLAB Smoke Tests

- [x] MATLAB detected: R2026b Prerelease.
- [x] Simulink detected.
- [x] Simscape detected.
- [x] Simscape Electrical detected.
- [x] MATLAB MCP Server Toolbox detected.
- [x] Repository-path smoke test passed with `release/smoke_test_citt_release.m`.
- [x] `which citt` resolved to `vericircuit-tutor/matlab/citt.m` in repository-path smoke.
- [x] `citt.checkSetup` ran without crashing.
- [x] Required UI resources exist.
- [x] Required prompt resources exist.
- [x] Required schema resources exist.
- [x] `citt` launched the MATLAB UI and returned a valid figure.
- [x] The app closed cleanly.
- [x] No Node/npm/web server was required for launch.
- [x] No custom Simscape library was required by default.
- [x] No `.env` was required for launch; Gemini key is required for configured parsing.
- [x] MATLAB plugin regression suite passed: `matlab/tests/run_all` completed 7 tests.

## Installed Toolbox Smoke

- [x] Installed `release/CiTT_BMES_2026.mltbx` using `matlab.addons.toolbox.installToolbox`.
- [x] Removed repository plugin paths before checking installed launch.
- [x] `which citt` resolved to the MATLAB Add-Ons install path.
- [x] `citt.checkSetup` ran from the installed toolbox.
- [x] Installed toolbox used writable work directory: `prefdir/CiTT/work`.
- [x] Installed `citt` launched and closed cleanly.
- [x] Test toolbox was uninstalled after smoke test.
- [x] Installed-toolbox examples verification passed with `release/verify_installed_examples.m`.
- [x] Installed GUI launch screenshot captured: `release/example_repro/installed_gui_smoke.png`.
- [x] Benchmark 1 RC reproduced installed-plugin artifacts, model check, Bode plot, teaching plan, and evidence pack.
- [x] Benchmark 2 TEVC opened/checked the evidence model and reproduced teaching/evidence outputs.
- [x] Benchmark 3 mixed-signal opened/checked the evidence model and reproduced teaching/evidence outputs from parameterized metrics.

## Evidence Package

- [x] `submission_assets/README.md` points to `live_gui_evidence/` as final evidence.
- [x] `live_gui_evidence/README.md` describes all three current benchmarks.
- [x] `bmes_live_evidence_report.md` says all three benchmarks are complete.
- [x] Benchmark 3 is labeled educational scaled benchmark evidence, not clinical validation.
- [x] Lab Delta CSV comparison is not claimed as completed.
- [x] Gemini-only no-tools baseline outputs exist for all three benchmarks.
- [x] Scorecard reflects honest Gemini-only and CiTT comparisons.

## Not Claimed

- [ ] Full live benchmark regeneration was not rerun during package creation.
- [ ] Full Lab Delta CSV comparison is not complete without an external CSV.
- [ ] Benchmark 3 is not clinical validation.
