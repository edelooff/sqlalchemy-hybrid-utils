from typing import Any, Callable, Dict, Set, Type, TYPE_CHECKING

from sqlalchemy.sql.schema import Column

if TYPE_CHECKING:
    ColType = Column[Any]
else:
    ColType = Column

ColumnDefaults = Dict[bool, Any]
ColumnValues = Dict[ColType, Any]
ColumnSet = Set[ColType]
ExpressionEvaluation = Callable[[Any], Any]
MapperTargets = Dict[Type[Any], Dict[ColType, str]]
ResolveAttrName = Callable[[Any], str]
ResolveAttrValues = Callable[[Any], ColumnValues]
