# Evidence Summary

Final evidence entry point:

```text
vericircuit-tutor/submission_assets/live_gui_evidence/
```

Primary evidence report:

```text
vericircuit-tutor/submission_assets/live_gui_evidence/bmes_live_evidence_report.md
```

Current evidence state:

- Benchmark 1, textbook RC anti-aliasing: live evidence complete.
- Benchmark 2, two-electrode voltage clamp equilibrium: live evidence complete with symbolic-value caveat.
- Benchmark 3, mixed-signal neural clamp: live evidence complete with educational scaled parameters.
- Natural-language probe evidence exists in the chat-style learning dialog.
- Gemini-only no-tools baseline outputs exist for all three benchmark folders.
- Full Lab Delta CSV comparison remains pending because no external lab CSV was supplied.

Release verification:

- `release/CiTT_BMES_2026.mltbx` created.
- `release/CiTT_BMES_2026_Source.zip` created.
- Installed-toolbox smoke passed.
- Installed examples verification passed with `release/verify_installed_examples.m`.
- Installed GUI screenshot captured at `release/example_repro/installed_gui_smoke.png`.

Important evidence boundaries:

- Benchmark 3 is educational scaled benchmark evidence and should not be described as a patient or biological validation.
- The Gemini-only baseline is a non-exhaustive no-tools comparison.
- Internal scorecards are evidence rubrics, not external validation metrics.
- Older offline draft assets are background/provenance only and should not be used as final proof.
