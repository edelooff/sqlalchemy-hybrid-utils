"""Compatibility layer for SQLAlchemy version differences."""

from typing import Any, Callable

from .typing import ColumnType


def column_presence_checker(columnset: Any) -> Callable[[ColumnType], bool]:
    """Returns a check function to determine if a given column is present.

    SQLAlchemy 1.4 abstracts the columns in a mapper into a ColumnSet, which
    provides a `contains_column` method, whereas the older versions expose a
    simple dictionary, with columns available through the `values` method.
    """
    if checker := getattr(columnset, "contains_column", None):
        return checker
    return lambda column: column in columnset.values()
