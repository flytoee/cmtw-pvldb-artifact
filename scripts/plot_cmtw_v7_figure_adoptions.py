"""CMTW-v7 figure adoption: frozen source-data only; no experiment execution.

Adopts Kimi's Fig. 4 visual grammar (without an enclosing panel-a frame) and
Kimi's Fig. 5a factorial grammar, while preserving the reviewed v6 Fig. 5b
exact-support silhouette.  All outputs are vector PDF/SVG plus inspection
raster copies; no JSON results are written or changed.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "figure-source-data"
OUT = ROOT / "reproduced" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
MM = 1 / 25.4

TEAL = "#168A8A"
RED = "#C94C4C"
AMBER = "#D79A2B"
SLATE = "#5B6770"
GREY = "#C7CDD1"
INK = "#1F2933"
GRID = "#D9E1E8"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans", "Liberation Sans"],
    "font.size": 7,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
    "axes.linewidth": 0.6,
    "legend.frameon": False,
})


def export(fig: plt.Figure, stem: str) -> None:
    base = OUT / stem
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(base.with_suffix(".tiff"), bbox_inches="tight", pad_inches=0.02, dpi=600)
    fig.savefig(base.with_suffix(".png"), bbox_inches="tight", pad_inches=0.02, dpi=300)
    plt.close(fig)


def panel(ax, label: str) -> None:
    ax.text(-0.10, 1.035, label, transform=ax.transAxes, fontsize=9,
            fontweight="bold", color=INK, va="top")


def lantern(ax, x: float, y: float, count: int, color: str, *, width: float = .075,
            stripe_h: float = .041, dot_limit: int | None = None) -> None:
    """Exact-count lantern: one horizontal stripe per fixed-seed observation.

    Width is deliberately non-quantitative: it makes a discrete count readable
    at column scale.  Count labels and the stripe count retain the evidence.
    """
    if count <= 0:
        return
    marks = count if dot_limit is None else min(count, dot_limit)
    spacing = stripe_h * .62
    for idx in range(count):
        rel = (idx - (count - 1) / 2) / max((count - 1) / 2, 1)
        half = width * (1 - .56 * abs(rel) ** 1.7)
        yy = y + idx * spacing - (count - 1) * spacing / 2
        ax.add_patch(plt.Rectangle((x - half, yy - stripe_h / 2), 2 * half, stripe_h,
                                   fc=color, ec="none", alpha=.30, zorder=2))
    dot_spacing = .075
    for idx in range(marks):
        yy = y + idx * dot_spacing - (marks - 1) * dot_spacing / 2
        ax.scatter(x, yy, s=15, color=color, edgecolors="white", linewidths=.25, zorder=4)
    top = y + max((count - 1) * spacing / 2, (marks - 1) * dot_spacing / 2)
    ax.annotate(f"n={count}", (x, top), xytext=(0, 4), textcoords="offset points",
                ha="center", fontsize=5.9, color=color, fontweight="bold", zorder=5)


def fig4() -> None:
    seeds = []
    with open(SRC / "fig4-v6-admission-seeds.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seeds.append((row["model"], float(row["contamination_recall"]),
                          float(row["safe_admission"])))
    models = ["Mistral 14B", "LFM2 24B", "Llama MoE"]
    colors = {"Mistral 14B": TEAL, "LFM2 24B": AMBER, "Llama MoE": SLATE}
    dodge = {"Mistral 14B": -0.13, "LFM2 24B": 0.0, "Llama MoE": 0.13}
    counts = Counter((m, 1.0 - safe, recall) for m, recall, safe in seeds)

    # Qwen's exact-count ``lantern'' grammar, compacted for a real 89-mm column.
    fig = plt.figure(figsize=(89 * MM, 104 * MM))
    axa = fig.add_axes([0.17, 0.555, 0.77, 0.37])
    row_y = {"Mistral 14B": 2, "LFM2 24B": 1, "Llama MoE": 0}
    row_colors = {"Mistral 14B": TEAL, "LFM2 24B": AMBER, "Llama MoE": RED}
    recall_by_model = {m: next(recall for model, recall, _ in seeds if model == m) for m in models}
    for model in models:
        y = row_y[model]
        axa.plot([-.10, 1.08], [y, y], color=GRID, lw=.5, zorder=0)
        for (m, fq, _), n in sorted(counts.items()):
            if m == model:
                lantern(axa, fq, y, n, row_colors[model])
        axa.text(1.12, y, f"CR={recall_by_model[model]:.1f}", fontsize=5.6,
                 ha="left", va="center", color=row_colors[model], fontweight="bold")
    axa.add_patch(FancyBboxPatch((-.14, 1.65), .34, .68,
                                 boxstyle="round,pad=.02,rounding_size=.03",
                                 fc=mpl.colors.to_rgba(TEAL, .035), ec=mpl.colors.to_rgba(TEAL, .25),
                                 ls="--", lw=.45, zorder=0))
    axa.text(.03, 1.72, "usable", fontsize=5.0, color=TEAL, alpha=.55, style="italic")
    axa.set_xlim(-0.20, 1.31)
    axa.set_ylim(-.58, 2.58)
    axa.set_xticks([0, 0.5, 1.0])
    axa.set_yticks([2, 1, 0], models, fontsize=6.2)
    axa.set_xlabel("false-quarantine rate", fontsize=6.45, labelpad=2)
    axa.grid(axis="x", color=GRID, lw=0.55, zorder=0)
    axa.tick_params(axis="x", labelsize=6.1, length=2)
    axa.tick_params(axis="y", length=0, pad=2)
    # No enclosing frame: direct labels, exact counts, and a light grid carry the scale.
    for spine in axa.spines.values():
        spine.set_visible(False)
    # Fixed figure-coordinate anchors keep a and b on the same vertical line.
    fig.text(.07, .938, "a", fontsize=9, fontweight="bold",
             color=INK, va="top")
    axa.text(1.30, 2.53, "CR = contamination recall", fontsize=5.0,
             ha="right", va="top", color=SLATE)

    cases = ["direct_conflict", "gradual_conflict", "legitimate_state", "unrelated"]
    matrix = {m: {} for m in models}
    with open(SRC / "fig4-v6-case-matrix.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            matrix[row["model"]][row["case"]] = float(row["accuracy"])
    values = np.array([[matrix[m][c] for c in cases] for m in models])
    axb = fig.add_axes([0.17, 0.115, 0.64, 0.32])
    cmap = LinearSegmentedColormap.from_list("red_teal", [RED, "#F2EFEA", TEAL])
    im = axb.imshow(values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(3):
        for j in range(4):
            value = values[i, j]
            axb.text(j, i, f"{value:.0%}", ha="center", va="center", fontsize=6.9,
                     fontweight="bold", color="white" if value < .25 or value > .75 else SLATE)
    axb.set_xticks(range(4), ["direct\ncontradiction", "gradual\ncontamination", "legitimate\nstate", "unrelated\nsafe write"], fontsize=5.5)
    axb.set_yticks(range(3), models, fontsize=6.15)
    axb.set_xticks(np.arange(-.5, 4, 1), minor=True)
    axb.set_yticks(np.arange(-.5, 3, 1), minor=True)
    axb.grid(which="minor", color="white", lw=1.1)
    axb.tick_params(which="both", length=0)
    for spine in axb.spines.values():
        spine.set_visible(False)
    fig.text(.07, .446, "b", fontsize=9, fontweight="bold",
             color=INK, va="top")
    cax = fig.add_axes([0.85, 0.115, 0.038, 0.32])
    cb = fig.colorbar(im, cax=cax, ticks=[0, .5, 1])
    cb.ax.set_yticklabels(["0%", "50%", "100%"], fontsize=5.8)
    cb.set_label("correct execution", fontsize=5.9, labelpad=2)
    cb.outline.set_linewidth(.45)
    fig.text(.5, .025, "synthetic route instances (20 fixed seeds / model); supplied-invariant execution only",
             ha="center", fontsize=5.35, color=SLATE, style="italic")
    export(fig, "cmtw-v7-fig4-admission-calibration")


def silhouette(ax, values: list[float], baseline: float, color: str, *, width=.055, max_height=.31) -> None:
    """Exact-support frequency silhouettes; no KDE or pseudo-samples."""
    count = Counter(round(float(v), 4) for v in values)
    n = len(values)
    for support, k in sorted(count.items()):
        h = max(.034, max_height * k / n)
        box = FancyBboxPatch((support - width / 2, baseline + .014), width, h,
                             boxstyle="round,pad=.002,rounding_size=.012",
                             facecolor=mpl.colors.to_rgba(color, .78), edgecolor=color,
                             linewidth=.65, zorder=3)
        ax.add_patch(box)
        ax.text(support, baseline + .014 + h / 2, str(k), ha="center", va="center",
                fontsize=4.8, fontweight="bold", color="white" if k >= n * .35 else INK, zorder=4)
        for off in np.linspace(-width * .40, width * .40, k) if k > 1 else [0.0]:
            ax.plot([support + off, support + off], [baseline - .018, baseline - .048],
                    color=mpl.colors.to_rgba(color, .56), lw=.42, solid_capstyle="round", zorder=2)


def fig5() -> None:
    contract = {}
    with open(SRC / "fig5-v6-factorial.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            contract[(int(row["T"]), int(row["I"]), int(row["C"]))] = float(row["compliance"])
    per_model = {}
    with open(SRC / "fig5-v6-generator-adherence.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = per_model.setdefault(row["model"], {"values": [], "mean": float(row["mean"]),
                                                       "lo": float(row["bootstrap95_lo"]), "hi": float(row["bootstrap95_hi"])})
            d["values"].append(float(row["adherence"]))

    # Keep panel b tall enough for three discrete-support silhouettes at final
    # single-column width; the former 74 mm canvas compressed them into stripes.
    fig = plt.figure(figsize=(89 * MM, 78 * MM))
    cmap = LinearSegmentedColormap.from_list("red_teal", [RED, "#F2EFEA", TEAL])
    # Adopt Kimi's factorial grammar: I is horizontal, C vertical, split by T.
    ax0 = fig.add_axes([.15, .64, .29, .28])
    ax1 = fig.add_axes([.51, .64, .29, .28])
    for t, ax in [(0, ax0), (1, ax1)]:
        m = np.array([[contract[(t, 0, 0)], contract[(t, 1, 0)]],
                      [contract[(t, 0, 1)], contract[(t, 1, 1)]]])
        im = ax.imshow(m, cmap=cmap, vmin=0, vmax=1, origin="lower", aspect="auto")
        for y in range(2):
            for x in range(2):
                v = m[y, x]
                ax.text(x, y, f"{v:.0%}", ha="center", va="center", fontsize=7.1,
                        fontweight="bold", color="white" if v < .25 or v > .75 else SLATE)
        ax.set_xticks([0, 1], ["I=0", "I=1"], fontsize=6.2)
        ax.set_yticks([0, 1], ["C=0", "C=1"] if t == 0 else ["", ""], fontsize=6.2)
        ax.tick_params(length=0)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(f"T = {t}", fontsize=7.0, color=SLATE, pad=3)
    ax1.add_patch(plt.Rectangle((.5, .5), 1, 1, fill=False, ec=TEAL, lw=1.45))
    ax0.set_ylabel("C: recorded-\nderivative closure", fontsize=6.0)
    fig.text(.475, .545, "I: persona-invariant admission", ha="center", fontsize=6.05)
    panel(ax0, "a")
    cax = fig.add_axes([.84, .64, .038, .28])
    cb = fig.colorbar(im, cax=cax, ticks=[0, .5, 1])
    cb.ax.set_yticklabels(["0%", "50%", "100%"], fontsize=5.7)
    cb.set_label("compliance", fontsize=5.9, labelpad=2)
    cb.outline.set_linewidth(.45)

    # Exact-count lanterns preserve the reviewed discrete-support semantics.
    order = ["Mistral 14B", "Llama MoE", "LFM2 24B"]
    ax = fig.add_axes([.20, .07, .69, .40])
    colors = [TEAL, RED, AMBER]
    y_pos = [2, 1, 0]
    for y, model, color in zip(y_pos, order, colors):
        row = per_model[model]
        ax.plot([.47, 1.05], [y, y], color=GRID, lw=.55, zorder=0)
        ci_y = y
        ax.plot([row["lo"], row["hi"]], [ci_y, ci_y], color=color, lw=2.0,
                alpha=.70, solid_capstyle="round", zorder=2)
        for endpoint in (row["lo"], row["hi"]):
            ax.plot([endpoint, endpoint], [ci_y-.045, ci_y+.045], color=color, lw=1.0, alpha=.75, zorder=2)
        lantern(ax, 0.5, y, row["values"].count(.5), color)
        lantern(ax, .75, y, row["values"].count(.75), color)
        lantern(ax, 1.0, y, row["values"].count(1.0), color)
        ax.scatter(row["mean"], y, marker="s", s=34, color=color, edgecolors="white", linewidths=.65, zorder=6)
        ax.text(1.055, y, f"{row['mean']:.3f}", ha="left", va="center", fontsize=5.25, color=color)
    ax.set_xlim(.43, 1.105)
    ax.set_ylim(-.56, 2.56)
    ax.set_xticks([.50, .75, 1.00])
    ax.set_yticks(y_pos, order)
    ax.tick_params(axis="y", length=0, pad=4)
    ax.grid(axis="x", color=GRID, lw=.45)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("exact-answer adherence  |  square = mean; line = bootstrap 95% CI", fontsize=6.0, labelpad=2)
    ax.text(.47, 2.37, "20 fixed seeds / model", ha="left", va="top", fontsize=4.9, color=SLATE)
    panel(ax, "b")
    export(fig, "cmtw-v7-fig5-contract-evidence")


def rounded(ax, xy, wh, *, face="white", edge=SLATE, lw=.72, text=None,
            fontsize=5.8, text_color=INK, weight="normal", dashed=False) -> None:
    x, y = xy
    w, h = wh
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=.03,rounding_size=.10",
                                facecolor=face, edgecolor=edge, linewidth=lw,
                                linestyle="--" if dashed else "-", zorder=3))
    if text:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fontsize, color=text_color, fontweight=weight, zorder=4,
                linespacing=.92)


def arrow(ax, start, end, *, color=SLATE, lw=.72) -> None:
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=7,
                                 linewidth=lw, color=color, zorder=2,
                                 connectionstyle="arc3,rad=0"))


def fig5c() -> None:
    """Editable, parallel lifecycle-contract stack for Figure 5(c).

    The visual deliberately makes I, T, and C three sibling gates entering an
    eligibility boundary; no arrow is ever drawn from one operator to another.
    """
    fig = plt.figure(figsize=(89 * MM, 78 * MM))
    ax = fig.add_axes([.01, .02, .98, .96])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8.8)
    ax.axis("off")
    # Match the exact panel-label typography used by panels a and b.
    # Keep c on the same visual top-line as panel a in the adjacent PDF.
    ax.text(.02, 8.58, "c", fontsize=9, fontweight="bold", color=INK, va="top")
    # Lower the diagram as a unit so the panel label has a clean, independent
    # corner and no longer touches the outer contract frame.
    dy = -.24

    # CMTW is the outer contract.  A direct scope key states that the reference
    # substrate supplies T+C, while CMTW adds I+AnswerTrace; no inner frame can
    # accidentally claim the shared eligibility boundary.
    rounded(ax, (.18, .34 + dy), (9.58, 8.04), face="none", edge=SLATE, lw=.72)
    # Keep the scope label clearly inside the frame instead of sitting on its stroke.
    ax.text(.54, 8.08 + dy, "CMTW contract layer", fontsize=5.7, color=SLATE,
            fontweight="bold", va="center")
    ax.text(.58, 7.72 + dy, "reference substrate:  T + C", fontsize=5.0,
            color=SLATE, fontweight="bold", va="center")
    ax.text(5.26, 7.72 + dy, "CMTW adds:  I + AnswerTrace", fontsize=5.0,
            color=TEAL, fontweight="bold", va="center")

    lanes = [
        (6.78 + dy, "ASSERT", "I: persona\nadmission", "admitted\npersona fact", TEAL),
        (4.98 + dy, "AS-OF QUERY", "T: valid-time\neligibility", "current typed\nstate", AMBER),
        (3.18 + dy, "FORGET", "C: recorded\nclosure", "tombstones +\nderived IDs excluded", SLATE),
    ]
    for y, op, contract, outcome, color in lanes:
        rounded(ax, (.56, y-.39), (1.55, .78), text=op, fontsize=5.45, text_color=SLATE)
        arrow(ax, (2.13, y), (2.48, y))
        rounded(ax, (2.50, y-.39), (2.20, .78), face=color, edge=color, lw=.0,
                text=contract, fontsize=5.25, text_color="white", weight="bold")
        arrow(ax, (4.72, y), (5.02, y), color=color, lw=.78)
        rounded(ax, (5.04, y-.34), (1.80, .68),
                face=mpl.colors.to_rgba(color, .10), edge=color, lw=.55,
                text=outcome, fontsize=4.55, text_color=color, weight="bold")
        # Each output directly enters its own port in the same boundary.
        arrow(ax, (6.86, y), (7.26, y), color=color, lw=.78)

    rounded(ax, (7.28, 2.58 + dy), (1.62, 4.59), face="#F2F5F6", edge=SLATE, lw=.88,
            text="eligibility\nboundary", fontsize=5.75, text_color=SLATE, weight="bold")

    # Boundary -> witness -> answer, a downstream answer lineage rather than an operator pipeline.
    rounded(ax, (3.54, 1.12 + dy), (5.16, .72), face="white", edge=SLATE, lw=.78,
            text="AnswerTrace", fontsize=5.65, text_color=SLATE, weight="bold")
    ax.text(6.13, 1.30 + dy,
            "evidence IDs  |  as-of predicate  |  invariant  |  tombstone set",
            ha="center", va="center", fontsize=4.55, color=SLATE, zorder=4)
    arrow(ax, (8.09, 2.56 + dy), (8.09, 1.86 + dy), color=SLATE, lw=.82)
    arrow(ax, (6.13, 1.10 + dy), (6.13, .66 + dy), color=SLATE, lw=.76)
    ax.text(6.13, .51 + dy, "answer", ha="center", va="center", fontsize=6.0,
            color=TEAL, fontweight="bold")
    ax.text(9.58, .51 + dy, "recorded derivatives only", ha="right", va="center",
            fontsize=4.45, color=SLATE, style="italic")
    export(fig, "cmtw-v7-fig5c-contract-stack")


if __name__ == "__main__":
    fig4()
    fig5()
    fig5c()
    print("Wrote CMTW v7 adopted figures from frozen source-data only.")
