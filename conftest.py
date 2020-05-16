from datetime import datetime

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy_column_flag import column_flag


@pytest.fixture(scope="session")
def Base():
    return declarative_base()


@pytest.fixture(scope="session")
def Message(Base):
    class Message(Base):
        __tablename__ = "message"
        id = sa.Column(sa.Integer, primary_key=True)
        content = sa.Column(sa.Text)
        sent_at = sa.Column(sa.DateTime)
        delivered_at = sa.Column("delivery_date", sa.DateTime)

        has_content = column_flag(content)
        is_sent = column_flag(sent_at, default=sa.func.now())
        is_sent_scalar = column_flag(sent_at, default=datetime(2020, 1, 1))
        is_delivered = column_flag(delivered_at, default=datetime.utcnow)

    return Message


@pytest.fixture(scope="session")
def engine(Base, Message):
    """Sets up an SQLite databae engine and configures required tables."""
    engine = sa.create_engine("sqlite://", echo=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def session(engine):
    """Returns a session with a transaction that is rolled back after test."""
    with engine.connect() as connection:
        with connection.begin() as transaction:
            yield sa.orm.Session(bind=connection)
            transaction.rollback()
