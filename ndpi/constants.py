from enum import StrEnum


c_default_short_figsize = (6, 1.5)
"""Default short paper figure size"""


class GraphName(StrEnum):
    """StrEnum for three letter graph names.

    Attributes:
        bar: "bar"
        scatter: "sca"
    """

    bar = "bar"
    scatter = "sca"
