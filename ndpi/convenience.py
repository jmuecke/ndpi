from typing import Union
from .config import PROCESSED_DATA_DIR
from pathlib import Path
import polars as pl
import os
import shutil


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
            files
        ), f"Input files missing: {set([str(file) for file in files]) - set(existing)}"

    return pl.concat([pl.scan_parquet(file, **kwargs) for file in existing])


def sink_parquet(df: pl.LazyFrame, path: Union[str, Path], **kwargs):
    """A wrapper for `pl.sink_parquet` that writes to `f"{path}.temp"` and then moves the file to `path`. This allows working with the existing dataset until the file is replaced

    Args:
        path: str or Path to the destination file
        **kwargs: kwargs for sink_parquet
    """
    temp_path = f"{path}.temp"
    df.sink_parquet(path=temp_path, **kwargs)
    shutil.move(temp_path, path)


def write_parquet(df: pl.DataFrame, path: Union[str, Path], **kwargs):
    """A wrapper for `pl.write_parquet` that writes to `f"{path}.temp"` and then moves the file to `path`. This allows working with the existing dataset until the file is replaced

    Args:
        path: str or Path to the destination file
        **kwargs: kwargs for sink_parquet
    """
    temp_path = f"{path}.temp"
    df.write_parquet(file=temp_path, **kwargs)
    shutil.move(temp_path, path)
