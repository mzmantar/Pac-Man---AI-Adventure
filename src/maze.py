from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import pygame

from . import settings

MazeGrid = List[List[str]]


MAZE_BLUEPRINT = [
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "X............XX............X",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "XoXXXX.XXXXX.XX.XXXXX.XXXXoX",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "X..........................X",
    "X.XXXX.XX.XXXXXXXX.XX.XXXX.X",
    "X.XXXX.XX.XXXXXXXX.XX.XXXX.X",
    "X......XX....XX....XX......X",
    "XXXXXX.XXXXX XX XXXXX.XXXXXX",
    "     X.XXXXX XX XXXXX.X     ",
    "     X.XX          XX.X     ",
    "     X.XX XXX  XXX XX.X     ",
    "XXXXXX.XX XGGGGGGX XX.XXXXXX",
    "      .   XGGGGGGX   .      ",
    "XXXXXX.XX XXXXXXXX XX.XXXXXX",
    "     X.XX          XX.X     ",
    "     X.XX XXXXXXXX XX.X     ",
    "XXXXXX.XX XXXXXXXX XX.XXXXXX",
    "X............XX............X",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "X.XXXX.XXXXX.XX.XXXXX.XXXX.X",
    "Xo..XX.......  .......XX..oX",
    "XXX.XX.XX.XX    XX.XX.XX.XXX",
    "XXX.XX.XX.XXXXXXXX.XX.XX.XXX",
    "X......XX....XX....XX......X",
    "X.XXXXXXXXXX.XX.XXXXXXXXXX.X",
    "X.XXXXXXXXXX.XX.XXXXXXXXXX.X",
    "X..........................X",
    "XXXXXXXXXXXXXXXXXXXXXXXXXXXX",
]


@dataclass
class Maze:
    grid: MazeGrid

    @classmethod
    def from_blueprint(cls, blueprint: Iterable[str]) -> "Maze":
        grid = [list(row.replace("G", " ")) for row in blueprint]
        return cls(grid=grid)

    def pellets(self) -> Iterable[Tuple[int, int]]:
        for y, row in enumerate(self.grid):
            for x, value in enumerate(row):
                if value in {".", "o"}:
                    yield x, y

    def walls(self) -> Iterable[Tuple[int, int]]:
        for y, row in enumerate(self.grid):
            for x, value in enumerate(row):
                if value == "X":
                    yield x, y

    def reset_pellet(self, x: int, y: int) -> None:
        if self.grid[y][x] == " ":
            self.grid[y][x] = "."

    def consume_tile(self, x: int, y: int) -> str:
        value = self.grid[y][x]
        if value in {".", "o"}:
            self.grid[y][x] = " "
        return value

    def remaining_pellets(self) -> Tuple[Tuple[int, int], ...]:
        return tuple(self.pellets())

    def draw(self, surface: pygame.Surface) -> None:
        tile = settings.TILE_SIZE
        for y, row in enumerate(self.grid):
            for x, value in enumerate(row):
                rect = pygame.Rect(x * tile, y * tile, tile, tile)
                if value == "X":
                    pygame.draw.rect(surface, settings.MAZE_WALL_COLOUR, rect)
                    pygame.draw.rect(surface, settings.MAZE_BORDER_COLOUR, rect, 2)
                elif value == ".":
                    pygame.draw.circle(
                        surface,
                        settings.PELLET_COLOUR,
                        rect.center,
                        tile // 10,
                    )
                elif value == "o":
                    pygame.draw.circle(
                        surface,
                        settings.POWER_PELLET_COLOUR,
                        rect.center,
                        tile // 4,
                    )

