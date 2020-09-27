import pytest
from sqlalchemy import Boolean, Column

from sqlalchemy_hybrid_utils.expression import (
    ColumnSymbol,
    LiteralSymbol,
    OperatorSymbol,
)

BOOL_A = Column("bool_a", Boolean)
BOOL_B = Column("bool_b", Boolean)


def test_symbol_equality():
    left = ColumnSymbol(BOOL_A)
    right = ColumnSymbol(BOOL_A)
    assert left is not right
    assert left == right


@pytest.mark.parametrize(
    "left, right",
    [
        (ColumnSymbol(BOOL_A), ColumnSymbol(BOOL_B)),
        (ColumnSymbol(BOOL_A), LiteralSymbol(BOOL_A)),
    ],
)
def test_symbol_inequality(left, right):
    assert left != right


@pytest.mark.parametrize("other", [[], [None], 0, 100, "bool_a", True, False, None])
def test_symbol_other_type_inequality(other):
    assert ColumnSymbol(BOOL_A) != other


def test_symbol_column_must_be_column():
    with pytest.raises(TypeError, match="Value must be column-like:"):
        ColumnSymbol("foo")  # type: ignore[arg-type]


def test_symbol_operator_must_be_callable():
    with pytest.raises(TypeError, match="Operator must be callable:"):
        OperatorSymbol("foo", arity=1)  # type: ignore[arg-type]


def test_symbol_operator_arity_must_be_integer():
    with pytest.raises(TypeError, match="Arity must be an integer:"):
        OperatorSymbol(any, "1")  # type: ignore[arg-type]
