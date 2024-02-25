import pytest
from sqlalchemy import Column, Integer, MetaData, Table, Text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import mapper

from sqlalchemy_hybrid_utils import column_flag
from sqlalchemy_hybrid_utils.resolver import (
    AttributeResolver,
    PrefetchedAttributeResolver,
)

try:
    # Prioritize import path from SQLAlchemy 2.0
    from sqlalchemy.orm import declarative_base  # type: ignore[attr-defined]
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base

try:
    from sqlalchemy.orm import registry  # type: ignore[attr-defined]
except ImportError:
    registry = None


def map_class_imperatively(*args, **kwargs):
    if registry is None:  # SQLAlchemy 1.3 compatibility
        mapper(*args, **kwargs)
    else:
        registry().map_imperatively(*args, **kwargs)


@pytest.fixture
def Thing():
    class Thing(declarative_base()):  # type: ignore
        __tablename__ = "resolver_thing"
        id = Column(Integer, primary_key=True)
        named = Column(Text)
        renamed = Column("unnamed", Text)

    return Thing


@pytest.fixture
def column_map(Thing):
    columns = Thing.__table__.columns
    return {"named": columns.named, "renamed": columns.unnamed}


@pytest.fixture(params=[AttributeResolver, PrefetchedAttributeResolver])
def resolver_type(request):
    """Returns each of the resolver types in turn."""
    return request.param


@pytest.fixture
def make_resolver(Thing, resolver_type):
    """Returns a factory to create and initializes AttributeResolvers."""

    def _resolver(columns):
        resolver = resolver_type(set(columns))
        # This ensures prefetching gets triggered. This event is usually dispatched
        # after mapper configuration, run shortly after the class containing the
        # DerivedColumn with the PrefetchedAttributeResolver is created, or shortly
        # before its first use. For tests however, this event needs to be triggered
        # (configure_mappers() is smart about not doing work when there is none)
        mapper = inspect(Thing).mapper
        mapper.dispatch.mapper_configured(mapper, Thing)
        return resolver

    return _resolver


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({}, id="uninitialized"),
        pytest.param({"named": None, "renamed": None}, id="explicitly nulled"),
        pytest.param({"named": "ham", "renamed": "spam"}, id="basic strings"),
    ],
)
def test_resolve_simple_values(Thing, column_map, make_resolver, params):
    thing = Thing(**params)
    resolver = make_resolver(column_map.values())
    value_resolver = resolver.values(thing)
    for attr_name, column in column_map.items():
        assert getattr(thing, attr_name) == value_resolver(column)


def test_single_name_getter(Thing, column_map, make_resolver):
    thing = Thing()
    for attr_name, column in column_map.items():
        resolver = make_resolver({column})
        assert resolver.single_name(thing) == attr_name


def test_single_name_multi_column(Thing, column_map, make_resolver):
    thing = Thing()
    resolver = make_resolver(set(column_map.values()))
    with pytest.raises(ValueError, match="Resolver contains multiple columns"):
        resolver.single_name(thing)


def test_ambiguous_attribute_names_across_mappers(make_resolver):
    """Ambiguously mapped column works normally for AttributeResolver."""
    table = Table("test", MetaData(), Column("value", Text, primary_key=True))

    class Base:
        def __init__(self, value):
            self.value = value

    class Alias:
        def __init__(self, value):
            self.alias = value

    resolver = make_resolver({table.c.value})
    map_class_imperatively(Base, table)
    map_class_imperatively(Alias, table, properties={"alias": table.c.value})
    base = Base("spam")
    alias = Alias("eggs")
    assert resolver.single_name(base) == "value"
    assert resolver.single_name(alias) == "alias"
    assert resolver.values(base)(table.c.value) == "spam"
    assert resolver.values(alias)(table.c.value) == "eggs"


@pytest.mark.parametrize("prefetch", [False, True])
def test_column_flag_prefetch_switch(prefetch):
    class Mapped(declarative_base()):  # type: ignore
        __tablename__ = "mapped"
        value = Column(Text, primary_key=True)
        has_value = column_flag(
            value, default="eggs", prefetch_attribute_names=prefetch
        )

    mapped = Mapped()
    assert not mapped.has_value
    mapped.has_value = True
    assert mapped.has_value
    assert mapped.value == "eggs"
