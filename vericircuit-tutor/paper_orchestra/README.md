# CiTT PaperOrchestra Package

This folder contains a PaperOrchestra-compatible writing package for CiTT.

The first pass created raw materials and a manual CVPR-style systems-paper draft. A second pass used the bundled `paper-orchestra` skill source from `/Users/Raalm/.codex/skills/paper-orchestra/assets/paper-orchestra` and generated a PaperOrchestra draft under `paper_orchestra_generated/`.

## Structure

- `raw_materials/`: curated narrative, evidence summaries, benchmark summaries, limitations, figure/table inventories, and claim-to-evidence map.
- `paper/`: manually curated LaTeX systems-paper draft, BibTeX file, figures copied from live evidence, tables, and compile notes.
- `bmes_application/`: polished BMES/Medtronic application answer draft, word counts, upload checklist, and executive-summary variants.
- `_paper_orchestra_runner/`: project-local copy of the bundled PaperOrchestra source used for execution. This is not the installed skill source.
- `paper_orchestra_generated/cvpr2025_run_20260623_lite/`: PaperOrchestra run output using the CVPR 2025 template.

## How To Use With PaperOrchestra

The PaperOrchestra-compatible raw materials are already prepared under `raw_materials/`. The generated run used `raw_materials/idea_sparse.md`, `raw_materials/experimental_log.md`, `raw_materials/figures/info.json`, and the built-in CVPR 2025 template.

Suggested prompt:

```text
Use the CiTT raw materials to revise paper/main.tex or paper_orchestra_generated/cvpr2025_run_20260623_lite/final_paper.tex into a concise CVPR-style systems paper draft. Preserve all evidence boundaries: no patient claims, Benchmark 3 uses educational scaled parameters, full Lab Delta CSV comparison remains pending, and LLM-only baselines are non-exhaustive comparison artifacts.
```

## Drafts

Compile from `paper/` with:

```bash
latexmk -pdf main.tex
```

If `latexmk` is unavailable, see `paper/compile_notes.md`.

The PaperOrchestra-generated draft is:

```text
paper_orchestra_generated/cvpr2025_run_20260623_lite/final_paper.tex
```

Run notes and limitations are documented in:

```text
paper_orchestra_generated/cvpr2025_run_20260623_lite/RUN_NOTES.md
```
