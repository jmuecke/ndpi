from pathlib import Path
from .constants import *


def init(proj_root: Path, graph_defaults: str):
    global PROJ_ROOT
    PROJ_ROOT = proj_root


def set_graphic_defaults(graph_defaults: str):
    if graph_defaults == "short":
        set_short_paper_graphic_defaults()


def set_short_paper_graphic_defaults():
    global c_figsize
    c_figsize = c_default_short_figsize
