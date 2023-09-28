from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class BootstrapInit(_message.Message):
    __slots__ = ["ip", "port"]
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    ip: str
    port: int
    def __init__(self, ip: _Optional[str] = ..., port: _Optional[int] = ...) -> None: ...

class BootstrapInitReply(_message.Message):
    __slots__ = ["board_size"]
    BOARD_SIZE_FIELD_NUMBER: _ClassVar[int]
    board_size: int
    def __init__(self, board_size: _Optional[int] = ...) -> None: ...

class GamePosition(_message.Message):
    __slots__ = ["x", "y"]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    x: int
    y: int
    def __init__(self, x: _Optional[int] = ..., y: _Optional[int] = ...) -> None: ...

class GameMissileApproaching(_message.Message):
    __slots__ = ["position", "time_to_approach", "missile_type"]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    TIME_TO_APPROACH_FIELD_NUMBER: _ClassVar[int]
    MISSILE_TYPE_FIELD_NUMBER: _ClassVar[int]
    position: GamePosition
    time_to_approach: int
    missile_type: int
    def __init__(self, position: _Optional[_Union[GamePosition, _Mapping]] = ..., time_to_approach: _Optional[int] = ..., missile_type: _Optional[int] = ...) -> None: ...

class GamePositionStatus(_message.Message):
    __slots__ = ["is_occupied"]
    IS_OCCUPIED_FIELD_NUMBER: _ClassVar[int]
    is_occupied: bool
    def __init__(self, is_occupied: bool = ...) -> None: ...

class GamePositionReady(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GamePositionStatusReply(_message.Message):
    __slots__ = ["position", "ready"]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    READY_FIELD_NUMBER: _ClassVar[int]
    position: GamePosition
    ready: GamePositionReady
    def __init__(self, position: _Optional[_Union[GamePosition, _Mapping]] = ..., ready: _Optional[_Union[GamePositionReady, _Mapping]] = ...) -> None: ...

class GameSoldierStatus(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...

class GameSoldierWasHit(_message.Message):
    __slots__ = ["was_hit"]
    WAS_HIT_FIELD_NUMBER: _ClassVar[int]
    was_hit: bool
    def __init__(self, was_hit: bool = ...) -> None: ...

class SoldierParams(_message.Message):
    __slots__ = ["s_id", "ip", "port", "pos"]
    S_ID_FIELD_NUMBER: _ClassVar[int]
    IP_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    POS_FIELD_NUMBER: _ClassVar[int]
    s_id: str
    ip: str
    port: int
    pos: GamePosition
    def __init__(self, s_id: _Optional[str] = ..., ip: _Optional[str] = ..., port: _Optional[int] = ..., pos: _Optional[_Union[GamePosition, _Mapping]] = ...) -> None: ...

class CommanderParams(_message.Message):
    __slots__ = ["M", "ct", "t", "T", "m", "soldiers"]
    M_FIELD_NUMBER: _ClassVar[int]
    CT_FIELD_NUMBER: _ClassVar[int]
    T_FIELD_NUMBER: _ClassVar[int]
    T_FIELD_NUMBER: _ClassVar[int]
    M_FIELD_NUMBER: _ClassVar[int]
    SOLDIERS_FIELD_NUMBER: _ClassVar[int]
    M: int
    ct: int
    t: int
    T: int
    m: GameMissileApproaching
    soldiers: _containers.RepeatedCompositeFieldContainer[SoldierParams]
    def __init__(self, M: _Optional[int] = ..., ct: _Optional[int] = ..., t: _Optional[int] = ..., T: _Optional[int] = ..., m: _Optional[_Union[GameMissileApproaching, _Mapping]] = ..., soldiers: _Optional[_Iterable[_Union[SoldierParams, _Mapping]]] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
