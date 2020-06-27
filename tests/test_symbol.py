import pytest
from sqlalchemy import Column, Boolean

from sqlalchemy_hybrid_utils.expression import Symbol

BOOL_A = Column("bool_a", Boolean)
BOOL_B = Column("bool_b", Boolean)


def test_symbol_equality():
    left = Symbol(BOOL_A)
    right = Symbol(BOOL_A)
    assert left is not right
    assert left == right


def test_symbol_inequality():
    left = Symbol(BOOL_A)
    right = Symbol(BOOL_B)
    assert left != right


@pytest.mark.parametrize("other", [[], [None], 0, 100, "bool_a", True, False, None])
def test_symbol_other_type_inequality(other):
    assert Symbol(BOOL_A) != other


@pytest.mark.parametrize("value", [BOOL_A, [1, 2], None, 5])
def test_symbol_arity_operator_only(value):
    with pytest.raises(ValueError, match="Arity not allowed"):
        Symbol(value, arity=2)


def test_symbol_operator_arity_required():
    with pytest.raises(ValueError, match="Arity required"):
        Symbol(all)


@pytest.mark.parametrize("value, arity", [(BOOL_A, None), (any, 2), (5, None)])
def test_symbol_representation(value, arity):
    symbol = Symbol(value, arity=arity)
    assert repr(symbol)
