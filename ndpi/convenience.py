from typing import Union
from numpy import isin
from .config import PROCESSED_DATA_DIR
from pathlib import Path
import polars as pl
import os


def load_data(
    name: Union[str, list[str]],
    skip_missing: bool = False,
    default_ext: str = ".pq.zst",
    directory: Path = PROCESSED_DATA_DIR,
    **kwargs,
) -> pl.LazyFrame:
    """Read one or more files from directory in concise notation.

    Args:
        name: input file or files
        skip_missing: if True skip missing files otherwise throws an error
        default_ext: expected extension after each input filename
        directory: directory to search for files to read
        **kwargs: kwargs for pl.scan_parquet

    Returns:
        pl.LazyFrame from all input files
    """
    files = name
    if not isinstance(files, list):
        files = [name]

    files = [directory / f"{file}{default_ext}" for file in files]

    existing = [file for file in name if os.path.isfile(file)]
    if not skip_missing:
        assert len(existing) == len(
            name
        ), f"Input files missing: {set(name) - set(existing)}"

    return pl.concat([pl.scan_parquet(file, **kwargs) for file in existing])
