from copy import Error

from enum import StrEnum
from pathlib import Path
from .constants import c_default_short_figsize

# ACM recommended fonttypes
import matplotlib

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42


class GraphDefaults(StrEnum):
    short = "short"
    long = "long"


def init(proj_root: Path, graph_defaults: GraphDefaults):
    """Initialize global variables for this module.

    If you use ccds datascience this removes the need to specify storage locations for every function

    Args:
        proj_root: root directory of your ccds project. Hint: Pass config.PROJ_ROOT
        graph_defaults: kind of paper to setup defaults for some configuration parameters. Allowed values: `short`
    """
    global PROJ_ROOT
    PROJ_ROOT = proj_root

    set_graphic_defaults(graph_defaults)


def set_graphic_defaults(graph_defaults: str):
    if graph_defaults == "short":
        set_short_paper_graphic_defaults()
    else:
        raise Error("Not implemented yet")


def set_short_paper_graphic_defaults():
    global c_figsize
    c_figsize = c_default_short_figsize
