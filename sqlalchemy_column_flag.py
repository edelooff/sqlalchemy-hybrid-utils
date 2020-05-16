from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect


def column_flag(column, **options):
    def target_key(instance):
        target = inspect(instance).mapper.get_property_by_column(column)
        return target.key

    def fget(self):
        return getattr(self, target_key(self)) is not None

    def fset(self, value, default=options.get("default")):
        if not isinstance(value, bool):
            raise TypeError("Flag only accepts boolean values")
        if callable(default):
            default = default()
        return setattr(self, target_key(self), default if value else None)

    def expr(cls):
        return column.isnot(None)

    return hybrid_property(
        fget=fget, fset=fset if "default" in options else None, expr=expr)
