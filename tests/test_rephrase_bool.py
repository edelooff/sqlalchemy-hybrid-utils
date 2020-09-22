import pytest
from sqlalchemy import Boolean, Column, Text

from sqlalchemy_hybrid_utils.expression import rephrase_as_boolean

HAS_PROPOSAL = Column("has_proposal", Boolean)
HAS_RESPONSE = Column("has_response", Boolean)
PROPOSAL = Column("proposal", Text)
RESPONSE = Column("response", Text)


def assert_identical_expression(left, right):
    """Returns whether two expressions compile to the same SQL string."""
    # Lacking better equality comparison for expressions, this compares strings
    assert str(left.compile()) == str(right.compile())


@pytest.mark.parametrize(
    "expr",
    [
        HAS_PROPOSAL,
        ~HAS_PROPOSAL,
        HAS_PROPOSAL | HAS_RESPONSE,
        HAS_PROPOSAL & ~HAS_RESPONSE,
    ],
)
def test_boolean_expression_unaffected(expr):
    assert_identical_expression(rephrase_as_boolean(expr), expr)


def test_convert_non_bool_cols():
    simple = PROPOSAL & ~RESPONSE
    expected = PROPOSAL.isnot(None) & RESPONSE.is_(None)
    assert_identical_expression(rephrase_as_boolean(simple), expected)


def test_skip_non_bool_check():
    expr = PROPOSAL.contains("spam")
    assert_identical_expression(rephrase_as_boolean(expr), expr)


def test_mixed_bool_and_other():
    simple = PROPOSAL.contains("spam") & ~RESPONSE
    expected = PROPOSAL.contains("spam") & RESPONSE.is_(None)
    assert_identical_expression(rephrase_as_boolean(simple), expected)
