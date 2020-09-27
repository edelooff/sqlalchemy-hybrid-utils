from __future__ import annotations

import operator
from collections import deque
from dataclasses import dataclass
from itertools import chain
from typing import Any, Deque, Iterator, Set

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

from .typing import ColType, ColumnSet, ColumnValues, Function, FunctionMap

BOOLEAN_MULTICLAUSE_OPERATORS: FunctionMap = {
    operator.and_: lambda *args: all(args),
    operator.or_: lambda *args: any(args),
}
NIL_OPERATORS: Set[Function] = {operators.istrue}
OPERATOR_MAP: FunctionMap = {
    operators.in_op: lambda left, right: left in right,
    operators.is_: operator.eq,
    operators.isnot: operator.ne,
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
        stack: Deque[Any] = deque()
        stack_push = stack.append
        stack_pop = stack.pop
        for symbol in self.serialized:
            if isinstance(symbol, LiteralSymbol):
                stack_push(symbol.value)
            elif isinstance(symbol, ColumnSymbol):
                stack_push(column_values(symbol.column))
            elif isinstance(symbol, OperatorSymbol):
                arity = symbol.arity
                if arity == 1:
                    stack_push(symbol.operator(stack_pop()))
                elif arity == 2:
                    stack_push(symbol.operator(stack_pop(), stack_pop()))
                else:
                    stack_push(symbol.operator(*(stack_pop() for _ in range(arity))))
            else:
                raise RuntimeError(f"Bad Symbol type {symbol}")  # pragma: no cover
        return stack_pop()

    @property
    def columns(self) -> ColumnSet:
        """Returns a set of columns used in the expression."""
        symbols = self.serialized
        return {symbol.column for symbol in symbols if isinstance(symbol, ColumnSymbol)}

    def _serialize(self, expr: ClauseElement) -> Iterator[Symbol]:
        """Serializes an SQLAlchemy expression to Python functions.

        This takes an SQLAlchemy expression tree and converts it into an
        equivalent set of Python Symbols. The generated format is that
        of a reverse Polish notation. This allows the expression to be easily
        evaluated with column value substitutions.
        """
        # Simple and direct value types
        if isinstance(expr, BindParameter):
            yield LiteralSymbol(expr.value)
        elif isinstance(expr, Grouping):
            value = [elem.value for elem in expr.element]  # type: ignore[attr-defined]
            yield LiteralSymbol(value)
        elif isinstance(expr, Null):
            yield LiteralSymbol(None)
        # Columns and column-wrapping functions
        elif isinstance(expr, Column):
            yield ColumnSymbol(expr)
        elif isinstance(expr, AsBoolean):
            yield ColumnSymbol(expr.element)
            if expr.operator not in NIL_OPERATORS:
                yield OperatorSymbol(OPERATOR_MAP[expr.operator], arity=1)
        elif isinstance(expr, UnaryExpression):
            target = expr.element
            yield from self._serialize(target)
            yield OperatorSymbol(expr.operator, arity=1)
        # Multi-clause expressions
        elif isinstance(expr, BinaryExpression):
            if isinstance(expr.operator, operators.custom_op):
                raise TypeError(f"Unsupported operator {expr.operator}")
            yield from self._serialize(expr.right)
            yield from self._serialize(expr.left)
            operator = OPERATOR_MAP.get(expr.operator, expr.operator)
            yield OperatorSymbol(operator, arity=2)
        elif isinstance(expr, BooleanClauseList):
            yield from chain.from_iterable(map(self._serialize, expr.clauses))
            if (arity := len(expr.clauses)) == 0:
                yield LiteralSymbol(True)
            elif arity == 2:
                yield OperatorSymbol(expr.operator, arity=arity)
            else:
                operator = BOOLEAN_MULTICLAUSE_OPERATORS[expr.operator]
                yield OperatorSymbol(operator, arity)
        else:
            expr_type = type(expr).__name__
            raise TypeError(f"Unsupported expression {expr} of type {expr_type}")


class Symbol:
    """Base class for Symbols created and used by the Expression class."""


@dataclass(frozen=True)
class ColumnSymbol(Symbol):
    column: ColType

    def __post_init__(self) -> None:
        if not isinstance(self.column, Column):
            raise TypeError(f"Value must be column-like: {self.column}")


@dataclass(frozen=True)
class LiteralSymbol(Symbol):
    value: Any


@dataclass(frozen=True)
class OperatorSymbol(Symbol):
    operator: Function
    arity: int

    def __post_init__(self) -> None:
        if not callable(self.operator):
            raise TypeError(f"Operator must be callable: {self.operator}")
        if not isinstance(self.arity, int):
            raise TypeError(f"Arity must be an integer: {self.arity}")


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
