from matplotlib.axes import Axes
from matplotlib.dates import DateFormatter
import re


TIME_AXIS_LABEL = "Time "


def polars_unit_to_str(format: str) -> str:
    mapper = {
        "i": " index",
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
    }
    pattern = re.compile(
        r"(\d+)(" + "|".join(re.escape(k) for k in mapper.keys()) + r")\b"
    )

    return pattern.sub(lambda m: m.group(1) + mapper[m.group(2)], format)


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
        "\n": " ",
    }

    result = format_string
    for pattern, display in replacements.items():
        result = result.replace(pattern, display)

    return result


def set_time_format(axis, format: str, unit: str, prefix: str = TIME_AXIS_LABEL):
    axis.set_label_text(time_label(format, unit, prefix))
    axis.set_major_formatter(DateFormatter(format))


def time_label(format: str, unit: str, prefix: str = TIME_AXIS_LABEL):
    formatted_unit = ""
    if unit != "":
        formatted_unit = f" [{polars_unit_to_str(unit)}]"
    return f"{prefix} {strftime_to_display(format)}{formatted_unit}"
