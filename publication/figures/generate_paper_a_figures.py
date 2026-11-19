#!/usr/bin/env python3
"""Generate Paper A figures from protected, serialized QTR evidence only.

No experiment is performed; no scientific sources or exact result values are changed.
Run at the repository root:
    python3 publication/figures/generate_paper_a_figures.py
Requires: matplotlib, Python 3.10+.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
SOURCE = {
    "c18": ROOT / "evidence/TCM-QDEC-004-report.json",
    "c72": ROOT / "evidence/QLDPC-SCALE-001A-report.json",
}
PAYLOADS = {
    "c18": "a5c7e59fa849ddc37c070d78d4a4dab8b07ae5ceccfecefeb5a20f4ae0dc83a7",
    "c72": "198bb28f47844aa98efa20d8c838c48870a8aef41ccfda266b16661677e363e1",
}


def load_report(key: str) -> dict:
    report = json.loads(SOURCE[key].read_text(encoding="utf-8"))
    if report.get("payload_sha256") != PAYLOADS[key]:
        raise ValueError("protected report identity mismatch: " + key)
    if report.get("status") != "candidate_executable_not_promoted":
        raise ValueError("status drift: " + key)
    return report


def plot_semantics(c18: dict) -> None:
    per = c18["compiled_structure"]["per_algebra"]
    algebras = ["sum_product_bsc_p_0_1", "soft_tropical_base_2", "min_plus_hamming"]
    labels = ["BSC sum-product", "Base-2 partition", "Min-plus + keys"]
    numbers = [int(per[a]["retained_reachable_nodes"]) for a in algebras]
    assert numbers == [371, 371, 388]
    assert sum(numbers) == c18["compiled_structure"]["retained_reachable_nodes_total"] == 1130
    fig, ax = plt.subplots(figsize=(7.8, 3.1))
    fig.patch.set_facecolor("white")
    bars = ax.barh(labels[::-1], numbers[::-1], height=0.54,
                   color=["#555555", "#858585", "#222222"])
    ax.set_xlim(0, 450)
    for bar, number in zip(bars, numbers[::-1]):
        ax.text(bar.get_width() + 9, bar.get_y() + bar.get_height() / 2, str(number),
                va="center", fontsize=10)
    ax.set_xlabel("Reachable expression-DAG nodes (C18, fixed compile order)")
    ax.set_title("C18: exact reusable selector-parametric objects", pad=13, loc="left",
                 fontsize=13, weight="bold")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#E0E0E0", alpha=0.75)
    ax.set_axisbelow(True)
    fig.text(0.11, 0.015,
             "Protected TCM-QDEC-004 evidence. These are object sizes, not wall-time or memory comparisons.",
             fontsize=8, color="#444444")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUTPUT / "paper_a_c18_compiled_nodes.png", dpi=210)
    fig.savefig(OUTPUT / "paper_a_c18_compiled_nodes.svg")
    plt.close(fig)


def plot_structure(c72: dict) -> None:
    width = c72["elimination_order_audit"]["induced_width"]
    orders = ["lexicographic", "min_degree", "min_fill"]
    values = [int(width[o]) for o in orders]
    assert values == [24, 18, 18]
    labels = ["Lexicographic", "Min-degree", "Min-fill (frozen)"]
    fig, ax = plt.subplots(figsize=(7.8, 3.1))
    bars = ax.barh(labels[::-1], values[::-1], height=0.56,
                   color=["#222222", "#858585", "#555555"])
    for b, val in zip(bars, values[::-1]):
        ax.text(val + .3, b.get_y() + b.get_height() / 2, str(val),
                fontsize=10, va="center")
    ax.set_xlim(0, 28)
    ax.set_xlabel("Induced width of the named elimination order")
    ax.set_title("C72: observed width depends on the elimination order", pad=13, loc="left",
                 fontsize=13, weight="bold")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="#E0E0E0", alpha=0.75)
    ax.set_axisbelow(True)
    fig.text(0.11, 0.015,
             "Protected QLDPC-SCALE-001A evidence. Not a globally optimal treewidth certificate.",
             fontsize=8, color="#444444")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(OUTPUT / "paper_a_c72_elimination_width.png", dpi=210)
    fig.savefig(OUTPUT / "paper_a_c72_elimination_width.svg")
    plt.close(fig)


def plot_pipeline(c18: dict, c72: dict) -> None:
    # Diagram is descriptive; labels denote the theorem's construction, not
    # a measured timing result or a newly asserted implementation identity.
    fig, ax = plt.subplots(figsize=(9.4, 2.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    boxes = [
        (0.3, "Selector a\n+ degeneracy z", "Full-rank selector lift"),
        (3.5, "Physical bits e(a,z)", "Local exact qubit factors"),
        (6.7, "Eliminate only z", "Reuse one expression DAG"),
        (9.9, "Evaluate R(a)", "Exact class records"),
    ]
    for x, head, sub in boxes:
        block = patches.FancyBboxPatch((x, 0.75), 2.0, 1.65,
                                       boxstyle="round,pad=0.06,rounding_size=.12",
                                       linewidth=1.1, edgecolor="#222222", facecolor="#F6F6F6")
        ax.add_patch(block)
        ax.text(x + 1, 1.68, head, ha="center", va="center", fontsize=10, weight="bold")
        ax.text(x + 1, 1.03, sub, ha="center", va="center", fontsize=7.9, color="#444444")
    for i in range(3):
        x = boxes[i][0] + 2.15
        ax.annotate("", xy=(boxes[i+1][0] - .12, 1.57), xytext=(x, 1.57),
                    arrowprops={"arrowstyle":"->", "lw":1.45, "color":"#111111"})
    ax.text(0.3, 2.85, "Selector-parametric exact inference", fontsize=13, weight="bold", va="top")
    ax.text(0.3, .25, "Theorem: specialization of R at any a equals fixed-selector exact elimination (under the stated full-kernel and semiring hypotheses).",
            fontsize=8.3, color="#333333")
    fig.tight_layout()
    fig.savefig(OUTPUT / "paper_a_selector_pipeline.png", dpi=210)
    fig.savefig(OUTPUT / "paper_a_selector_pipeline.svg")
    plt.close(fig)


def main() -> int:
    c18, c72 = load_report("c18"), load_report("c72")
    plot_semantics(c18)
    plot_structure(c72)
    plot_pipeline(c18, c72)
    for name in sorted(OUTPUT.glob("paper_a_*.png")):
        print(name.relative_to(ROOT), name.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
