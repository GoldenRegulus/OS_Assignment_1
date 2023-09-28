import argparse
import random
from time import sleep
import grpc
import socket
from concurrent import futures
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TextColumn, BarColumn
from rpc.rpc_pb2 import (
    BootstrapInit,
    BootstrapInitReply,
    CommanderParams,
    Empty,
    GameMissileApproaching,
    GamePosition,
    GamePositionReady,
    GamePositionStatus,
    GamePositionStatusReply,
    GameSoldierStatus,
    GameSoldierWasHit,
    SoldierParams,
)
from rpc import rpc_pb2_grpc as rpc

def get_ipv4_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("10.254.254.254", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def generate_random_pos(N):
    x = random.randint(0, N - 1)
    y = random.randint(0, N - 1)
    return (x, y)

"""
This function first creates a list of coordinates 'redzone_area' based on the 'm_pos' and 'm_type' values. 
It then checks if the 's_pos' coordinate is within the redzone_area using a list comprehension and the any function.
If the 's_pos' coordinate is not in the 'red zone', the function returns 'None'.
Otherwise, it proceeds to calculate the possible escape locations for the soldier based on the 's_pos', 'N', and 's_speed' values.
The escape locations are stored in the 'soldier_escape_locations' list.
Finally, the function removes any escape locations that are within the 'redzone_area' and returns the updated 'soldier_escape_locations' list.
"""
def generate_shelter_locations(
    N: int,
    s_pos: (int, int),
    s_speed: int,
    m_pos: GamePosition,
    m_type: int,
):
    redzone_area = [
        (x, y)
        for x in range(max(m_pos.x - m_type + 1, 0), min(m_pos.x + m_type, N))
        for y in range(max(m_pos.y - m_type + 1, 0), min(m_pos.y + m_type, N))
    ]
    is_soldier_in_redzone = any([True for pos in redzone_area if pos == s_pos])
    if not is_soldier_in_redzone:
        return None
    soldier_escape_locations = []
    for i in range(0, s_speed + 1):
        # top
        if s_pos[1] + i < N:
            soldier_escape_locations.append((s_pos[0], s_pos[1] + i))
        # top-right
        if s_pos[1] + i < N and s_pos[0] + i < N:
            soldier_escape_locations.append((s_pos[0] + i, s_pos[1] + i))
        # top-left
        if s_pos[1] + i < N and s_pos[0] - i >= 0:
            soldier_escape_locations.append((s_pos[0] - i, s_pos[1] + i))
        # bottom
        if s_pos[1] - i >= 0:
            soldier_escape_locations.append((s_pos[0], s_pos[1] - i))
        # bottom-right
        if s_pos[1] - i >= 0 and s_pos[0] + i < N:
            soldier_escape_locations.append((s_pos[0] + i, s_pos[1] - i))
        # bottom-left
        if s_pos[1] - i >= 0 and s_pos[0] - i >= 0:
            soldier_escape_locations.append((s_pos[0] - i, s_pos[1] - i))
        # left
        if s_pos[0] - i >= 0:
            soldier_escape_locations.append((s_pos[0] - i, s_pos[1]))
        # right
        if s_pos[0] + i < N:
            soldier_escape_locations.append((s_pos[0] + i, s_pos[1]))
    soldier_escape_locations = [pos for pos in soldier_escape_locations if pos not in redzone_area]
    return soldier_escape_locations


class Soldier:
    def stop_server(self):
        self.server.stop(10)

    """    
    This function communicates with the commander and tells it it's own IP address and port and receives the board size from the commander.
    It is also generating it's own position randomly, based on the board size it receives.
    """
    def initialize(self):
        with grpc.insecure_channel(f"{self.host_ip}:{self.host_port}") as channel:
            stub = rpc.BootstrapStub(channel)
            self.N = stub.Initialize(BootstrapInit(ip=self.ip, port=self.port)).board_size  # important change
            self.pos = generate_random_pos(self.N)
            Console().clear()
            print("Soldier Initialized")

    def __init__(self, s, ip, port) -> None:
        self.s = s
        self.host_ip = ip
        self.host_port = port
        self.pos = (-1, -1)
        self.ip = get_ipv4_address()
        self.serverclass = self.GameServer(self)
        self.server = grpc.server(futures.ThreadPoolExecutor())
        self.port = self.server.add_insecure_port(f"{self.ip}:0")
        self.will_be_commander = False
        self.commander_args = {}

        self.initialize()

        rpc.add_GameServicer_to_server(self.serverclass, self.server)
        self.server.start()
        self.server.wait_for_termination()
        self.serverclass = None

    class GameServer(rpc.GameServicer):
        def __init__(self, outerself) -> None:
            super().__init__()
            self.outer_self = outerself
            self.possible_locations = []
            self.is_hit = False

        """
        This function replies to the commander's 'missile_approaching' call.
        If the soldier is not in the red zone, it returns the current game position.
        If the soldier is in the red zone, it generates a list of possible shelter locations and keeps it temporarily.
        If there are possible locations, the soldier sets it's own position to the first position generated by this function and also sends it to the commander.
        If there are no possible locations, the soldier is marked as being hit and the commander is notified that soldier has finished computation.
        """
        def MissileApproaching(self, request, context):
            self.possible_locations = generate_shelter_locations(
                self.outer_self.N,
                self.outer_self.pos,
                self.outer_self.s,
                request.position,
                request.missile_type,
            )
            if self.possible_locations is None:
                return GamePosition(x=self.outer_self.pos[0], y=self.outer_self.pos[1])
            if len(self.possible_locations) > 0:
                self.outer_self.pos = self.possible_locations.pop(0)
            else:
                self.is_hit = True
            return GamePosition(x=self.outer_self.pos[0], y=self.outer_self.pos[1])

        """
        The commander notifies this function whether the position returned to the 'missile_approaching' call is occupied or free.
        If the position is free, the soldier notifies the commander that it has finished computation.
        If the position is not free and their is a possible shelter location, the soldier sets it's own position to new location and sends it to the commander.
        If position is not free and there are no possible shelter locations, the soldier is marked as being hit and the commander is notified that soldier has finished computation 
        """
        def PositionStatus(self, request, context):
            if request.is_occupied is False:
                self.possible_locations = []
                return GamePositionStatusReply(ready=GamePositionReady())
            if self.is_hit is False and self.possible_locations is None:
                self.outer_self.pos = generate_random_pos(self.outer_self.N)
                return GamePositionStatusReply(
                    position=GamePosition(x=self.outer_self.pos[0], y=self.outer_self.pos[1])
                )
            if self.is_hit is False and len(self.possible_locations) > 0:
                self.outer_self.pos = self.possible_locations.pop(0)
                return GamePositionStatusReply(
                    position=GamePosition(x=self.outer_self.pos[0], y=self.outer_self.pos[1])
                )
            self.is_hit = True
            return GamePositionStatusReply(ready=GamePositionReady())

        def Status(self, request, context):
            reply = GameSoldierWasHit(was_hit=self.is_hit)
            if self.is_hit:
                self.outer_self.stop_server()
            return reply

        def TransferCommander(self, request, context):
            self.outer_self.commander_args["M"] = request.M
            self.outer_self.commander_args["ct"] = request.ct
            self.outer_self.commander_args["t"] = request.t
            self.outer_self.commander_args["T"] = request.T
            self.outer_self.commander_args["m_pos"] = (
                request.m.position.x,
                request.m.position.y,
            )
            self.outer_self.commander_args["m_type"] = request.m.missile_type
            self.outer_self.commander_args["soldiers"] = {}
            for soldier in request.soldiers:
                self.outer_self.commander_args["soldiers"][int(soldier.s_id)] = (
                    soldier.ip,
                    soldier.port,
                    (soldier.pos.x, soldier.pos.y),
                )
            self.outer_self.will_be_commander = True
            self.outer_self.stop_server()
            return Empty()
            
        def GameOver(self, request, context):
            self.outer_self.stop_server()
            return Empty()


class Commander:
    @classmethod
    def resume(cls, N, s, pos, M, ct, t, T, m_pos, m_type, soldiers):
        instance = cls(*[i for i in range(6)], skip_init=True)
        instance.N = N
        instance.M = M
        instance.t = t
        instance.T = T
        instance.s = s
        instance.current_time = ct
        instance.pos = pos
        instance.soldiers = soldiers
        instance.console = Console()

        instance.m_pos = m_pos
        instance.m_type = m_type
        instance.current_time += instance.t
        instance.print_board()
        sleep(1)
        instance.game_loop()
        instance.game_over()
        if len(instance.soldiers.keys()) >= 0.5 * instance.M:
            instance.console.print("[#66ff66]Game ended. The battle is won.[/#66ff66]")
        else:
            instance.console.print("[#ff5566]Game ended. The battle is lost.[/#ff5566]")

    def __init__(self, N, M, t, T, s, port, skip_init=False) -> None:
        if not skip_init:
            self.N = N
            self.M = M
            self.t = t
            self.T = T
            self.s = s
            self.soldiers = {}  # soldier = (ip, port, (x, y))
            self.pos = generate_random_pos(self.N)
            self.current_time = 0
            self.console = Console()
            self.console.clear()

            self.initialize(port)
            self.game_loop()
            self.game_over()
            if len(self.soldiers.keys()) >= 0.5 * self.M:
                self.console.print("[#66ff66]Game ended. The battle is won.[/#66ff66]")
            else:
                self.console.print("[#ff5566]Game ended. The battle is lost.[/#ff5566]")

    """
    This function initializes a  gRPC server and waits for all the soldiers to connect.
    It records their IP addresses and ports and sends board size to all of them.
    """
    def initialize(self, port):
        self.serverclass = self.CommanderInitializer(self)
        self.server = grpc.server(futures.ThreadPoolExecutor())
        self.server.add_insecure_port(f"{get_ipv4_address()}:{port}")
        rpc.add_BootstrapServicer_to_server(self.serverclass, self.server)
        self.progress = Progress(
            # SpinnerColumn('simpleDotsScrolling', '#ff5566', 2),
            TextColumn("[#999999]{task.description}"),
            BarColumn(pulse_style="#ffff55"),
            TextColumn("[#eeee55]{task.completed}/{task.total}"),
            transient=True,
            refresh_per_second=30,
        )
        with self.progress:
            self.task = self.progress.add_task("Waiting for clients ", total=self.M, start=False)
            self.server.start()
            self.server.wait_for_termination()
        self.server = None
        self.serverclass = None


    """
    this function is the main game loop that simulates the progression of the game over time.
    Each iteration of the loop includes:
        1. Randomly generating - position for a missile, type of missile.
        2. Simulating the approach of the missile and updating the game status.
        3. Checking for the status of all the soldiers and transferring the commander control accordingly (if needed).
        4. Displaying the current status of the game board.
        5. Checking for specific conditions and transferring game elements accordingly.
        6. Incrementing the current time by the specified time interval (self.t).
        7. Printing the updated game board to the console.
    """
    def game_loop(self):
        while self.current_time < self.T:
            self.m_pos = generate_random_pos(self.N)
            self.m_type = random.randint(1, 4)
            self.missile_approaching(self.m_pos, self.t, self.m_type)
            self.status_all()
            self.check_and_transfer_self()
            self.current_time += self.t
            self.print_board()
            sleep(1)

    # print the NxN board, with redzone, missile position, soldier location and commander location
    def print_board(self):
        self.console.clear()
        redzone_area = [
            (x, y)
            for x in range(
                max(self.m_pos[0] - self.m_type + 1, 0),
                min(self.m_pos[0] + self.m_type, self.N),
            )
            for y in range(
                max(self.m_pos[1] - self.m_type + 1, 0),
                min(self.m_pos[1] + self.m_type, self.N),
            )
        ]

        table = Table(
            show_header=False,
            show_lines=True,
            header_style="",
            collapse_padding=False,
            padding=0,
            border_style="#555555",
        )
        for col in range(self.N + 1):
            table.add_column(
                "",
                justify="center",
                width=3,
                vertical="middle",
            )
        # Add y coordinate at the left with the same style
        for col in range(self.N - 1, -1, -1):
            row_values = [f"[#ff66ff]{col}[/#ff66ff]"]
            for row in range(self.N):
                if (row, col) == self.m_pos:
                    cell_value = "[#ff5566]M[/#ff5566]"
                elif (row, col) in redzone_area:
                    cell_value = "[#ff5566]•[/#ff5566]"
                else:
                    cell_value = "[black]·[/black]"
                for s_idx, (_, _, s_pos) in (self.soldiers | {"C": ("", "", self.pos)}).items():
                    if (row, col) == s_pos:
                        if (row, col) == self.m_pos:
                            cell_value = f"[#ff7788 underline]{s_idx}[/#ff7788 underline]"
                        elif (row, col) in redzone_area:
                            cell_value = f"[#ffff66]{s_idx}[/#ffff66]"
                        else:
                            cell_value = f"[#6655ff]{s_idx}[/#6655ff]"
                row_values.append(cell_value)
            table.add_row(*row_values)
        table.add_row(*[""] + [f"[#ff66ff]{col}[/#ff66ff]" for col in range(self.N)])
        self.console.print(table)
        grid = Table(
            show_header=True,
            show_lines=False,
            box=None,
            padding=0,
            width=5 + self.N * 4,
            expand=True,
        )
        grid.add_column("Time", justify="left")
        grid.add_column("")
        grid.add_column("Soldiers", justify="right")
        grid.add_row(f"{self.current_time}/{self.T}", "", f"{len(self.soldiers.keys())}/{self.M}")
        self.console.print(grid)

    """
     This function checks if any of the soldiers have the same coordinates as the given position, including the commander himself.
    """
    def check_pos_if_free(self, pos):
        if any(
            [
                True
                for soldier in (self.soldiers | {"C": ("", "", self.pos)}).values()
                if soldier[2][0] == pos.x and soldier[2][1] == pos.y
            ]
        ):
            return False
        return True

    def check_and_transfer_self(self):
        possible_locations = generate_shelter_locations(
            self.N,
            self.pos,
            self.s,
            GamePosition(x=self.m_pos[0], y=self.m_pos[1]),
            self.m_type,
        )
        if possible_locations is None:
            return
        while len(possible_locations) > 0:
            new_pos = possible_locations.pop(0)
            if self.check_pos_if_free(GamePosition(x=new_pos[0], y=new_pos[1])):
                self.pos = new_pos
                return
        if len(self.soldiers.keys()) == 0:
            raise Exception()
        target = self.soldiers.pop([i for i in self.soldiers.keys()][0])
        with grpc.insecure_channel(f"{target[0]}:{target[1]}") as channel:
            stub = rpc.GameStub(channel)
            _ = stub.TransferCommander(
                CommanderParams(
                    M=self.M,
                    ct=self.current_time,
                    t=self.t,
                    T=self.T,
                    m=GameMissileApproaching(
                        position=GamePosition(x=self.m_pos[0], y=self.m_pos[1]),
                        time_to_approach=self.t,
                        missile_type=self.m_type,
                    ),
                    soldiers=[
                        SoldierParams(
                            s_id=str(s_id),
                            ip=ip,
                            port=port,
                            pos=GamePosition(x=x, y=y),
                        )
                        for (s_id, (ip, port, (x, y))) in self.soldiers.items()
                    ]
                    if len(self.soldiers.items()) > 0
                    else [],
                )
            )
        self.console.print("[#ff5566]Commander transferred.[/#ff5566]")
        raise Exception()

    def game_over(self):
        for soldier in self.soldiers.values():
            with grpc.insecure_channel(f"{soldier[0]}:{soldier[1]}") as channel:
                stub = rpc.GameStub(channel)
                _ = stub.GameOver(Empty())

    """
    This function sends a missile position, missile type and time to approach to all the soldiers.
    We recive the position form each soldier, and if the positon is same as the last time, then do nothing.
    If the soldier has moved, we check if the position is free ot not and notify the soldier accodingly.
    And if the posoiton is not free, we notify the soldier to send a new position
    """
    def missile_approaching(self, m_pos, t, m_type):
        for soldier_id, soldier in self.soldiers.items():
            with grpc.insecure_channel(f"{soldier[0]}:{soldier[1]}") as channel:
                stub = rpc.GameStub(channel)
                pos: GamePosition = stub.MissileApproaching(
                    GameMissileApproaching(
                        position=GamePosition(x=m_pos[0], y=m_pos[1]),
                        time_to_approach=t,
                        missile_type=m_type,
                    )
                )
                while True:
                    if (pos.x, pos.y) == soldier[2]:
                        break
                    if self.check_pos_if_free(pos):
                        self.soldiers[soldier_id] = (
                            self.soldiers[soldier_id][0],
                            self.soldiers[soldier_id][1],
                            (pos.x, pos.y),
                        )
                        _ = stub.PositionStatus(GamePositionStatus(is_occupied=False))
                        break
                    reply = stub.PositionStatus(GamePositionStatus(is_occupied=True))
                    if reply.WhichOneof("status") == "ready":
                        break
                    pos = reply.position

    def status(self, soldier_id):
        with grpc.insecure_channel(f"{self.soldiers[soldier_id][0]}:{self.soldiers[soldier_id][1]}") as channel:
            stub = rpc.GameStub(channel)
            reply: GameSoldierWasHit = stub.Status(GameSoldierStatus())
            if reply.was_hit:
                _ = self.soldiers.pop(soldier_id)

    def status_all(self):
        keys = [i for i in self.soldiers.keys()]
        for soldier_id in keys:
            self.status(soldier_id)

    def stop_server(self):
        self.server.stop(10)

    class CommanderInitializer(rpc.BootstrapServicer):
        def __init__(self, outerself) -> None:
            super().__init__()
            self.outer_self = outerself 

        def Initialize(self, request, context):
            self.outer_self.soldiers[len(self.outer_self.soldiers.keys()) + 1] = (
                request.ip,
                request.port,
                (-1, -1),
            )
            self.outer_self.progress.update(self.outer_self.task, advance=1)
            reply = BootstrapInitReply(board_size=self.outer_self.N)
            if len(self.outer_self.soldiers.keys()) == self.outer_self.M:
                self.outer_self.stop_server()
            return reply


"""
It checks if the string is a valid IP address by splitting it into four parts separated by dots.
It then checks if each part is a number between 0 and 255.
"""
def is_ip(string: str):
    split_str = string.split(".")
    if len(split_str) != 4:
        return False
    for sub in split_str[:3]:
        if not (0 <= int(sub) < 256):
            return False
    if not (1 <= int(split_str[-1]) < 255):
        return False
    return True


parser = argparse.ArgumentParser(description="Initialize soldier or commander")
subparsers = parser.add_subparsers(required=True)

parser_s = subparsers.add_parser("soldier")
parser_s.add_argument("s", help="Speed of soldier (0-4 inclusive)", type=int)
parser_s.add_argument("ip", help="IPv4 address of commander")
parser_s.add_argument("port", help="Port number of commander", type=int)

parser_c = subparsers.add_parser("commander")
parser_c.add_argument("N", help="Size N of NxN matrix", type=int)
parser_c.add_argument("M", help="Number of soldiers, excluding this unit (minimum 9)", type=int)
parser_c.add_argument("t", help="Missiles will hit every t seconds", type=int)
parser_c.add_argument("T", help="The game will run for T seconds", type=int)
parser_c.add_argument("s", help="Speed of commander (0-4 inclusive)", type=int)
parser_c.add_argument("port", help="Port number on which soldiers will connect", type=int)


"""
Check if
    -Speed is in range [0 to 4].
    -Port is in range [1024 to 65535].
    -IP address is in range [0.0.0.1 to 255.255.255.254].
    -N is not less than 4x4.
    -M is not less than 9.
"""
args = vars(parser.parse_args())

if args["s"] < 0 or args["s"] > 4:
    raise ValueError("Speed must be between 0 and 4, both inclusive")
if args["port"] > 65535 or args["port"] < 1024:
    raise ValueError("Port must be a valid number between 1024 to 65535, both inclusive")
if "ip" in args:  # soldier
    if not is_ip(args["ip"]):
        raise ValueError("IP address must be a valid address between 0.0.0.1 and 255.255.255.254, both inclusive")
else:  # commander
    if args["N"] < 4:
        raise ValueError("NxN matrix cannot be less than 4x4 in size")
    if args["M"] < 1:
        raise ValueError("Number of soldiers cannot be less than 9")
    if args["T"] <= 0 or args["t"] <= 0:
        raise ValueError("Time invalid")
    if args["t"] > args["T"]:
        raise ValueError("t cannot be greater than T")


"""
If the script is for a soldier, create a Soldier instance (s) with the provided arguments.
If the soldier is also a commander, attempt to resume the commander from previous state.
If the script is for a commander, create a Commander instance with the specified parameters.
"""
if "ip" in args:
    s = Soldier(args["s"], args["ip"], args["port"])
    if s.will_be_commander:
        try:
            s = Commander.resume(
                ct=s.commander_args["ct"],
                N=s.N,
                s=s.s,
                pos=s.pos,
                M=s.commander_args["M"],
                t=s.commander_args["t"],
                T=s.commander_args["T"],
                m_pos=s.commander_args["m_pos"],
                m_type=s.commander_args["m_type"],
                soldiers=s.commander_args["soldiers"],
            )
        except Exception:
            pass
else:
    try:
        Commander(args["N"], args["M"], args["t"], args["T"], args["s"], args["port"])
    except Exception:
        pass