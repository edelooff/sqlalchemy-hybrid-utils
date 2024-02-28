from datetime import datetime

import pytest
from freezegun import freeze_time
from sqlalchemy import func
from sqlalchemy.inspection import inspect
from sqlalchemy.sql import functions


@pytest.mark.parametrize(
    "content, expected_value", [("Eggs and spam", True), ("", True), (None, False)]
)
def test_flag_initial_value(Message, content, expected_value):
    empty_message = Message(content=content)
    assert empty_message.has_content == expected_value


def test_flag_runtime_evaluation(Message):
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
    with freeze_time() as clock:
        delivery_time = clock()
        message.is_delivered = True
        assert message.delivered_at == delivery_time
        session.commit()
        clock.tick(1)  # progress time
        assert message.delivered_at == delivery_time


def test_assign_default_scalar(Message, session):
    message = Message(content="Spam")
    session.add(message)
    assert message.sent_at is None
    message.is_sent_scalar = True
    assert message.sent_at == datetime(2020, 1, 1)
    session.commit()
    assert message.sent_at == datetime(2020, 1, 1)


def test_assign_default_sql_func(Message, session):
    message = Message(content="Spam")
    session.add(message)
    assert message.sent_at is None
    message.is_sent = True
    assert isinstance(message.sent_at, functions.Function)
    current_time = session.query(func.now()).scalar()  # type: ignore[unreachable]
    session.commit()
    assert message.sent_at == current_time


def test_default_at_creation_python_func(Message, session):
    with freeze_time() as clock:
        message = Message(content="Spam", is_delivered=True)
        session.add(message)
        delivery_time = clock()
        assert message.delivered_at == delivery_time
        session.commit()
        clock.tick(1)  # progress time
        assert message.delivered_at == delivery_time


def test_default_at_creation_scalar(Message, session):
    message = Message(content="Spam", is_sent_scalar=True)
    session.add(message)
    assert message.sent_at == datetime(2020, 1, 1)
    session.commit()
    assert message.sent_at == datetime(2020, 1, 1)


def test_default_at_creation_sql_func(Message, session):
    message = Message(content="Spam", is_sent=True)
    session.add(message)
    assert isinstance(message.sent_at, functions.Function)
    current_time = session.query(func.now()).scalar()
    session.commit()
    assert message.sent_at == current_time


@pytest.mark.parametrize(
    "column, flag",
    [
        ("sent_at", "is_sent"),
        ("sent_at", "is_sent_scalar"),
        ("delivered_at", "is_delivered"),
    ],
)
def test_default_false(Message, column, flag):
    message = Message(content="spam", **{column: datetime.utcnow()})
    assert getattr(message, column) is not None
    assert getattr(message, flag)
    setattr(message, flag, False)
    assert getattr(message, column) is None


def test_assign_readonly_error(Message):
    message = Message(content="Spam")
    with pytest.raises(AttributeError):
        message.has_content = True

    with pytest.raises(AttributeError):
        Message(has_content=True)


@pytest.mark.parametrize("flag_value", [None, 1, "ham"])
def test_assign_non_bool_error(Message, flag_value):
    message = Message(content="Spam")
    with pytest.raises(TypeError, match="boolean"):
        message.is_sent = flag_value

    with pytest.raises(TypeError, match="boolean"):
        Message(is_sent=flag_value)


def test_table_inheritance_base(Booking):
    booking = Booking(paid_at=datetime.utcnow())
    assert booking.type == "standard"
    assert booking.is_paid
    assert not hasattr(booking, "cancelled_at")
    assert not hasattr(booking, "is_cancelled")


def test_table_inheritance_subclass(Cancellable):
    booking = Cancellable(paid_at=datetime.utcnow())
    assert booking.type == "cancellable"
    assert booking.is_paid
    assert not booking.is_cancelled
    booking.cancelled_at = datetime.utcnow()
    assert booking.is_cancelled
