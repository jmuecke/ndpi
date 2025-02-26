from pathlib import Path
from enum import StrEnum

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from typing import Tuple

from ndpi.init import c_figsize
from ndpi.config import FIGURES_DIR


def fig_ax(figsize: tuple = c_figsize, **kwargs) -> Tuple[Figure, Axes]:
    """Wrapper for plt.subplots with default figure size.

    Args:
        figsize: figsize for plt.sublots, default chosen based on paper kind
        **kwargs: kwargs for plt.subplots

    Returns:
        tuple[Figure, Axes]: similar to plt.subplots
    """
    return plt.subplots(figsize=figsize, **kwargs)


def save_plot(
    fig: Figure, file_name: str, directory: Path = FIGURES_DIR, autoclose: bool = False
):
    """Save figure into FIGURES_DIR in high resolution png and pdf format.

    Args:
        fig: matplotlib figure
        file_name: filename without file extensions. Suggested pattern: f'{3ltr_plot_kind}_{description}'
        directory: destination folder, default: FIGURES_DIR
        autoclose: autoclose matplotlib figures
    """
    if file_name is not None:
        print(directory / f"{file_name}.png")
        fig.savefig(directory / f"{file_name}.png", bbox_inches="tight", dpi=200)
        fig.savefig(directory / f"{file_name}.pdf", bbox_inches="tight")

    if autoclose:
        plt.close()
