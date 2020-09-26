from typing import TYPE_CHECKING, Any, Callable, Dict, Set, Type

from sqlalchemy.sql.schema import Column

if TYPE_CHECKING:
    ColType = Column[Any]
else:
    ColType = Column

ColumnDefaults = Dict[bool, Any]
ColumnValues = Callable[[ColType], Any]
ColumnSet = Set[ColType]
MapperTargets = Dict[Type[Any], Dict[ColType, str]]
