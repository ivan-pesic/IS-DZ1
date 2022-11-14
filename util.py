import ctypes
import time
from threading import Timer, Thread
import math

def find_next_coin_dfs(visit, paths):
        min_path = math.inf
        next_coin = None
        for i in range(len(paths)):
            if paths[i] != 0 and not visit[i] and paths[i] < min_path:
                min_path = paths[i]
                next_coin = i

        return next_coin


def find_min(S1, S2, graph):
    min_path = math.inf
    u = v = -1
    for i in S1:
        for j in S2:
            if graph[i][j] < min_path:
                u = i
                v = j
                min_path = graph[i][j]

    return u, v


def calculate_heuristic(node, rest, graph):
    U = set()
    U.add(node)
    heuristic = 0
    V = set([x for x in range(len(graph))]) - rest
    while(U != V):
        u, v = find_min(U, V - U, graph)
        U.add(v)
        heuristic += graph[u][v]

    return heuristic


class PartialPath:
    def __init__(self, path, cost):
        self.path = path
        self.cost = cost

    def __lt__(self, other):
        if self.cost < other.cost:
            return True
        elif self.cost > other.cost:
            return False
        else:
            if len(self.path) > len(other.path):
                return True
            elif len(self.path) < len(other.path):
                return False
            else:
                if len(self.path) != 0 and len(other.path) != 0:
                    for i in range(len(self.path)):
                        if self.path[i] > other.path[i]:
                            return False
                    return True
                else:
                    return False


class PartialPathAStar:
    def __init__(self, path, cost, heuristic):
        self.path = path
        self.cost = cost
        self.heuristic = heuristic

    def __lt__(self, other):
        if self.cost < other.cost:
            return True
        elif self.cost > other.cost:
            return False
        else:
            if len(self.path) > len(other.path):
                return True
            elif len(self.path) < len(other.path):
                return False
            else:
                if len(self.path) != 0 and len(other.path) != 0:
                    for i in range(len(self.path)):
                        if self.path[i] > other.path[i]:
                            return False
                    return True
                else:
                    return False


class Timeout(Exception):
    pass


def send_thread_exception(*args):
    for t_id in args:
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(t_id), ctypes.py_object(Timeout))
        if not res:
            print(f'ERR: Thread {t_id} not found')
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(t_id, 0)
            print(f'ERR: Failed to send exception to thread {t_id}')


class TimedFunction(Thread):
    def __init__(self, parent_id, queue, max_time_sec, method, *args):
        super().__init__()
        self.parent_id = parent_id
        self.queue = queue
        self.max_time_sec = max_time_sec
        self.method = method
        self.args = args

    def get_id(self):
        return self.ident

    def run(self) -> None:
        timer = Timer(interval=self.max_time_sec,
                      function=send_thread_exception, args=[self.ident, self.parent_id])
        timer.start()
        try:
            start_time = time.time()
            result = self.method(*self.args)
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.queue.put((result, elapsed_time), block=False)
        except (Timeout, Exception):
            pass
        finally:
            timer.cancel()
