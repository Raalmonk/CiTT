# Install And Smoke Test

This document records the commands used for the release smoke checks.

## Repository Path Smoke

Run from the repository:

```matlab
run("release/smoke_test_citt_release.m")
```

Observed result:

```text
CiTT release smoke test status: passed
which citt: matlab/citt.m
citt.checkSetup: passed
resource checks: passed
citt launch: passed
citt close: passed
```

## Toolbox Install Smoke

The installed-toolbox smoke removed repository plugin paths from MATLAB's path, installed the `.mltbx`, verified `which citt`, ran setup, launched CiTT, closed the app, and uninstalled the test add-on.

Commands:

```matlab
info = matlab.addons.toolbox.installToolbox("release/CiTT_BMES_2026.mltbx");
which citt
setupReport = citt.checkSetup;
app = citt;
delete(app.Figure)
matlab.addons.toolbox.uninstallToolbox(info)
```

Observed installed path:

```text
/Users/Raalm/Library/Application Support/MathWorks/MATLAB Add-Ons/CiTT_BMES_2026@0.9.0(4)/matlab/citt.m
```

Observed installed work directory:

```text
/Users/Raalm/Library/Application Support/MathWorks/MATLAB/R2026b/CiTT/work
```

Observed result:

```text
Installed toolbox launch/close smoke passed.
Uninstalled test toolbox.
Remaining CiTT BMES 2026 toolbox installs: 0
```

## Source Zip Smoke

Unzip:

```bash
unzip release/CiTT_BMES_2026_Source.zip
```

Launch from MATLAB:

```matlab
addpath("CiTT_BMES_2026_Source/matlab")
citt.checkSetup
citt
```

## Installed Examples Verification

Run:

```matlab
run("release/verify_installed_examples.m")
```

Observed result:

```text
Installed CiTT examples verification: passed
Summary: release/example_repro/verification_summary.md
GUI screenshot: release/example_repro/installed_gui_smoke.png
Remaining CiTT BMES 2026 toolbox installs: 0
```

Verified examples:

```text
benchmark_01_textbook_rc: passed
benchmark_02_tevc_equilibrium: passed
benchmark_03_mixed_signal: passed
```

The validation uses the installed MATLAB Add-On path for `citt`, not the repository MATLAB path. Reproduction outputs are under `release/example_repro/`.

## Setup Notes

- `GEMINI_API_KEY` is required for Gemini-backed parsing, not for opening the app.
- `GEMINI_MODEL` is optional.
- `CITT_AGENT_COMMAND` is optional if Codex CLI or Gemini CLI is discoverable.
- Full SATK/MCP model generation requires configured MATLAB MCP/SATK tooling.
- No Node/npm/web server is required for MATLAB app launch.
- No custom Simscape library is required by default.
