import pytest
from sqlalchemy import Column, Boolean, Integer, Text, func, null

from expression import Expression

BOOL_A = Column("bool_a", Boolean)
BOOL_B = Column("bool_b", Boolean)
BOOL_C = Column("bool_c", Boolean)
INT_A = Column("int_a", Integer)
INT_B = Column("int_b", Integer)
INT_C = Column("int_c", Integer)
TEXT = Column("text", Text)


# Equality and comparability
def test_expression_self_equality():
    expr = Expression(BOOL_A & (INT_A > 5))
    assert expr == expr


def test_expression_equality():
    expr = BOOL_A & (INT_A > 5)
    left = Expression(expr)
    right = Expression(expr)
    assert left is not right
    assert left == right


def test_expression_inequality():
    assert Expression(BOOL_A) != Expression(~BOOL_A)


@pytest.mark.parametrize("other", [[], [None], 0, 100, True, False, None])
def test_expression_and_symbol_comparability(other):
    expr = Expression(BOOL_A & (INT_A > 5))
    assert expr != other
    for symbol in expr.serialized:
        assert symbol == symbol
        assert symbol != other


# Serialization limits
def test_serlialize_unsupported_expression():
    with pytest.raises(TypeError, match="Unsupported expression"):
        Expression(func.exp(INT_A, 2))


def test_serlialize_unsupported_opeator():
    with pytest.raises(TypeError, match="Unsupported operator"):
        Expression(INT_A.op("^")(INT_A))


# Coercion
@pytest.mark.parametrize("column", [INT_A, TEXT])
def test_sql_equivalences(column):
    left = Expression(column != null())
    right = Expression(column.isnot(None))
    assert left == right


@pytest.mark.parametrize("column", [INT_A, TEXT])
def test_coerce_simple_expression(column):
    left = Expression(column, force_bool=True)
    right = Expression(column.isnot(None))
    assert left == right


@pytest.mark.parametrize("column", [INT_A, TEXT])
def test_coerce_negated_expression(column):
    left = Expression(~column, force_bool=True)
    right = Expression(column.is_(None))
    assert left == right


def test_do_not_coerce_bool_column():
    left = Expression(~BOOL_A, force_bool=True)
    right = Expression(~BOOL_A)
    assert left == right


def test_do_not_coerce_negated_bool_column():
    left = Expression(BOOL_A, force_bool=True)
    right = Expression(BOOL_A)
    assert left == right


@pytest.mark.parametrize("column", [INT_A, TEXT])
def test_do_not_coerce_nonbool_expr(column):
    left = Expression(~column.in_(["foo", "bar"]), force_bool=True)
    right = Expression(~column.in_(["foo", "bar"]))
    assert left == right


# Boolean expression evaluation
@pytest.mark.parametrize(
    "inputs, expected", [({BOOL_A: False}, False), ({BOOL_A: True}, True)]
)
def test_bool_expr_direct_column(inputs, expected):
    expression = Expression(BOOL_A)
    assert expression.evaluate(inputs) == expected


@pytest.mark.parametrize(
    "inputs, expected", [({BOOL_A: False}, True), ({BOOL_A: True}, False)]
)
def test_bool_expr_negation(inputs, expected):
    expression = Expression(~BOOL_A)
    assert expression.evaluate(inputs) == expected


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ({BOOL_A: False, BOOL_B: False}, False),
        ({BOOL_A: True, BOOL_B: False}, False),
        ({BOOL_A: False, BOOL_B: True}, False),
        ({BOOL_A: True, BOOL_B: True}, True),
    ],
)
def test_bool_expr_conjunction(inputs, expected):
    expression = Expression(BOOL_A & BOOL_B)
    assert expression.evaluate(inputs) == expected


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ({BOOL_A: False, BOOL_B: False}, False),
        ({BOOL_A: True, BOOL_B: False}, True),
        ({BOOL_A: False, BOOL_B: True}, True),
        ({BOOL_A: True, BOOL_B: True}, True),
    ],
)
def test_bool_expr_disjunction(inputs, expected):
    expression = Expression(BOOL_A | BOOL_B)
    assert expression.evaluate(inputs) == expected


@pytest.mark.parametrize(
    "inputs, expected",
    [
        ({BOOL_A: False, BOOL_B: False, BOOL_C: False}, False),
        ({BOOL_A: True, BOOL_B: False, BOOL_C: False}, True),
        ({BOOL_A: False, BOOL_B: True, BOOL_C: False}, False),
        ({BOOL_A: True, BOOL_B: True, BOOL_C: False}, False),
        ({BOOL_A: False, BOOL_B: False, BOOL_C: True}, True),
        ({BOOL_A: True, BOOL_B: False, BOOL_C: True}, True),
        ({BOOL_A: False, BOOL_B: True, BOOL_C: True}, True),
        ({BOOL_A: True, BOOL_B: True, BOOL_C: True}, True),
    ],
)
def test_bool_expr_mixed(inputs, expected):
    expression = Expression((BOOL_A & ~BOOL_B) | BOOL_C)
    assert expression.evaluate(inputs) == expected


# Math expression evaluation
def test_addition():
    expr = Expression(INT_A + INT_B)
    assert expr.evaluate({INT_A: 2, INT_B: -10}) == -8


def test_subtraction():
    expr = Expression(INT_A - INT_B)
    assert expr.evaluate({INT_A: 2, INT_B: 5}) == -3


def test_division():
    expr = Expression(INT_A / INT_B)
    assert expr.evaluate({INT_A: 4, INT_B: 2}) == 2


def test_multiplication():
    expr = Expression(INT_A * INT_B)
    assert expr.evaluate({INT_A: 4, INT_B: -3}) == -12


def test_bitwise_inversion():
    expr = Expression(~INT_A)
    assert expr.evaluate({INT_A: 127}) == -128
    assert expr.evaluate({INT_A: -128}) == 127


def test_mixed_math():
    expr = Expression((INT_A * INT_B) + (INT_A / INT_C))
    assert expr.evaluate({INT_A: 8, INT_B: 2, INT_C: 4}) == 18


# Test additional expression evaluation
def test_evaluate_bind_param_equals():
    expr = Expression(INT_A == 5)
    assert not expr.evaluate({INT_A: 4})
    assert expr.evaluate({INT_A: 5})


def test_evaluate_bind_param_contains():
    expr = Expression(INT_A.in_([1, 2, 3, 4, 5]))
    assert expr.evaluate({INT_A: 3})
    assert not expr.evaluate({INT_A: 6})
