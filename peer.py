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
    # stops server
    def stop_server(self):
        self.server.stop(10)

    def initialize(self):
        with grpc.insecure_channel(f"{self.host_ip}:{self.host_port}") as channel:
            stub = rpc.BootstrapStub(channel)
            self.N = stub.Initialize(BootstrapInit(ip=self.ip, port=self.port)).board_size  # important change
            self.pos = generate_random_pos(self.N)
            Console().clear()
            print("Soldier Initialized")

    """
    Creates new soldier with given speed, ipv4 address and port.
    Sets up commander arguments in case it will be switched later
    Initializes its identity with the server
    Runs the game loop
    """
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

        """
        Checks if soldier was hit and informs commander of same.
        If it is hit, it stops the gRPC server and quits.
        """
        def Status(self, request, context):
            reply = GameSoldierWasHit(was_hit=self.is_hit)
            if self.is_hit:
                self.outer_self.stop_server()
            return reply

        """
        Initiates transfer of control of program from Soldier to Commander
        Prepares arguments for Commander
        Stops gRPC server and Client instance.
        """
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
    """
    Initiates a new Commander instance from the Soldier's parameters upon transfer of control
    Continues game logic from same position in game loop as the previous commander.
    Informs user of game outcome.
    """
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

    """
    Initiates a new Commander instance.
    Optionally skips all initialization if commander is to be resumed instead.
    Waits for soldiers to connect and sends board size to them
    Begins game loop.
    Informs user of game outcome.
    """
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

    """
    Prints the current state of the game board including:
    - Soldier positions
    - Commander position
    - Missile position
    - Missile radius
    - Elapsed time and Total time
    - Number of remaining soldiers on the board
    """
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

    """
    Handles commander movement and transfer logic.
    If the commander is in the red zone, it moves to possible shelter locations in order, checking if the new position is free.
    If the commander determines it will be killed, it selects the next commander from the available soldiers and transfers to it.
    """
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

    """
    Checks status of a given soldier.
    If the soldier is hit, it is considered dead and is evicted from the list of available soldiers.
    """
    def status(self, soldier_id):
        with grpc.insecure_channel(f"{self.soldiers[soldier_id][0]}:{self.soldiers[soldier_id][1]}") as channel:
            stub = rpc.GameStub(channel)
            reply: GameSoldierWasHit = stub.Status(GameSoldierStatus())
            if reply.was_hit:
                _ = self.soldiers.pop(soldier_id)

    # Checks status of all available soldiers
    def status_all(self):
        keys = [i for i in self.soldiers.keys()]
        for soldier_id in keys:
            self.status(soldier_id)

    # Stops the server
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

# Initializes soldier or commander based on command line arguments
if "ip" in args:  # Soldier
    s = Soldier(args["s"], args["ip"], args["port"])
    if s.will_be_commander:  # create new Commander if Soldier is to be promoted
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
else:  # Commander
    try:
        Commander(args["N"], args["M"], args["t"], args["T"], args["s"], args["port"])
    except Exception:
        pass
