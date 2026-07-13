from contextlib import AsyncExitStack
from pathlib import Path
from enum import StrEnum

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Tuple

from ndpi.settings import settings
from ndpi.visualization.helpers.labels import set_time_format


def fig_ax(figsize: tuple | None = None, **kwargs) -> Tuple[Figure, Axes]:
    """Wrapper for plt.subplots with default figure size.

    Args:
        figsize: figsize for plt.sublots, default: settings.figsize (chosen based on paper kind)
        **kwargs: kwargs for plt.subplots

    Returns:
        tuple[Figure, Axes]: similar to plt.subplots
    """
    return plt.subplots(figsize=figsize or settings.figsize, **kwargs)


def legend_upper_center(ax: Axes, **kwargs):
    """Place the legend above the axes, horizontally centered.

    The legend itself is anchored by its lower-center point, so it sits
    just above the axes rather than overlapping the plotted data.

    Args:
        ax: axes to attach the legend to
        **kwargs: kwargs for Axes.legend
    """
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1), **kwargs)


def legend_upper_right(ax: Axes, **kwargs):
    """Place the legend above the axes, aligned to the right edge.

    The legend itself is anchored by its lower-right point, so it sits
    just above the axes rather than overlapping the plotted data.

    Args:
        ax: axes to attach the legend to
        **kwargs: kwargs for Axes.legend
    """
    ax.legend(loc="lower right", bbox_to_anchor=(0.5, 1), **kwargs)


def mark_axis_break(
    ax1: Axes, ax2: Axes, axis: str = "x", d: float = 0.3, markersize: float = 8
):
    """Draw a `//` cut mark on the shared edge of two broken axes.

    Hides the spine between ax1 and ax2 and draws diagonal markers on both
    sides to indicate a break in the axis. For axis="x", ax1/ax2 are the
    left/right axes of a horizontal break; for axis="y", ax1/ax2 are the
    top/bottom axes of a vertical break. Only the axis whose tick labels
    would be redundant next to the break (ax2's y-axis for a horizontal
    break, ax1's x-axis for a vertical break) is hidden, so the pair still
    reads like a single labeled axis.

    Args:
        ax1: left (axis="x") or top (axis="y") axes of the break
        ax2: right (axis="x") or bottom (axis="y") axes of the break
        axis: "x" for a horizontal break, "y" for a vertical break
        d: half-length of the diagonal marker, in axes fraction units
        markersize: marker size passed to Axes.plot
    """
    kwargs = dict(
        markersize=markersize,
        linestyle="none",
        color="k",
        mec="k",
        mew=1,
        clip_on=False,
    )

    if axis == "x":
        ax1.spines["right"].set_visible(False)
        ax2.spines["left"].set_visible(False)
        ax2.tick_params(labelleft=False, left=False)
        ax1.plot(
            [1, 1], [0, 1], transform=ax1.transAxes, marker=[(-d, -1), (d, 1)], **kwargs
        )
        ax2.plot(
            [0, 0], [0, 1], transform=ax2.transAxes, marker=[(-d, -1), (d, 1)], **kwargs
        )
    elif axis == "y":
        ax1.spines["bottom"].set_visible(False)
        ax2.spines["top"].set_visible(False)
        ax1.tick_params(labelbottom=False, bottom=False)
        ax1.plot(
            [0, 1], [0, 0], transform=ax1.transAxes, marker=[(-1, -d), (1, d)], **kwargs
        )
        ax2.plot(
            [0, 1], [1, 1], transform=ax2.transAxes, marker=[(-1, -d), (1, d)], **kwargs
        )
    else:
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")


def center_label(fig: Figure, axes: list[Axes], axis: str = "x"):
    """Center the x- or y-axis label of the first axes across a row/column of axes.

    Useful when a row or column is split into multiple axes (e.g. via
    mark_axis_break) but only the first axes carries the axis label, which
    by default centers under/beside itself rather than across the whole
    row/column.

    Args:
        fig: figure containing axes
        axes: axes forming one logical row (axis="x", left to right) or
            column (axis="y", top to bottom); the label of axes[0] is
            repositioned to center across axes[0]..axes[-1]
        axis: "x" to center the x-axis label, "y" to center the y-axis label
    """
    if axis == "x":
        start = axes[0].get_position().x0
        end = axes[-1].get_position().x1
        label = axes[0].xaxis.label
        component = 0
    elif axis == "y":
        start = axes[-1].get_position().y0
        end = axes[0].get_position().y1
        label = axes[0].yaxis.label
        component = 1
    else:
        raise ValueError(f"axis must be 'x' or 'y', got {axis!r}")

    center_fig = (start + end) / 2
    fig_point = (center_fig, 0.0) if axis == "x" else (0.0, center_fig)
    center_axes = (
        axes[0]
        .transAxes.inverted()
        .transform(fig.transFigure.transform(fig_point))[component]
    )
    if axis == "x":
        label.set_x(center_axes)
    else:
        label.set_y(center_axes)
    fig.canvas.draw()


def row_title(
    fig: Figure, ax_left: Axes, ax_right: Axes, title: str, pad: float = 0.01, **kwargs
):
    """Center a title above a pair of axes that together form one logical row.

    Useful for grids where a row is split into multiple axes (e.g. via
    mark_axis_break) and a single title should span all of them.

    Args:
        fig: figure containing ax_left and ax_right
        ax_left: leftmost axes of the row
        ax_right: rightmost axes of the row
        title: title text
        pad: vertical gap between the axes and the title, in figure fraction units
        **kwargs: kwargs for Figure.text
    """
    pos_left = ax_left.get_position()
    pos_right = ax_right.get_position()
    fig.text(
        (pos_left.x0 + pos_right.x1) / 2,
        pos_left.y1 + pad,
        title,
        ha="center",
        va="bottom",
        **kwargs,
    )


def save_plot(
    fig: Figure, file_name: str, directory: Path | None = None, autoclose: bool = False
):
    """Save figure into settings.figures_dir in high resolution png and pdf format.

    Args:
        fig: matplotlib figure
        file_name: filename without file extensions. Suggested pattern: f'{3ltr_plot_kind}_{description}'
        directory: destination folder, default: settings.figures_dir
        autoclose: autoclose matplotlib figures
    """
    directory = directory or settings.figures_dir
    if file_name is not None:
        print(directory / f"{file_name}.png")
        fig.savefig(directory / f"{file_name}.png", bbox_inches="tight", dpi=200)
        fig.savefig(directory / f"{file_name}.pdf", bbox_inches="tight")

    if autoclose:
        plt.close()
