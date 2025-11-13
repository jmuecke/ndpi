from matplotlib.axes import Axes
from matplotlib.dates import DateFormatter


TIME_AXIS_LABEL = "TIME "


def polars_unit_to_str(format: str) -> str:
    mapper = {
        "m": " min",
        "ns": " ns",
        "us": " us",
        "ms": " ms",
        "s": " s",
        "h": " h",
        "d": " d",
        "w": " w",
        "mo": " mo",
        "q": " q",
        "y": " y",
        "i": " index",
    }

    for old, new in mapper.items():
        format = format.replace(old, new)

    return format


def strftime_to_display(format_string):
    """Convert strftime format to human-readable display format."""
    replacements = {
        "%Y": "YYYY",
        "%y": "YY",
        "%m": "MM",
        "%d": "DD",
        "%H": "HH",
        "%I": "HH",
        "%M": "MM",
        "%S": "SS",
        "%p": "AM/PM",
        "%B": "Month",
        "%b": "Mon",
        "%A": "Weekday",
        "%a": "Day",
        "%f": "microseconds",
        "%z": "timezone",
        "%Z": "TZ",
    }

    result = format_string
    for pattern, display in replacements.items():
        result = result.replace(pattern, display)

    return result


def set_time_format(axis, format: str, unit: str):
    axis.set_label_text(time_label(format, unit))
    axis.set_major_formatter(DateFormatter(format))


def time_label(format: str, unit: str):
    return (
        f"{TIME_AXIS_LABEL} {strftime_to_display(format)} [{polars_unit_to_str(unit)}]"
    )
