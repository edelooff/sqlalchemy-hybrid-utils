from typing import TYPE_CHECKING, Any, Callable, Dict, Set, Type, Union

from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.schema import Column

if TYPE_CHECKING:
    ColType = Union[Column[Any], ColumnElement[Any]]
else:
    ColType = Union[Column, ColumnElement]

ColumnDefaults = Dict[bool, Any]
ColumnValues = Callable[[ColType], Any]
ColumnSet = Set[ColType]
Function = Callable[..., Any]
FunctionMap = Dict[Function, Function]
MapperTargets = Dict[Type[Any], Dict[ColType, str]]
