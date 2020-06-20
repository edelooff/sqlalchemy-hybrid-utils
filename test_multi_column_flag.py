from datetime import datetime

import pytest
from sqlalchemy import Column, Integer

from sqlalchemy_column_flag import column_flag


@pytest.mark.parametrize(
    "sent_at, delivered_at, expected",
    [
        pytest.param(None, None, False, id="not shipped"),
        pytest.param(datetime(2020, 1, 1), None, True, id="in transit"),
        pytest.param(None, datetime(2020, 1, 1), False, id="magic arrival"),
    ],
)
def test_flag_initial_value(Message, sent_at, delivered_at, expected):
    message = Message(sent_at=sent_at, delivered_at=delivered_at)
    assert message.in_transit == expected


def test_flag_runtime_evaluation(Message):
    message = Message(content="Spam")
    message.sent_at = datetime(2020, 1, 1)
    assert message.in_transit

    message.delivered_at = datetime(2020, 1, 2)
    assert not message.in_transit


def test_flag_after_database_read(Message, session):
    msg = Message(sent_at=datetime(2020, 1, 1))
    session.add(msg)
    session.commit()
    assert msg.in_transit


def test_flag_select_expr(Message, session):
    monday = datetime(2020, 6, 1)
    tuesday = datetime(2020, 6, 2)
    session.add(Message(sent_at=monday))
    session.add(Message(sent_at=monday, delivered_at=tuesday))
    session.add(Message(sent_at=tuesday))
    assert session.query(Message).filter(Message.in_transit).count() == 2


def test_multi_column_no_default():
    col_one = Column("foo", Integer)
    col_two = Column("bar", Integer)

    with pytest.raises(TypeError, match="default for multi-column expression"):
        column_flag(col_one & col_two, default="baz")
