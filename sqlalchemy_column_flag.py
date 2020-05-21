from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect


class DerivedColumn:
    def __init__(self, column, default=None):
        self.column = column
        self.default = default

    def _default_functions(self):
        setter = self.default
        if not callable(setter):
            setter = lambda: self.default  # noqa
        return {True: setter, False: lambda: None}

    def make_getter(self):
        def _fget(self, column=self.column):
            mapper = inspect(self).mapper
            target = mapper.get_property_by_column(column).key
            return getattr(self, target) is not None

        return _fget

    def make_setter(self):
        if self.default is None:
            return None
        defaults = self._default_functions()

        def _fset(self, value, column=self.column, defaults=defaults):
            if not isinstance(value, bool):
                raise TypeError("Flag only accepts boolean values")
            mapper = inspect(self).mapper
            target = mapper.get_property_by_column(column).key
            return setattr(self, target, defaults[value]())

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
