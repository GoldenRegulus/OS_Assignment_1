from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

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
    __slots__ = ["soldier_id"]
    SOLDIER_ID_FIELD_NUMBER: _ClassVar[int]
    soldier_id: int
    def __init__(self, soldier_id: _Optional[int] = ...) -> None: ...

class GameSoldierWasHit(_message.Message):
    __slots__ = ["soldier_id", "was_hit"]
    SOLDIER_ID_FIELD_NUMBER: _ClassVar[int]
    WAS_HIT_FIELD_NUMBER: _ClassVar[int]
    soldier_id: int
    was_hit: bool
    def __init__(self, soldier_id: _Optional[int] = ..., was_hit: bool = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = []
    def __init__(self) -> None: ...
