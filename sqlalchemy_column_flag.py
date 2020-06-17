from sqlalchemy.event import listen
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapper, mapperlib

from expression import Expression


class DerivedColumn:
    def __init__(self, expression, default=None):
        self.expression = Expression(expression, force_bool=True)
        self.default = default
        self.targets = {}
        if len(self.expression.columns) > 1 and self.default is not None:
            raise TypeError("Cannot use default for multi-column expression.")
        listen(Mapper, "after_configured", self._set_static_target_attr)

    def _default_functions(self):
        setter = self.default
        if not callable(setter):
            setter = lambda: self.default  # noqa
        return {True: setter, False: lambda: None}

    def _set_static_target_attr(self):
        """Looks up the attribute name that points to the tracked column.

        When multiple mappers exist for the same table, this may lead to an
        unresolvable conflict, but only if the column's attribute name differs
        between mappers.

        In the case of single table inheritance, the column property might be
        absent on some mappers, but has the same name on those that contain it.
        """
        for column in self.expression.columns:
            target_names = set()
            for mapper in mapperlib._mapper_registry:
                if column.table in mapper.tables:
                    if column in mapper.columns.values():
                        attr = mapper.get_property_by_column(column)
                        target_names.add(attr.key)
            if len(target_names) != 1:
                raise TypeError(
                    f"Unable to find unambiguous mapped attribute "
                    f"name for {column!r}: {target_names}."
                )
            self.targets[column] = next(iter(target_names))

    def column_values(self, orm_obj):
        """Returns values of column-attributes for given ORM object."""
        return {col: getattr(orm_obj, attr) for col, attr in self.targets.items()}

    def make_getter(self):
        def _fget(self, outer=self):
            return outer.expression.evaluate(outer.column_values(self))

        return _fget

    def make_setter(self):
        if self.default is None:
            return None
        defaults = self._default_functions()

        def _fset(self, value, targets=self.targets, defaults=defaults):
            if not isinstance(value, bool):
                raise TypeError("Flag only accepts boolean values")
            return setattr(self, next(iter(targets.values())), defaults[value]())

        return _fset

    def make_expression(self):
        def _expr(cls, expr=self.expression.sql):
            return expr

        return _expr

    def create_hybrid(self):
        return hybrid_property(
            fget=self.make_getter(),
            fset=self.make_setter(),
            expr=self.make_expression(),
        )


def column_flag(column, **options):
    derived = DerivedColumn(column, **options)
    return derived.create_hybrid()
