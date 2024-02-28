from typing import TYPE_CHECKING, Any, Callable, Dict, Set, Type

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapper
from sqlalchemy.sql.schema import Column

try:
    from sqlalchemy.ext.hybrid import _HybridGetterType as HybridGetterType
except ImportError:
    HybridGetterType = Callable[[Any], Any]  # type: ignore
try:
    from sqlalchemy.ext.hybrid import _HybridSetterType as HybridSetterType
except ImportError:
    HybridSetterType = Callable[[Any, Any], None]  # type: ignore

# Types that are not yet generics in SQLAlchemy 1.3 and 1.4 need special treatment
if TYPE_CHECKING:
    ColumnType = Column[Any]
    HybridPropertyType = hybrid_property[bool]
    MapperType = Mapper[Any]
else:
    ColumnType = Column
    HybridPropertyType = hybrid_property
    MapperType = Mapper

ColumnDefaults = Dict[bool, Any]
ColumnValues = Callable[[ColumnType], Any]
ColumnSet = Set[ColumnType]
Function = Callable[..., Any]
FunctionMap = Dict[Function, Function]
MapperTargets = Dict[Type[Any], Dict[ColumnType, str]]

__all__ = (
    "ColumnDefaults",
    "ColumnSet",
    "ColumnValues",
    "Function",
    "FunctionMap",
    "HybridGetterType",
    "HybridSetterType",
    "MapperTargets",
)
