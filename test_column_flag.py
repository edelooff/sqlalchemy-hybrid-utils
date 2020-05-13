import pytest
from sqlalchemy.inspection import inspect


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


def test_flag_is_descriptor_not_column(Message):
    mapper = inspect(Message).mapper
    assert 'content' in mapper.all_orm_descriptors
    assert 'content' in mapper.columns
    assert 'has_content' in mapper.all_orm_descriptors
    assert 'has_content' not in mapper.columns


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
        message.is_sent = 'ham'
