from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple
from typing import Optional

import pygame

from . import settings
from .audio import ensure_audio_manager, AudioManager
from .levels import get_level
from .entities import Ghost, GhostMode, Pacman, valid_tile
from .maze import MAZE_BLUEPRINT, Maze
from .ai.pathfinding import astar_path

from pygame.math import Vector2


@dataclass
class Game:
    screen: pygame.Surface
    clock: pygame.time.Clock
    maze: Maze
    pacman: Pacman
    ghosts: List[Ghost]
    score: int = 0
    lives: int = settings.PACMAN_LIVES
    scatter_timer: float = 0.0
    running: bool = True
    font: pygame.font.Font | None = None
    auto_replan: bool = False
    score_multiplier: float = 1.0
    level_name: str = ""
    level_index: int = 0
    audio: Optional[AudioManager] = None

    @classmethod
    def create(cls, level_index: int = 0) -> "Game":
        pygame.init()
        pygame.font.init()
        screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        pygame.display.set_caption(settings.WINDOW_TITLE)
        clock = pygame.time.Clock()

        # Appliquer les paramètres de niveau
        level = get_level(level_index)
        level.apply()

        # Audio
        audio = ensure_audio_manager()

        maze = Maze.from_blueprint(MAZE_BLUEPRINT)
        pacman = Pacman(maze, start_pos=(13, 23))
        ghosts = [
            Ghost(maze, "Blinky", (13, 11), settings.GHOST_RED, (25, 1)),
            Ghost(maze, "Inky", (11, 11), settings.GHOST_TEAL, (2, 1)),
            Ghost(maze, "Pinky", (15, 11), settings.GHOST_PINK, (1, 29)),
            Ghost(maze, "Clyde", (13, 16), settings.GHOST_ORANGE, (26, 29)),
        ]
        
        # Initialize ghost directions
        ghosts[0].direction = pygame.math.Vector2(-1, 0)  # Blinky left
        ghosts[1].direction = pygame.math.Vector2(1, 0)   # Inky right
        ghosts[2].direction = pygame.math.Vector2(-1, 0)  # Pinky left
        ghosts[3].direction = pygame.math.Vector2(0, 1)   # Clyde down

        font = pygame.font.SysFont("arialroundedmtbold", 26)
        game = cls(screen, clock, maze, pacman, ghosts, font=font)
        game.score_multiplier = level.score_multiplier
        game.level_name = level.name
        game.level_index = level_index
        game.auto_replan = level.auto_replan
        game.audio = audio
        game.pacman.enable_autopilot(False)
        if game.audio:
            game.audio.play_music(loop=True)
        return game

    def reset_positions(self, lost_life: bool = False) -> None:
        if lost_life:
            self.lives -= 1
            if self.lives <= 0:
                self.running = False
                return
        self.pacman.grid_pos = pygame.math.Vector2(13, 23)
        self.pacman.pixel_pos = pygame.math.Vector2(
            self.pacman.grid_pos.x * settings.TILE_SIZE + settings.TILE_SIZE / 2,
            self.pacman.grid_pos.y * settings.TILE_SIZE + settings.TILE_SIZE / 2,
        )
        self.pacman.direction = pygame.math.Vector2(0, 0)

        ghost_positions = [(13, 11), (11, 11), (15, 11), (13, 16)]
        ghost_directions = [
            pygame.math.Vector2(-1, 0),  # Blinky left
            pygame.math.Vector2(1, 0),   # Inky right
            pygame.math.Vector2(-1, 0),  # Pinky left
            pygame.math.Vector2(0, 1)    # Clyde down
        ]
        for ghost, pos, direction in zip(self.ghosts, ghost_positions, ghost_directions):
            ghost.grid_pos = pygame.math.Vector2(pos)
            ghost.pixel_pos = pygame.math.Vector2(
                ghost.grid_pos.x * settings.TILE_SIZE + settings.TILE_SIZE / 2,
                ghost.grid_pos.y * settings.TILE_SIZE + settings.TILE_SIZE / 2,
            )
            ghost.direction = direction
            ghost.set_mode(GhostMode.SCATTER)
            # Reset escape mode counters
            ghost.stuck_counter = 0
            ghost.escape_mode = False
        self.pacman.enable_autopilot(False)
        if self.auto_replan:
            self.compute_autopilot_path()

    def run(self) -> None:
        self.reset_positions()
        while self.running:
            dt = self.clock.tick(settings.FRAMES_PER_SECOND) / 1000.0
            self.scatter_timer += dt

            self.handle_events()
            self.update(dt)
            self.draw()

        self.show_game_over()
        if self.audio:
            self.audio.stop_music()

    def handle_events(self) -> None:
        manual_override = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_c:
                self.toggle_auto_replan()
            elif event.type == pygame.KEYDOWN and event.key in (
                pygame.K_LEFT,
                pygame.K_RIGHT,
                pygame.K_UP,
                pygame.K_DOWN,
            ):
                manual_override = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_mouse_click(event.pos)

        keys = pygame.key.get_pressed()
        if manual_override or any(
            keys[key]
            for key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)
        ):
            if self.pacman.autopilot_enabled or self.auto_replan:
                self.pacman.enable_autopilot(False)
                self.auto_replan = False
        self.pacman.handle_input(keys)

    def update(self, dt: float) -> None:
        if not self.running:
            return
        if self.pacman.autopilot_enabled and not self.pacman.auto_queue:
            self.pacman.enable_autopilot(False)
            if self.auto_replan:
                self.compute_autopilot_path()
        if self.auto_replan and not self.pacman.autopilot_enabled:
            self.compute_autopilot_path()
        self.pacman.update(dt)
        for ghost in self.ghosts:
            # Skip updating permanently eaten ghosts
            if not ghost.permanently_eaten:
                ghost.update(dt, self.pacman, self.scatter_timer, self.ghosts)

        if self.pacman.is_at_center():
            tile_value = self.maze.consume_tile(
                int(self.pacman.grid_pos.x), int(self.pacman.grid_pos.y)
            )
            if tile_value == ".":
                self.score += int(10 * getattr(self, "score_multiplier", 1.0))
                if self.audio:
                    self.audio.play("pellet")
            elif tile_value == "o":
                self.score += int(50 * getattr(self, "score_multiplier", 1.0))
                if self.audio:
                    self.audio.play("power")
                for ghost in self.ghosts:
                    ghost.set_mode(GhostMode.FRIGHTENED)
            if tile_value in {".", "o"} and self.auto_replan:
                self.compute_autopilot_path()

            # Tous les pellets mangés -> niveau suivant
            if not self.maze.remaining_pellets():
                self.next_level()

        self.handle_collisions()

    def handle_collisions(self) -> None:
        pac_rect = pygame.Rect(
            self.pacman.pixel_pos.x - settings.TILE_SIZE / 2,
            self.pacman.pixel_pos.y - settings.TILE_SIZE / 2,
            settings.TILE_SIZE,
            settings.TILE_SIZE,
        )
        for ghost in self.ghosts:
            # Skip permanently eaten ghosts
            if ghost.permanently_eaten:
                continue
                
            ghost_rect = pygame.Rect(
                ghost.pixel_pos.x - settings.TILE_SIZE / 2,
                ghost.pixel_pos.y - settings.TILE_SIZE / 2,
                settings.TILE_SIZE,
                settings.TILE_SIZE,
            )
            if pac_rect.colliderect(ghost_rect):
                if ghost.mode == GhostMode.FRIGHTENED:
                    ghost.permanently_eaten = True  # Marquer comme définitivement mangé
                    self.score += 200
                    if self.audio:
                        self.audio.play("eat_ghost")
                    # Vérifier si tous les fantômes sont mangés
                    if all(g.permanently_eaten for g in self.ghosts):
                        if self.audio:
                            self.audio.play("win")
                        self.show_winner()
                        self.running = False
                elif ghost.mode != GhostMode.EATEN:
                    if self.audio:
                        self.audio.play("death")
                    self.reset_positions(lost_life=True)
        
        # Régénérer les points si tous mangés mais des fantômes restent
        if not self.maze.remaining_pellets() and any(not g.permanently_eaten for g in self.ghosts):
            self.regenerate_pellets()

    def draw(self) -> None:
        self.draw_background()
        self.maze.draw(self.screen)
        self.pacman.draw(self.screen)
        for ghost in self.ghosts:
            ghost.draw(self.screen)
        self.draw_ui()
        pygame.display.flip()

    def draw_background(self) -> None:
        self.screen.fill(settings.BACKGROUND_COLOUR)
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(120):
            size = 18 + (i % 5) * 6
            alpha = 20 + (i * 3) % 80
            colour = (*settings.SKY_BLUE, alpha)
            pygame.draw.circle(
                overlay,
                colour,
                (
                    (i * 47) % settings.SCREEN_WIDTH,
                    (i * 91 + pygame.time.get_ticks() // 15) % settings.SCREEN_HEIGHT,
                ),
                size,
                1,
            )
        self.screen.blit(overlay, (0, 0))

    def draw_ui(self) -> None:
        if not self.font:
            return
        score_text = self.font.render(f"Score: {self.score}", True, settings.WHITE)
        lives_text = self.font.render(f"Vies: {self.lives}", True, settings.AMBER)
        level_text = None
        if hasattr(self, "level_name"):
            level_text = self.font.render(self.level_name, True, settings.SKY_BLUE)
        self.screen.blit(score_text, (16, 8))
        self.screen.blit(lives_text, (settings.SCREEN_WIDTH - lives_text.get_width() - 16, 8))
        if level_text:
            self.screen.blit(level_text, (settings.SCREEN_WIDTH // 2 - level_text.get_width() // 2, 8))

        indicator = None
        if self.auto_replan:
            indicator = "Mode IA (A*)"
        elif self.pacman.autopilot_enabled and self.pacman.auto_queue:
            indicator = "Trajet ciblé"
        if indicator:
            badge = self.font.render(indicator, True, settings.FUCHSIA)
            self.screen.blit(
                badge, (settings.SCREEN_WIDTH // 2 - badge.get_width() // 2, 8)
            )

        for i in range(self.lives):
            x = 20 + i * (settings.TILE_SIZE + 6)
            y = settings.SCREEN_HEIGHT - settings.TILE_SIZE
            pygame.draw.circle(
                self.screen, settings.AMBER, (x, y), settings.TILE_SIZE // 2 - 3
            )

    def regenerate_pellets(self) -> None:
        """Regenerate all pellets when all are eaten but ghosts remain."""
        for y, row in enumerate(self.maze.grid):
            for x, value in enumerate(row):
                if value == " ":
                    self.maze.grid[y][x] = "."

    def next_level(self) -> None:
        """Passer au niveau suivant en réappliquant les paramètres."""
        # Incrémenter un attribut de niveau si présent
        current_level = getattr(self, "level_index", 0)
        next_level = current_level + 1
        self.level_index = next_level

        # Appliquer la nouvelle config
        level = get_level(next_level)
        level.apply()
        self.score_multiplier = level.score_multiplier
        self.level_name = level.name
        self.auto_replan = level.auto_replan

        # Réinitialiser le plateau
        self.maze = Maze.from_blueprint(MAZE_BLUEPRINT)
        self.reset_positions(lost_life=False)
        self.scatter_timer = 0.0

        # Réinitialiser les fantômes avec la nouvelle maze
        ghost_starts = [
            (13, 11),
            (11, 11),
            (15, 11),
            (13, 16),
        ]
        corners = [(25, 1), (2, 1), (1, 29), (26, 29)]
        colours = [
            settings.GHOST_RED,
            settings.GHOST_TEAL,
            settings.GHOST_PINK,
            settings.GHOST_ORANGE,
        ]

        self.ghosts = [
            Ghost(self.maze, name, pos, col, corner)
            for (pos, col, corner, name) in zip(
                ghost_starts,
                colours,
                corners,
                ["Blinky", "Inky", "Pinky", "Clyde"],
            )
        ]

        # Directions initiales
        initial_dirs = [
            pygame.math.Vector2(-1, 0),
            pygame.math.Vector2(1, 0),
            pygame.math.Vector2(-1, 0),
            pygame.math.Vector2(0, 1),
        ]
        for ghost, d in zip(self.ghosts, initial_dirs):
            ghost.direction = d

        # Remettre Pac-Man sur la nouvelle maze
        self.pacman.maze = self.maze
        self.pacman.grid_pos = pygame.math.Vector2(13, 23)
        self.pacman.pixel_pos = pygame.math.Vector2(
            self.pacman.grid_pos.x * settings.TILE_SIZE + settings.TILE_SIZE / 2,
            self.pacman.grid_pos.y * settings.TILE_SIZE + settings.TILE_SIZE / 2,
        )
        self.pacman.direction = pygame.math.Vector2(0, 0)
        self.pacman.enable_autopilot(False)

        if self.audio:
            self.audio.play_music(loop=True)

        # Informer sur le niveau
        print(f"➡️ Passage à {self.level_name}")
    
    def show_winner(self) -> None:
        """Display winner screen when all ghosts are eaten."""
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(settings.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        if self.font:
            # Winner title
            title_font = pygame.font.SysFont("arialroundedmtbold", 72)
            title = title_font.render("WINNER!", True, settings.AMBER)
            title_rect = title.get_rect(center=(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2 - 60))
            self.screen.blit(title, title_rect)
            
            # Score
            score_text = self.font.render(f"Score Final: {self.score}", True, settings.WHITE)
            score_rect = score_text.get_rect(center=(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2 + 20))
            self.screen.blit(score_text, score_rect)
            
            # Instructions
            instruction = self.font.render("Appuyez sur Echap pour quitter", True, settings.SKY_BLUE)
            instruction_rect = instruction.get_rect(center=(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2 + 80))
            self.screen.blit(instruction, instruction_rect)
        
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    return
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    waiting = False

    def show_game_over(self) -> None:
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        overlay.set_alpha(160)
        overlay.fill(settings.BLACK)
        self.screen.blit(overlay, (0, 0))
        if self.font:
            text = self.font.render("Game Over - Appuyez sur Echap", True, settings.WHITE)
            rect = text.get_rect(center=(settings.SCREEN_WIDTH / 2, settings.SCREEN_HEIGHT / 2))
            self.screen.blit(text, rect)
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    return
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    waiting = False

    def handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        tile_size = settings.TILE_SIZE
        grid_x = pos[0] // tile_size
        grid_y = pos[1] // tile_size
        if not (0 <= grid_x < settings.GRID_WIDTH and 0 <= grid_y < settings.GRID_HEIGHT):
            return
        target = Vector2(grid_x, grid_y)
        if not valid_tile(self.maze, target):
            return
        self.auto_replan = False
        self.compute_autopilot_path({(grid_x, grid_y)})

    def toggle_auto_replan(self) -> None:
        self.auto_replan = not self.auto_replan
        if self.auto_replan:
            self.compute_autopilot_path()
        else:
            self.pacman.enable_autopilot(False)

    def compute_autopilot_path(
        self, targets: Iterable[Tuple[int, int]] | None = None
    ) -> None:
        if targets is None:
            targets_set: Set[Tuple[int, int]] = set(self.maze.remaining_pellets())
        else:
            targets_set = set(targets)
        start = (int(self.pacman.grid_pos.x), int(self.pacman.grid_pos.y))
        if not targets_set:
            self.pacman.enable_autopilot(False)
            return
        path = astar_path(self.maze, start, targets_set)
        if len(path) < 2:
            self.pacman.enable_autopilot(False)
            return
        directions: List[Vector2] = []
        for current, nxt in zip(path, path[1:]):
            dx = nxt[0] - current[0]
            dy = nxt[1] - current[1]
            if dx > 1:
                dx = -1
            elif dx < -1:
                dx = 1
            if dy > 1:
                dy = -1
            elif dy < -1:
                dy = 1
            directions.append(Vector2(dx, dy))
        self.pacman.enable_autopilot(True)
        self.pacman.set_autopilot_path(directions)

