# BMES Submission Upload Checklist

## Portal Basics

- Project name: CiTT: Simscape-Grounded Agentic Tutor for Biomedical Circuits
- Track: Electrical / Computer Science / AI
- Primary upload file: `release/prototype_upload_images/01_workflow_llm_vs_citt.png`
- Prototype image set: `release/prototype_upload_images/`
- Optional video link:
- Suggested GitHub release/tag: `v0.9.0-bmes-2026-submission`
- Submission branch: `bmes-2026-submission`

## Prototype Upload Images

Recommended upload order if the portal accepts multiple images:

- `01_workflow_llm_vs_citt.png`
- `02_benchmark_rc_model_teach_probe.png`
- `03_benchmark_tevc_feedback_tutor.png`
- `04_benchmark_mixed_signal_simscape_advantage.png`

If the portal accepts only one image, upload `01_workflow_llm_vs_citt.png`. If the reviewer-facing form needs a single collage instead, use `00_contact_sheet_optional.png`.

The same image set is mirrored under `submission_assets/live_gui_evidence/prototype_upload_images/` with `visual_qa_report.md` and `visual_qa_contact_sheet.png`.

## Upload Artifacts

- Prototype upload images: `release/prototype_upload_images/`
- MATLAB toolbox package: `CiTT_BMES_2026.mltbx`
- Source fallback package: `CiTT_BMES_2026_Source.zip`
- Release notes: `CiTT_Release_Notes.md`
- Reproducibility checklist: `CiTT_Reproducibility_Checklist.md`
- Live GUI evidence entry point: `../submission_assets/live_gui_evidence/`

## Application Field Mapping

Use `paper_orchestra/bmes_application/application_answers_draft.md` as the source text.

- Project title or name: use the project title at the top of the draft.
- Executive summary: use `Executive Summary`.
- Unmet need or problem statement: use `Problem Description`.
- Proposed solution or prototype description: use `Product/Prototype Description`.
- Technical approach: use `Technical Approach / How It Works`.
- Innovation: use `Innovation / Differentiation`.
- Prototype status or proof: use `Prototype Evidence / Current Status`.
- Testing, evidence, or validation: use `Functional Proof`.
- Market/user fit or impact: use `Impact / Users`.
- Limitations, risks, or regulatory boundary: use `Limitations / Scope`.
- Team, author, or acknowledgements: use `Acknowledgements`.

Use `paper_orchestra/bmes_application/application_answers_word_counts.md` to check portal word limits before pasting.

## Caveats To Preserve

- Benchmark 3 uses educational scaled parameters; it is not patient-facing or medical-use validation.
- Lab Delta CSV comparison is incomplete until an external lab CSV is supplied.
- Gemini-only baseline is a no-tools comparison artifact and is non-exhaustive.
- CiTT is educational software, not a patient-facing device.
- Gemini remains one supported provider; the required dependency is a configured LLM/agent backend.

## Manual Steps Before Submit

- Confirm whether an optional video URL will be provided.
- Create the suggested GitHub release/tag only after final review.
- Upload the prototype image set in the recommended order, or use `01_workflow_llm_vs_citt.png` if only one image is allowed.
- Confirm the portal fields match the final word limits.
