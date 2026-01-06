"""Labyrinthe dynamique avec murs qui bougent."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Set, Tuple

import numpy as np
import pygame

from .. import settings
from ..maze import Maze, MazeGrid


@dataclass
class MovingWall:
    """Représente un mur qui peut bouger."""

    x: int
    y: int
    target_x: int
    target_y: int
    speed: float = 0.1
    progress: float = 0.0
    
    def update(self, dt: float) -> bool:
        """
        Met à jour la position du mur.
        
        Returns:
            True si le mur a atteint sa destination
        """
        self.progress += self.speed * dt
        if self.progress >= 1.0:
            self.x = self.target_x
            self.y = self.target_y
            self.progress = 0.0
            return True
        return False
    
    def get_current_pos(self) -> Tuple[float, float]:
        """Retourne la position interpolée actuelle."""
        current_x = self.x + (self.target_x - self.x) * self.progress
        current_y = self.y + (self.target_y - self.y) * self.progress
        return current_x, current_y


@dataclass
class WallPattern:
    """Motif de mouvement pour les murs."""

    name: str
    walls: List[Tuple[int, int]]  # Positions des murs
    sequence: List[Tuple[int, int]]  # Séquence de déplacements
    duration: float = 5.0  # Durée d'un cycle en secondes


class DynamicMaze(Maze):
    """Labyrinthe avec murs qui bougent."""

    def __init__(self, grid: MazeGrid):
        super().__init__(grid)
        
        self.moving_walls: List[MovingWall] = []
        self.wall_timer: float = 0.0
        self.pattern_index: int = 0
        self.current_pattern: WallPattern | None = None
        
        # Zones sûres où les murs ne bougent jamais
        self.safe_zones: Set[Tuple[int, int]] = self._define_safe_zones()
        
        # Murs mobiles potentiels
        self.movable_walls: List[Tuple[int, int]] = self._find_movable_walls()
    
    def _define_safe_zones(self) -> Set[Tuple[int, int]]:
        """Définit les zones où les murs ne peuvent pas bouger."""
        safe = set()
        
        # Bordures du labyrinthe
        for x in range(len(self.grid[0])):
            safe.add((x, 0))
            safe.add((x, len(self.grid) - 1))
        
        for y in range(len(self.grid)):
            safe.add((0, y))
            safe.add((len(self.grid[0]) - 1, y))
        
        # Zone centrale (maison des fantômes)
        for y in range(12, 17):
            for x in range(11, 17):
                safe.add((x, y))
        
        return safe
    
    def _find_movable_walls(self) -> List[Tuple[int, int]]:
        """Trouve tous les murs qui peuvent potentiellement bouger."""
        movable = []
        
        for y in range(1, len(self.grid) - 1):
            for x in range(1, len(self.grid[0]) - 1):
                if (x, y) in self.safe_zones:
                    continue
                
                if self.grid[y][x] == "X":
                    # Vérifier que le mur n'est pas structurellement critique
                    if self._can_move_wall(x, y):
                        movable.append((x, y))
        
        return movable
    
    def _can_move_wall(self, x: int, y: int) -> bool:
        """Vérifie si un mur peut bouger sans casser la structure."""
        # Un mur peut bouger s'il a au moins 2 côtés avec des espaces
        neighbors = [
            (x - 1, y),
            (x + 1, y),
            (x, y - 1),
            (x, y + 1),
        ]
        
        empty_sides = 0
        for nx, ny in neighbors:
            if 0 <= nx < len(self.grid[0]) and 0 <= ny < len(self.grid):
                if self.grid[ny][nx] != "X":
                    empty_sides += 1
        
        return empty_sides >= 2
    
    def activate_pattern(self, pattern: WallPattern):
        """Active un motif de mouvement."""
        self.current_pattern = pattern
        self.pattern_index = 0
        self.wall_timer = 0.0
        
        # Créer les murs mobiles pour ce motif
        self.moving_walls.clear()
        for wall_pos in pattern.walls:
            if wall_pos in self.movable_walls:
                x, y = wall_pos
                target = pattern.sequence[0] if pattern.sequence else wall_pos
                self.moving_walls.append(
                    MovingWall(x, y, target[0], target[1], speed=0.2)
                )
    
    def update(self, dt: float):
        """Met à jour les murs mobiles."""
        if not self.current_pattern:
            return
        
        self.wall_timer += dt
        
        # Mettre à jour chaque mur mobile
        for wall in self.moving_walls:
            if wall.update(dt):
                # Le mur a atteint sa destination, choisir la suivante
                self.pattern_index = (self.pattern_index + 1) % len(
                    self.current_pattern.sequence
                )
                next_pos = self.current_pattern.sequence[self.pattern_index]
                
                # Mettre à jour le grid
                old_x, old_y = wall.x, wall.y
                if self.grid[old_y][old_x] == "X":
                    self.grid[old_y][old_x] = " "
                
                wall.target_x = next_pos[0]
                wall.target_y = next_pos[1]
        
        # Réinitialiser après un cycle complet
        if self.wall_timer >= self.current_pattern.duration:
            self.wall_timer = 0.0
    
    def create_random_pattern(self, num_walls: int = 5) -> WallPattern:
        """Crée un motif de mouvement aléatoire."""
        if len(self.movable_walls) < num_walls:
            num_walls = len(self.movable_walls)
        
        # Sélectionner des murs aléatoires
        selected = random.sample(self.movable_walls, num_walls)
        
        # Créer une séquence de déplacements
        sequence = []
        for wall_pos in selected:
            x, y = wall_pos
            # Déplacer de 1-3 cases dans une direction aléatoire
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            dx, dy = random.choice(directions)
            distance = random.randint(1, 3)
            
            new_x = max(1, min(len(self.grid[0]) - 2, x + dx * distance))
            new_y = max(1, min(len(self.grid) - 2, y + dy * distance))
            
            if (new_x, new_y) not in self.safe_zones:
                sequence.append((new_x, new_y))
            else:
                sequence.append(wall_pos)
        
        return WallPattern(
            name="Random",
            walls=selected,
            sequence=sequence,
            duration=random.uniform(3.0, 8.0),
        )
    
    def create_wave_pattern(self) -> WallPattern:
        """Crée un motif de vague horizontale."""
        # Sélectionner une ligne de murs au milieu
        mid_y = len(self.grid) // 2
        walls = [(x, mid_y) for x in range(5, 23) if (x, mid_y) in self.movable_walls]
        
        # Créer une séquence de vague
        sequence = []
        for i, (x, y) in enumerate(walls):
            # Mouvement sinusoïdal
            offset = int(3 * np.sin(i * 0.5))
            new_y = max(3, min(len(self.grid) - 4, y + offset))
            sequence.append((x, new_y))
        
        return WallPattern(
            name="Wave",
            walls=walls,
            sequence=sequence,
            duration=6.0,
        )
    
    def create_spiral_pattern(self) -> WallPattern:
        """Crée un motif en spirale."""
        center_x = len(self.grid[0]) // 2
        center_y = len(self.grid) // 2
        
        # Trouver des murs autour du centre
        walls = []
        for radius in range(3, 8):
            for angle in range(0, 360, 45):
                rad = np.radians(angle)
                x = int(center_x + radius * np.cos(rad))
                y = int(center_y + radius * np.sin(rad))
                
                if (x, y) in self.movable_walls:
                    walls.append((x, y))
        
        # Rotation de la spirale
        sequence = []
        for x, y in walls:
            # Rotation de 45 degrés autour du centre
            rel_x = x - center_x
            rel_y = y - center_y
            
            angle = np.arctan2(rel_y, rel_x)
            radius = np.sqrt(rel_x**2 + rel_y**2)
            
            new_angle = angle + np.pi / 4
            new_x = int(center_x + radius * np.cos(new_angle))
            new_y = int(center_y + radius * np.sin(new_angle))
            
            if (new_x, new_y) not in self.safe_zones:
                sequence.append((new_x, new_y))
            else:
                sequence.append((x, y))
        
        return WallPattern(
            name="Spiral",
            walls=walls,
            sequence=sequence,
            duration=5.0,
        )
    
    def draw(self, surface: pygame.Surface):
        """Dessine le labyrinthe avec les murs mobiles."""
        tile = settings.TILE_SIZE
        
        # Dessiner le labyrinthe statique
        for y, row in enumerate(self.grid):
            for x, value in enumerate(row):
                rect = pygame.Rect(x * tile, y * tile, tile, tile)
                
                # Ne pas dessiner les murs qui bougent
                is_moving = any(
                    (wall.x == x and wall.y == y) for wall in self.moving_walls
                )
                
                if value == "X" and not is_moving:
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
        
        # Dessiner les murs mobiles avec interpolation
        for wall in self.moving_walls:
            current_x, current_y = wall.get_current_pos()
            rect = pygame.Rect(
                int(current_x * tile),
                int(current_y * tile),
                tile,
                tile,
            )
            
            # Effet visuel de mouvement (légère transparence)
            s = pygame.Surface((tile, tile))
            s.set_alpha(200 + int(55 * wall.progress))
            s.fill(settings.MAZE_WALL_COLOUR)
            surface.blit(s, rect)
            pygame.draw.rect(surface, settings.MAZE_BORDER_COLOUR, rect, 2)
    
    @classmethod
    def from_blueprint(cls, blueprint: List[str]) -> DynamicMaze:
        """Crée un labyrinthe dynamique à partir d'un blueprint."""
        grid = [list(row.replace("G", " ")) for row in blueprint]
        return cls(grid=grid)
    
    def enable_random_movements(self, interval: float = 5.0):
        """Active des mouvements aléatoires périodiques."""
        pattern = self.create_random_pattern(num_walls=3)
        self.activate_pattern(pattern)
    
    def enable_wave_movement(self):
        """Active le mouvement en vague."""
        pattern = self.create_wave_pattern()
        self.activate_pattern(pattern)
    
    def enable_spiral_movement(self):
        """Active le mouvement en spirale."""
        pattern = self.create_spiral_pattern()
        self.activate_pattern(pattern)
    
    def disable_movement(self):
        """Désactive tous les mouvements."""
        self.current_pattern = None
        self.moving_walls.clear()
