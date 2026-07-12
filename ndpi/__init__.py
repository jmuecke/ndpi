import matplotlib

from .settings import GraphStyle, Settings, configure, settings

# ACM recommended fonttypes.
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

__all__ = ["GraphStyle", "Settings", "configure", "settings"]
