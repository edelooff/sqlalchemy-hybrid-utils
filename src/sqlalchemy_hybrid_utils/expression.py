from __future__ import annotations

import operator
from collections import deque
from enum import Enum, auto
from itertools import chain
from typing import Any, Deque, Iterator, Optional

from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import (
    AsBoolean,
    BinaryExpression,
    BindParameter,
    BooleanClauseList,
    ClauseElement,
    Grouping,
    Null,
    UnaryExpression,
)
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import Boolean

from .typing import ColumnSet, ColumnValues

BOOLEAN_MULTICLAUSE_OPERATORS = {
    operator.and_: lambda *args: all(args),
    operator.or_: lambda *args: any(args),
}
OPERATOR_MAP = {
    operators.in_op: lambda left, right: left in right,
    operators.is_: operator.eq,
    operators.isnot: operator.ne,
    operators.istrue: None,
    operators.isfalse: operator.not_,
}


class Expression:
    """Provides runtime Python evaluation of SQLAlchemy expressions.

    A given SQLAlchemy expression is converted into an internal serialized
    format that allows runtime Python execution based on substitute values for
    the columns involved in the expression. The method to use for this is
    `.evaluate()`.

    When `forrce_bool` is True, bare columns and inverted columns (~Column) are
    converted to booleans. In this operating mode, a column value is False when
    it is None (equivalent `IS NULL`) and True otherwise. In this operating
    mode, the given expression itself is also modified with these same semantics
    and stored on the `sql` attribute.
    """

    def __init__(self, expression: ClauseElement):
        self.serialized = tuple(self._serialize(expression))
        self.sql = expression

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.serialized == other.serialized

    def evaluate(self, column_values: ColumnValues) -> Any:
        """Evaluates the SQLAlchemy expression on the current column values."""
        stack = Stack()
        for itype, arity, value in self.serialized:
            if itype is SymbolType.literal:
                stack.push(value)
            elif itype is SymbolType.column:
                stack.push(column_values[value])
            else:
                stack.push(value(*stack.popn(arity)))
        return stack.pop()

    @property
    def columns(self) -> ColumnSet:
        """Returns a set of columns used in the expression."""
        coltype = SymbolType.column
        return {symbol.value for symbol in self.serialized if symbol.type is coltype}

    def _serialize(self, expr: ClauseElement) -> Iterator[Symbol]:
        """Serializes an SQLAlchemy expression to Python functions.

        This takes an SQLAlchemy expression tree and converts it into an
        equivalent set of Python Symbols. The generated format is that
        of a reverse Polish notation. This allows the expression to be easily
        evaluated with column value substitutions.
        """
        # Simple and direct value types
        if isinstance(expr, BindParameter):
            yield Symbol(expr.value)
        elif isinstance(expr, Grouping):
            value = [elem.value for elem in expr.element]  # type: ignore[attr-defined]
            yield Symbol(value)
        elif isinstance(expr, Null):
            yield Symbol(None)
        # Columns and column-wrapping functions
        elif isinstance(expr, Column):
            yield Symbol(expr)
        elif isinstance(expr, AsBoolean):
            yield Symbol(expr.element)
            if (func := OPERATOR_MAP[expr.operator]) is not None:
                yield Symbol(func, arity=1)
        elif isinstance(expr, UnaryExpression):
            target = expr.element
            yield from self._serialize(target)
            yield Symbol(expr.operator, arity=1)
        # Multi-clause expressions
        elif isinstance(expr, BooleanClauseList):
            yield from chain.from_iterable(map(self._serialize, expr.clauses))
            if (arity := len(expr.clauses)) == 0:
                yield Symbol(True)
            elif arity == 2:
                yield Symbol(expr.operator, arity=arity)
            else:
                yield Symbol(BOOLEAN_MULTICLAUSE_OPERATORS[expr.operator], arity=arity)
        elif isinstance(expr, BinaryExpression):
            if isinstance(expr.operator, operators.custom_op):
                raise TypeError(f"Unsupported operator {expr.operator}")
            yield from self._serialize(expr.right)
            yield from self._serialize(expr.left)
            yield Symbol(OPERATOR_MAP.get(expr.operator, expr.operator), arity=2)
        else:
            expr_type = type(expr).__name__
            raise TypeError(f"Unsupported expression {expr} of type {expr_type}")


class Stack:
    def __init__(self) -> None:
        self._stack: Deque[Any] = deque()

    def push(self, frame: Any) -> None:
        self._stack.append(frame)

    def pop(self) -> Any:
        return self._stack.pop()

    def popn(self, size: int) -> Iterator[Any]:
        return (self._stack.pop() for _ in range(size))


class Symbol:
    __slots__ = "value", "type", "arity"

    def __init__(self, value: Any, *, arity: Optional[int] = None):
        self.value = value
        self.type = self._determine_type(value)
        self.arity = arity
        if self.type is SymbolType.operator:
            if self.arity is None:
                raise ValueError(f"Arity required for Symbol of type {self.type}.")
        elif self.arity is not None:
            raise ValueError(f"Arity not allowed for non-operator type {self.type}.")

    def _determine_type(self, value: Any) -> SymbolType:
        if isinstance(value, Column):
            return SymbolType.column
        if callable(value):
            return SymbolType.operator
        return SymbolType.literal

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        return tuple(self) == tuple(other)

    def __iter__(self) -> Iterator[Any]:
        yield from (self.type, self.arity, self.value)

    def __repr__(self) -> str:
        params = [f"type={self.type!r}", f"value={self.value!r}"]
        if self.arity is not None:
            params.append(f"arity={self.arity!r}")
        return f"<Symbol({', '.join(params)})"


class SymbolType(Enum):
    column = auto()
    literal = auto()
    operator = auto()

    def __repr__(self) -> str:
        return f"<{self.name}>"


def rephrase_as_boolean(expr: ClauseElement) -> ClauseElement:
    """Rephrases SQL expression allowing boolean usage of non-bool columns.

    This is done by converting bare non-Boolean columns (those not used in
    a binary expression) in to "IS NOT NULL" clauses, and inversed columns
    (~Column) into the negated form ("IS NULL").
    """
    if isinstance(expr, Column) and not isinstance(expr.type, Boolean):
        return expr.isnot(None)
    elif isinstance(expr, UnaryExpression):
        if expr.operator is operator.inv and isinstance(expr.element, Column):
            return expr.element.is_(None)
        return expr
    elif isinstance(expr, BooleanClauseList):
        expr.clauses = list(map(rephrase_as_boolean, expr.clauses))
        return expr
    return expr
