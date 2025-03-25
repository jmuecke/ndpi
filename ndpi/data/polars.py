from collections.abc import Collection
from typing import Any, Union
import polars as pl


@pl.api.register_expr_namespace("ndpi")
class Ndpi:
    def __init__(self, expr: pl.Expr) -> None:
        self._expr = expr

    def list_index_of(
        self, values: Union[pl.Expr, Collection[Any], pl.Series]
    ) -> pl.Expr:
        """Return the indices of elements in a list. This is not yet supported natively by polars.

        Args:
            values: Values to get the indices from.

        Returns:
            list of indices or empty list if values are not found.
        """
        position = pl.int_range(start=1, end=pl.len() + 1)
        true_if_in_p = pl.element().is_in(values)
        # position * true_if_in_p = 0 for non elements not in p, and index for elements in p

        filter_lt_0 = pl.element().filter(pl.element() > 0)
        begin_index_at_zero = pl.element() - 1
        return (
            self._expr.list.eval(position * true_if_in_p)
            .list.eval(filter_lt_0)
            .list.eval(begin_index_at_zero)
        )
