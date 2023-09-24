# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import rpc_pb2 as rpc__pb2


class BootstrapStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Initialize = channel.unary_unary(
                '/Bootstrap/Initialize',
                request_serializer=rpc__pb2.BootstrapInit.SerializeToString,
                response_deserializer=rpc__pb2.BootstrapInitReply.FromString,
                )
        self.GameOver = channel.unary_unary(
                '/Bootstrap/GameOver',
                request_serializer=rpc__pb2.Empty.SerializeToString,
                response_deserializer=rpc__pb2.Empty.FromString,
                )


class BootstrapServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Initialize(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GameOver(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_BootstrapServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Initialize': grpc.unary_unary_rpc_method_handler(
                    servicer.Initialize,
                    request_deserializer=rpc__pb2.BootstrapInit.FromString,
                    response_serializer=rpc__pb2.BootstrapInitReply.SerializeToString,
            ),
            'GameOver': grpc.unary_unary_rpc_method_handler(
                    servicer.GameOver,
                    request_deserializer=rpc__pb2.Empty.FromString,
                    response_serializer=rpc__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Bootstrap', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Bootstrap(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Initialize(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Bootstrap/Initialize',
            rpc__pb2.BootstrapInit.SerializeToString,
            rpc__pb2.BootstrapInitReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GameOver(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Bootstrap/GameOver',
            rpc__pb2.Empty.SerializeToString,
            rpc__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)


class GameStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.MissileApproaching = channel.unary_unary(
                '/Game/MissileApproaching',
                request_serializer=rpc__pb2.GameMissileApproaching.SerializeToString,
                response_deserializer=rpc__pb2.GamePosition.FromString,
                )
        self.PositionStatus = channel.unary_unary(
                '/Game/PositionStatus',
                request_serializer=rpc__pb2.GamePositionStatus.SerializeToString,
                response_deserializer=rpc__pb2.GamePositionStatusReply.FromString,
                )
        self.Status = channel.unary_unary(
                '/Game/Status',
                request_serializer=rpc__pb2.GameSoldierStatus.SerializeToString,
                response_deserializer=rpc__pb2.GameSoldierWasHit.FromString,
                )


class GameServicer(object):
    """Missing associated documentation comment in .proto file."""

    def MissileApproaching(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PositionStatus(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Status(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_GameServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'MissileApproaching': grpc.unary_unary_rpc_method_handler(
                    servicer.MissileApproaching,
                    request_deserializer=rpc__pb2.GameMissileApproaching.FromString,
                    response_serializer=rpc__pb2.GamePosition.SerializeToString,
            ),
            'PositionStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.PositionStatus,
                    request_deserializer=rpc__pb2.GamePositionStatus.FromString,
                    response_serializer=rpc__pb2.GamePositionStatusReply.SerializeToString,
            ),
            'Status': grpc.unary_unary_rpc_method_handler(
                    servicer.Status,
                    request_deserializer=rpc__pb2.GameSoldierStatus.FromString,
                    response_serializer=rpc__pb2.GameSoldierWasHit.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Game', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Game(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def MissileApproaching(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Game/MissileApproaching',
            rpc__pb2.GameMissileApproaching.SerializeToString,
            rpc__pb2.GamePosition.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def PositionStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Game/PositionStatus',
            rpc__pb2.GamePositionStatus.SerializeToString,
            rpc__pb2.GamePositionStatusReply.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Status(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Game/Status',
            rpc__pb2.GameSoldierStatus.SerializeToString,
            rpc__pb2.GameSoldierWasHit.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)