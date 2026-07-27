"""CMTW-v6 publication figures: Python/Matplotlib-only visual-argument rebuild.

This script reads frozen accepted JSON artifacts only. It performs no inference,
data generation, or statistical re-estimation. Discrete seed-level values stay
discrete: no KDE or pseudo-samples are introduced. All visual exports are made
by Matplotlib: editable SVG, vector PDF, 600-dpi TIFF, and a PNG inspection copy.
"""

from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path as FilePath

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch, PathPatch, Rectangle
from matplotlib.path import Path as MplPath
import numpy as np

# Mandatory editable-text settings.
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Arial", "DejaVu Sans", "Liberation Sans"]
plt.rcParams["svg.fonttype"] = "none"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams.update(
    {
        "font.size": 7,
        "axes.linewidth": 0.65,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "legend.frameon": False,
    }
)

ROOT = FilePath(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "paper" / "figures" / "v4"
SRC = OUT / "source-data"
OUT.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)

COL = {
    "ink": "#1F2933",
    "muted": "#697586",
    "grid": "#D9E1E8",
    "teal": "#168A8A",
    "teal_light": "#D5ECE9",
    "amber": "#D79A2B",
    "amber_light": "#F6E2C7",
    "red": "#C94C4C",
    "red_light": "#F6D9DB",
    "slate": "#5B6770",
    "grey": "#DDE2E8",
    "grey_dark": "#6B7280",
}

MODEL_MAP = {
    "mistralai_ministral-3-14b-instruct-2512": "Mistral 14B",
    "liquid/lfm2-24b-a2b": "LFM2 24B",
    "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b": "Llama MoE",
}


def read_json(rel: str):
    with open(ROOT / rel, encoding="utf-8") as f:
        return json.load(f)


def save(fig: plt.Figure, stem: str) -> None:
    base = OUT / stem
    fig.savefig(base.with_suffix(".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(base.with_suffix(".tiff"), bbox_inches="tight", pad_inches=0.02, dpi=600)
    fig.savefig(base.with_suffix(".png"), bbox_inches="tight", pad_inches=0.02, dpi=300)
    plt.close(fig)


def panel_label(ax, label: str) -> None:
    ax.text(-0.09, 1.03, label, transform=ax.transAxes, fontsize=9, fontweight="bold", color=COL["ink"])


def ribbon(ax, x0, y0, h0, x1, y1, h1, color, alpha=0.78):
    """A directed semantic-lineage ribbon. Width is visual grouping, not count."""
    c1 = x0 + (x1 - x0) * 0.42
    c2 = x0 + (x1 - x0) * 0.58
    verts = [
        (x0, y0 + h0 / 2), (c1, y0 + h0 / 2), (c2, y1 + h1 / 2), (x1, y1 + h1 / 2),
        (x1, y1 - h1 / 2), (c2, y1 - h1 / 2), (c1, y0 - h0 / 2), (x0, y0 - h0 / 2),
        (x0, y0 + h0 / 2),
    ]
    codes = [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4,
             MplPath.LINETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4, MplPath.CLOSEPOLY]
    ax.add_patch(PathPatch(MplPath(verts, codes), facecolor=color, edgecolor="none", alpha=alpha, zorder=1))


def node(ax, x, y, w, h, label, face, text=COL["ink"], fs=5.7):
    box = FancyBboxPatch((x, y - h / 2), w, h, boxstyle="round,pad=0.01,rounding_size=0.018",
                         facecolor=face, edgecolor=COL["ink"], linewidth=0.45, zorder=3)
    ax.add_patch(box)
    ax.text(x + w / 2, y, label, ha="center", va="center", fontsize=fs, color=text, zorder=4, linespacing=0.93)


def discrete_cloud(
    ax,
    values,
    baseline,
    color,
    *,
    side=1,
    width=0.064,
    max_height=0.18,
    rain=True,
    annotate_counts=False,
):
    """Draw an exact-support raincloud without continuous density estimation.

    Capsule height is proportional to the observed count at an exact support
    value. Short ticks are overlap-jittered only along x and retain exact y/x
    support semantics described in the figure caption.
    """
    counts = Counter(round(float(v), 4) for v in values)
    total = len(values)
    for support, count in sorted(counts.items()):
        height = max(0.034, max_height * count / total)
        y0 = baseline + 0.014 if side > 0 else baseline - 0.014 - height
        cap = FancyBboxPatch(
            (support - width / 2, y0),
            width,
            height,
            boxstyle=f"round,pad=0.002,rounding_size={min(width, height) / 2.2}",
            facecolor=mpl.colors.to_rgba(color, 0.78),
            edgecolor=color,
            linewidth=0.65,
            zorder=3,
        )
        ax.add_patch(cap)
        if annotate_counts:
            label_y = y0 + height / 2
            ax.text(
                support,
                label_y,
                str(count),
                ha="center",
                va="center",
                fontsize=4.8,
                color="white" if count >= total * 0.35 else COL["ink"],
                fontweight="bold",
                zorder=4,
            )
        if rain:
            offsets = np.linspace(-width * 0.40, width * 0.40, count) if count > 1 else np.array([0.0])
            tick_base = baseline - 0.018 if side > 0 else baseline + 0.018
            tick_end = tick_base - 0.030 if side > 0 else tick_base + 0.030
            for off in offsets:
                ax.plot(
                    [support + off, support + off],
                    [tick_base, tick_end],
                    color=mpl.colors.to_rgba(color, 0.56),
                    linewidth=0.42,
                    solid_capstyle="round",
                    zorder=2,
                )
    return counts


def fig3():
    e1 = read_json("results/v4/e1_structural_20seeds_mistral_r1.json")
    latencies = np.array([r["mean_recon_seconds"] for r in e1["seed_rows"]], dtype=float)
    with open(SRC / "fig3-v6-rebuild-latency.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["seed", "seconds"])
        w.writerows((r["seed"], r["mean_recon_seconds"]) for r in e1["seed_rows"])

    fig = plt.figure(figsize=(7.16, 3.02))
    gs = fig.add_gridspec(2, 1, height_ratios=[2.34, 0.66], hspace=0.26)

    # One shared derivative fans into three intervention-specific outcomes.
    ax = fig.add_subplot(gs[0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    panel_label(ax, "a")

    node(ax, 0.018, 0.67, 0.115, 0.18, "withdrawn\nepisode", COL["red_light"], fs=5.7)
    node(ax, 0.018, 0.31, 0.115, 0.18, "safe route\nfact", COL["teal_light"], fs=5.7)
    ribbon(ax, 0.133, 0.67, 0.105, 0.205, 0.61, 0.16, COL["red"], alpha=0.82)
    ribbon(ax, 0.133, 0.31, 0.105, 0.205, 0.39, 0.16, COL["teal"], alpha=0.82)
    node(ax, 0.205, 0.50, 0.135, 0.52, "coarse\nsummary\n\n8 personas", COL["grey"], fs=6.2)

    policy_x, policy_w = 0.435, 0.145
    policies = [
        (0.82, "preserve\nold view", COL["red_light"]),
        (0.50, "invalidate\nwhole view", "#E9EDF1"),
        (0.18, "selective\nrebuild", COL["amber_light"]),
    ]
    for y, label, face in policies:
        ribbon(ax, 0.340, 0.50, 0.14, policy_x, y, 0.12, COL["grey_dark"], alpha=0.25)
        node(ax, policy_x, y, policy_w, 0.15, label, face, fs=5.8)

    outcomes = [
        (0.82, 0.91, "withdrawn still eligible\n10 / 24 probes", COL["red_light"], COL["red"]),
        (0.82, 0.75, "safe fact retained\n8 / 8", COL["teal_light"], COL["teal"]),
        (0.50, 0.59, "withdrawn blocked\n0 / 24 probes", COL["teal_light"], COL["teal"]),
        (0.50, 0.43, "safe fact over-deleted\n0 / 8", "#E8EBEF", COL["grey_dark"]),
        (0.18, 0.27, "withdrawn blocked\n0 / 24 probes", COL["teal_light"], COL["teal"]),
        (0.18, 0.11, "safe fact retained\n8 / 8", COL["teal_light"], COL["teal"]),
    ]
    out_x, out_w = 0.735, 0.205
    for policy_y, out_y, label, face, flow_col in outcomes:
        ribbon(ax, policy_x + policy_w, policy_y, 0.075, out_x, out_y, 0.072, flow_col, alpha=0.62)
        node(ax, out_x, out_y, out_w, 0.125, label, face, fs=5.35)

    ax.text(0.270, 0.935, "one recorded derivative", ha="center", va="center", fontsize=5.45, color=COL["muted"])
    ax.text(0.508, 0.955, "policy intervention", ha="center", va="center", fontsize=5.45, color=COL["muted"])
    ax.text(0.835, 1.025, "observable contract outcome", ha="center", va="center", fontsize=5.45, color=COL["muted"], clip_on=False)
    # Broken axis: 19 tightly clustered seeds and one isolated observation.
    lower = gs[1].subgridspec(1, 2, width_ratios=[5.5, 1.25], wspace=0.105)
    ax_l = fig.add_subplot(lower[0, 0])
    ax_r = fig.add_subplot(lower[0, 1], sharey=ax_l)
    central = latencies[latencies < 4.0]
    isolated = latencies[latencies >= 4.0]
    violin = ax_l.violinplot(
        central,
        positions=[0],
        vert=False,
        widths=0.52,
        showmeans=False,
        showmedians=False,
        showextrema=False,
        bw_method=0.32,
    )
    for body in violin["bodies"]:
        body.set_facecolor(COL["amber_light"])
        body.set_edgecolor(COL["amber"])
        body.set_linewidth(0.75)
        body.set_alpha(0.92)
    q1, median, q3 = np.quantile(central, [0.25, 0.5, 0.75])
    ax_l.plot([q1, q3], [0, 0], color=COL["ink"], linewidth=2.2, solid_capstyle="round", zorder=4)
    ax_l.plot([median, median], [-0.18, 0.18], color=COL["ink"], linewidth=0.9, zorder=4)
    ax_l.text(3.605, 0.33, f"19 seeds  |  median {median:.3f} s  |  IQR {q1:.3f}-{q3:.3f}", fontsize=5.55, color=COL["ink"], va="center")

    if len(isolated):
        x_iso = float(isolated[0])
        capsule = FancyBboxPatch(
            (x_iso - 0.012, -0.18),
            0.024,
            0.36,
            boxstyle="round,pad=0.002,rounding_size=0.012",
            facecolor=COL["amber"],
            edgecolor=COL["ink"],
            linewidth=0.55,
            zorder=3,
        )
        ax_r.add_patch(capsule)
        ax_r.text(x_iso, 0.33, f"1 seed\n{x_iso:.3f} s", ha="center", va="center", fontsize=5.4, color=COL["ink"])

    for axis in (ax_l, ax_r):
        axis.set_ylim(-0.42, 0.46)
        axis.set_yticks([])
        axis.spines["left"].set_visible(False)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="x", labelsize=5.5, length=2.5, pad=1.5)
    ax_l.set_xlim(3.60, 3.78)
    ax_l.set_xticks([3.60, 3.66, 3.72])
    ax_r.set_xlim(6.20, 6.31)
    ax_r.set_xticks([6.26, 6.31])
    ax_l.spines["bottom"].set_bounds(3.60, 3.78)
    ax_r.spines["bottom"].set_bounds(6.20, 6.31)

    # Explicit diagonal cut marks at the adjoining bottom axes.
    d = 0.014
    kwargs_l = dict(transform=ax_l.transAxes, color=COL["ink"], clip_on=False, linewidth=0.8)
    kwargs_r = dict(transform=ax_r.transAxes, color=COL["ink"], clip_on=False, linewidth=0.8)
    ax_l.plot((1 - d, 1 + d), (-d, +d), **kwargs_l)
    ax_r.plot((-d, +d), (-d, +d), **kwargs_r)
    panel_label(ax_l, "b")
    fig.text(0.53, 0.012, "local selective re-consolidation time per persona (s; broken axis)", ha="center", fontsize=6.1, color=COL["ink"])
    save(fig, "cmtw-v6-fig3-deletion-lineage")


def fig3_single():
    """Single-column reflow of Figure 3; values and visual grammar are unchanged."""
    e1 = read_json("results/v4/e1_structural_20seeds_mistral_r1.json")
    latencies = np.array([r["mean_recon_seconds"] for r in e1["seed_rows"]], dtype=float)

    fig = plt.figure(figsize=(3.50, 3.62))

    # (a) Reflow the lineage into a taller single-column argument so labels
    # remain 4.4--5.7 pt instead of shrinking a double-column source by 50%.
    ax = fig.add_axes([.055, .30, .92, .67])
    ax.set_xlim(0, 1)
    ax.set_ylim(.36, 1.02)
    ax.axis("off")
    panel_label(ax, "a")

    node(ax, .01, .79, .16, .12, "withdrawn\nepisode", COL["red_light"], fs=5.2)
    node(ax, .01, .58, .16, .12, "safe route\nfact", COL["teal_light"], fs=5.2)
    ribbon(ax, .17, .79, .075, .215, .72, .105, COL["red"], alpha=.82)
    ribbon(ax, .17, .58, .075, .215, .63, .105, COL["teal"], alpha=.82)
    node(ax, .215, .675, .18, .31, "coarse\nsummary\n\n8 personas", COL["grey"], fs=5.4)

    policy_x, policy_w = .45, .18
    policies = [
        (.86, "preserve\nold view", COL["red_light"]),
        (.67, "invalidate\nwhole view", "#E9EDF1"),
        (.48, "selective\nrebuild", COL["amber_light"]),
    ]
    for y, label, face in policies:
        ribbon(ax, .395, .675, .055, policy_x, y, .060, COL["grey_dark"], alpha=.25)
        node(ax, policy_x, y, policy_w, .105, label, face, fs=5.0)

    outcomes = [
        (.86, .90, "withdrawn eligible\n10 / 24 probes", COL["red_light"], COL["red"]),
        (.86, .82, "safe fact retained\n8 / 8", COL["teal_light"], COL["teal"]),
        (.67, .71, "withdrawn blocked\n0 / 24 probes", COL["teal_light"], COL["teal"]),
        (.67, .63, "safe fact over-deleted\n0 / 8", "#E8EBEF", COL["grey_dark"]),
        (.48, .52, "withdrawn blocked\n0 / 24 probes", COL["teal_light"], COL["teal"]),
        (.48, .44, "safe fact retained\n8 / 8", COL["teal_light"], COL["teal"]),
    ]
    out_x, out_w = .69, .295
    for policy_y, out_y, label, face, flow_col in outcomes:
        ribbon(ax, policy_x + policy_w, policy_y, .043, out_x, out_y, .038,
               flow_col, alpha=.62)
        node(ax, out_x, out_y, out_w, .063, label, face, fs=4.35)

    ax.text(.305, .995, "one recorded derivative", ha="center", va="center",
            fontsize=4.8, color=COL["muted"])
    ax.text(.54, .995, "policy intervention", ha="center", va="center",
            fontsize=4.8, color=COL["muted"])
    ax.text(.83, .995, "observable contract outcome", ha="center", va="center",
            fontsize=4.8, color=COL["muted"])

    # (b) Preserve the reviewed broken-axis distribution with a larger vertical
    # envelope than the former scaled-down double-column panel.
    ax_l = fig.add_axes([.16, .075, .64, .15])
    ax_r = fig.add_axes([.84, .075, .12, .15], sharey=ax_l)
    central = latencies[latencies < 4.0]
    isolated = latencies[latencies >= 4.0]
    violin = ax_l.violinplot(
        central, positions=[0], vert=False, widths=.48,
        showmeans=False, showmedians=False, showextrema=False, bw_method=.32,
    )
    for body in violin["bodies"]:
        body.set_facecolor(COL["amber_light"])
        body.set_edgecolor(COL["amber"])
        body.set_linewidth(.75)
        body.set_alpha(.92)
    q1, median, q3 = np.quantile(central, [.25, .5, .75])
    ax_l.plot([q1, q3], [0, 0], color=COL["ink"], linewidth=2.0,
              solid_capstyle="round", zorder=4)
    ax_l.plot([median, median], [-.16, .16], color=COL["ink"], linewidth=.85, zorder=4)
    ax_l.text(3.602, .31,
              f"19 seeds  |  median {median:.3f} s  |  IQR {q1:.3f}-{q3:.3f}",
              fontsize=4.55, color=COL["ink"], va="center")
    if len(isolated):
        x_iso = float(isolated[0])
        ax_r.add_patch(FancyBboxPatch(
            (x_iso - .012, -.16), .024, .32,
            boxstyle="round,pad=0.002,rounding_size=0.012",
            facecolor=COL["amber"], edgecolor=COL["ink"], linewidth=.55, zorder=3,
        ))
        ax_r.text(x_iso, .31, f"1 seed\n{x_iso:.3f} s", ha="center",
                  va="center", fontsize=4.45, color=COL["ink"])
    for axis in (ax_l, ax_r):
        axis.set_ylim(-.38, .40)
        axis.set_yticks([])
        axis.spines["left"].set_visible(False)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.tick_params(axis="x", labelsize=4.65, length=2.2, pad=1.3)
    ax_l.set_xlim(3.60, 3.78)
    ax_l.set_xticks([3.60, 3.66, 3.72])
    ax_r.set_xlim(6.20, 6.31)
    ax_r.set_xticks([6.26, 6.31])
    d = .018
    ax_l.plot((1-d, 1+d), (-d, +d), transform=ax_l.transAxes,
              color=COL["ink"], clip_on=False, linewidth=.75)
    ax_r.plot((-d, +d), (-d, +d), transform=ax_r.transAxes,
              color=COL["ink"], clip_on=False, linewidth=.75)
    fig.text(.035, .235, "b", fontsize=9, fontweight="bold", color=COL["ink"])
    fig.text(.555, .012,
             "local selective re-consolidation time per persona (s; broken axis)",
             ha="center", fontsize=5.25, color=COL["ink"])
    save(fig, "cmtw-v8-fig3-deletion-lineage-single")


def admission_seed_rows():
    files = [
        "results/v4/e4_admission_20seeds_mistral_r1.json",
        "results/v4/e4_admission_20seeds_lfm2_r1.json",
        "results/v4/e4_admission_20seeds_llama18b_r1.json",
    ]
    seed_rows = []
    case_rows = []
    for rel in files:
        raw = read_json(rel)
        model = MODEL_MAP[raw["model"]]
        by_seed = {}
        for rec in raw["records"]:
            by_seed.setdefault(rec["seed"], []).append(rec)
        for seed, recs in sorted(by_seed.items()):
            conflicts = [r for r in recs if r["should_quarantine"]]
            safe = [r for r in recs if not r["should_quarantine"]]
            recall = sum(r["decision"] == "QUARANTINE" for r in conflicts) / len(conflicts)
            safe_admission = sum(r["decision"] == "ACCEPT" for r in safe) / len(safe)
            seed_rows.append(
                {
                    "model": model,
                    "seed": seed,
                    "contamination_recall": recall,
                    "safe_admission": safe_admission,
                }
            )
        for kind, stats in raw["aggregate"]["by_case_kind"].items():
            case_rows.append(
                {
                    "model": model,
                    "case": kind,
                    "accuracy": stats["accuracy"],
                    "n": stats["n"],
                }
            )
    return seed_rows, case_rows


def fig4():
    rows, cases = admission_seed_rows()
    with open(SRC / "fig4-v6-admission-seeds.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    with open(SRC / "fig4-v6-case-matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cases[0].keys())
        w.writeheader()
        w.writerows(cases)

    order_m = ["Mistral 14B", "LFM2 24B", "Llama MoE"]
    fig = plt.figure(figsize=(3.50, 3.74))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.36, 1.00], hspace=0.39)

    ax = fig.add_subplot(gs[0])
    y_positions = [2, 1, 0]
    for y, model in zip(y_positions, order_m):
        model_rows = [r for r in rows if r["model"] == model]
        recall = [r["contamination_recall"] for r in model_rows]
        safe = [r["safe_admission"] for r in model_rows]
        ax.plot([-0.045, 1.045], [y, y], color=COL["grid"], linewidth=0.55, zorder=0)
        discrete_cloud(
            ax,
            recall,
            y + 0.015,
            COL["teal"],
            side=1,
            width=0.070,
            max_height=0.245,
            rain=True,
            annotate_counts=True,
        )
        discrete_cloud(
            ax,
            safe,
            y - 0.015,
            COL["amber"],
            side=-1,
            width=0.070,
            max_height=0.245,
            rain=True,
            annotate_counts=True,
        )
    ax.set_xlim(-0.075, 1.075)
    ax.set_ylim(-0.43, 2.43)
    ax.set_xticks([0, 0.5, 1.0], ["0", ".5", "1"])
    ax.set_yticks(y_positions, order_m)
    ax.set_xlabel("per-seed rate  (two probes per metric)", labelpad=2)
    ax.tick_params(axis="y", length=0, pad=5)
    ax.grid(axis="x", color=COL["grid"], linewidth=0.45)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    panel_label(ax, "a")
    legend_handles = [
        mpl.lines.Line2D([0], [0], color=COL["teal"], linewidth=5, solid_capstyle="round", label="contamination recall"),
        mpl.lines.Line2D([0], [0], color=COL["amber"], linewidth=5, solid_capstyle="round", label="safe-write acceptance"),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.53, 1.12),
        ncol=2,
        handlelength=1.25,
        columnspacing=1.1,
        fontsize=5.45,
    )
    order_c = ["direct_conflict", "gradual_conflict", "legitimate_state", "unrelated"]
    matrix = np.array(
        [
            [
                next(x["accuracy"] for x in cases if x["model"] == model and x["case"] == case)
                for case in order_c
            ]
            for model in order_m
        ]
    )
    cmap = LinearSegmentedColormap.from_list("cmtw", [COL["red_light"], "#F4F1EC", COL["teal_light"]])
    ax = fig.add_subplot(gs[1])
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto", interpolation="nearest")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, f"{matrix[i, j]:.0%}", ha="center", va="center", fontsize=6.0, color=COL["ink"])
    ax.set_xticks(range(4), ["Direct\nconflict", "Gradual\nconflict", "Legitimate\nstate", "Unrelated"])
    ax.set_yticks(range(3), order_m)
    ax.tick_params(length=0, pad=2)
    ax.set_xticks(np.arange(-0.5, 4, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, 3, 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=0.9)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    cbar = fig.colorbar(im, ax=ax, fraction=0.045, pad=0.025, ticks=[0, 0.5, 1])
    cbar.ax.set_ylabel("admission accuracy", rotation=90, labelpad=5)
    cbar.ax.tick_params(labelsize=5.2, length=2)
    panel_label(ax, "b")
    save(fig, "cmtw-v6-fig4-admission-calibration")


def fig5():
    e2 = read_json("results/v4/e2_e5_contract_suite_20seeds_r2.json")
    adherence = read_json("results/v4/e2_full_contract_3models_analysis_r3.json")
    agg = {x["configuration"]: x["overall"]["mean"] for x in e2["e2_factorial"]["aggregate"]}

    def value(i, c, t):
        parts = [
            "persona_invariant" if i else "no_persona_invariant",
            "forget_cascade" if c else "no_forget_cascade",
            "typed_valid_retrieval" if t else "no_typed_valid_retrieval",
        ]
        return agg["+".join(parts)]

    matrices = [
        np.array([[value(1, 0, t), value(1, 1, t)], [value(0, 0, t), value(0, 1, t)]])
        for t in [0, 1]
    ]
    with open(SRC / "fig5-v6-factorial.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["T", "I", "C", "compliance"])
        for t in [0, 1]:
            for i in [0, 1]:
                for c in [0, 1]:
                    w.writerow([t, i, c, value(i, c, t)])

    gen = []
    for item in adherence["aggregate"]:
        if item["category"] != "overall":
            continue
        gen.append(
            {
                "model": MODEL_MAP[item["model"]],
                "mean": item["mean"],
                "lo": item["bootstrap95"][0],
                "hi": item["bootstrap95"][1],
                "seed_values": item["seed_values"],
            }
        )
    order = ["Mistral 14B", "Llama MoE", "LFM2 24B"]
    gen.sort(key=lambda r: order.index(r["model"]))
    with open(SRC / "fig5-v6-generator-adherence.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "seed", "adherence", "mean", "bootstrap95_lo", "bootstrap95_hi"])
        for row in gen:
            for idx, val in enumerate(row["seed_values"]):
                w.writerow([row["model"], idx + 1, val, row["mean"], row["lo"], row["hi"]])

    cmap = LinearSegmentedColormap.from_list("cmtw", [COL["red_light"], "#F4F1EC", COL["teal_light"]])
    fig = plt.figure(figsize=(3.50, 2.92))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.12, 1.00], hspace=0.50)
    top = gs[0].subgridspec(1, 3, width_ratios=[1, 1, 0.08], wspace=0.13)
    axes = [fig.add_subplot(top[0, 0]), fig.add_subplot(top[0, 1])]
    for idx, (ax, matrix) in enumerate(zip(axes, matrices)):
        im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="equal", interpolation="nearest")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{matrix[i, j]:.0%}", ha="center", va="center", fontsize=7.0, color=COL["ink"])
        ax.text(0.5, 1.08, f"T = {idx}", transform=ax.transAxes, ha="center", fontsize=6.6, fontweight="bold")
        ax.set_xticks([0, 1], ["C=0", "C=1"])
        if idx == 0:
            ax.set_yticks([0, 1], ["I=1", "I=0"])
            panel_label(ax, "a")
        else:
            ax.set_yticks([0, 1], ["", ""])
        ax.tick_params(length=0)
        ax.set_xticks(np.arange(-0.5, 2, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, 2, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.0)
        ax.tick_params(which="minor", bottom=False, left=False)
        for spine in ax.spines.values():
            spine.set_visible(False)
    cax = fig.add_subplot(top[0, 2])
    cb = fig.colorbar(im, cax=cax, ticks=[0, 0.5, 1])
    cb.ax.set_ylabel("exact obligation compliance", rotation=90, labelpad=5, fontsize=5.25)
    cb.ax.tick_params(labelsize=5.0, length=2)

    # Exact-support frequency silhouettes; no bars or smoothed density.
    ax = fig.add_subplot(gs[1])
    y_positions = [2, 1, 0]
    row_colors = [COL["teal"], COL["slate"], COL["amber"]]
    for y, row, color in zip(y_positions, gen, row_colors):
        ax.plot([0.47, 1.03], [y, y], color=COL["grid"], linewidth=0.55, zorder=0)
        discrete_cloud(
            ax,
            row["seed_values"],
            y,
            color,
            side=1,
            width=0.055,
            max_height=0.31,
            rain=True,
            annotate_counts=True,
        )
        ci_y = y - 0.20
        ax.plot([row["lo"], row["hi"]], [ci_y, ci_y], color=COL["ink"], linewidth=1.05, solid_capstyle="round", zorder=4)
        ax.plot([row["lo"], row["lo"]], [ci_y - 0.035, ci_y + 0.035], color=COL["ink"], linewidth=0.75)
        ax.plot([row["hi"], row["hi"]], [ci_y - 0.035, ci_y + 0.035], color=COL["ink"], linewidth=0.75)
        ax.plot([row["mean"], row["mean"]], [ci_y - 0.065, ci_y + 0.065], color=COL["ink"], linewidth=1.0)
        ax.text(
            1.045,
            y + 0.085,
            f"{row['mean']:.3f}",
            ha="left",
            va="center",
            fontsize=5.3,
            color=COL["ink"],
        )
    ax.set_xlim(0.45, 1.09)
    ax.set_ylim(-0.35, 2.46)
    ax.set_xticks([0.50, 0.75, 1.00])
    ax.set_yticks(y_positions, [r["model"] for r in gen])
    ax.tick_params(axis="y", length=0, pad=4)
    ax.grid(axis="x", color=COL["grid"], linewidth=0.45)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("exact-answer adherence  |  line below = bootstrap 95% CI", labelpad=2)
    ax.text(0.47, 2.37, "20 fixed seeds / model", ha="left", va="top", fontsize=4.95, color=COL["muted"])
    panel_label(ax, "b")
    save(fig, "cmtw-v6-fig5-contract-evidence")


if __name__ == "__main__":
    fig3()
    fig4()
    fig5()
    print(f"Wrote Matplotlib CMTW-v6 figures to {OUT}")
