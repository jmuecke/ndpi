from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class GraphStyle(StrEnum):
    short = "short"
    long = "long"


@dataclass(frozen=True)
class GraphicPreset:
    figsize: tuple[float, float]


# One place to add new preset fields (font sizes, dpi, ...) later without
# touching call sites -- they all go through `settings.figsize` etc.
# `long` is intentionally missing -- there's no defined preset for it yet;
# selecting it raises NotImplementedError from `Settings.figsize` below.
GRAPHIC_PRESETS: dict[GraphStyle, GraphicPreset] = {
    GraphStyle.short: GraphicPreset(figsize=(6, 1.5)),
}


def _autodetect_proj_root(start: Path | None = None) -> Path:
    """Walk up from `start` (default: cwd) for a directory containing both
    `.env` and `pyproject.toml` -- the combination ccds datascience projects
    always have at their root. Requiring both avoids false positives from an
    unrelated ancestor `.env` (home directory, an enclosing monorepo, ...).
    """
    directory = (start or Path.cwd()).resolve()
    for candidate in (directory, *directory.parents):
        if (candidate / ".env").is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError(
        "Could not auto-detect the project root (no ancestor directory has both "
        "a .env and a pyproject.toml). Set it explicitly: ndpi.configure(proj_root=...)"
    )


@dataclass
class Settings:
    _proj_root: Path | None = None
    graph_style: GraphStyle = GraphStyle.short

    # `proj_root` is resolved lazily on first access (not at Settings()
    # construction, and not at import time) -- so importing ndpi never
    # fails, only actually using a path does, and only if nothing has set
    # one by then.
    @property
    def proj_root(self) -> Path:
        if self._proj_root is None:
            self._proj_root = _autodetect_proj_root()
        return self._proj_root

    @proj_root.setter
    def proj_root(self, value: Path) -> None:
        self._proj_root = Path(value)

    # -- ccds data layout, derived from proj_root --
    @property
    def data_dir(self) -> Path:
        return self.proj_root / "data"

    @property
    def raw_data_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def interim_data_dir(self) -> Path:
        return self.data_dir / "interim"

    @property
    def processed_data_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def external_data_dir(self) -> Path:
        return self.data_dir / "external"

    @property
    def models_dir(self) -> Path:
        return self.proj_root / "models"

    @property
    def reports_dir(self) -> Path:
        return self.proj_root / "reports"

    @property
    def figures_dir(self) -> Path:
        return self.reports_dir / "figures"

    # -- graphics preset, derived from graph_style --
    @property
    def figsize(self) -> tuple[float, float]:
        try:
            return GRAPHIC_PRESETS[self.graph_style].figsize
        except KeyError:
            raise NotImplementedError(
                f"No graphic preset defined yet for graph_style={self.graph_style!r}"
            ) from None


# Module-level singleton with working defaults. Constructing it never fails
# (no auto-detection runs yet) -- only reading a path-derived property does.
settings = Settings()


def configure(
    proj_root: Path | str | None = None,
    graph_style: GraphStyle | str | None = None,
) -> None:
    """Override settings that would otherwise be auto-detected/defaulted.

    Optional: `settings` already works without calling this, as long as
    proj_root can be auto-detected and the default graph_style is fine. Call
    this to point at a different proj_root (auto-detection failed, or you
    want a non-cwd project) or to pick a paper size other than the default.
    Can be called at any point before settings are actually read -- there is
    no import-order requirement.
    """
    if proj_root is not None:
        settings.proj_root = Path(proj_root)
    if graph_style is not None:
        settings.graph_style = GraphStyle(graph_style)
