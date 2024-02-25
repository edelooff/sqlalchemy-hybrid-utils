from typing import Any

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import ClauseElement

from .derived_column import DerivedColumn
from .expression import Expression, rephrase_as_boolean

__version__ = "0.2.0"


def column_flag(
    expr: ClauseElement, default: Any = None, prefetch_attribute_names: bool = True
) -> hybrid_property:
    expression = Expression(rephrase_as_boolean(expr))
    derived = DerivedColumn(
        expression, default=default, prefetch_attribute_names=prefetch_attribute_names
    )
    return derived.create_hybrid()
