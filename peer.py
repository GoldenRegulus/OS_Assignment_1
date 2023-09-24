import argparse
import random
import grpc
import socket
from concurrent import futures
from rpc import rpc_pb2_grpc

def get_ipv4_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

# switches from Soldier to Commander class
def switch_to_commander():
    pass

class Soldier():
    def initialize_position(self, N):
        x = random.randint(0, N - 1)
        y = random.randint(0, N - 1)
        self.pos = (x, y)
        
    def stop_server(self):
        self.server.stop()
        self.serverclass = None
    
    def __init__(self, s, ip, port) -> None:
        self.s = s
        self.host_ip = ip
        self.host_port = port
        self.ip = get_ipv4_address()
        self.serverclass = self.GameServer(self)
        self.server = grpc.server(futures.ThreadPoolExecutor())
        self.port = self.server.add_insecure_port('0.0.0.0:0')
        self.will_be_commander = False
        self.pos = (-1, -1)
        
        with grpc.insecure_channel(':'.join([self.host_ip, self.host_port])) as channel:
            stub = rpc_pb2_grpc.BootstrapStub(channel)
            self.N =  stub.Initialize(rpc_pb2_grpc.rpc__pb2.BootstrapInit(self.ip, self.port))
            self.initialize_position(self.N)
            print('Initialized, transforming into server')
        
        rpc_pb2_grpc.add_GameServicer_to_server(self.serverclass, self.server)
        self.server.start()
        self.server.wait_for_termination()
        if self.will_be_commander:
            switch_to_commander()
                
    class GameServer(rpc_pb2_grpc.GameServicer):
        def __init__(self, outerself) -> None:
            super().__init__()
            self.outer_self = outerself
            self.possible_locations = []
            self.is_hit = False
        
        def MissileApproaching(self, request, context):
            self.possible_locations = []
            # generate possible locations
            pos = self.possible_locations.pop(0)
            return rpc_pb2_grpc.rpc__pb2.GamePosition(x=pos[0], y=pos[1])
            
        def PositionStatus(self, request, context):
            if not request.is_occupied:
                self.possible_locations = []
                return rpc_pb2_grpc.rpc__pb2.GamePositionStatusReply(ready = rpc_pb2_grpc.rpc__pb2.GamePositionReady())
            else:
                if len(self.possible_locations) > 0:
                    new_pos = self.possible_locations.pop(0)
                    return rpc_pb2_grpc.rpc__pb2.GamePositionStatusReply(position = rpc_pb2_grpc.rpc__pb2.GamePosition(x=new_pos[0], y=new_pos[1]))
                else:
                    self.is_hit = True
                    return rpc_pb2_grpc.rpc__pb2.GamePositionStatusReply(ready = rpc_pb2_grpc.rpc__pb2.GamePositionReady())
            
        def Status(self, request, context):
            reply = rpc_pb2_grpc.rpc__pb2.GameSoldierWasHit(was_hit = self.is_hit)
            if self.is_hit:
                context.send_reponse(reply)
                self.outer_self.stop_server()
            else:
                return reply
                
class Commander():
    
    def __init__(self, N, M, t, T, s, port) -> None:
        self.N = N
        self.M = M
        self.t = t
        self.T = T
        self.s = s
        # soldier = (ip, port, (x, y))
        self.soldiers = {}
        self.serverclass = self.CommanderInitializer(self)
        self.server = grpc.server(futures.ThreadPoolExecutor())
        self.port = port
        self.server.add_insecure_port(f'0.0.0.0:{port}')
        rpc_pb2_grpc.add_BootstrapServicer_to_server(self.serverclass, self.server)
        self.server.start()
        self.server.wait_for_termination()
        
        self.current_time = 0
        while self.current_time < self.T:
            
            self.current_time += self.t
            
    def check_pos_if_free(self, pos):
        if any([True for soldier in self.soldiers.values() if soldier[2][0] == pos.x and soldier[2][1] == pos.y]):
            return False
        return True
    
    def missile_approaching(self, pos, t, m_type):
        for (soldier_id, soldier) in self.soldiers.items():
            with grpc.insecure_channel(':'.join([soldier[0], soldier[1]])) as channel:
                stub = rpc_pb2_grpc.GameStub(channel)
                pos = stub.MissileApproaching(rpc_pb2_grpc.GameMissileApproaching(x = pos[0], y = pos[1], t = t, type = m_type))
                while True:
                    if self.check_pos_if_free(pos):
                        self.soldiers[soldier_id][2] = (pos.x, pos.y)
                        _ = stub.PositionStatus(rpc_pb2_grpc.rpc__pb2.GamePositionStatus(is_occupied=False))
                        break
                    else:
                        reply = stub.PositionStatus(rpc_pb2_grpc.rpc__pb2.GamePositionStatus(is_occupied=True))
                        if isinstance(reply, rpc_pb2_grpc.rpc__pb2.GamePositionReady):
                            break
                        else:
                            pos = reply
                        
    def status(self, soldier_id):
        with grpc.insecure_channel(':'.join([self.soldiers[soldier_id][0], self.soldiers[soldier_id][1]])) as channel:
            stub = rpc_pb2_grpc.GameStub(channel)
            reply = stub.Status(rpc_pb2_grpc.rpc__pb2.GameSoldierStatus())
            if reply.was_hit:
                _ = self.soldiers.pop(soldier_id)
        
    def stop_server(self):
        self.server.stop()
        self.serverclass = None

    class CommanderInitializer(rpc_pb2_grpc.BootstrapServicer):
        def __init__(self, outerself) -> None:
            super().__init__()
            self.outer_self = outerself
        
        def Initialize (self, request, context):
            self.outer_self.soldiers[len(self.outer_self.soldiers.keys())] = (request.ip, request.port, (-1, -1))
            reply = rpc_pb2_grpc.rpc__pb2.BootstrapInitReply(board_size = self.outer_self.N)
            if len(self.outer_self.soldiers.keys()) == self.outer_self.M:
                context.send_reponse(reply)
                self.outer_self.stop_server()
            else:
                return reply
        

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
 
 