from functools import partial
import polars as pl
from typing import Any, Callable, Tuple, Union
from tqdm.auto import tqdm
import time


def extract_function_name(filter: Callable):
    name = getattr(filter, "__name__", "Unknown")
    if isinstance(filter, partial):
        name = getattr(filter.func, "__name__", "Unknown")
    return name


def filter(
    df, fltr: Union[pl.Expr, Callable], id_col="id"
) -> Tuple[pl.LazyFrame, list[pl.LazyFrame]]:
    """Common filtering API. Returns filtered dataframe and metadata on the filtered IDs.

    Args:
        df: input dataframe
        id_col: column with unique value
        filter: polars expression or filter function that operates on a dataframe
        name: label for this filtering step

    Returns:
        Tuple with filtered lazy dataframe and metadata
    """
    # Cast to lazy
    df = df.lazy()

    len_in = df.select(pl.len())
    ids = df.select(id_col)

    if isinstance(fltr, pl.Expr):
        df_out = df.filter(fltr)
    else:
        df_out = fltr(df)

    len_out = df_out.select(pl.len())
    filtered = ids.join(df_out, on=id_col, how="anti").select(id_col)

    stat = [len_in, len_out, filtered]

    return df_out, stat


def assemble_meta_frame(
    meta_information: list[pl.LazyFrame], name: Union[str, None] = None
) -> pl.DataFrame:
    evaluated = pl.collect_all(meta_information)

    return pl.DataFrame(
        {
            "before": [x.item() for x in evaluated[0::3]],
            "after": [x.item() for x in evaluated[1::3]],
            "ids": [x.get_columns()[0] for x in evaluated[2::3]],
            "name": name,
        }
    )


def apply_filters(
    df: Union[pl.DataFrame, pl.LazyFrame], filters: list
) -> Tuple[pl.LazyFrame, list[pl.LazyFrame], list[str]]:
    """Apply a set of filters in order to `df`.

    Args:
        df: to apply filters on
        filters: list of filters with (filter_function, optional_filter_name)

    Returns:

    """
    df = df.lazy()

    stats = []
    names = []
    filters = [item if isinstance(item, tuple) else (item, None) for item in filters]

    for f, *name in (pbar := tqdm(filters)):
        name = name[0] if len(name) > 0 else None
        if name is None:
            name = extract_function_name(f)
        pbar.set_postfix_str(str(name))

        df, stat = filter(df, f)
        stats.extend(stat)
        names.append(name)
    return df, stats, names
