#!/usr/bin/env python3
"""Generate the CiTT BMES submission evidence package.

This script is intentionally honest about provenance. In this environment it
creates analytical/offline figures and clearly labeled screenshot panels. Live
Simscape/SATK screenshots should be regenerated from MATLAB with the wrapper
scripts after local setup is complete.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
ASSET_DIR = SCRIPT_DIR.parent
PROJECT_DIR = ASSET_DIR.parent
TIMESTAMP = "2026-06-22T00:00:00+08:00"

COLORS = {
    "ink": "#1d2433",
    "muted": "#677084",
    "blue": "#2f6fed",
    "cyan": "#00a7b5",
    "green": "#2f9e44",
    "gold": "#f2a900",
    "orange": "#f97316",
    "red": "#d64545",
    "purple": "#7c3aed",
    "panel": "#f7f9fc",
    "line": "#cfd6e4",
}


BENCHMARKS = {
    "benchmark_01_textbook_rc": {
        "short": "RC anti-aliasing",
        "title": "Textbook RC Anti-Aliasing Filter Before an ADC",
        "status": "offline-analytical",
    },
    "benchmark_02_tevc_equilibrium": {
        "short": "TEVC feedback",
        "title": "Two-Electrode Voltage Clamp Equivalent Circuit",
        "status": "offline-analytical",
    },
    "benchmark_03_mixed_signal_simscape": {
        "short": "Mixed-signal clamp",
        "title": "Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic",
        "status": "offline-illustrative",
    },
}


def ensure_dirs() -> None:
    base_dirs = [
        "figures",
        "screenshots",
        "benchmark_01_textbook_rc/plots",
        "benchmark_02_tevc_equilibrium/plots",
        "benchmark_03_mixed_signal_simscape/plots",
        "scripts",
    ]
    for item in base_dirs:
        (ASSET_DIR / item).mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fig_ax(width: float = 10, height: float = 6):
    fig, ax = plt.subplots(figsize=(width, height), dpi=160)
    fig.patch.set_facecolor("white")
    return fig, ax


def savefig(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def add_title(ax, title: str, subtitle: str | None = None) -> None:
    ax.text(
        0.0,
        1.05,
        title,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=16,
        fontweight="bold",
        color=COLORS["ink"],
    )
    if subtitle:
        ax.text(
            0.0,
            1.0,
            subtitle,
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=10,
            color=COLORS["muted"],
        )


def draw_arrow(ax, start, end, color=COLORS["blue"], lw=2.2, rad=0.0):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
    )
    ax.add_patch(arrow)


def draw_box(ax, xy, wh, label, fc="white", ec=COLORS["line"], lw=1.5, fontsize=10):
    x, y = xy
    w, h = wh
    rect = Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(rect)
    ax.text(
        x + w / 2,
        y + h / 2,
        label,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=COLORS["ink"],
        wrap=True,
    )
    return rect


def draw_resistor(ax, x0, x1, y, amp=0.18, n=7, color=COLORS["ink"]):
    xs = np.linspace(x0, x1, n * 2 + 1)
    ys = np.full_like(xs, y)
    for i in range(1, len(xs) - 1):
        ys[i] += amp if i % 2 else -amp
    ax.plot(xs, ys, color=color, lw=2)


def draw_capacitor(ax, x, y_top, y_bottom, color=COLORS["ink"]):
    ax.plot([x, x], [y_top, y_top - 0.35], color=color, lw=2)
    ax.plot([x - 0.35, x + 0.35], [y_top - 0.35, y_top - 0.35], color=color, lw=2)
    ax.plot([x - 0.35, x + 0.35], [y_top - 0.55, y_top - 0.55], color=color, lw=2)
    ax.plot([x, x], [y_top - 0.55, y_bottom], color=color, lw=2)
    ax.plot([x - 0.45, x + 0.45], [y_bottom, y_bottom], color=color, lw=2)
    ax.plot([x - 0.28, x + 0.28], [y_bottom - 0.14, y_bottom - 0.14], color=color, lw=2)
    ax.plot([x - 0.12, x + 0.12], [y_bottom - 0.28, y_bottom - 0.28], color=color, lw=2)


def create_problem_images() -> None:
    rc_schematic()
    tevc_schematic()
    mixed_signal_schematic()


def rc_schematic() -> None:
    fig, ax = fig_ax(10, 5.2)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")
    add_title(ax, "Benchmark 1 Input Schematic", "RC low-pass anti-alias filter before a 500 Hz ADC")
    ax.add_patch(Circle((1.1, 2.5), 0.45, fill=False, lw=2, ec=COLORS["ink"]))
    ax.text(1.1, 3.15, "Vin: ECG + 60 Hz + HF noise", ha="center", fontsize=9, color=COLORS["ink"])
    ax.plot([1.55, 2.2], [2.5, 2.5], color=COLORS["ink"], lw=2)
    draw_resistor(ax, 2.2, 4.1, 2.5)
    ax.text(3.15, 3.0, "R = 39.8 kOhm", ha="center", fontsize=9, color=COLORS["ink"])
    ax.plot([4.1, 6.2], [2.5, 2.5], color=COLORS["ink"], lw=2)
    ax.add_patch(Circle((5.2, 2.5), 0.07, color=COLORS["blue"]))
    ax.text(5.2, 2.82, "Probe Vout", ha="center", fontsize=9, color=COLORS["blue"])
    draw_capacitor(ax, 5.2, 2.5, 1.1)
    ax.text(5.95, 1.78, "C = 100 nF", fontsize=9, color=COLORS["ink"])
    draw_box(ax, (6.6, 1.85), (1.5, 1.3), "ADC\nfs = 500 Hz", fc="#edf5ff", ec=COLORS["blue"])
    draw_arrow(ax, (6.2, 2.5), (6.6, 2.5), COLORS["blue"])
    draw_box(ax, (8.5, 1.85), (1.0, 1.3), "Samples", fc="#f2fbf5", ec=COLORS["green"])
    draw_arrow(ax, (8.1, 2.5), (8.5, 2.5), COLORS["green"])
    savefig(fig, ASSET_DIR / "benchmark_01_textbook_rc/input_schematic.png")


def tevc_schematic() -> None:
    fig, ax = fig_ax(11, 6)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    add_title(ax, "Benchmark 2 Input Schematic", "Simplified TEVC equilibrium feedback model")
    draw_box(ax, (0.5, 3.7), (1.2, 0.8), "Vc\ncommand", fc="#edf5ff", ec=COLORS["blue"])
    draw_box(ax, (2.2, 3.7), (1.2, 0.8), "Ideal\nbuffer", fc="#f7f9fc")
    draw_box(ax, (4.2, 3.2), (1.5, 1.6), "Diff amp\nA = 100", fc="#fff7e8", ec=COLORS["gold"])
    draw_box(ax, (6.5, 3.7), (1.0, 0.8), "Ro\n10 Ohm", fc="white")
    draw_box(ax, (8.2, 2.7), (1.1, 1.8), "Membrane\nRm = 10 Ohm\nVm", fc="#f2fbf5", ec=COLORS["green"])
    draw_box(ax, (6.5, 1.1), (1.0, 0.8), "Re", fc="white")
    draw_arrow(ax, (1.7, 4.1), (2.2, 4.1), COLORS["blue"])
    draw_arrow(ax, (3.4, 4.1), (4.2, 4.1), COLORS["blue"])
    draw_arrow(ax, (5.7, 4.1), (6.5, 4.1), COLORS["orange"])
    draw_arrow(ax, (7.5, 4.1), (8.2, 4.1), COLORS["orange"])
    draw_arrow(ax, (8.75, 2.7), (7.0, 1.9), COLORS["cyan"], rad=0.25)
    draw_arrow(ax, (6.5, 1.5), (4.2, 3.5), COLORS["cyan"], rad=0.18)
    ax.text(5.5, 1.6, "feedback voltage electrode", fontsize=9, color=COLORS["cyan"], ha="center")
    ax.text(8.9, 2.35, "probe Vm", fontsize=9, color=COLORS["green"], ha="center")
    ax.text(7.0, 4.65, "probe clamp current", fontsize=9, color=COLORS["orange"], ha="center")
    savefig(fig, ASSET_DIR / "benchmark_02_tevc_equilibrium/input_schematic.png")


def mixed_signal_schematic() -> None:
    fig, ax = fig_ax(12, 6.4)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    add_title(ax, "Benchmark 3 Input Schematic", "Physical neural clamp plus sampled digital control")
    draw_box(ax, (0.4, 3.8), (1.2, 0.8), "Vc(t)\nstep", fc="#edf5ff", ec=COLORS["blue"])
    draw_box(ax, (2.1, 3.5), (1.4, 1.2), "Finite-gain\namplifier\nrails/current limit", fc="#fff7e8", ec=COLORS["gold"], fontsize=8)
    draw_box(ax, (4.2, 3.5), (1.2, 1.2), "Electrode\nseries R", fc="white")
    draw_box(ax, (6.0, 2.9), (1.5, 1.8), "Simscape\nmembrane\nCm, Rm,\nleak current", fc="#f2fbf5", ec=COLORS["green"], fontsize=8)
    draw_box(ax, (8.2, 3.5), (1.1, 1.2), "ADC\nsample +\nquantize", fc="#f2f7ff", ec=COLORS["blue"], fontsize=8)
    draw_box(ax, (10.0, 3.2), (1.5, 1.8), "Digital\nstate logic\ncompare,\nsettle,\nsaturate", fc="#f7f2ff", ec=COLORS["purple"], fontsize=8)
    draw_box(ax, (9.8, 1.0), (1.4, 0.9), "DAC or\ncommand update", fc="#f7f9fc", fontsize=8)
    for a, b, c in [
        ((1.6, 4.2), (2.1, 4.2), COLORS["blue"]),
        ((3.5, 4.1), (4.2, 4.1), COLORS["gold"]),
        ((5.4, 4.1), (6.0, 4.1), COLORS["green"]),
        ((7.5, 4.0), (8.2, 4.0), COLORS["blue"]),
        ((9.3, 4.0), (10.0, 4.0), COLORS["purple"]),
        ((10.5, 3.2), (10.5, 1.9), COLORS["purple"]),
        ((9.8, 1.45), (2.8, 3.5), COLORS["cyan"]),
    ]:
        draw_arrow(ax, a, b, c, rad=-0.12 if c == COLORS["cyan"] else 0.0)
    ax.text(6.75, 2.55, "probes: Vm, clamp current", ha="center", fontsize=9, color=COLORS["green"])
    ax.text(10.75, 5.25, "state trace + ADC codes", ha="center", fontsize=9, color=COLORS["purple"])
    savefig(fig, ASSET_DIR / "benchmark_03_mixed_signal_simscape/input_schematic.png")


def create_top_figures() -> None:
    overview_architecture()
    llm_vs_citt_workflow()
    bmes_alignment()
    comparison_score_figures()


def overview_architecture() -> None:
    fig, ax = fig_ax(12, 6.2)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    add_title(ax, "CiTT Evidence Architecture", "Model-grounded tutoring flow used by the benchmark package")
    labels = [
        ("Circuit image\nor prompt", "#edf5ff", COLORS["blue"]),
        ("Gemini\nstructured spec", "#f7f9fc", COLORS["line"]),
        ("SATK task\nand build request", "#fff7e8", COLORS["gold"]),
        ("Simscape /\nSimulink model", "#f2fbf5", COLORS["green"]),
        ("Teach, highlight,\nprobe, Lab Delta", "#f7f2ff", COLORS["purple"]),
        ("Evidence export\nfor BMES", "#fff2f2", COLORS["red"]),
    ]
    xs = [0.5, 2.45, 4.4, 6.35, 8.3, 10.2]
    for i, ((label, fc, ec), x) in enumerate(zip(labels, xs)):
        draw_box(ax, (x, 2.35), (1.45, 1.3), label, fc=fc, ec=ec, fontsize=8.5)
        if i < len(xs) - 1:
            draw_arrow(ax, (x + 1.45, 3.0), (xs[i + 1], 3.0), COLORS["blue"])
    ax.text(6.0, 1.1, "Core claim: the tutor teaches from an executable model, not free-floating text.", ha="center", fontsize=12, color=COLORS["ink"])
    savefig(fig, ASSET_DIR / "figures/overview_architecture.png")


def llm_vs_citt_workflow() -> None:
    fig, ax = fig_ax(12, 6.4)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    add_title(ax, "LLM-Only Workflow vs CiTT Workflow", "The benchmark separates fluent explanation from executable evidence")
    ax.text(0.4, 4.95, "Generic LLM-only", fontsize=12, fontweight="bold", color=COLORS["muted"])
    ax.text(0.4, 2.45, "CiTT model-grounded", fontsize=12, fontweight="bold", color=COLORS["blue"])
    top = ["Prompt", "Text answer", "No model\nor probes", "Manual trust\nrequired"]
    bot = ["Circuit image\nor prompt", "Structured\nspec", "Simscape\nmodel", "Highlights,\nprobes, plots", "Evidence\npack"]
    for i, label in enumerate(top):
        x = 2.0 + i * 2.2
        draw_box(ax, (x, 4.35), (1.45, 0.9), label, fc="#f8f8f8", ec=COLORS["line"], fontsize=8)
        if i < len(top) - 1:
            draw_arrow(ax, (x + 1.45, 4.8), (x + 2.2, 4.8), COLORS["muted"])
    for i, label in enumerate(bot):
        x = 1.4 + i * 2.05
        draw_box(ax, (x, 1.65), (1.45, 0.9), label, fc="#eef7ff" if i < 2 else "#f2fbf5", ec=COLORS["blue"] if i < 2 else COLORS["green"], fontsize=8)
        if i < len(bot) - 1:
            draw_arrow(ax, (x + 1.45, 2.1), (x + 2.05, 2.1), COLORS["blue"])
    ax.text(10.7, 3.25, "Benchmark 3\nrequires transient,\nsaturation, ADC,\nand state evidence", ha="center", fontsize=10, color=COLORS["red"])
    savefig(fig, ASSET_DIR / "figures/llm_vs_citt_workflow.png")


def bmes_alignment() -> None:
    fig, ax = fig_ax(12, 7)
    ax.axis("off")
    add_title(ax, "BMES Judging Alignment", "How the evidence package maps artifacts to judging categories")
    rows = [
        ("Product need and market", "Biomedical circuits are hard to debug with text-only tutoring"),
        ("Utility and novelty", "Circuit read -> model build -> Socratic teaching -> evidence export"),
        ("Technical feasibility", "Specs, agent tasks, plots, model-capture scripts, live-run hooks"),
        ("Budget/economics", "Uses MATLAB/SATK/Gemini setup; report includes dependency limits"),
        ("Writing clarity", "Per-benchmark problem, comparison, run notes, scorecard"),
        ("Product performance", "RC, TEVC, and mixed-signal benchmarks with requirements"),
        ("Limitations", "No clinical verification; live Simscape capture pending in this run"),
        ("Presentation clarity", "Architecture, workflow, score, and evidence figures"),
    ]
    y = 0.88
    for i, (cat, evidence) in enumerate(rows):
        color = [COLORS["blue"], COLORS["cyan"], COLORS["green"], COLORS["gold"], COLORS["purple"], COLORS["orange"], COLORS["red"], COLORS["muted"]][i]
        ax.add_patch(Rectangle((0.02, y - 0.065), 0.025, 0.05, transform=ax.transAxes, color=color))
        ax.text(0.06, y, cat, transform=ax.transAxes, fontsize=11, fontweight="bold", color=COLORS["ink"], va="top")
        ax.text(0.34, y, evidence, transform=ax.transAxes, fontsize=10, color=COLORS["muted"], va="top")
        y -= 0.1
    savefig(fig, ASSET_DIR / "figures/bmes_judging_alignment.png")


def score_rows():
    return [
        {
            "benchmark": "benchmark_01_textbook_rc",
            "system": "LLM-only",
            "status": "manual-pending",
            "topology_model_understanding": "",
            "numerical_simulation_correctness": "",
            "unit_sign_reference_correctness": "",
            "executable_model_evidence": "",
            "teaching_usefulness": "",
            "honest_assumptions_limitations": "",
            "total": "",
            "notes": "Prompt prepared. Baseline not run because no verified pure no-tool LLM baseline invocation was executed.",
        },
        {
            "benchmark": "benchmark_01_textbook_rc",
            "system": "CiTT offline package",
            "status": "offline-generated-live-matlab-pending",
            "topology_model_understanding": 3,
            "numerical_simulation_correctness": 3,
            "unit_sign_reference_correctness": 3,
            "executable_model_evidence": 1,
            "teaching_usefulness": 3,
            "honest_assumptions_limitations": 2,
            "total": 15,
            "notes": "Analytical plots/specs generated; live Simscape screenshot/model evidence still pending.",
        },
        {
            "benchmark": "benchmark_02_tevc_equilibrium",
            "system": "LLM-only",
            "status": "manual-pending",
            "topology_model_understanding": "",
            "numerical_simulation_correctness": "",
            "unit_sign_reference_correctness": "",
            "executable_model_evidence": "",
            "teaching_usefulness": "",
            "honest_assumptions_limitations": "",
            "total": "",
            "notes": "Prompt prepared. Baseline not run because no verified pure no-tool LLM baseline invocation was executed.",
        },
        {
            "benchmark": "benchmark_02_tevc_equilibrium",
            "system": "CiTT offline package",
            "status": "offline-generated-live-matlab-pending",
            "topology_model_understanding": 3,
            "numerical_simulation_correctness": 2,
            "unit_sign_reference_correctness": 2,
            "executable_model_evidence": 1,
            "teaching_usefulness": 3,
            "honest_assumptions_limitations": 2,
            "total": 13,
            "notes": "Equilibrium feedback evidence generated; live Simscape/SATK arrangement still pending.",
        },
        {
            "benchmark": "benchmark_03_mixed_signal_simscape",
            "system": "LLM-only",
            "status": "manual-pending",
            "topology_model_understanding": "",
            "numerical_simulation_correctness": "",
            "unit_sign_reference_correctness": "",
            "executable_model_evidence": "",
            "teaching_usefulness": "",
            "honest_assumptions_limitations": "",
            "total": "",
            "notes": "Prompt prepared. Baseline not run because no verified pure no-tool LLM baseline invocation was executed.",
        },
        {
            "benchmark": "benchmark_03_mixed_signal_simscape",
            "system": "CiTT offline package",
            "status": "offline-illustrative-live-matlab-pending",
            "topology_model_understanding": 3,
            "numerical_simulation_correctness": 2,
            "unit_sign_reference_correctness": 2,
            "executable_model_evidence": 1,
            "teaching_usefulness": 3,
            "honest_assumptions_limitations": 2,
            "total": 13,
            "notes": "Mixed-signal plots are explicitly illustrative until Simscape/Simulink is run locally.",
        },
    ]


def comparison_score_figures() -> None:
    rows = [r for r in score_rows() if r["system"] == "CiTT offline package"]
    labels = ["RC", "TEVC", "Mixed"]
    totals = [r["total"] for r in rows]
    fig, ax = fig_ax(9, 5.2)
    add_title(ax, "Benchmark Score Bars", "LLM baseline pending; CiTT bars show offline package score with live MATLAB evidence pending")
    x = np.arange(len(labels))
    ax.bar(x, totals, color=[COLORS["blue"], COLORS["green"], COLORS["purple"]], width=0.55, label="CiTT offline package")
    ax.set_ylim(0, 20)
    ax.set_ylabel("Score out of 20")
    ax.set_xticks(x, labels)
    ax.axhspan(0, 20, facecolor="#fafafa", zorder=-2)
    for i, v in enumerate(totals):
        ax.text(i, v + 0.45, f"{v}/20", ha="center", fontsize=10, color=COLORS["ink"])
        ax.text(i, 1.2, "LLM\npending", ha="center", fontsize=8, color=COLORS["muted"])
    ax.legend(loc="upper right")
    ax.grid(axis="y", color="#e7eaf0")
    savefig(fig, ASSET_DIR / "figures/comparison_score_bars.png")

    cats = [
        "Topology",
        "Numerical",
        "Units",
        "Executable",
        "Teaching",
        "Limits",
    ]
    vals = np.array([
        [3, 3, 3, 1, 3, 2],
        [3, 2, 2, 1, 3, 2],
        [3, 2, 2, 1, 3, 2],
    ], dtype=float)
    maxes = np.array([4, 4, 3, 4, 3, 2], dtype=float)
    avg = vals.mean(axis=0) / maxes
    angles = np.linspace(0, 2 * np.pi, len(cats), endpoint=False)
    closed_angles = np.r_[angles, angles[0]]
    closed_avg = np.r_[avg, avg[0]]
    fig = plt.figure(figsize=(7.5, 7.5), dpi=160)
    ax = fig.add_subplot(111, polar=True)
    ax.plot(closed_angles, closed_avg, color=COLORS["blue"], lw=2.5)
    ax.fill(closed_angles, closed_avg, color=COLORS["blue"], alpha=0.18)
    ax.set_xticks(angles, cats)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0], ["25%", "50%", "75%", "100%"])
    ax.set_ylim(0, 1)
    ax.set_title("CiTT Offline Evidence Radar\nLive Simscape evidence pending", pad=22, fontsize=15, color=COLORS["ink"], fontweight="bold")
    savefig(fig, ASSET_DIR / "figures/comparison_score_radar.png")


def create_rc_plots() -> None:
    out = ASSET_DIR / "benchmark_01_textbook_rc/plots"
    r = 39.8e3
    c = 100e-9
    fc = 1 / (2 * math.pi * r * c)
    f = np.logspace(0, 4, 1200)
    mag = 1 / np.sqrt(1 + (f / fc) ** 2)
    phase = -np.degrees(np.arctan(f / fc))

    fig, ax = fig_ax(9, 5.3)
    add_title(ax, "RC Bode Magnitude", "Analytical RC response, offline figure; not a Simscape simulation")
    ax.semilogx(f, 20 * np.log10(mag), color=COLORS["blue"], lw=2.4)
    for fx, label, color in [(fc, f"fc = {fc:.1f} Hz", COLORS["green"]), (60, "60 Hz", COLORS["gold"]), (250, "Nyquist = 250 Hz", COLORS["red"])]:
        ax.axvline(fx, color=color, lw=1.8, ls="--")
        ax.text(fx * 1.04, -34, label, rotation=90, va="bottom", fontsize=8, color=color)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude (dB)")
    ax.set_ylim(-42, 2)
    ax.grid(True, which="both", color="#e7eaf0")
    savefig(fig, out / "rc_bode_magnitude.png")

    fig, ax = fig_ax(9, 5.3)
    add_title(ax, "RC Bode Phase", "Analytical phase response")
    ax.semilogx(f, phase, color=COLORS["purple"], lw=2.4)
    ax.axvline(fc, color=COLORS["green"], lw=1.8, ls="--", label=f"fc = {fc:.1f} Hz")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Phase (degrees)")
    ax.set_ylim(-95, 5)
    ax.grid(True, which="both", color="#e7eaf0")
    ax.legend()
    savefig(fig, out / "rc_bode_phase.png")

    fs = 4000
    t = np.arange(0, 1.0, 1 / fs)
    vin_ecg = 1.0 * np.sin(2 * np.pi * 5 * t)
    vin_interference = 0.35 * np.sin(2 * np.pi * 60 * t)
    vin = vin_ecg + vin_interference
    dt = 1 / fs
    tau = r * c
    alpha = dt / (tau + dt)
    y = np.zeros_like(vin)
    for i in range(1, len(vin)):
        y[i] = y[i - 1] + alpha * (vin[i] - y[i - 1])
    fig, ax = fig_ax(10, 5.5)
    add_title(ax, "RC Time Response", "Analytical discrete integration of the first-order low-pass equation")
    mask = t <= 0.45
    ax.plot(t[mask], vin_ecg[mask], color=COLORS["green"], lw=1.8, label="5 Hz ECG-like component")
    ax.plot(t[mask], vin[mask], color=COLORS["muted"], lw=1.1, alpha=0.75, label="Input with 60 Hz interference")
    ax.plot(t[mask], y[mask], color=COLORS["blue"], lw=2.5, label="Filtered output")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (normalized)")
    ax.grid(True, color="#e7eaf0")
    ax.legend(loc="upper right")
    savefig(fig, out / "rc_time_response.png")

    t2 = np.arange(0, 0.08, 1 / 20000)
    x = np.sin(2 * np.pi * 5 * t2) + 0.35 * np.sin(2 * np.pi * 310 * t2)
    ts = np.arange(0, 0.08, 1 / 500)
    xs = np.sin(2 * np.pi * 5 * ts) + 0.35 * np.sin(2 * np.pi * 310 * ts)
    alias = np.sin(2 * np.pi * 5 * t2) + 0.35 * np.sin(2 * np.pi * 190 * t2)
    fig, ax = fig_ax(10, 5.5)
    add_title(ax, "RC Aliasing Demo", "310 Hz content sampled at 500 Hz aliases to 190 Hz; analytical demo")
    ax.plot(t2, x, color=COLORS["muted"], lw=1.0, alpha=0.45, label="Continuous 310 Hz-contaminated signal")
    ax.plot(t2, alias, color=COLORS["red"], lw=1.8, alpha=0.85, label="Apparent 190 Hz alias")
    ax.scatter(ts, xs, color=COLORS["blue"], s=24, zorder=5, label="500 Hz samples")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (normalized)")
    ax.grid(True, color="#e7eaf0")
    ax.legend(loc="upper right")
    savefig(fig, out / "rc_aliasing_demo.png")

    c_bad = 100e-6
    fc_bad = 1 / (2 * math.pi * r * c_bad)
    mag_bad = 1 / np.sqrt(1 + (f / fc_bad) ** 2)
    fig, ax = fig_ax(9, 5.3)
    add_title(ax, "Lab Delta: 100 nF vs 100 uF", "Wrong capacitor unit shifts cutoff by 1000x")
    ax.semilogx(f, 20 * np.log10(mag), color=COLORS["blue"], lw=2.4, label=f"Expected 100 nF, fc={fc:.1f} Hz")
    ax.semilogx(f, 20 * np.log10(mag_bad), color=COLORS["red"], lw=2.4, label=f"Mistake 100 uF, fc={fc_bad:.3f} Hz")
    ax.axvline(5, color=COLORS["green"], ls="--", label="5 Hz ECG")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude (dB)")
    ax.set_ylim(-85, 3)
    ax.grid(True, which="both", color="#e7eaf0")
    ax.legend()
    savefig(fig, out / "rc_unit_mistake_delta.png")

    rows = [
        ["Requirement", "Result", "Status"],
        ["Cutoff near 40 Hz", f"{fc:.1f} Hz", "PASS"],
        ["60 Hz attenuated", f"{20 * math.log10(1 / math.sqrt(1 + (60 / fc) ** 2)):.1f} dB", "PASS"],
        ["Nyquist attenuation", f"{20 * math.log10(1 / math.sqrt(1 + (250 / fc) ** 2)):.1f} dB", "WARN"],
        ["Single pole proves alias-free", "No", "WARN"],
    ]
    save_table_figure(out / "rc_requirement_pass_fail.png", "RC Requirement Pass/Fail", rows)


def tevc_data():
    vc = 50e-3
    rm = 10
    ro = 10
    k = rm / (rm + ro)
    gains = np.logspace(0, 4, 180)
    vm_ratio = gains * k / (1 + gains * k)
    err_mv = (1 - vm_ratio) * vc * 1e3
    return vc, rm, ro, k, gains, vm_ratio, err_mv


def create_tevc_plots() -> None:
    out = ASSET_DIR / "benchmark_02_tevc_equilibrium/plots"
    vc, rm, ro, k, gains, vm_ratio, err_mv = tevc_data()
    t = np.linspace(0, 0.04, 1200)
    tau = 0.004
    vm_final = vm_ratio[np.argmin(abs(gains - 100))] * vc
    vm = vm_final * (1 - np.exp(-t / tau))
    vout = vm / k
    iclamp = (vout - vm) / ro

    fig, ax = fig_ax(10, 5.4)
    add_title(ax, "TEVC Feedback Response", "Simplified equilibrium model with illustrative first-order approach")
    ax.plot(t * 1000, np.full_like(t, vc * 1e3), color=COLORS["muted"], lw=1.8, ls="--", label="Vc command")
    ax.plot(t * 1000, vm * 1e3, color=COLORS["blue"], lw=2.5, label="Vm")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (mV)")
    ax.grid(True, color="#e7eaf0")
    ax.legend()
    savefig(fig, out / "tevc_feedback_response.png")

    fig, ax = fig_ax(9, 5.3)
    add_title(ax, "TEVC Loop Error vs Gain", "Equilibrium tracking error falls as amplifier gain increases")
    ax.loglog(gains, err_mv, color=COLORS["green"], lw=2.5)
    ax.axvline(100, color=COLORS["gold"], ls="--", label="A = 100")
    ax.set_xlabel("Amplifier gain A")
    ax.set_ylabel("Command tracking error (mV)")
    ax.grid(True, which="both", color="#e7eaf0")
    ax.legend()
    savefig(fig, out / "tevc_loop_error_vs_gain.png")

    fig, ax1 = fig_ax(10, 5.4)
    add_title(ax1, "TEVC Probe Outputs", "Vm, amplifier output, and clamp current probes")
    ax1.plot(t * 1000, vm * 1e3, color=COLORS["blue"], lw=2.3, label="Vm")
    ax1.plot(t * 1000, vout * 1e3, color=COLORS["gold"], lw=2.0, label="Amplifier output")
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Voltage (mV)")
    ax2 = ax1.twinx()
    ax2.plot(t * 1000, iclamp * 1e3, color=COLORS["red"], lw=2.0, label="Clamp current")
    ax2.set_ylabel("Current (mA)")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="lower right")
    ax1.grid(True, color="#e7eaf0")
    savefig(fig, out / "tevc_probe_outputs.png")

    rows = [
        ["Assumption", "Benchmark treatment", "Impact"],
        ["Passive membrane", "Explicit simplification", "Build-ready for equilibrium"],
        ["Membrane capacitance ignored", "Not a blocker", "No transient claim"],
        ["Ion channels omitted", "Scope limitation", "Not Hodgkin-Huxley"],
        ["Finite gain A=100", "Modeled", "Tracking error remains"],
        ["Electrode resistance", "Probed and discussed", "Affects loop error"],
    ]
    save_table_figure(out / "tevc_assumption_map.png", "TEVC Assumption Map", rows, width=11, height=5.2)


def mixed_signal_sim():
    dt = 2e-5
    t = np.arange(0, 0.09, dt)
    vc = np.where(t < 0.008, -65e-3, -45e-3)
    vm = np.zeros_like(t)
    vm[0] = -65e-3
    tau_m = 0.012
    gain = 1.8e-6
    i_limit = 1.8e-9
    rail = 1.2
    iclamp = np.zeros_like(t)
    vout = np.zeros_like(t)
    sat = np.zeros_like(t, dtype=bool)
    noise = 0.00045 * np.sin(2 * np.pi * 380 * t)
    for i in range(1, len(t)):
        err = vc[i - 1] - vm[i - 1]
        cmd_i = np.clip(gain * err, -i_limit, i_limit)
        iclamp[i] = cmd_i
        sat[i] = abs(cmd_i) >= 0.995 * i_limit
        dv = ((vc[i - 1] - vm[i - 1]) / tau_m + cmd_i / 180e-9) * dt
        vm[i] = vm[i - 1] + dv + 0.00002 * np.sin(2 * np.pi * 60 * t[i])
        vout[i] = np.clip(cmd_i / i_limit * rail, -rail, rail)
    vm_meas = vm + noise
    fs_adc = 2000
    sample_step = int(round(1 / (fs_adc * dt)))
    sample_idx = np.arange(0, len(t), sample_step)
    adc_min, adc_max = -0.10, 0.05
    codes = np.clip(np.round((vm_meas[sample_idx] - adc_min) / (adc_max - adc_min) * 4095), 0, 4095)
    states = np.zeros_like(sample_idx, dtype=int)
    for j, idx in enumerate(sample_idx):
        if t[idx] < 0.008:
            states[j] = 0
        elif sat[idx]:
            states[j] = 3
        elif abs(vm[idx] - vc[idx]) < 0.0015:
            states[j] = 4
        elif t[idx] < 0.012:
            states[j] = 1
        else:
            states[j] = 2
    return t, vc, vm, vm_meas, iclamp, vout, sat, sample_idx, codes, states


def create_mixed_plots() -> None:
    out = ASSET_DIR / "benchmark_03_mixed_signal_simscape/plots"
    t, vc, vm, vm_meas, iclamp, vout, sat, sample_idx, codes, states = mixed_signal_sim()
    ts_ms = t * 1000

    fig, axes = plt.subplots(5, 1, figsize=(11, 9), dpi=160, sharex=True)
    fig.patch.set_facecolor("white")
    fig.suptitle("Mixed-Signal Full Timeline\nIllustrative demo data, not a live Simscape run", fontsize=16, fontweight="bold", color=COLORS["ink"])
    axes[0].plot(ts_ms, vc * 1e3, color=COLORS["muted"], lw=1.8, label="Vc")
    axes[0].plot(ts_ms, vm * 1e3, color=COLORS["blue"], lw=2.0, label="Vm")
    axes[0].set_ylabel("mV")
    axes[0].legend(loc="right")
    axes[1].plot(ts_ms, vout, color=COLORS["gold"], lw=1.8)
    axes[1].axhline(1.2, color=COLORS["red"], ls="--", lw=1)
    axes[1].axhline(-1.2, color=COLORS["red"], ls="--", lw=1)
    axes[1].set_ylabel("Amp V")
    axes[2].plot(ts_ms, iclamp * 1e9, color=COLORS["green"], lw=1.8)
    axes[2].set_ylabel("Iclamp nA")
    axes[3].step(t[sample_idx] * 1000, codes, where="post", color=COLORS["purple"], lw=1.6)
    axes[3].set_ylabel("ADC code")
    axes[4].step(t[sample_idx] * 1000, states, where="post", color=COLORS["red"], lw=1.6)
    axes[4].set_yticks([0, 1, 2, 3, 4], ["idle", "acq", "clamp", "sat", "settled"])
    axes[4].set_xlabel("Time (ms)")
    for ax in axes:
        ax.grid(True, color="#e7eaf0")
    savefig(fig, out / "mixed_signal_full_timeline.png")

    fig, ax1 = fig_ax(10, 5.5)
    add_title(ax1, "Membrane Voltage and Clamp Current", "Illustrative physical/digital co-simulation surrogate")
    ax1.plot(ts_ms, vm * 1e3, color=COLORS["blue"], lw=2.4, label="Vm")
    ax1.plot(ts_ms, vc * 1e3, color=COLORS["muted"], lw=1.5, ls="--", label="Vc")
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Voltage (mV)")
    ax2 = ax1.twinx()
    ax2.plot(ts_ms, iclamp * 1e9, color=COLORS["green"], lw=1.8, label="Clamp current")
    ax2.set_ylabel("Current (nA)")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="lower right")
    ax1.grid(True, color="#e7eaf0")
    savefig(fig, out / "membrane_voltage_and_clamp_current.png")

    fig, ax = fig_ax(10, 5.2)
    add_title(ax, "Amplifier Saturation", "Illustrative rail-limit and current-limit intervals")
    ax.plot(ts_ms, vout, color=COLORS["gold"], lw=2.2, label="Amplifier output")
    ax.axhline(1.2, color=COLORS["red"], ls="--", label="Rails")
    ax.axhline(-1.2, color=COLORS["red"], ls="--")
    ax.fill_between(ts_ms, -1.25, 1.25, where=sat, color=COLORS["red"], alpha=0.16, label="Current-limit saturation")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplifier output (V)")
    ax.grid(True, color="#e7eaf0")
    ax.legend()
    savefig(fig, out / "amplifier_saturation.png")

    fig, ax1 = fig_ax(10, 5.2)
    add_title(ax1, "ADC Codes and Digital Logic", "Illustrative sampled quantization and state trace")
    ax1.step(t[sample_idx] * 1000, codes, where="post", color=COLORS["purple"], lw=2, label="ADC code")
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("12-bit ADC code")
    ax2 = ax1.twinx()
    ax2.step(t[sample_idx] * 1000, states, where="post", color=COLORS["red"], lw=1.8, label="State")
    ax2.set_yticks([0, 1, 2, 3, 4], ["idle", "acquire", "clamp", "saturated", "settled"])
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="lower right")
    ax1.grid(True, color="#e7eaf0")
    savefig(fig, out / "adc_codes_and_digital_logic.png")

    fig, ax = fig_ax(10, 4.8)
    add_title(ax, "Digital State Machine Trace", "Illustrative state transitions")
    ax.step(t[sample_idx] * 1000, states, where="post", color=COLORS["red"], lw=2.4)
    ax.set_yticks([0, 1, 2, 3, 4], ["idle", "acquire", "clamp", "saturated", "settled"])
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("State")
    ax.grid(True, color="#e7eaf0")
    savefig(fig, out / "digital_state_machine_trace.png")

    gains = np.logspace(1.4, 3.8, 36)
    re_vals = np.linspace(1, 50, 32)
    heat = np.zeros((len(re_vals), len(gains)))
    for i, re in enumerate(re_vals):
        for j, g in enumerate(gains):
            heat[i, j] = 1000 * (0.8 / np.log10(g + 10) + 0.015 * re + 0.2 * np.exp(-g / 2000))
    fig, ax = fig_ax(9.5, 5.7)
    add_title(ax, "Parameter Sweep Heatmap", "Illustrative settling error map; rerun in Simscape for final evidence")
    im = ax.imshow(heat, origin="lower", aspect="auto", extent=[gains[0], gains[-1], re_vals[0], re_vals[-1]], cmap="viridis")
    ax.set_xscale("log")
    ax.set_xlabel("Amplifier gain")
    ax.set_ylabel("Electrode resistance (Ohm)")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Settling error proxy (mV)")
    savefig(fig, out / "parameter_sweep_heatmap.png")

    rows = [
        ["Fault", "Expected effect", "Status"],
        ["Wrong membrane capacitance", "Settling time shifts", "WARN"],
        ["Low ADC rate", "Misses transient and aliases", "FAIL"],
        ["High electrode resistance", "More tracking error", "WARN"],
        ["Amplifier current limit", "Longer saturation interval", "WARN"],
        ["Wrong units", "Large time-constant error", "FAIL"],
        ["Noisy measurement", "Comparator chatter risk", "WARN"],
    ]
    save_table_figure(out / "fault_injection_summary.png", "Fault Injection Summary", rows, width=11, height=5.2)

    rows = [
        ["Evidence item", "LLM-only", "CiTT + Simscape"],
        ["Executable model", "No", "Yes when live run completes"],
        ["Transient dynamics", "May invent", "Simulated"],
        ["Saturation timing", "Fragile", "Measured from trace"],
        ["ADC code sequence", "Usually guessed", "Logged signal"],
        ["Probe/highlight evidence", "No", "Model-grounded"],
        ["Limitations exposed", "Often implicit", "Run notes + checks"],
    ]
    save_table_figure(out / "simscape_vs_llm_impossibility.png", "Why Benchmark 3 Needs Simulation", rows, width=11, height=5.4)


def save_table_figure(path: Path, title: str, rows, width: float = 10, height: float = 4.8) -> None:
    fig, ax = fig_ax(width, height)
    ax.axis("off")
    add_title(ax, title)
    table = ax.table(cellText=rows[1:], colLabels=rows[0], cellLoc="left", colLoc="left", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.55)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#dce2eb")
        if row == 0:
            cell.set_facecolor("#eef3fb")
            cell.set_text_props(weight="bold", color=COLORS["ink"])
        elif col == len(rows[0]) - 1:
            text = cell.get_text().get_text().upper()
            if "PASS" in text:
                cell.set_facecolor("#eaf7ef")
            elif "FAIL" in text:
                cell.set_facecolor("#fdecec")
            elif "WARN" in text:
                cell.set_facecolor("#fff7e6")
    savefig(fig, path)


def create_screenshot_panels() -> None:
    app_pages = [
        ("app_read.png", "Read", "Parsed circuit summary, structured spec status, and next build step"),
        ("app_build.png", "Build", "SATK task prepared, model generation status, manual arrangement pause"),
        ("app_teach.png", "Teach", "Socratic prompt with LaTeX explanation and focus action"),
        ("app_probe.png", "Probe", "Guided probes for Vout, Vm, clamp current, ADC code"),
        ("app_evidence.png", "Evidence", "Requirement checks, sweeps, Lab Delta, export status"),
    ]
    for file_name, tab, detail in app_pages:
        screenshot_panel(ASSET_DIR / "screenshots" / file_name, f"CiTT App: {tab}", detail)

    screenshot_panel(
        ASSET_DIR / "benchmark_01_textbook_rc/model_screenshot.png",
        "RC Simscape Model Screenshot",
        "Live model capture pending. Expected blocks: source, R, C, electrical reference, solver, voltage sensor, ADC sample path.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_01_textbook_rc/teach_highlight.png",
        "RC Teach Highlight",
        "Offline panel. Live highlight should mark cutoff math, Vout node, and Nyquist warning.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_01_textbook_rc/probe_screenshot.png",
        "RC Probe Screenshot",
        "Offline panel. Probe target: Vout node between resistor and capacitor.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_01_textbook_rc/lab_delta_screenshot.png",
        "RC Lab Delta Screenshot",
        "Offline panel. Lab Delta compares 100 nF expected behavior to 100 uF unit mistake.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_02_tevc_equilibrium/model_screenshot.png",
        "TEVC Simscape Model Screenshot",
        "Live model capture pending. Expected blocks: command source, differential amplifier, electrode/membrane network, probes.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_02_tevc_equilibrium/feedback_highlight.png",
        "TEVC Feedback Highlight",
        "Offline panel. Live highlight should trace Vc -> amplifier -> membrane Vm -> voltage electrode feedback.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_02_tevc_equilibrium/probe_screenshot.png",
        "TEVC Probe Screenshot",
        "Offline panel. Probe targets: Vm, amplifier output, clamp current.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_03_mixed_signal_simscape/model_screenshot.png",
        "Mixed-Signal Simscape/Simulink Model Screenshot",
        "Live capture pending. Expected view: physical membrane/electrode/amplifier plus ADC and digital logic.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_03_mixed_signal_simscape/highlight_feedback_or_signal_path.png",
        "Mixed-Signal Feedback or Signal Path Highlight",
        "Offline panel. Live highlight should show command, clamp current, membrane node, ADC, digital control, and DAC update.",
    )
    screenshot_panel(
        ASSET_DIR / "benchmark_03_mixed_signal_simscape/probe_screenshot.png",
        "Mixed-Signal Probe Screenshot",
        "Offline panel. Probe targets: Vm, clamp current, amplifier output, ADC code, digital state, saturation flag.",
    )


def screenshot_panel(path: Path, title: str, detail: str) -> None:
    fig, ax = fig_ax(11, 6.2)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.add_patch(Rectangle((0.15, 0.15), 10.7, 5.7, facecolor="#f4f7fb", edgecolor="#cbd5e1", lw=1.4))
    ax.add_patch(Rectangle((0.15, 5.25), 10.7, 0.6, facecolor="#182235", edgecolor="#182235"))
    ax.text(0.45, 5.55, "CiTT MATLAB Evidence Capture", color="white", fontsize=12, fontweight="bold", va="center")
    ax.text(10.5, 5.55, "OFFLINE PANEL", color="#facc15", fontsize=10, va="center", ha="right", fontweight="bold")
    tabs = ["Read", "Build", "Teach", "Probe", "Evidence"]
    for i, tab in enumerate(tabs):
        x = 0.45 + i * 1.05
        fc = "#e7eef8" if tab.lower() in title.lower() else "white"
        ax.add_patch(Rectangle((x, 4.75), 0.88, 0.34, facecolor=fc, edgecolor="#cbd5e1"))
        ax.text(x + 0.44, 4.92, tab, ha="center", va="center", fontsize=7.5, color=COLORS["ink"])
    draw_box(ax, (0.65, 3.0), (3.0, 1.2), title, fc="white", ec=COLORS["blue"], fontsize=11)
    draw_box(ax, (4.15, 3.0), (2.4, 1.2), "Structured spec\nfocus map\nprobe map", fc="#f2fbf5", ec=COLORS["green"], fontsize=10)
    draw_box(ax, (7.0, 3.0), (2.9, 1.2), "Exported evidence\nplots and report", fc="#fff7e8", ec=COLORS["gold"], fontsize=10)
    draw_arrow(ax, (3.65, 3.6), (4.15, 3.6), COLORS["blue"])
    draw_arrow(ax, (6.55, 3.6), (7.0, 3.6), COLORS["green"])
    wrapped = textwrap.fill(detail, 98)
    ax.text(0.75, 2.25, wrapped, fontsize=10, color=COLORS["ink"], va="top")
    provenance = textwrap.fill(
        "Provenance: generated offline because live Simscape/SATK capture was not completed in this run. "
        "Regenerate from MATLAB after the manual arrangement pause for final BMES upload.",
        92,
    )
    ax.text(0.75, 0.95, provenance, fontsize=8.4, color=COLORS["red"], va="top", linespacing=1.25)
    savefig(fig, path)


def benchmark_specs() -> dict[str, dict]:
    return {
        "benchmark_01_textbook_rc": {
            "benchmark": "textbook_rc_anti_aliasing",
            "title": BENCHMARKS["benchmark_01_textbook_rc"]["title"],
            "source": "offline programmatic equivalent; Gemini parse not run in this environment",
            "components": [
                {"id": "vin", "type": "voltage_source", "signals": ["5 Hz ECG-like", "60 Hz interference", "optional high-frequency noise"]},
                {"id": "R1", "type": "resistor", "value": 39.8, "unit": "kOhm"},
                {"id": "C1", "type": "capacitor", "value": 100, "unit": "nF"},
                {"id": "ADC1", "type": "adc", "sample_rate_hz": 500},
            ],
            "nodes": ["input", "vout", "ground", "adc_samples"],
            "focus_map": ["cutoff_frequency", "vout_probe_node", "nyquist_warning", "unit_mistake_delta"],
            "probe_map": ["Vout after R1 before C1", "ADC sampled output"],
            "requirements": {"fc_hz_expected": 39.99, "nyquist_hz": 250, "single_pole_alias_free": False},
            "limitations": ["Offline analytical package only; live Simscape model evidence pending."],
        },
        "benchmark_02_tevc_equilibrium": {
            "benchmark": "tevc_equilibrium_feedback",
            "title": BENCHMARKS["benchmark_02_tevc_equilibrium"]["title"],
            "source": "offline programmatic equivalent; Gemini parse not run in this environment",
            "components": [
                {"id": "Vc", "type": "command_voltage"},
                {"id": "buffer", "type": "ideal_buffer"},
                {"id": "amp", "type": "finite_gain_differential_amplifier", "gain": 100},
                {"id": "Rm", "type": "membrane_resistance", "value": 10, "unit": "Ohm"},
                {"id": "Ro", "type": "output_electrode_resistance", "value": 10, "unit": "Ohm"},
                {"id": "Re", "type": "voltage_electrode_resistance", "value": "symbolic"},
            ],
            "assumptions": ["equilibrium", "passive membrane", "capacitance ignored", "ion-channel dynamics out of scope"],
            "focus_map": ["feedback_loop", "membrane_node", "finite_gain_error", "electrode_resistance_assumption"],
            "probe_map": ["Vm", "amplifier output", "clamp current"],
            "limitations": ["Educational equilibrium model, not a full Hodgkin-Huxley or clinical verification model."],
        },
        "benchmark_03_mixed_signal_simscape": {
            "benchmark": "mixed_signal_neural_clamp",
            "title": BENCHMARKS["benchmark_03_mixed_signal_simscape"]["title"],
            "source": "offline illustrative surrogate; live Simscape/Simulink model evidence pending",
            "components": [
                {"id": "membrane", "type": "simscape_electrical_membrane", "parameters": ["Cm", "Rm", "leak current"]},
                {"id": "electrode", "type": "series_resistance"},
                {"id": "amplifier", "type": "finite_gain_nonideal", "features": ["rail saturation", "current limit"]},
                {"id": "adc", "type": "sample_and_quantize", "bits": 12},
                {"id": "logic", "type": "digital_state_control", "states": ["idle", "acquire", "clamp", "saturated", "settled"]},
            ],
            "focus_map": [
                "command_path",
                "membrane_node",
                "feedback_loop",
                "amplifier_saturation",
                "adc_sampling",
                "digital_control_logic",
                "clamp_current_probe",
            ],
            "probe_map": ["Vm(t)", "clamp current", "amplifier output", "ADC code sequence", "digital control state", "saturation flags"],
            "limitations": ["Plots are illustrative until regenerated from a live Simscape/Simulink run."],
        },
    }


def write_benchmark_files() -> None:
    specs = benchmark_specs()
    for folder, spec in specs.items():
        root = ASSET_DIR / folder
        write_json(root / "citt_spec.json", spec)
        write_json(root / "focus_map.json", {"focus_points": spec["focus_map"], "source": spec["source"]})
        write_json(root / "probe_map.json", {"probes": spec["probe_map"], "source": spec["source"]})
        write_text(root / "citt_agent_task.md", agent_task(folder, spec))
        write_text(root / "citt_run_notes.md", run_notes(folder, spec))
        write_text(root / "problem_statement.md", problem_statement(folder))
        write_text(root / "llm_baseline_prompt.md", baseline_prompt(folder))
        write_text(root / "llm_baseline_output.md", baseline_output())
        write_text(root / "comparison.md", comparison_md(folder))


def agent_task(folder: str, spec: dict) -> str:
    focus = "\n".join([f"- {item}" for item in spec["focus_map"]])
    probes = "\n".join([f"- {item}" for item in spec["probe_map"]])
    return f"""
    # CiTT SATK Agent Task: {spec['title']}

    Build a Simscape/Simulink teaching model for `{spec['benchmark']}` using the structured spec in `citt_spec.json`.

    Required focus points:
    {focus}

    Required probes:
    {probes}

    After model generation, open the model visibly in Simulink and print this exact pause:

    ```text
    PAUSE FOR MANUAL SIMSCAPE ARRANGEMENT

    Please manually drag, reposition, and clean up the Simscape/Simulink blocks now.
    Arrange the model so screenshots clearly show:
    - signal flow,
    - feedback loops,
    - probes,
    - sensors,
    - ADC / digital logic,
    - important Simscape physical components,
    - source, reference, solver configuration, and output paths.

    When done, save the model and press Enter in the MATLAB command window to continue.
    ```

    Then wait with:

    ```matlab
    input("Arrange the Simscape model, save it, then press Enter to continue: ", "s");
    ```

    Capture the model screenshot only after the pause. If MATLAB is headless or SATK/Simscape is unavailable, record `manual_arrangement = "skipped-headless"` in `citt_run_notes.md` and continue with offline plots and report generation.
    """


def run_notes(folder: str, spec: dict) -> str:
    return f"""
    # CiTT Run Notes: {spec['title']}

    manual_arrangement: skipped-headless
    arranged_by: user
    timestamp: {TIMESTAMP}
    notes: Offline evidence package generated because live SATK/Simscape model generation was not completed in this run. Screenshot PNGs in this folder are clearly labeled offline panels and should be replaced by live MATLAB/Simulink captures after local setup.

    Environment observations:
    - Existing MATLAB wrapper initially failed because `citt_submission_generate` was missing.
    - Shell `matlab` was not on PATH, but MATLAB MCP tooling was available.
    - `.satk/reuse-libraries.json`, `.satk/block-policy.json`, and `.satk/library-kg/index.md` were not present in the repository, so live SATK structural editing was not treated as proven.
    - MATLAB CiTT `checkSetup` reported Gemini/SATK/MCP/Codex agent readiness, but a verified pure no-tool LLM baseline invocation was not executed.
    - Baseline prompts were prepared for manual execution.

    Provenance:
    - `citt_spec.json` is a programmatic/offline equivalent of the structured circuit spec.
    - Plots are analytical for RC and TEVC; mixed-signal plots are explicitly illustrative surrogate data pending live Simscape/Simulink regeneration.
    """


def problem_statement(folder: str) -> str:
    if folder == "benchmark_01_textbook_rc":
        return """
        # Textbook RC Anti-Aliasing Filter Before an ADC

        An ECG acquisition front end uses a first-order RC low-pass filter before a 500 Hz ADC. The circuit uses R = 39.8 kOhm and C = 100 nF. The input contains a 5 Hz ECG-like component, 60 Hz interference, and optional high-frequency noise.

        Tasks:
        1. Compute the cutoff frequency.
        2. Compute attenuation at 60 Hz.
        3. Compute attenuation at the Nyquist frequency.
        4. Explain whether a single-pole RC filter is sufficient for anti-aliasing.
        5. Identify where the output voltage should be probed in a Simscape/Simulink model.
        6. Diagnose a lab mistake where the student accidentally used 100 uF instead of 100 nF.

        Expected concepts: fc = 1/(2*pi*R*C) is about 40 Hz. Nyquist is 250 Hz. A single-pole RC filter helps, but does not prove alias-free sampling.
        """
    if folder == "benchmark_02_tevc_equilibrium":
        return """
        # Two-Electrode Voltage Clamp Equivalent Circuit

        A simplified two-electrode voltage clamp circuit measures and controls axon membrane voltage Vm. The diagram includes command voltage Vc, an ideal buffer, finite-gain differential amplifier A = 100, membrane resistance Rm = 10 Ohm, output/electrode resistance Ro = 10 Ohm, voltage electrode resistance Re, and requested output Vm.

        At equilibrium, membrane capacitance and ion-channel dynamics are ignored. The teaching goal is to explain the feedback loop and how Vm is driven toward Vc.

        Tasks:
        1. Parse the diagram as a simplified equilibrium electrical equivalent.
        2. Do not mark omitted biological dynamics as build blockers.
        3. Build or prepare a Simscape-first model.
        4. Highlight the feedback loop.
        5. Probe Vm, amplifier output, and clamp current.
        6. Explain how finite gain and electrode resistance affect tracking error.
        """
    return """
    # Closed-Loop Neural Clamp With Nonideal Amplifier, ADC, and Digital Control Logic

    Model a closed-loop neural clamp system with membrane capacitance Cm, membrane leakage resistance Rm, optional simplified nonlinear membrane current, electrode series resistance, finite-gain amplifier, output current limit, rail saturation, command voltage step Vc(t), ADC sampling and quantization of Vm, digital comparator or finite-state control logic, DAC or command update path, and requested outputs Vm(t), clamp current, amplifier output, ADC code sequence, digital control state, saturation flags, settling time, and overshoot.

    This problem is intentionally too complex for reliable LLM-only closed-form solving. It requires simulation.
    """


def baseline_prompt(folder: str) -> str:
    if folder == "benchmark_01_textbook_rc":
        return """
        Solve and explain this problem without using Simscape, SATK, code execution, or external tools.

        An ECG acquisition front end uses a first-order RC low-pass filter before a 500 Hz ADC. R = 39.8 kOhm and C = 100 nF. The input includes a 5 Hz ECG-like component, 60 Hz interference, and optional high-frequency noise.

        Compute the cutoff frequency, attenuation at 60 Hz, attenuation at the Nyquist frequency, whether the single-pole filter is sufficient for anti-aliasing, where Vout should be probed, and diagnose the mistake of using 100 uF instead of 100 nF.
        """
    if folder == "benchmark_02_tevc_equilibrium":
        return """
        Solve and explain this circuit without using Simscape, SATK, code execution, or external tools.

        A simplified two-electrode voltage clamp equivalent circuit has command voltage Vc, an ideal buffer, finite-gain differential amplifier A = 100, membrane resistance Rm = 10 Ohm, output/electrode resistance Ro = 10 Ohm, voltage electrode resistance Re, and requested output Vm. At equilibrium, membrane capacitance and ion-channel dynamics are ignored.

        Explain the feedback loop, decide whether omitted membrane dynamics prevent modeling, identify probes for Vm, amplifier output, and clamp current, and explain how finite gain and electrode resistance affect tracking error.
        """
    return """
    Solve and explain this problem without using Simscape, SATK, code execution, simulation, or external tools.

    A closed-loop neural clamp includes membrane capacitance, membrane leakage resistance, optional nonlinear membrane current, electrode series resistance, finite-gain amplifier, current limit, rail saturation, command voltage step Vc(t), ADC sampling and quantization of Vm, digital comparator/state logic, DAC or command update path, and requested outputs Vm(t), clamp current, amplifier output, ADC code sequence, digital control state, saturation flags, settling time, and overshoot.

    Compute Vm(t), clamp current, ADC code sequence, saturation intervals, settling time, and explain the feedback loop. State any assumptions.
    """


def baseline_output() -> str:
    return """
    Not run in this environment. Prompt prepared for manual baseline run.

    Reason: a verified pure no-tool baseline invocation was not executed in this run. MATLAB CiTT setup reported a Gemini key in its local configuration, but the shell environment did not expose that key and the available Codex/Gemini CLIs are agentic workspace CLIs unless carefully constrained. No LLM output or failure was fabricated.
    """


def comparison_md(folder: str) -> str:
    if folder == "benchmark_01_textbook_rc":
        return """
        # Comparison: RC Anti-Aliasing Filter

        A pure LLM can often compute the cutoff, but common fragile points are 2*pi mistakes, kOhm/nF conversion errors, and overclaiming that one pole proves alias-free sampling.

        CiTT adds a structured spec, explicit Vout probe placement, Bode/time/alias plots, a Lab Delta view for the 100 uF unit mistake, and requirement status. In this run, those artifacts are generated offline and should be replaced with live Simscape screenshots after MATLAB/SATK setup.
        """
    if folder == "benchmark_02_tevc_equilibrium":
        return """
        # Comparison: TEVC Equilibrium Feedback

        A pure LLM may produce fluent but ungrounded feedback explanations or treat omitted membrane capacitance/ion-channel dynamics as either irrelevant or fatal without exposing the assumption.

        CiTT represents the equilibrium simplification explicitly, connects the feedback path to model focus points, identifies Vm/amplifier/clamp-current probes, and records biological omissions as limitations rather than build blockers. Live Simscape evidence remains pending in this run.
        """
    return """
    # Comparison: Mixed-Signal Neural Clamp

        LLM-only text is not enough for this benchmark. The requested outputs depend on transient dynamics, saturation timing, ADC quantization, digital state transitions, parameter sweeps, and fault injection.

        CiTT is designed to use Simscape/Simulink as executable evidence, then teach from highlights and probes. The figures here are clearly labeled illustrative surrogate data; final BMES proof should be regenerated from the live model after manual Simscape arrangement.
        """


def write_scorecards() -> None:
    rows = score_rows()
    fieldnames = list(rows[0].keys())
    with (ASSET_DIR / "benchmark_scorecard.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    md = ["# Benchmark Scorecard", "", "Scores are honest for the current offline package. LLM-only baselines are pending because no verified pure no-tool baseline invocation was executed. CiTT scores should be updated after live Simscape/SATK screenshots and simulations are regenerated.", ""]
    md.append("| Benchmark | System | Status | Topology | Numerical | Units | Executable | Teaching | Limits | Total |")
    md.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        md.append(
            f"| {r['benchmark']} | {r['system']} | {r['status']} | {r['topology_model_understanding']} | "
            f"{r['numerical_simulation_correctness']} | {r['unit_sign_reference_correctness']} | {r['executable_model_evidence']} | "
            f"{r['teaching_usefulness']} | {r['honest_assumptions_limitations']} | {r['total']} |"
        )
    write_text(ASSET_DIR / "benchmark_scorecard.md", "\n".join(md))


def write_readme_summary_report() -> None:
    write_text(
        ASSET_DIR / "README.md",
        """
        # CiTT BMES/Medtronic Submission Evidence Package

        This directory contains a benchmark evidence package for CiTT: a model-grounded AI tutor for biomedical circuit simulation.

        Contents:
        - `figures/`: architecture, workflow, score, and BMES-alignment visuals.
        - `screenshots/`: offline CiTT app evidence panels. Replace with live MATLAB app screenshots before final submission when possible.
        - `benchmark_01_textbook_rc/`: textbook RC anti-aliasing benchmark.
        - `benchmark_02_tevc_equilibrium/`: simplified TEVC equilibrium feedback benchmark.
        - `benchmark_03_mixed_signal_simscape/`: mixed physical/digital neural clamp benchmark.
        - `benchmark_scorecard.csv` and `.md`: honest current scoring.
        - `bmes_evidence_report.md` and `.pdf`: submission-facing report.
        - `scripts/`: MATLAB wrappers plus the offline generator used in this environment.

        Required live environment for the full CiTT evidence run:
        - MATLAB
        - Simulink
        - Simscape
        - Simscape Electrical preferred
        - Simulink Agentic Toolkit initialized with SATK policy/library gates
        - MATLAB MCP Server
        - Gemini API key for circuit parsing
        - SATK-configured agent CLI via `CITT_AGENT_COMMAND`, Codex CLI, or Gemini CLI

        Reproduce offline package:

        ```bash
        python3 vericircuit-tutor/submission_assets/scripts/generate_offline_assets.py --mode all
        ```

        Reproduce from MATLAB:

        ```matlab
        run("vericircuit-tutor/submission_assets/scripts/run_all_benchmarks.m")
        ```

        Manual Simscape arrangement pause:
        After live model generation, the MATLAB workflow must open the model and pause with the required `PAUSE FOR MANUAL SIMSCAPE ARRANGEMENT` message. The user should drag and clean up the diagram, save it, then press Enter. Screenshots should be captured only after that pause.

        Provenance in this run:
        - RC and TEVC plots are analytical/offline.
        - Mixed-signal plots are illustrative surrogate data and explicitly labeled.
        - App/model screenshot PNGs are offline panels, not live MATLAB screenshots.
        - LLM baseline prompts are prepared, but baseline outputs are manual-pending because no pure no-tool baseline invocation was executed.
        """,
    )

    write_text(
        ASSET_DIR / "benchmark_run_log.md",
        """
        # Benchmark Run Log

        Timestamp: 2026-06-22T00:00:00+08:00

        Actions:
        - Read the benchmark-generation request.
        - Ran `git status --short`.
        - Inspected existing `submission_assets/scripts`.
        - Found five wrapper scripts pointing to missing `citt_submission_generate`.
        - Reproduced the wrapper failure through MATLAB MCP: `Unrecognized function or variable 'citt_submission_generate'`.
        - Added `generate_offline_assets.py`, `citt_submission_generate.m`, and missing capture wrappers.
        - Generated problem images, plots, scorecards, reports, and offline screenshot panels.
        - Updated repository ignore rules for Simulink caches and compiled artifacts.

        Practical bugs encountered and fixed:
        - Missing generator function for existing MATLAB wrappers. Fixed by adding `scripts/citt_submission_generate.m` and the Python offline generator it delegates to.
        - Missing requested capture scripts. Fixed by adding `capture_app_screenshots.m` and `capture_model_screenshots.m`.

        Limitations:
        - Live SATK model generation was not treated as complete because `.satk/reuse-libraries.json`, `.satk/block-policy.json`, and `.satk/library-kg/index.md` were absent.
        - Shell `matlab` was not on PATH; MATLAB MCP was available.
        - MATLAB CiTT `checkSetup` reported MATLAB, Simulink, Simscape, Simscape Electrical, MATLAB MCP, SATK, Gemini key, and Codex agent command as available.
        - A verified pure no-tool LLM baseline invocation was not executed.
        - Offline screenshot panels are placeholders for live MATLAB/Simulink screenshots.
        """,
    )

    write_text(
        ASSET_DIR / "benchmark_summary.md",
        """
        # Benchmark Summary

        This package contains three benchmark cases intended to show why CiTT should be judged as a model-grounded biomedical circuit tutor rather than an LLM-only answer generator.

        1. RC anti-aliasing: shows a textbook calculation with cutoff, attenuation, Nyquist warning, probe location, and Lab Delta for a capacitor unit mistake.
        2. TEVC equilibrium feedback: shows BME relevance, feedback-loop explainability, probes, and explicit treatment of biological simplifications as assumptions.
        3. Mixed-signal neural clamp: shows why transient behavior, amplifier saturation, ADC quantization, digital state logic, parameter sweeps, and fault injection require simulation.

        Current run status:
        - Analytical/offline plots were generated for benchmarks 1 and 2.
        - Illustrative surrogate plots were generated for benchmark 3 and labeled accordingly.
        - Live Simscape/SATK model screenshots and simulations remain pending.
        - LLM-only baselines remain manual-pending.
        """,
    )

    report = bmes_report_text()
    write_text(ASSET_DIR / "bmes_evidence_report.md", report)
    write_pdf_report(report)


def bmes_report_text() -> str:
    return """
    # CiTT: Model-Grounded AI Tutor for Biomedical Circuit Simulation

    CiTT turns a circuit diagram or prompt into a structured circuit spec, prepares a Simulink/Simscape build task, and teaches on top of the model using Socratic reasoning, highlight/zoom, probes, Lab Delta, requirement checks, sweeps, fault injection, and exported evidence.

    ## Why LLM-only tutoring is insufficient

    LLM-only circuit tutoring can hallucinate signs, units, topologies, and transient behavior. It does not produce an executable model, cannot prove probe/highlight evidence, and is especially fragile on simulation-only systems with saturation, sampled ADC behavior, and digital state logic.

    ## What CiTT does

    CiTT connects circuit image or prompt input to a Gemini structured spec, SATK/Simscape model generation, Socratic teaching, highlight/zoom actions, probes, Lab Delta comparison, requirement checks, and evidence export.

    ## Benchmark overview

    Benchmark 1 is a textbook RC anti-aliasing filter before a 500 Hz ADC. It demonstrates correct cutoff and attenuation reasoning, probe placement, and a 100 nF versus 100 uF Lab Delta.

    Benchmark 2 is a simplified two-electrode voltage clamp equilibrium feedback circuit. It demonstrates BME relevance, feedback-loop explainability, and honest scope control for omitted biological dynamics.

    Benchmark 3 is a closed-loop neural clamp with physical membrane/electrode behavior, nonideal amplifier limits, ADC quantization, and digital state control. It is intentionally beyond reliable closed-form LLM-only solving.

    ## Scorecard

    The current scorecard is honest for this offline package. LLM-only baselines are pending. CiTT scores are partial because live Simscape/SATK model screenshots and simulations still need to be regenerated.

    See `benchmark_scorecard.md` and `benchmark_scorecard.csv`.

    ## What Simscape contributes

    Simscape contributes physical component modeling, executable simulation, mixed physical/digital co-simulation, transient behavior, parameter sweeps, fault injection, and model-grounded probe/highlight evidence. This is the core difference between CiTT and a text-only tutor.

    ## Technical feasibility

    This run created the full evidence package structure, structured specs, agent tasks, analytical/offline plots, illustrative mixed-signal plots, scorecards, run notes, and a report. Full technical proof still depends on local MATLAB, Simulink, Simscape, Simscape Electrical, Simulink Agentic Toolkit, MATLAB MCP Server, Gemini, and a configured agent CLI.

    ## Limitations

    CiTT requires MATLAB/Simulink/Simscape/SATK/Gemini for the live workflow. Image parsing can be ambiguous. The package is educational evidence, not clinical verification. Complex Simscape diagrams may require human layout cleanup. Live agent reliability depends on local setup. In this run, screenshots are offline panels and mixed-signal traces are illustrative surrogate data.

    ## Mapping to BMES judging criteria

    Product need and market potential: biomedical circuit learning and debugging need model-grounded tutoring.

    Device utility and novelty: CiTT links circuit parsing, executable modeling, Socratic teaching, probes, Lab Delta, and exportable evidence.

    Technical feasibility: the package defines reproducible scripts and benchmark artifacts, with clear dependency limits for the live model run.

    Budget/economic plan: the report identifies required software/services and dependency constraints.

    Writing and presentation clarity: each benchmark includes problem statements, specs, prompts, comparisons, plots, run notes, and a scorecard.

    Device performance: benchmark artifacts target correctness, model evidence, teaching usefulness, and limitations.

    Limitations: external tools, image ambiguity, educational scope, and manual layout cleanup are explicitly documented.

    ## Prototype files list

    - `figures/overview_architecture.png`
    - `figures/llm_vs_citt_workflow.png`
    - `figures/comparison_score_bars.png`
    - `figures/comparison_score_radar.png`
    - `figures/bmes_judging_alignment.png`
    - `screenshots/app_read.png`
    - `screenshots/app_build.png`
    - `screenshots/app_teach.png`
    - `screenshots/app_probe.png`
    - `screenshots/app_evidence.png`
    - benchmark folders with problem statements, specs, agent tasks, plots, comparison notes, focus maps, and probe maps.
    """


def write_pdf_report(report: str) -> None:
    path = ASSET_DIR / "bmes_evidence_report.pdf"
    paragraphs = [p.strip() for p in report.split("\n\n") if p.strip()]
    with PdfPages(path) as pdf:
        page_lines = []
        for paragraph in paragraphs:
            wrapped = textwrap.wrap(paragraph.replace("#", "").strip(), width=92)
            if len(page_lines) + len(wrapped) + 1 > 34:
                write_pdf_page(pdf, page_lines)
                page_lines = []
            page_lines.extend(wrapped)
            page_lines.append("")
        if page_lines:
            write_pdf_page(pdf, page_lines)
        for image in [
            ASSET_DIR / "figures/overview_architecture.png",
            ASSET_DIR / "figures/llm_vs_citt_workflow.png",
            ASSET_DIR / "figures/comparison_score_bars.png",
            ASSET_DIR / "benchmark_03_mixed_signal_simscape/plots/mixed_signal_full_timeline.png",
        ]:
            if image.exists():
                fig, ax = fig_ax(11, 8)
                ax.axis("off")
                img = plt.imread(image)
                ax.imshow(img)
                ax.set_title(image.name, fontsize=13, fontweight="bold", color=COLORS["ink"])
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)


def write_pdf_page(pdf: PdfPages, lines: list[str]) -> None:
    fig, ax = fig_ax(8.5, 11)
    ax.axis("off")
    y = 0.96
    for line in lines:
        ax.text(0.06, y, line, transform=ax.transAxes, ha="left", va="top", fontsize=9, color=COLORS["ink"])
        y -= 0.026
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def create_all_figures() -> None:
    create_top_figures()
    create_rc_plots()
    create_tevc_plots()
    create_mixed_plots()


def run(mode: str) -> None:
    ensure_dirs()
    mode = mode.lower()
    if mode in {"all", "images"}:
        create_problem_images()
    if mode in {"all", "figures"}:
        create_all_figures()
    if mode in {"all", "screenshots", "app_screenshots", "model_screenshots"}:
        create_screenshot_panels()
    if mode in {"all", "baseline"}:
        write_benchmark_files()
    if mode in {"all", "report"}:
        write_benchmark_files()
        write_scorecards()
        write_readme_summary_report()
    if mode not in {"all", "images", "figures", "screenshots", "app_screenshots", "model_screenshots", "baseline", "report"}:
        raise SystemExit(f"Unknown mode: {mode}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="all")
    args = parser.parse_args()
    run(args.mode)
    print(f"Generated CiTT submission assets in {ASSET_DIR}")


if __name__ == "__main__":
    main()
