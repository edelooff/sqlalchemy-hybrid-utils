from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.ext.hybrid import hybrid_property

from .expression import Expression
from .resolver import (
    AttributeResolver,
    PrefetchedAttributeResolver,
)
from .typing import (
    ColumnDefaults,
    ExpressionEvaluation,
    ResolveAttrName,
    ResolveAttrValues,
)


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

    def make_getter(
        self,
    ) -> Callable[[Any, ExpressionEvaluation, ResolveAttrValues], Any]:
        def _fget(
            self: Any,
            evaluate: ExpressionEvaluation = self.expression.evaluate,
            values: ResolveAttrValues = self.resolver.values,
        ) -> Any:
            return evaluate(values(self))

        return _fget

    def make_setter(
        self,
    ) -> Callable[[Any, Any, ResolveAttrName, ColumnDefaults], None]:
        def _fset(
            self: Any,
            value: Any,
            target_name: ResolveAttrName = self.resolver.single_name,
            defaults: ColumnDefaults = self._default_functions(),
        ) -> None:
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
