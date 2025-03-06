import polars as pl
from typing import Any, Callable, Tuple, Union


def filter(
    df, filter: Union[pl.Expr, Callable], name: Union[str, None] = None, id_col="id"
) -> Tuple[pl.LazyFrame, pl.DataFrame]:
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

    len_in = df.select(pl.len()).collect()
    ids = df.select(id_col)

    if isinstance(filter, pl.Expr):
        df_out = df.filter(filter)
    else:
        df_out = filter(df)

    len_out = df_out.select(pl.len()).collect()
    filtered = ids.join(df_out, on=id_col, how="anti").collect().get_column(id_col)

    if name is None:
        # Add default name from function name
        name = getattr(filter, "__name__", "Unknown").split("filter_", maxsplit=1)[-1]

    stat = {
        "name": name,
        "before": len_in,
        "after": len_out,
        "reduction": len_in - len_out,
        "ids": [filtered],
    }

    return df_out, pl.DataFrame(stat)


def apply_filters(
    df: Union[pl.DataFrame, pl.LazyFrame], filters: list
) -> Tuple[pl.LazyFrame, pl.DataFrame]:
    """Apply a set of filters in order to `df`.

    Args:
        df: to apply filters on
        filters: list of filters with (filter_function, optional_filter_name)

    Returns:

    """
    df = df.lazy()

    stats = []
    for f, *name in filters:
        name = name[0] if len(name) > 0 else None

        df, stat = filter(df, f, name)
        stats.append(stat)
    return df, pl.concat(stats)
