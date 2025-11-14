from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple, TYPE_CHECKING

from pygame.math import Vector2

from ..maze import Maze
from .pathfinding import astar_path

if TYPE_CHECKING:
    from ..entities import GhostMode

GridPos = Tuple[int, int]


@dataclass(frozen=True)
class GhostContext:
    """Minimal snapshot of the world for a given ghost."""

    pacman_pos: Vector2
    ghost_pos: Vector2
    scatter_corner: Vector2
    maze: Maze
    power_mode_active: bool
    distance_threshold: int = 6


def observe_ghost_state(
    maze: Maze,
    pacman_pos: Vector2,
    ghost_pos: Vector2,
    scatter_corner: Vector2,
    ghosts: Sequence["GhostLike"],
) -> GhostContext:
    """Create a `GhostContext` reflecting the current board for a ghost."""

    from ..entities import GhostMode  # Local import to avoid circular dependency

    power_mode = any(
        getattr(ghost, "mode", GhostMode.CHASE) == GhostMode.FRIGHTENED for ghost in ghosts
    )
    return GhostContext(
        pacman_pos=pacman_pos,
        ghost_pos=ghost_pos,
        scatter_corner=scatter_corner,
        maze=maze,
        power_mode_active=power_mode,
    )


def manhattan(a: Vector2, b: Vector2) -> int:
    return int(abs(a.x - b.x) + abs(a.y - b.y))


def decide_mode(context: GhostContext) -> Tuple[str, Vector2]:
    """Return behaviour mode label and desired target tile."""

    distance = manhattan(context.ghost_pos, context.pacman_pos)

    if context.power_mode_active:
        return "fuite", context.scatter_corner

    if distance <= context.distance_threshold:
        return "attaque", context.pacman_pos

    return "patrouille", context.scatter_corner


def compute_path(
    context: GhostContext,
    target: Vector2,
) -> List[GridPos]:
    goals = {(int(target.x), int(target.y))}
    start = (int(context.ghost_pos.x), int(context.ghost_pos.y))
    return astar_path(context.maze, start, goals)


# Protocol-like helper to avoid circular typing imports.
class GhostLike:
    mode: GhostMode


