from datetime import datetime, timedelta

import pytest
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import functions


def datetime_equal(test_value, reference, max_delta=1):
    """Returns whether test value is within max_delta of reference value."""
    return abs(test_value - reference) < timedelta(seconds=max_delta)


def test_flag_initial_value(Message):
    empty_message = Message()
    assert not empty_message.has_content

    message = Message(content="Eggs and spam")
    assert message.has_content


def test_flag_follows_column(Message):
    message = Message()
    message.content = "Spam spam spam"
    assert message.has_content

    message.content = None
    assert not message.has_content


def test_flag_after_database_read(Message, session):
    msg = Message(content="Hello world")
    session.add(msg)
    session.commit()
    assert msg.has_content
    assert not msg.is_sent


def test_flag_select_expr(Message, session):
    session.add(Message(content="Spam"))
    session.add(Message(content="Spam and eggs"))
    session.add(Message(content="Ham and spam", sent_at=datetime.utcnow()))

    assert session.query(Message).filter(Message.has_content).count() == 3
    assert session.query(Message).filter(Message.is_sent).count() == 1
    assert session.query(Message).filter(~Message.is_sent).count() == 2


def test_flag_is_descriptor_not_column(Message):
    mapper = inspect(Message).mapper
    assert "content" in mapper.all_orm_descriptors
    assert "content" in mapper.columns
    assert "has_content" in mapper.all_orm_descriptors
    assert "has_content" not in mapper.columns


def test_assign_default_python_func(Message, session):
    message = Message(content="Spam")
    session.add(message)
    assert message.sent_at is None
    message.is_delivered = True
    assert datetime_equal(message.delivered_at, datetime.utcnow())
    session.commit()
    assert datetime_equal(message.delivered_at, datetime.utcnow())


def test_assign_default_scalar(Message, session):
    message = Message(content="Spam")
    session.add(message)
    assert message.sent_at is None
    message.is_sent_scalar = True
    assert datetime_equal(message.sent_at, datetime(2020, 1, 1))
    session.commit()
    assert datetime_equal(message.sent_at, datetime(2020, 1, 1))


def test_assign_default_sql_func(Message, session):
    message = Message(content="Spam")
    session.add(message)
    assert message.sent_at is None
    message.is_sent = True
    assert isinstance(message.sent_at, functions.Function)
    session.commit()
    assert datetime_equal(message.sent_at, datetime.utcnow())


def test_default_at_creation_python_func(Message, session):
    message = Message(content="Spam", is_delivered=True)
    session.add(message)
    assert datetime_equal(message.delivered_at, datetime.utcnow())
    session.commit()
    assert datetime_equal(message.delivered_at, datetime.utcnow())


def test_default_at_creation_scalar(Message, session):
    message = Message(content="Spam", is_sent_scalar=True)
    session.add(message)
    assert datetime_equal(message.sent_at, datetime(2020, 1, 1))
    session.commit()
    assert datetime_equal(message.sent_at, datetime(2020, 1, 1))


def test_default_at_creation_sql_func(Message, session):
    message = Message(content="Spam", is_sent=True)
    session.add(message)
    assert isinstance(message.sent_at, functions.Function)
    session.commit()
    assert datetime_equal(message.sent_at, datetime.utcnow())


def test_assign_readonly(Message):
    message = Message(content="Spam")
    with pytest.raises(AttributeError):
        message.has_content = True


def test_assign_non_bool(Message):
    message = Message(content="Spam")
    with pytest.raises(TypeError, match="boolean"):
        message.is_sent = None

    with pytest.raises(TypeError, match="boolean"):
        message.is_sent = 1

    with pytest.raises(TypeError, match="boolean"):
        message.is_sent = "ham"
