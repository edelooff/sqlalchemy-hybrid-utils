from typing import Any

from sqlalchemy.sql.elements import ColumnElement

from .derived_column import DerivedColumn
from .expression import Expression, rephrase_as_boolean
from .typing import HybridPropertyType

__version__ = "0.2.0"


def column_flag(
    expr: ColumnElement[Any], default: Any = None, prefetch_attribute_names: bool = True
) -> HybridPropertyType:
    expression = Expression(rephrase_as_boolean(expr))
    derived = DerivedColumn(
        expression, default=default, prefetch_attribute_names=prefetch_attribute_names
    )
    return derived.create_hybrid()
