from typing import Any

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.elements import ClauseElement

from .derived_column import DerivedColumn
from .expression import Expression, rephrase_as_boolean


def column_flag(expr: ClauseElement, default: Any = None) -> hybrid_property:
    expression = Expression(rephrase_as_boolean(expr))
    derived = DerivedColumn(expression, default=default)
    return derived.create_hybrid()
