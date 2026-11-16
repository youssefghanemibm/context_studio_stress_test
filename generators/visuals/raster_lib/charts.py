"""matplotlib charts rendered to PIL images, so the data exists only in pixels.

Deterministic: Agg backend, DejaVu Sans, no PNG metadata, fixed dpi.
"""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 15,
    "axes.titlesize": 19,
    "axes.titleweight": "bold",
    "axes.labelsize": 16,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 14,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "svg.hashsalt": "corvane",
    "path.simplify": False,
})

SERIES = ["#1F4E8C", "#0E7C7B", "#B26A00", "#5B3F95", "#B3261E", "#6B7787"]


def fig_to_image(fig, dpi: int = 150) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, metadata={"Software": None}, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    im = Image.open(buf)
    im.load()
    return im.convert("RGB")


def new_fig(w_in: float = 12, h_in: float = 6.5, dark: bool = False):
    if dark:
        fig, ax = plt.subplots(figsize=(w_in, h_in), facecolor="#16233A")
        ax.set_facecolor("#16233A")
        for sp in ax.spines.values():
            sp.set_color("#5E6F8F")
        ax.tick_params(colors="#EAF0FA")
        ax.xaxis.label.set_color("#EAF0FA")
        ax.yaxis.label.set_color("#EAF0FA")
        ax.title.set_color("#EAF0FA")
    else:
        fig, ax = plt.subplots(figsize=(w_in, h_in), facecolor="white")
    return fig, ax


def bar_chart(categories, values, title: str = "", ylabel: str = "", value_labels=None, colors=None,
              w_in: float = 12, h_in: float = 6.5, dark: bool = False, ylim=None, annotate_size: int = 17,
              note: str = "", horizontal: bool = False) -> Image.Image:
    fig, ax = new_fig(w_in, h_in, dark)
    cols = colors or [SERIES[i % len(SERIES)] for i in range(len(values))]
    if horizontal:
        bars = ax.barh(categories, values, color=cols)
        ax.invert_yaxis()
    else:
        bars = ax.bar(categories, values, color=cols, width=0.6)
    if title:
        ax.set_title(title, loc="left", pad=16)
    if ylabel:
        (ax.set_xlabel if horizontal else ax.set_ylabel)(ylabel)
    if ylim:
        (ax.set_xlim if horizontal else ax.set_ylim)(*ylim)
    if value_labels:
        for b, lab in zip(bars, value_labels):
            if not lab:
                continue
            if horizontal:
                ax.annotate(lab, (b.get_width(), b.get_y() + b.get_height() / 2), xytext=(8, 0),
                            textcoords="offset points", va="center", fontsize=annotate_size, fontweight="bold",
                            color="#EAF0FA" if dark else "#1B2430")
            else:
                ax.annotate(lab, (b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 8),
                            textcoords="offset points", ha="center", fontsize=annotate_size, fontweight="bold",
                            color="#EAF0FA" if dark else "#1B2430")
    ax.grid(axis="x" if horizontal else "y", color="#D5DBE3" if not dark else "#2A3B5C", linewidth=0.8)
    ax.set_axisbelow(True)
    if note:
        fig.text(0.01, 0.01, note, fontsize=12, color="#6B7787" if not dark else "#A9B7CF")
    fig.tight_layout(rect=(0, 0.04 if note else 0, 1, 1))
    return fig_to_image(fig)


def line_chart(x, ys: dict, title: str = "", ylabel: str = "", annotate=None, w_in: float = 12, h_in: float = 6.5,
               dark: bool = False, step: bool = False, ylim=None, note: str = "", xtick_labels=None,
               marker: str = "o", annotate_size: int = 16) -> Image.Image:
    """annotate: list of (x, y, text, (dx, dy)) annotations drawn with arrows."""
    fig, ax = new_fig(w_in, h_in, dark)
    for i, (name, y) in enumerate(ys.items()):
        if step:
            ax.step(x, y, where="post", color=SERIES[i % len(SERIES)], linewidth=3, label=name)
        else:
            ax.plot(x, y, color=SERIES[i % len(SERIES)], linewidth=3, marker=marker, markersize=8, label=name)
    if title:
        ax.set_title(title, loc="left", pad=16)
    if ylabel:
        ax.set_ylabel(ylabel)
    if ylim:
        ax.set_ylim(*ylim)
    if xtick_labels:
        ax.set_xticks(range(len(xtick_labels)))
        ax.set_xticklabels(xtick_labels)
    for (ax_x, ax_y, txt, off) in (annotate or []):
        ax.annotate(txt, (ax_x, ax_y), xytext=off, textcoords="offset points", fontsize=annotate_size,
                    fontweight="bold", color="#1B2430" if not dark else "#EAF0FA",
                    bbox=dict(boxstyle="round,pad=0.35", fc="white" if not dark else "#203453",
                              ec="#5A6678", lw=1),
                    arrowprops=dict(arrowstyle="->", color="#5A6678", lw=1.5))
    if len(ys) > 1:
        ax.legend(frameon=False, loc="best")
    ax.grid(axis="y", color="#D5DBE3" if not dark else "#2A3B5C", linewidth=0.8)
    ax.set_axisbelow(True)
    if note:
        fig.text(0.01, 0.01, note, fontsize=12, color="#6B7787")
    fig.tight_layout(rect=(0, 0.04 if note else 0, 1, 1))
    return fig_to_image(fig)


def donut(labels, values, title: str = "", colors=None, w_in: float = 9, h_in: float = 7, show_values=False,
          center_text: str = "") -> Image.Image:
    fig, ax = new_fig(w_in, h_in)
    cols = colors or SERIES[:len(values)]
    wedges, _ = ax.pie(values, colors=cols, startangle=90, counterclock=False,
                       wedgeprops=dict(width=0.38, edgecolor="white", linewidth=3))
    ax.axis("equal")
    if center_text:
        ax.text(0, 0, center_text, ha="center", va="center", fontsize=18, fontweight="bold", color="#1B2430")
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.95, 0.5), frameon=False, fontsize=16)
    if title:
        ax.set_title(title, loc="left", pad=12)
    fig.tight_layout()
    return fig_to_image(fig)


def grouped_bars(categories, series: dict, title: str = "", ylabel: str = "", w_in: float = 12, h_in: float = 6.5,
                 value_fmt: str | None = "{:,.0f}", dark: bool = False, note: str = "") -> Image.Image:
    import numpy as np
    fig, ax = new_fig(w_in, h_in, dark)
    n = len(series)
    x = np.arange(len(categories))
    bw = 0.8 / max(n, 1)
    for i, (name, vals) in enumerate(series.items()):
        bars = ax.bar(x + (i - (n - 1) / 2) * bw, vals, bw * 0.92, label=name, color=SERIES[i % len(SERIES)])
        if value_fmt:
            for b, v in zip(bars, vals):
                ax.annotate(value_fmt.format(v), (b.get_x() + b.get_width() / 2, b.get_height()), xytext=(0, 6),
                            textcoords="offset points", ha="center", fontsize=14, fontweight="bold",
                            color="#1B2430" if not dark else "#EAF0FA")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    if title:
        ax.set_title(title, loc="left", pad=16)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.legend(frameon=False)
    ax.grid(axis="y", color="#D5DBE3" if not dark else "#2A3B5C", linewidth=0.8)
    ax.set_axisbelow(True)
    if note:
        fig.text(0.01, 0.01, note, fontsize=12, color="#6B7787")
    fig.tight_layout(rect=(0, 0.04 if note else 0, 1, 1))
    return fig_to_image(fig)


def histogram_bins(edges_labels, counts, title: str = "", dark: bool = True, w_in: float = 11, h_in: float = 5.2,
                   highlight_from: int | None = None, xlabel: str = "", ylabel: str = "",
                   vlines=None) -> Image.Image:
    """Bars for pre-binned data; bins from index `highlight_from` drawn in the warning colour.
    vlines: list of (bin_position_float, label)."""
    fig, ax = new_fig(w_in, h_in, dark)
    cols = ["#36C2B4" if (highlight_from is None or i < highlight_from) else "#F2B84B" for i in range(len(counts))]
    ax.bar(range(len(counts)), counts, color=cols, width=0.85)
    ax.set_xticks(range(len(counts)))
    ax.set_xticklabels(edges_labels, rotation=0)
    if title:
        ax.set_title(title, loc="left", pad=14)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    for pos, lab in (vlines or []):
        ax.axvline(pos, color="#FF6B6B", linestyle="--", linewidth=2.5)
        ax.text(pos + 0.08, ax.get_ylim()[1] * 0.92, lab, color="#FF6B6B", fontsize=15, fontweight="bold")
    ax.grid(axis="y", color="#2A3B5C" if dark else "#D5DBE3", linewidth=0.8)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig_to_image(fig)
