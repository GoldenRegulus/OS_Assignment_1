# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: rpc.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\trpc.proto\")\n\rBootstrapInit\x12\n\n\x02ip\x18\x01 \x01(\t\x12\x0c\n\x04port\x18\x02 \x01(\x05\"(\n\x12\x42ootstrapInitReply\x12\x12\n\nboard_size\x18\x01 \x01(\x05\"$\n\x0cGamePosition\x12\t\n\x01x\x18\x01 \x01(\x05\x12\t\n\x01y\x18\x02 \x01(\x05\"i\n\x16GameMissileApproaching\x12\x1f\n\x08position\x18\x01 \x01(\x0b\x32\r.GamePosition\x12\x18\n\x10time_to_approach\x18\x03 \x01(\x05\x12\x14\n\x0cmissile_type\x18\x04 \x01(\x05\")\n\x12GamePositionStatus\x12\x13\n\x0bis_occupied\x18\x01 \x01(\x08\"\x13\n\x11GamePositionReady\"k\n\x17GamePositionStatusReply\x12!\n\x08position\x18\x01 \x01(\x0b\x32\r.GamePositionH\x00\x12#\n\x05ready\x18\x02 \x01(\x0b\x32\x12.GamePositionReadyH\x00\x42\x08\n\x06status\"\x13\n\x11GameSoldierStatus\"$\n\x11GameSoldierWasHit\x12\x0f\n\x07was_hit\x18\x01 \x01(\x08\"\x07\n\x05\x45mpty2Z\n\tBootstrap\x12\x31\n\nInitialize\x12\x0e.BootstrapInit\x1a\x13.BootstrapInitReply\x12\x1a\n\x08GameOver\x12\x06.Empty\x1a\x06.Empty2\xb7\x01\n\x04Game\x12<\n\x12MissileApproaching\x12\x17.GameMissileApproaching\x1a\r.GamePosition\x12?\n\x0ePositionStatus\x12\x13.GamePositionStatus\x1a\x18.GamePositionStatusReply\x12\x30\n\x06Status\x12\x12.GameSoldierStatus\x1a\x12.GameSoldierWasHitb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'rpc_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _globals['_BOOTSTRAPINIT']._serialized_start=13
  _globals['_BOOTSTRAPINIT']._serialized_end=54
  _globals['_BOOTSTRAPINITREPLY']._serialized_start=56
  _globals['_BOOTSTRAPINITREPLY']._serialized_end=96
  _globals['_GAMEPOSITION']._serialized_start=98
  _globals['_GAMEPOSITION']._serialized_end=134
  _globals['_GAMEMISSILEAPPROACHING']._serialized_start=136
  _globals['_GAMEMISSILEAPPROACHING']._serialized_end=241
  _globals['_GAMEPOSITIONSTATUS']._serialized_start=243
  _globals['_GAMEPOSITIONSTATUS']._serialized_end=284
  _globals['_GAMEPOSITIONREADY']._serialized_start=286
  _globals['_GAMEPOSITIONREADY']._serialized_end=305
  _globals['_GAMEPOSITIONSTATUSREPLY']._serialized_start=307
  _globals['_GAMEPOSITIONSTATUSREPLY']._serialized_end=414
  _globals['_GAMESOLDIERSTATUS']._serialized_start=416
  _globals['_GAMESOLDIERSTATUS']._serialized_end=435
  _globals['_GAMESOLDIERWASHIT']._serialized_start=437
  _globals['_GAMESOLDIERWASHIT']._serialized_end=473
  _globals['_EMPTY']._serialized_start=475
  _globals['_EMPTY']._serialized_end=482
  _globals['_BOOTSTRAP']._serialized_start=484
  _globals['_BOOTSTRAP']._serialized_end=574
  _globals['_GAME']._serialized_start=577
  _globals['_GAME']._serialized_end=760
# @@protoc_insertion_point(module_scope)
