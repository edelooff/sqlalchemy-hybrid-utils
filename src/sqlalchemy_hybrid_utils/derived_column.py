from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.event import listen
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapper, mapperlib

from .expression import Expression
from .typing import ColumnDefaults, ColumnValues, MapperTargets


class DerivedColumn:
    def __init__(self, expression: Expression, default: Any = None):
        self.expression = expression
        self.default = default
        self.targets: MapperTargets = {}
        if len(self.expression.columns) > 1 and self.default is not None:
            raise TypeError("Cannot use default for multi-column expression.")
        listen(Mapper, "after_configured", self._set_static_target_attr)

    def _default_functions(self) -> ColumnDefaults:
        setter = self.default
        if not callable(setter):
            setter = lambda: self.default  # noqa
        return {True: setter, False: lambda: None}

    def _set_static_target_attr(self) -> None:
        """Looks up the attribute name that points to the tracked column.

        When multiple mappers exist for the same table, this may lead to an
        unresolvable conflict, but only if the column's attribute name differs
        between mappers.

        In the case of single table inheritance, the column property might be
        absent on some mappers, but has the same name on those that contain it.
        """
        for column in self.expression.columns:
            target_names = set()
            for mapper in mapperlib._mapper_registry:  # type: ignore[attr-defined]
                if column.table in mapper.tables:
                    if column in mapper.columns.values():
                        attr = mapper.get_property_by_column(column)
                        target_names.add(attr.key)
            if len(target_names) != 1:  # pragma: no cover
                raise TypeError(
                    f"Unable to find unambiguous mapped attribute "
                    f"name for {column!r}: {target_names}."
                )
            self.targets[column] = next(iter(target_names))

    def column_values(self, orm_obj: Any) -> ColumnValues:
        """Returns values of column-attributes for given ORM object."""
        return {col: getattr(orm_obj, attr) for col, attr in self.targets.items()}

    def make_getter(self) -> Callable[[Any, DerivedColumn], Any]:
        def _fget(self: Any, outer: DerivedColumn = self) -> Any:
            return outer.expression.evaluate(outer.column_values(self))

        return _fget

    def make_setter(self,) -> Callable[[Any, Any, MapperTargets, ColumnDefaults], None]:
        def _fset(
            self: Any,
            value: Any,
            targets: MapperTargets = self.targets,
            defaults: ColumnDefaults = self._default_functions(),
        ) -> None:
            if not isinstance(value, bool):
                raise TypeError("Flag only accepts boolean values")
            setattr(self, next(iter(targets.values())), defaults[value]())

        return _fset

    def create_hybrid(self) -> hybrid_property:
        return hybrid_property(
            fget=self.make_getter(),
            fset=self.make_setter() if self.default is not None else None,
            expr=lambda cls: self.expression.sql,
        )
