from collections import defaultdict
from typing import Any, Dict, Type

from sqlalchemy.event import listen
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapper

from .typing import ColumnSet, ColumnValues, MapperTargets


class AttributeResolver:
    """A runtime inspection-based resolver for attribute names and values."""

    def __init__(self, columns: ColumnSet):
        self._columns = columns
        if len(self._columns) == 1:
            self._single = next(iter(columns))

    def single_name(self, orm_obj: Any) -> str:
        """Returns the first (and only) attribute name for __fset__."""
        mapper = inspect(orm_obj).mapper
        try:
            return mapper.get_property_by_column(self._single).key
        except AttributeError:
            raise ValueError("Resolver contains multiple columns.")

    def values(self, orm_obj: Any) -> ColumnValues:
        """Returns values of column-attributes for given ORM object."""
        mapper = inspect(orm_obj).mapper
        getter = mapper.get_property_by_column
        return lambda col: getattr(orm_obj, getter(col).key)


class PrefetchedAttributeResolver(AttributeResolver):
    def __init__(self, columns: ColumnSet):
        super().__init__(columns)
        self._singles: Dict[Type[Any], str] = {}
        self._targets: MapperTargets = defaultdict(dict)
        listen(Mapper, "mapper_configured", self._resolve_mapped_attribute_names)

    def _resolve_mapped_attribute_names(
        self, mapper: Mapper, mapped_class: Type[Any]
    ) -> None:
        """Looks up attribute name on the mapped class for each tracked column.

        This column->attribute name mapping is created separately for each
        mapped class. This allows multiple mapped classes against the same
        table to have different attribute names to refer to a column.
        """
        for column in self._columns:
            if column in mapper.columns.values():
                attr = mapper.get_property_by_column(column)
                if len(self._columns) == 1:
                    self._singles[mapped_class] = attr.key
                self._targets[mapped_class][column] = attr.key

    def single_name(self, orm_obj: Any) -> str:
        """Returns the first (and only) attribute name for __fset__."""
        try:
            return self._singles[type(orm_obj)]
        except KeyError:
            raise ValueError("Resolver contains multiple columns.")

    def values(self, orm_obj: Any) -> ColumnValues:
        targets = self._targets[type(orm_obj)]
        return lambda col: getattr(orm_obj, targets[col])
