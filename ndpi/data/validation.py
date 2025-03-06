from typing import Union
import polars as pl


def col_names(
    df: Union[pl.DataFrame, pl.LazyFrame], verbose: bool = True, silent: bool = False
) -> bool:
    """Validates if a dataframe adheres to the column name standard (cns).

    Args:
        df: dataframe to analyze
        verbose: print information about non cns-columns and added columns
        silent: fail silently by returning false instead of raising an Exception

    Returns:
        Whether the dataframes adheres to the standard or not.

    Raises:
        Exception: Raises an Exception if the dataframe does not adhere to the cns.
    """
    names = df.lazy().collect_schema().names()
    meta_df = pl.DataFrame({"column": names}).with_columns(
        cns=pl.col("column").str.count_matches("^[\\.a-z]$") == 1,
        added_columns=pl.col("column").str.contains("-", literal=True),
    )

    non_cns_columns = meta_df.filter(pl.col("cns") == False).get_column("column")

    # Optional summary
    if verbose:
        print("Non column name standard columns detected:")
        print(non_cns_columns)
        added_columns = meta_df.filter(pl.col("added_columns")).get_column("column")
        print("Columns added to this DataFrame:")
        print(added_columns)

    if len(non_cns_columns) > 0:
        if not silent:
            raise Exception("Dataframe does not adhere to column name standard (cns)")
        return False

    return True
