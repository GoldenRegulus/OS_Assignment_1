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


class Soldier:
    def stop_server(self):
        self.server.stop(10)

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
