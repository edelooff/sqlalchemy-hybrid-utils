from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.ext.hybrid import hybrid_property

from .expression import Expression
from .resolver import AttributeResolver, PrefetchedAttributeResolver
from .typing import ColumnDefaults


class DerivedColumn:
    def __init__(
        self,
        expression: Expression,
        default: Any = None,
        prefetch_attribute_names: bool = True,
    ):
        self.expression = expression
        self.default = default
        if not prefetch_attribute_names:
            self.resolver = AttributeResolver(expression.columns)
        else:
            self.resolver = PrefetchedAttributeResolver(expression.columns)
        if len(self.expression.columns) > 1 and self.default is not None:
            raise TypeError("Cannot use default for multi-column expression.")

    def _default_functions(self) -> ColumnDefaults:
        setter = self.default
        if not callable(setter):
            setter = lambda: self.default  # noqa
        return {True: setter, False: lambda: None}

    def make_getter(self) -> Callable[[Any], Any]:
        """Returns a getter function, evaluating the expression in bound scope."""
        evaluate = self.expression.evaluate
        values = self.resolver.values
        return lambda orm_obj: evaluate(values(orm_obj))

    def make_setter(self) -> Callable[[Any, Any], None]:
        """Returns a setter function setting default values based on given booleans."""
        defaults = self._default_functions()
        target_name = self.resolver.single_name

        def _fset(self: Any, value: Any) -> None:
            if not isinstance(value, bool):
                raise TypeError("Flag only accepts boolean values")
            setattr(self, target_name(self), defaults[value]())

        return _fset

    def create_hybrid(self) -> hybrid_property:
        return hybrid_property(
            fget=self.make_getter(),
            fset=self.make_setter() if self.default is not None else None,
            expr=lambda cls: self.expression.sql,
        )
