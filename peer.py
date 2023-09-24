import argparse
import grpc
import socket
import futures
from rpc import rpc_pb2_grpc

def get_ipv4_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

class Soldier():
    def __init__(self, s, ip, port) -> None:
        self.s = s
        self.host_ip = ip
        self.host_port = port
        self.ip = get_ipv4_address()
        self.port = None
        self.server = None
        self.possible_locations = []
        self.serverclass = self.GameServer(self)
        
        with grpc.insecure_channel(':'.join([self.host_ip, self.host_port])) as channel:
            stub = rpc_pb2_grpc.BootstrapStub(channel)
            self.N =  stub.Initialize(rpc_pb2_grpc.rpc__pb2.BootstrapInit(self.ip, self.port))
            print('Initialized, transforming into server')
        
        self.server.start()
                
    class GameServer(rpc_pb2_grpc.GameServicer):
        def __init__(self, outerself) -> None:
            super().__init__()
            self.outer_self = outerself
            self.outer_self.server = grpc.server(futures.ThreadPoolExecutor())
            self.outer_self.port = self.outer_self.server.add_insecure_port('0.0.0.0:0')
        
        def MissileApproaching(self, request, context):
            if len(self.outer_self.possible_locations) == 0:
                
            else:
                pos = self.outer_self.possible_locations.pop(0)
                return rpc_pb2_grpc.rpc__pb2.GamePosition(x=pos[0], y=pos[1])
            
        def PositionStatus(self, request, context):
            if not request.is_occupied:
                self.outer_self.possible_locations = []
                return rpc_pb2_grpc.rpc__pb2.GamePositionStatusReply(ready = rpc_pb2_grpc.rpc__pb2.GamePositionReady())
            return rpc_pb2_grpc.rpc__pb2.GamePositionStatusReply(position = rpc_pb2_grpc.rpc__pb2.GamePosition())
            
        # def Status(self, request, context):
        #     return rpc_pb2_grpc.rpc__pb2.GameSoldierWasHit(soldier_id = self.id, was_hit = )
                
class Commander(rpc_pb2_grpc.BootstrapServicer):
    def __init__(self, N, M, t, T, s, port) -> None:
        self.N = N
        self.M = M
        self.t = t
        self.T = T
        self.s = s
        self.port = port
        self.soldiers = []
        
    class CommanderInitializer(rpc_pb2_grpc.BootstrapServicer):
        def __init__(self, outerself) -> None:
            super().__init__()
            self.outer_self = outerself
        
        def Initialize (self, request, context):
            self.outer_self.soldiers.append((request.ip, request.port))
            return rpc_pb2_grpc.rpc__pb2.BootstrapInitReply(board_size = self.outer_self.N)
        

def is_ip(string: str):
    split_str = string.split('.')
    if len(split_str) != 4:
        return False
    for sub in split_str[:3]:
        if not (1 <= int(sub) < 256):
            return False
    if not (1 <= int(split_str[-1]) < 255):
        return False
    return True

parser = argparse.ArgumentParser(description="Initialize soldier or commander")
subparsers = parser.add_subparsers(required=True)

parser_s = subparsers.add_parser('soldier')
parser_s.add_argument('s', help='Speed of soldier (0-4 inclusive)', type=int)
parser_s.add_argument('ip', help='IPv4 address of commander')
parser_s.add_argument('port', help='Port number of commander', type=int)

parser_c = subparsers.add_parser('commander')
parser_c.add_argument('N', help='Size N of NxN matrix', type=int)
parser_c.add_argument('M', help='Number of soldiers, excluding this unit (minimum 9)', type=int)
parser_c.add_argument('t', help='Missiles will hit every t seconds', type=int)
parser_c.add_argument('T', help='The game will run for T seconds', type=int)
parser_c.add_argument('s', help='Speed of commander (0-4 inclusive)', type=int)
parser_c.add_argument('port', help='Port number on which soldiers will connect', type=int)

args = vars(parser.parse_args())

if args['s'] < 0 or args['s'] > 4:
    raise ValueError('Speed must be between 0 and 4, both inclusive')
if args['port'] > 65535 or args['port'] < 1024:
    raise ValueError('Port must be a valid number between 1024 to 65535, both inclusive')
if 'ip' in args: # soldier
    if not is_ip(args['ip']):
        raise ValueError('IP address must be a valid address between 0.0.0.1 and 255.255.255.254, both inclusive')
else: # commander
    if args['N'] < 4:
        raise ValueError('NxN matrix cannot be less than 4x4 in size')
    if args['M'] < 9:
        raise ValueError('Number of soldiers cannot be less than 9')
    if args['T'] <= 0 or args['t'] <= 0:
        raise ValueError('Time invalid')
    if args['t'] > args['T']:
        raise ValueError('t cannot be greater than T')
 
 