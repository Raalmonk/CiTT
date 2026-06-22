# Compile Notes

This is a CVPR-style systems-paper draft using the standard LaTeX `article` class in two columns. It is not a real CVPR submission package and does not include the official CVPR template.

Compile from this folder:

```bash
latexmk -pdf main.tex
```

Fallback:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Known manual follow-ups:

- Add author/institution information if the paper is shared externally.
- Add a shorter title variant if the BMES package prefers it.
- Re-check all claims against `submission_assets/live_gui_evidence/` before submission.
- Compile to PDF on a machine with `latexmk` or `pdflatex`; this workspace did not expose a LaTeX executable during the draft pass.
