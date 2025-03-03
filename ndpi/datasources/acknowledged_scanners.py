from pathlib import Path
import polars as pl
import ipaddress
from typing import Union


def dict_to_acknowledged_scanners(
    dictionary: dict, scanner_name_col="scanner", addr_col="ip.addr"
) -> pl.DataFrame:
    """Convert dictionary of kind { "scanner_name": [scan_addr1, scan_addr2]} into DataFrame

    Args:
        dictionary: scanner to address or subnet mapping
        scanner_name_col: name to use for column with dictionary keys
        addr_col: name to use for address/subnet column

    Returns:
        DataFrame with columns `scanner_name_col` and `addr_col`
    """
    return pl.concat(
        [
            pl.DataFrame({name: value}).unpivot(
                pl.selectors.string(), value_name="ip.addr", variable_name="scanner"
            )
            for name, value in dictionary.items()
        ]
    )


def acknowledged_scanners(
    path: Path,
    additional_prefixes: Union[pl.DataFrame, pl.LazyFrame] = pl.DataFrame({}),
    expand_subnets: bool = False,
    scanner_name_col: str = "scanners",
    addr_col: str = "ip.addr",
) -> pl.LazyFrame:
    """Load list of acknowledged scanners from folder.

    You can create the input folder with

    ```make
    acknowledged_scanners:
       git clone https://gitlab.com/mcollins_at_isi/acknowledged_scanners.git data/external/acknowledged_scanners

    ```

    Args:
        path: path to clone of repository
        additional_prefixes: add additional scanners to the list, must use the column names `scanner_name_col` and `addr_col`
        expand_subnets: expand all rows from the input address into IP addresses. Allows for fast polars joins
        scanner_name_col: column name for scanner information
        addr_col: column_name for address field

    Returns:
        DataFrame with acknowledged scanners and their used ip addresses/subnets
    """
    df = pl.concat(
        [
            pl.scan_csv(
                f"{str(path)}/data/*/ips.txt",
                include_file_paths=scanner_name_col,
                has_header=False,
                new_columns=[addr_col, scanner_name_col],
            ).with_columns(pl.col(scanner_name_col).str.split("/").slice(-2)),
            additional_prefixes.lazy(),
        ]
    )

    if expand_subnets:
        df = df.with_columns(
            pl.col(addr_col).map_elements(
                lambda x: [addr for addr in ipaddress.ip_network(x, strict=False)]
            )
        ).explode(addr_col)

    return df
