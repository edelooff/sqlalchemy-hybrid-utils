from typing import Any, Dict, Set, TYPE_CHECKING

from sqlalchemy.sql.schema import Column

if TYPE_CHECKING:
    ColType = Column[Any]
else:
    ColType = Column

ColumnDefaults = Dict[bool, Any]
ColumnValues = Dict[ColType, Any]
ColumnSet = Set[ColType]
MapperTargets = Dict[ColType, str]
