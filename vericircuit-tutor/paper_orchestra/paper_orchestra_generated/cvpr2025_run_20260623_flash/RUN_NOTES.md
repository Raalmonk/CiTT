# PaperOrchestra Run Notes

Run date: 2026-06-23

## Inputs

- Raw materials: `vericircuit-tutor/paper_orchestra/raw_materials/`
- PaperOrchestra working copy: `vericircuit-tutor/paper_orchestra/_paper_orchestra_runner/paper-orchestra/`
- Template: `templates/cvpr2025`
- Primary output directory: `vericircuit-tutor/paper_orchestra/paper_orchestra_generated/cvpr2025_run_20260623_lite/`

## Environment

- Python environment: `/tmp/citt_paper_orchestra_py311`
- Dependencies installed from PaperOrchestra `requirements.txt`.
- Gemini credentials were loaded at process runtime from the existing project `.env`; no new `.env` or secret-bearing file was written into this output folder.
- `OPENAI_API_KEY` was set to a dummy value only to avoid an upstream import-time check in the Gemini-only path.

## What Ran

1. Copied the bundled PaperOrchestra source from the skill asset directory into a project-local working copy.
2. Added PaperOrchestra-compatible raw-material entry files:
   - `raw_materials/idea_sparse.md`
   - `raw_materials/experimental_log.md`
   - `raw_materials/figures/info.json`
3. Ran the PaperOrchestra CLI with the CVPR 2025 template.
4. The default/project Gemini model timed out on a minimal probe, so the run switched to `gemini-2.5-flash-lite`.
5. PaperOrchestra generated `outline.json`.
6. The automatic literature-search agent repeatedly hit Gemini `503 UNAVAILABLE` high-demand errors. To keep the run evidence-grounded, the final draft generation used PaperOrchestra's `SectionWritingAgent` with a local citation map built from the already reviewed CiTT references.
7. The generated LaTeX draft was post-processed only to fix:
   - generated figure filenames that did not match the real evidence images,
   - one missing BibTeX key,
   - the MCP expansion, changed to Model Context Protocol,
   - Markdown-style backticks in LaTeX text,
   - required LaTeX packages for `subfigure` and `\cref`.

## Outputs

- PaperOrchestra outline: `outline.json`
- Original raw section-writer output: `latex_writeup/raw_draft_paper.original.tex`
- Cleaned PaperOrchestra draft: `final_paper.tex`
- Cleaned LaTeX writeup copy: `latex_writeup/raw_draft_paper.tex`
- References: `latex_writeup/references.bib`
- Figure assets: `latex_writeup/figures/`

## Verification

Checks run after post-processing:

- No missing `\includegraphics` files.
- No missing or unused BibTeX entries.
- No Markdown backticks left in generated LaTeX.
- No requested blocked wording set appeared in the cleaned generated draft.
- `git diff --check` passed for `vericircuit-tutor/paper_orchestra`.

## Known Limitations

- No PDF was generated because this machine does not expose `pdflatex`, `latexmk`, `tectonic`, `xelatex`, `lualatex`, or `bibtex` on PATH.
- The automatic literature-search stage was not completed because Gemini repeatedly returned high-demand `503 UNAVAILABLE` errors.
- The cleaned PaperOrchestra draft should be treated as a generated draft for author review, not as final submission prose.
