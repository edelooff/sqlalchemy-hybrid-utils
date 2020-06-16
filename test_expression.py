import pytest
from sqlalchemy import Table, MetaData, Column, Boolean, Integer, Text, null

from expression import Expression


class TestBooleanExpressions:
    BOOL = Table(
        "bool_expr",
        MetaData(),
        Column("a", Boolean),
        Column("b", Boolean),
        Column("c", Boolean),
    )

    @pytest.fixture
    def cols(self):
        return self.BOOL.columns

    @pytest.mark.parametrize(
        "inputs, expected", [({BOOL.c.a: False}, False), ({BOOL.c.a: True}, True)]
    )
    def test_direct_bool(self, cols, inputs, expected):
        expression = Expression(cols.a)
        assert expression.evaluate(inputs) == expected

    @pytest.mark.parametrize(
        "inputs, expected", [({BOOL.c.a: False}, True), ({BOOL.c.a: True}, False)]
    )
    def test_negation(self, cols, inputs, expected):
        expression = Expression(~cols.a)
        assert expression.evaluate(inputs) == expected

    @pytest.mark.parametrize(
        "inputs, expected",
        [
            ({BOOL.c.a: False, BOOL.c.b: False}, False),
            ({BOOL.c.a: True, BOOL.c.b: False}, False),
            ({BOOL.c.a: False, BOOL.c.b: True}, False),
            ({BOOL.c.a: True, BOOL.c.b: True}, True),
        ],
    )
    def test_conjunction(self, cols, inputs, expected):
        expression = Expression(cols.a & cols.b)
        assert expression.evaluate(inputs) == expected

    @pytest.mark.parametrize(
        "inputs, expected",
        [
            ({BOOL.c.a: False, BOOL.c.b: False}, False),
            ({BOOL.c.a: True, BOOL.c.b: False}, True),
            ({BOOL.c.a: False, BOOL.c.b: True}, True),
            ({BOOL.c.a: True, BOOL.c.b: True}, True),
        ],
    )
    def test_disjunction(self, cols, inputs, expected):
        expression = Expression(cols.a | cols.b)
        assert expression.evaluate(inputs) == expected

    @pytest.mark.parametrize(
        "inputs, expected",
        [
            ({BOOL.c.a: False, BOOL.c.b: False, BOOL.c.c: False}, False),
            ({BOOL.c.a: True, BOOL.c.b: False, BOOL.c.c: False}, True),
            ({BOOL.c.a: False, BOOL.c.b: True, BOOL.c.c: False}, False),
            ({BOOL.c.a: True, BOOL.c.b: True, BOOL.c.c: False}, False),
            ({BOOL.c.a: False, BOOL.c.b: False, BOOL.c.c: True}, True),
            ({BOOL.c.a: True, BOOL.c.b: False, BOOL.c.c: True}, True),
            ({BOOL.c.a: False, BOOL.c.b: True, BOOL.c.c: True}, True),
            ({BOOL.c.a: True, BOOL.c.b: True, BOOL.c.c: True}, True),
        ],
    )
    def test_mixed_expression(self, cols, inputs, expected):
        expression = Expression((cols.a & ~cols.b) | cols.c)
        assert expression.evaluate(inputs) == expected


class TestBooleanCoercion:
    COERCE = Table(
        "expr_coerce",
        MetaData(),
        Column("bool", Boolean),
        Column("number", Integer),
        Column("text", Text),
    )

    @pytest.mark.parametrize("column", [COERCE.c.number, COERCE.c.text])
    def test_sql_equivalences(self, column):
        left = Expression(column != null())
        right = Expression(column.isnot(None))
        assert left == right

    @pytest.mark.parametrize("column", [COERCE.c.number, COERCE.c.text])
    def test_coerce_simple_expression(self, column):
        left = Expression(column, force_bool=True)
        right = Expression(column.isnot(None))
        assert left == right

    @pytest.mark.parametrize("column", [COERCE.c.number, COERCE.c.text])
    def test_coerce_negated_expression(self, column):
        left = Expression(~column, force_bool=True)
        right = Expression(column.is_(None))
        assert left == right

    def test_do_not_coerce_bool_column(self):
        left = Expression(~self.COERCE.c.bool, force_bool=True)
        right = Expression(~self.COERCE.c.bool)
        assert left == right

    def test_do_not_coerce_negated_bool_column(self):
        left = Expression(self.COERCE.c.bool, force_bool=True)
        right = Expression(self.COERCE.c.bool)
        assert left == right

    @pytest.mark.parametrize("column", [COERCE.c.number, COERCE.c.text])
    def test_do_not_coerce_nonbool_expr(self, column):
        left = Expression(~column.in_(["foo", "bar"]), force_bool=True)
        right = Expression(~column.in_(["foo", "bar"]))
        assert left == right


class TestMathExpressions:
    MATH = Table(
        "expr_math",
        MetaData(),
        Column("a", Integer),
        Column("b", Integer),
        Column("c", Integer),
    )

    @pytest.fixture
    def cols(self):
        return self.MATH.columns

    @pytest.mark.parametrize(
        "inputs, expected",
        [
            ({MATH.c.a: 0, MATH.c.b: 0}, 0),
            ({MATH.c.a: 2, MATH.c.b: 0}, 2),
            ({MATH.c.a: 0, MATH.c.b: 3}, 3),
            ({MATH.c.a: 5, MATH.c.b: 5}, 10),
            ({MATH.c.a: -2, MATH.c.b: -2}, -4),
        ],
    )
    def test_addition(self, cols, inputs, expected):
        addition = Expression(cols.a + cols.b)
        assert addition.evaluate(inputs) == expected

    @pytest.mark.parametrize(
        "inputs, expected",
        [
            ({MATH.c.a: 0, MATH.c.b: 0}, 0),
            ({MATH.c.a: 2, MATH.c.b: 0}, 2),
            ({MATH.c.a: 0, MATH.c.b: 3}, -3),
            ({MATH.c.a: 5, MATH.c.b: -5}, 10),
        ],
    )
    def test_subtraction(self, cols, inputs, expected):
        subtraction = Expression(cols.a - cols.b)
        assert subtraction.evaluate(inputs) == expected

    @pytest.mark.parametrize(
        "inputs, expected",
        [
            ({MATH.c.a: 0, MATH.c.b: 0, MATH.c.c: 0}, 0),
            ({MATH.c.a: 2, MATH.c.b: 3, MATH.c.c: 0}, 6),
            ({MATH.c.a: 3, MATH.c.b: 4, MATH.c.c: 6}, 6),
            ({MATH.c.a: 3, MATH.c.b: -3, MATH.c.c: -3}, -6),
        ],
    )
    def test_mixed_match(self, cols, inputs, expected):
        multmin = Expression(cols.a * cols.b - cols.c)
        assert multmin.evaluate(inputs) == expected
