from sqlalchemy.event import listen
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapper, mapperlib


class DerivedColumn:
    def __init__(self, column, default=None):
        self.column = column
        self.default = default
        self.target = None
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
        target_names = set()
        for mapper in mapperlib._mapper_registry:
            if self.column.table in mapper.tables:
                if self.column in mapper.columns.values():
                    attr = mapper.get_property_by_column(self.column)
                    target_names.add(attr.key)
        if len(target_names) != 1:
            raise TypeError("Unable to find unambiguous column attribute name.")
        self.target = next(iter(target_names))

    def make_getter(self):
        def _fget(self, outer=self):
            return getattr(self, outer.target) is not None

        return _fget

    def make_setter(self):
        if self.default is None:
            return None

        def _fset(self, value, outer=self, defaults=self._default_functions()):
            if not isinstance(value, bool):
                raise TypeError("Flag only accepts boolean values")
            return setattr(self, outer.target, defaults[value]())

        return _fset

    def make_expression(self):
        def _expr(cls, expr=self.column.isnot(None)):
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
