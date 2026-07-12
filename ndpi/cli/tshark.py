import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass

import click

DEFAULT_DISABLED_OPTIONS = [
    ("ip.decode_tos_as_diffserv", "FALSE"),
    ("ip.defragment", "FALSE"),
    ("ip.summary_in_tree", "FALSE"),
    ("ip.check_checksum", "FALSE"),
    ("ip.tso_support", "FALSE"),
    ("ip.security_flag", "FALSE"),
    ("ip.try_heuristic_first", "FALSE"),
    ("udp.summary_in_tree", "FALSE"),
    ("udp.try_heuristic_first", "FALSE"),
    ("udp.check_checksum", "FALSE"),
    ("udp.process_info", "FALSE"),
    ("udp.calculate_timestamps", "FALSE"),
    ("gquic.debug.quic", "FALSE"),
]

FZF_HELP_REMARK = (
    "Tab/Shift-Tab toggles the hovered field, Enter confirms the selection, "
    "Alt-a selects all, Alt-d deselects all."
)


@dataclass
class TsharkField:
    name: str
    description: str = ""
    datatype: str = ""
    protocol: str = ""

    def display(self) -> str:
        extras = ", ".join(v for v in (self.description, self.datatype, self.protocol) if v)
        return f"{self.name} ({extras})" if extras else self.name


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if path is None:
        raise click.ClickException(f"'{binary}' was not found on PATH")
    return path


def query_fields() -> list[TsharkField]:
    """Ask the locally installed tshark for its field list.

    Queried live (not cached) so the field list always matches whatever
    tshark version the user actually has installed.
    """
    tshark_bin = _require("tshark")
    result = subprocess.run(
        [tshark_bin, "-G", "fields"], capture_output=True, text=True, check=True
    )

    fields = []
    for line in result.stdout.splitlines():
        columns = line.split("\t")
        if len(columns) < 3 or columns[0] not in ("F", "P"):
            continue
        fields.append(
            TsharkField(
                name=columns[2],
                description=columns[1],
                datatype=columns[3] if len(columns) > 3 else "",
                protocol=columns[4] if len(columns) > 4 else "",
            )
        )
    return fields


def select_fields(fields: list[TsharkField]) -> list[str]:
    fzf_bin = _require("fzf")
    listing = "\n".join(field.display() for field in fields)

    # Ignore the user's FZF_DEFAULT_OPTS: this picker's keybindings (multi-select
    # via tab/shift-tab, alt-a/alt-d) must behave the same for everyone regardless
    # of personal fzf config.
    env = os.environ.copy()
    env.pop("FZF_DEFAULT_OPTS", None)

    result = subprocess.run(
        [
            fzf_bin,
            "--multi",
            "--bind",
            "tab:toggle+down,shift-tab:toggle+up,alt-a:select-all,alt-d:deselect-all",
            "--marker",
            "*",
            "--header",
            f"Choose wireshark fields. {FZF_HELP_REMARK}",
        ],
        input=listing,
        capture_output=True,
        text=True,
        env=env,
    )
    # fzf exits 1 when nothing matches and 130 when the user aborts (esc/ctrl-c).
    if result.returncode not in (0, 1, 130):
        raise click.ClickException(f"fzf failed: {result.stderr.strip()}")

    return [line.split(" ", 1)[0] for line in result.stdout.splitlines() if line.strip()]


def build_command(
    field_names: list[str],
    only_fields: bool = False,
    include_disable_options: bool = True,
    output_format: str = "fields",
    separator: str = "|",
) -> str:
    lines = []
    if not only_fields:
        header = f"tshark -nr - -w - -T {shlex.quote(output_format)}"
        if output_format == "fields":
            header += f" -E {shlex.quote(f'separator={separator}')}"
        lines.append(header + " \\")

        if include_disable_options:
            for option, value in DEFAULT_DISABLED_OPTIONS:
                lines.append(f'  -o "{option}:{value}" \\')
    lines.extend(f"  -e {name} \\" for name in field_names)
    if lines:
        lines[-1] = lines[-1].rstrip(" \\")
    return "\n".join(lines)


def _command_building_options(f):
    """Options controlling how `extract` renders the tshark command."""
    f = click.option(
        "--only-fields",
        is_flag=True,
        help="Only emit -e flags; skip the tshark invocation and -o preamble entirely.",
    )(f)
    f = click.option(
        "--no-disable-options",
        is_flag=True,
        help="Skip the recommended -o disable options, but keep the tshark invocation.",
    )(f)
    f = click.option(
        "--output-format",
        "-T",
        default="fields",
        show_default=True,
        help="Value passed to tshark's -T, e.g. fields, json, pdml, psml, ek, text.",
    )(f)
    f = click.option(
        "--separator",
        "-E",
        default="|",
        show_default=True,
        help="Field separator used when --output-format is 'fields' (passed as -E separator=...).",
    )(f)
    return f


@click.group()
def tshark():
    """Build tshark field-extraction commands."""


@tshark.command(name="fields", short_help="Print all fields tshark knows about.")
def list_fields():
    """Print every field known to the locally installed tshark (via `tshark -G fields`).

    One field per line, formatted as `name (description, datatype, protocol)`
    with any missing parts omitted, e.g. `ip.src (Source Address, FT_IPv4, ip)`.
    """
    for field in query_fields():
        click.echo(field.display())


@tshark.command(
    name="select",
    short_help="Interactively select fields via fzf.",
    help=f"Interactively select fields via fzf.\n\n{FZF_HELP_REMARK} Selected field names are printed one per line.",
)
def select():
    for name in select_fields(query_fields()):
        click.echo(name)


@tshark.command(
    name="extract",
    short_help="Build a tshark command from selected fields.",
    help=(
        "Build a tshark command from field names.\n\n"
        "Field names are taken, in order of preference, from: (1) arguments, "
        "(2) stdin piped in one per line, e.g. via "
        "`ndpi tshark select | ndpi tshark extract`, or (3) if neither is "
        f"given, an interactive fzf picker ({FZF_HELP_REMARK})"
    ),
)
@_command_building_options
@click.argument("field_names", nargs=-1)
def extract(
    only_fields: bool,
    no_disable_options: bool,
    output_format: str,
    separator: str,
    field_names: tuple[str, ...],
):
    if field_names:
        names = list(field_names)
    elif not sys.stdin.isatty():
        names = [line.strip() for line in sys.stdin if line.strip()]
    else:
        names = select_fields(query_fields())

    if not names:
        raise click.ClickException("No fields selected.")
    click.echo(
        build_command(
            names,
            only_fields=only_fields,
            include_disable_options=not no_disable_options,
            output_format=output_format,
            separator=separator,
        )
    )
