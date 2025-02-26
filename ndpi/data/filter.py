import polars as pl
from typing import Any, Callable, Tuple, Union


def filter(
    df, filter: Union[pl.Expr, Callable], name: str, id_col="id"
) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """Common filtering API. Returns filtered dataframe and metadata on the filtered IDs.

    Args:
        df: input dataframe
        id_col: column with unique value
        filter: polars expression or filter function that operates on a dataframe
        name: label for the filtering step

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
    filtered = ids.join(df_out, on=id_col, how="anti").collect().get_column()

    stat = {
        "name": name,
        "before": len_in,
        "after": len_out,
        "reduction": len_in - len_out,
        "ids": [filtered],
    }

    return df_out, pl.DataFrame(stat)
