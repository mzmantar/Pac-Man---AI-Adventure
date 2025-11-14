from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Deque, Dict, Iterable, List, Tuple, TYPE_CHECKING

import pygame

from . import settings
from .ai.controller import compute_path as ai_compute_path
from .ai.controller import decide_mode as ai_decide_mode
from .ai.controller import observe_ghost_state

if TYPE_CHECKING:
    from .maze import Maze

Vector2 = pygame.math.Vector2

Direction = Vector2

DIRECTIONS: Dict[str, Direction] = {
    "left": Vector2(-1, 0),
    "right": Vector2(1, 0),
    "up": Vector2(0, -1),
    "down": Vector2(0, 1),
}


class GhostMode(Enum):
    SCATTER = auto()
    CHASE = auto()
    FRIGHTENED = auto()
    EATEN = auto()


def grid_to_pixel(grid_pos: Vector2) -> Vector2:
    return grid_pos * settings.TILE_SIZE + Vector2(settings.TILE_SIZE / 2)


def pixel_to_grid(pixel_pos: Vector2) -> Vector2:
    return Vector2(
        int(pixel_pos.x // settings.TILE_SIZE),
        int(pixel_pos.y // settings.TILE_SIZE),
    )


def valid_tile(maze, grid_pos: Vector2) -> bool:
    x, y = int(grid_pos.x), int(grid_pos.y)
    if x < 0 or y < 0 or y >= len(maze.grid) or x >= len(maze.grid[0]):
        return False
    return maze.grid[y][x] not in {"X"}


def portal_adjust(grid_pos: Vector2) -> Vector2:
    if grid_pos.x < 0:
        return Vector2(settings.GRID_WIDTH - 1, grid_pos.y)
    if grid_pos.x >= settings.GRID_WIDTH:
        return Vector2(0, grid_pos.y)
    return grid_pos


@dataclass
class Entity:
    maze: "Maze"
    grid_pos: Vector2
    speed: float
    direction: Direction = field(default_factory=lambda: Vector2(0, 0))
    pixel_pos: Vector2 = field(init=False)

    def __post_init__(self) -> None:
        self.pixel_pos = grid_to_pixel(self.grid_pos)

    def is_at_center(self) -> bool:
        center = grid_to_pixel(self.grid_pos)
        return (
            abs(self.pixel_pos.x - center.x) < 0.5
            and abs(self.pixel_pos.y - center.y) < 0.5
        )

    def update_position(self, dt: float) -> None:
        if not self.direction.length_squared():
            return

        previous_pixel = self.pixel_pos.copy()
        previous_grid = self.grid_pos.copy()
        self.pixel_pos += self.direction * self.speed * dt

        wrapped = False
        if self.pixel_pos.x < -settings.TILE_SIZE:
            self.pixel_pos.x = settings.SCREEN_WIDTH + settings.TILE_SIZE
            wrapped = True
        elif self.pixel_pos.x > settings.SCREEN_WIDTH + settings.TILE_SIZE:
            self.pixel_pos.x = -settings.TILE_SIZE
            wrapped = True

        new_grid = portal_adjust(pixel_to_grid(self.pixel_pos))

        if not wrapped and not valid_tile(self.maze, new_grid):
            self.pixel_pos = previous_pixel
            self.grid_pos = previous_grid
            self.direction = Vector2(0, 0)
            return

        self.grid_pos = new_grid
        if wrapped or new_grid != previous_grid:
            self.pixel_pos = grid_to_pixel(self.grid_pos)
        else:
            # lock to lane axis to reduce drift
            center = grid_to_pixel(self.grid_pos)
            if self.direction.x == 0:
                self.pixel_pos.x = center.x
            if self.direction.y == 0:
                self.pixel_pos.y = center.y

    def available_directions(self) -> List[Direction]:
        choices: List[Direction] = []
        for vector in DIRECTIONS.values():
            next_pos = portal_adjust(self.grid_pos + vector)
            if valid_tile(self.maze, next_pos):
                if self.direction.length_squared() and next_pos == portal_adjust(
                    self.grid_pos - self.direction
                ):
                    continue
                choices.append(vector)
        return choices


class Pacman(Entity):
    colour_cycle = [
        settings.AMBER,
        (255, 210, 80),
        (255, 226, 130),
        (255, 200, 70),
    ]

    def __init__(self, maze: "Maze", start_pos: Tuple[int, int]) -> None:
        super().__init__(maze=maze, grid_pos=Vector2(start_pos), speed=settings.PACMAN_SPEED)
        self.desired_direction: Direction = Vector2(0, 0)
        self.mouth_angle = 0
        self.animation_time = 0.0
        self.colour_index = 0
        self.autopilot_enabled = False
        self.auto_queue: Deque[Direction] = deque()

    def handle_input(self, keys: Iterable[bool]) -> None:
        if self.autopilot_enabled:
            return
        mapping = [
            (pygame.K_LEFT, DIRECTIONS["left"]),
            (pygame.K_RIGHT, DIRECTIONS["right"]),
            (pygame.K_UP, DIRECTIONS["up"]),
            (pygame.K_DOWN, DIRECTIONS["down"]),
        ]
        for key, vector in mapping:
            if keys[key]:
                self.desired_direction = vector

    def enable_autopilot(self, enabled: bool) -> None:
        self.autopilot_enabled = enabled
        if not enabled:
            self.auto_queue.clear()

    def set_autopilot_path(self, directions: Iterable[Direction]) -> None:
        self.auto_queue = deque(directions)

    def update_autopilot(self) -> None:
        if not self.autopilot_enabled:
            return
        if not self.auto_queue:
            self.desired_direction = Vector2(0, 0)
            return
        if self.is_at_center():
            next_direction = self.auto_queue[0]
            next_pos = portal_adjust(self.grid_pos + next_direction)
            if valid_tile(self.maze, next_pos):
                self.desired_direction = self.auto_queue.popleft()
            else:
                # path invalidated
                self.auto_queue.clear()

    def update(self, dt: float) -> None:
        self.update_autopilot()
        if self.desired_direction.length_squared() and self.is_at_center():
            next_pos = portal_adjust(self.grid_pos + self.desired_direction)
            if valid_tile(self.maze, next_pos):
                self.direction = self.desired_direction

        if not self.direction.length_squared():
            return

        if self.is_at_center():
            next_pos = portal_adjust(self.grid_pos + self.direction)
            if not valid_tile(self.maze, next_pos):
                self.direction = Vector2(0, 0)
                return

        self.update_position(dt)

        self.animation_time += dt
        if self.animation_time > 0.12:
            self.animation_time = 0.0
            self.colour_index = (self.colour_index + 1) % len(self.colour_cycle)

    def draw(self, surface: pygame.Surface) -> None:
        radius = settings.TILE_SIZE // 2 - 2
        mouth_open = abs(pygame.time.get_ticks() // 60 % 20 - 10) / 10
        start_angle = 0.2 * mouth_open
        end_angle = 2 * 3.14159 - start_angle

        if self.direction == DIRECTIONS["left"]:
            rotation = 180
        elif self.direction == DIRECTIONS["up"]:
            rotation = 90
        elif self.direction == DIRECTIONS["down"]:
            rotation = 270
        else:
            rotation = 0

        colour = self.colour_cycle[self.colour_index]

        image = pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(image, colour, (settings.TILE_SIZE // 2, settings.TILE_SIZE // 2), radius)
        pygame.draw.polygon(
            image,
            (0, 0, 0, 0),
            [
                (settings.TILE_SIZE // 2, settings.TILE_SIZE // 2),
                (
                    settings.TILE_SIZE // 2 + radius,
                    settings.TILE_SIZE // 2 - radius * mouth_open,
                ),
                (
                    settings.TILE_SIZE // 2 + radius,
                    settings.TILE_SIZE // 2 + radius * mouth_open,
                ),
            ],
        )
        rotated = pygame.transform.rotate(image, rotation)
        rect = rotated.get_rect(center=self.pixel_pos)
        surface.blit(rotated, rect)


class Ghost(Entity):
    def __init__(
        self,
        maze: "maze.Maze",
        name: str,
        start_pos: Tuple[int, int],
        colour: Tuple[int, int, int],
        home_corner: Tuple[int, int],
    ) -> None:
        super().__init__(maze=maze, grid_pos=Vector2(start_pos), speed=settings.GHOST_SPEED)
        self.name = name
        self.colour = colour
        self.home_corner = Vector2(home_corner)
        self.mode: GhostMode = GhostMode.SCATTER
        self.frightened_timer = 0.0
        self.eye_colour = settings.WHITE
        self.direction = DIRECTIONS["left"]
        self.behaviour = "patrouille"

    def set_mode(self, mode: GhostMode) -> None:
        if mode == GhostMode.FRIGHTENED:
            self.frightened_timer = settings.POWER_MODE_DURATION
        self.mode = mode

    def update(
        self,
        dt: float,
        pacman: Pacman,
        scatter_timer: float,
        ghosts: List["Ghost"],
    ) -> None:
        if self.mode == GhostMode.FRIGHTENED:
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                self.mode = GhostMode.CHASE

        if self.mode == GhostMode.EATEN:
            target_tile = Vector2(13, 11)
            context = observe_ghost_state(
                self.maze,
                pacman.grid_pos,
                self.grid_pos,
                self.home_corner,
                ghosts,
            )
            path = ai_compute_path(context, target_tile)
        else:
            context = observe_ghost_state(
                self.maze,
                pacman.grid_pos,
                self.grid_pos,
                self.home_corner,
                ghosts,
            )
            behaviour, target_tile = ai_decide_mode(context)
            self.behaviour = behaviour
            path = ai_compute_path(context, target_tile)

        if path and len(path) >= 2:
            next_step = Vector2(path[1])
            direction = Vector2(
                next_step.x - self.grid_pos.x, next_step.y - self.grid_pos.y
            )
            if direction.length_squared():
                self.direction = direction.normalize()
        else:
            # fall back to deterministic choice if path is unavailable
            target = self.choose_target(pacman, scatter_timer)
            self.move_towards(target, dt)
            return

        speed = (
            settings.FRIGHTENED_SPEED
            if self.mode == GhostMode.FRIGHTENED
            else settings.GHOST_SPEED
        )
        self.speed = speed
        self.update_position(dt)

    def move_towards(self, target: Vector2, dt: float) -> None:
        if self.mode == GhostMode.EATEN and self.is_at_center() and self.grid_pos == Vector2(
            13, 11
        ):
            self.mode = GhostMode.CHASE
            self.direction = DIRECTIONS["left"]
            return

        possible = self.available_directions()
        if not possible:
            self.direction *= -1
        else:
            best_dir = possible[0]
            best_distance = float("inf")
            for direction in possible:
                next_pos = portal_adjust(self.grid_pos + direction)
                distance = (next_pos - target).length_squared()
                if distance < best_distance:
                    best_distance = distance
                    best_dir = direction
            self.direction = best_dir
        speed = (
            settings.FRIGHTENED_SPEED
            if self.mode == GhostMode.FRIGHTENED
            else settings.GHOST_SPEED
        )
        self.speed = speed
        self.update_position(dt)

    def choose_target(self, pacman: Pacman, scatter_timer: float) -> Vector2:
        if self.mode == GhostMode.EATEN:
            return Vector2(13, 11)
        if self.mode == GhostMode.FRIGHTENED:
            return Vector2(
                settings.GRID_WIDTH - pacman.grid_pos.x,
                settings.GRID_HEIGHT - pacman.grid_pos.y,
            )
        # alternate between scatter and chase every few seconds
        cycle = int(scatter_timer) % 12
        if cycle < 4:
            return self.home_corner
        if self.mode == GhostMode.SCATTER:
            return self.home_corner
        return pacman.grid_pos

    def draw(self, surface: pygame.Surface) -> None:
        body = pygame.Surface((settings.TILE_SIZE, settings.TILE_SIZE), pygame.SRCALPHA)
        radius = settings.TILE_SIZE // 2 - 2
        rect = body.get_rect()
        if self.mode == GhostMode.FRIGHTENED:
            colour = settings.GHOST_TEAL
        elif self.mode == GhostMode.EATEN:
            colour = settings.WHITE
        else:
            colour = self.colour

        pygame.draw.circle(body, colour, (rect.width // 2, rect.height // 2), radius)
        pygame.draw.rect(
            body,
            colour,
            pygame.Rect(4, rect.height // 2, rect.width - 8, rect.height // 2),
        )
        wave_height = rect.height // 6
        for i in range(4):
            pygame.draw.circle(
                body,
                colour,
                (4 + i * (rect.width - 8) // 3, rect.height - wave_height),
                wave_height,
            )

        eye_offset = (self.direction * 4) if self.direction.length_squared() else Vector2(0, 0)
        for offset in (-6, 6):
            eye_center = Vector2(rect.width // 2 + offset, rect.height // 3)
            pygame.draw.circle(body, settings.WHITE, eye_center, 4)
            pygame.draw.circle(
                body,
                settings.NIGHT_BLUE,
                eye_center + eye_offset,
                2,
            )

        surface.blit(body, body.get_rect(center=self.pixel_pos))

