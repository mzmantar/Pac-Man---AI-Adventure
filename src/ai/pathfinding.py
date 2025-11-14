from __future__ import annotations

from heapq import heappop, heappush
from typing import Iterable, List, Set, Tuple

from pygame.math import Vector2

from .. import settings

GridPos = Tuple[int, int]


def heuristic(current: GridPos, goals: Set[GridPos]) -> float:
    if not goals:
        return 0.0
    cx, cy = current
    return min(abs(cx - gx) + abs(cy - gy) for gx, gy in goals)


def neighbours(position: GridPos, maze) -> Iterable[GridPos]:
    x, y = position
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nx = x + dx
        ny = y + dy
        if nx < 0:
            nx = settings.GRID_WIDTH - 1
        elif nx >= settings.GRID_WIDTH:
            nx = 0
        if ny < 0 or ny >= settings.GRID_HEIGHT:
            continue
        if maze.grid[ny][nx] != "X":
            yield nx, ny


def reconstruct_path(
    came_from: dict[GridPos, GridPos], current: GridPos
) -> List[GridPos]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def astar_path(
    maze,
    start: GridPos,
    goals: Set[GridPos],
) -> List[GridPos]:
    """Return a list of grid positions from start to nearest goal using A*."""
    if start in goals:
        return [start]

    open_heap: List[Tuple[float, float, GridPos]] = []
    heappush(open_heap, (heuristic(start, goals), 0.0, start))

    came_from: dict[GridPos, GridPos] = {}
    g_scores: dict[GridPos, float] = {start: 0.0}

    while open_heap:
        f_cost, g_cost, current = heappop(open_heap)
        if current in goals:
            return reconstruct_path(came_from, current)

        for neighbour in neighbours(current, maze):
            tentative_g = g_cost + 1
            if tentative_g < g_scores.get(neighbour, float("inf")):
                came_from[neighbour] = current
                g_scores[neighbour] = tentative_g
                f_score = tentative_g + heuristic(neighbour, goals)
                heappush(open_heap, (f_score, tentative_g, neighbour))

    return []

