"""Environnement Gymnasium pour l'entraînement RL de Pac-Man."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
import pygame
from gymnasium import spaces
from pygame.math import Vector2

from ..entities import Ghost, GhostMode, Pacman
from ..maze import MAZE_BLUEPRINT, Maze
from .. import settings


class PacManEnv(gym.Env):
    """Environnement Gym pour entraîner des agents RL sur Pac-Man."""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(
        self,
        render_mode: Optional[str] = None,
        max_steps: int = 1000,
        control_pacman: bool = True,
    ):
        super().__init__()

        self.render_mode = render_mode
        self.max_steps = max_steps
        self.control_pacman = control_pacman

        # Espaces d'observation et d'action
        # État: positions (10 dims) + labyrinthe local (25) + modes (5)
        self.observation_space = spaces.Box(
            low=-1, high=100, shape=(40,), dtype=np.float32
        )

        # 4 directions possibles
        self.action_space = spaces.Discrete(4)

        # Pygame
        self.screen = None
        self.clock = None
        self._initialized = False

        # État du jeu
        self.maze: Optional[Maze] = None
        self.pacman: Optional[Pacman] = None
        self.ghosts: List[Ghost] = []
        self.score = 0
        self.steps = 0

    def _init_pygame(self):
        """Initialise pygame si nécessaire."""
        if not self._initialized:
            pygame.init()
            if self.render_mode == "human":
                self.screen = pygame.display.set_mode(
                    (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
                )
                pygame.display.set_caption("Pac-Man RL Training")
            elif self.render_mode == "rgb_array":
                self.screen = pygame.Surface(
                    (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
                )
            self.clock = pygame.time.Clock()
            self._initialized = True

    def reset(
        self, seed: Optional[int] = None, options: Optional[Dict] = None
    ) -> Tuple[np.ndarray, Dict]:
        """Réinitialise l'environnement."""
        super().reset(seed=seed)

        # Créer un nouveau labyrinthe
        self.maze = Maze.from_blueprint(MAZE_BLUEPRINT)

        # Créer Pac-Man
        self.pacman = Pacman(self.maze, start_pos=(13, 23))

        # Créer les fantômes
        self.ghosts = [
            Ghost(self.maze, "Blinky", (13, 11), settings.GHOST_RED, (25, 1)),
            Ghost(self.maze, "Inky", (11, 11), settings.GHOST_TEAL, (2, 1)),
            Ghost(self.maze, "Pinky", (15, 11), settings.GHOST_PINK, (1, 29)),
            Ghost(self.maze, "Clyde", (13, 16), settings.GHOST_ORANGE, (26, 29)),
        ]

        # Initialiser les directions
        self.ghosts[0].direction = Vector2(-1, 0)
        self.ghosts[1].direction = Vector2(1, 0)
        self.ghosts[2].direction = Vector2(-1, 0)
        self.ghosts[3].direction = Vector2(0, 1)

        self.score = 0
        self.steps = 0

        return self._get_observation(), {}

    def _get_observation(self) -> np.ndarray:
        """Construit l'observation de l'état actuel."""
        obs = []

        # Position de Pac-Man
        obs.extend([self.pacman.grid_pos.x, self.pacman.grid_pos.y])

        # Positions des fantômes (4 fantômes × 2 coords)
        for ghost in self.ghosts:
            obs.extend([ghost.grid_pos.x, ghost.grid_pos.y])

        # Labyrinthe local 5×5 autour de Pac-Man
        local_maze = self._get_local_maze(self.pacman.grid_pos)
        obs.extend(local_maze.flatten().tolist())

        # Modes des fantômes (one-hot pour chaque fantôme)
        for ghost in self.ghosts:
            obs.append(1.0 if ghost.mode == GhostMode.FRIGHTENED else 0.0)

        # Power mode actif
        power_mode = any(g.mode == GhostMode.FRIGHTENED for g in self.ghosts)
        obs.append(1.0 if power_mode else 0.0)

        return np.array(obs, dtype=np.float32)

    def _get_local_maze(self, pos: Vector2, radius: int = 2) -> np.ndarray:
        """Extrait une vue locale 5×5 du labyrinthe."""
        x, y = int(pos.x), int(pos.y)
        local = np.zeros((2 * radius + 1, 2 * radius + 1))

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = x + dx
                ny = y + dy

                if 0 <= nx < len(self.maze.grid[0]) and 0 <= ny < len(self.maze.grid):
                    cell = self.maze.grid[ny][nx]
                    # Encoder: 0=vide, 1=mur, 0.5=pellet, 0.7=power pellet
                    if cell == "X":
                        local[dy + radius, dx + radius] = 1.0
                    elif cell == ".":
                        local[dy + radius, dx + radius] = 0.5
                    elif cell == "o":
                        local[dy + radius, dx + radius] = 0.7

        return local

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Exécute une action dans l'environnement."""
        self.steps += 1

        # Convertir l'action en direction
        directions = [
            Vector2(-1, 0),  # Gauche
            Vector2(1, 0),  # Droite
            Vector2(0, -1),  # Haut
            Vector2(0, 1),  # Bas
        ]

        if self.control_pacman:
            # L'agent contrôle Pac-Man
            self.pacman.set_direction(directions[action])
        else:
            # L'agent contrôle un fantôme (pour l'exemple, le premier)
            self.ghosts[0].set_direction(directions[action])

        # Mettre à jour les entités
        dt = 1.0 / 60.0
        self.pacman.update(dt)

        for ghost in self.ghosts:
            ghost.update(dt, self.pacman.grid_pos, self.ghosts)

        # Vérifier les collisions et calculer la récompense
        reward = 0.0
        terminated = False
        truncated = False

        # Manger des pellets
        old_score = self.score
        tile = self.maze.consume_tile(
            int(self.pacman.grid_pos.x), int(self.pacman.grid_pos.y)
        )

        if tile == ".":
            self.score += 10
            reward += 10.0
        elif tile == "o":
            self.score += 50
            reward += 50.0
            # Activer le mode frightened
            for ghost in self.ghosts:
                if ghost.mode != GhostMode.EATEN:
                    ghost.mode = GhostMode.FRIGHTENED

        # Vérifier les collisions avec les fantômes
        for ghost in self.ghosts:
            if self.pacman.grid_pos == ghost.grid_pos:
                if ghost.mode == GhostMode.FRIGHTENED:
                    # Pac-Man mange le fantôme
                    ghost.mode = GhostMode.EATEN
                    self.score += 200
                    reward += 200.0
                elif ghost.mode != GhostMode.EATEN:
                    # Le fantôme mange Pac-Man
                    terminated = True
                    reward -= 500.0

        # Vérifier si tous les pellets sont mangés
        if not self.maze.remaining_pellets():
            terminated = True
            reward += 1000.0  # Bonus pour victoire

        # Vérifier le nombre maximum de steps
        if self.steps >= self.max_steps:
            truncated = True

        # Petite pénalité pour encourager l'efficacité
        reward -= 0.1

        observation = self._get_observation()
        info = {"score": self.score, "steps": self.steps}

        return observation, reward, terminated, truncated, info

    def render(self):
        """Affiche l'environnement."""
        if self.render_mode is None:
            return

        self._init_pygame()

        # Dessiner le fond
        self.screen.fill(settings.BACKGROUND_COLOUR)

        # Dessiner le labyrinthe
        self.maze.draw(self.screen)

        # Dessiner les entités
        self.pacman.draw(self.screen)
        for ghost in self.ghosts:
            ghost.draw(self.screen)

        # Afficher le score
        if hasattr(self, "_font") and self._font:
            score_text = self._font.render(
                f"Score: {self.score}", True, settings.WHITE
            )
            self.screen.blit(score_text, (10, 10))

        if self.render_mode == "human":
            pygame.display.flip()
            self.clock.tick(self.metadata["render_fps"])
        elif self.render_mode == "rgb_array":
            return pygame.surfarray.array3d(self.screen)

    def close(self):
        """Ferme l'environnement."""
        if self.screen is not None:
            pygame.quit()
            self._initialized = False


# Variantes de l'environnement
class PacManEnvGhostControl(PacManEnv):
    """Environnement où l'agent contrôle un fantôme."""

    def __init__(self, render_mode: Optional[str] = None, max_steps: int = 1000):
        super().__init__(
            render_mode=render_mode, max_steps=max_steps, control_pacman=False
        )
