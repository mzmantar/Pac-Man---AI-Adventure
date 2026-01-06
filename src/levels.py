"""Gestion des niveaux et paramètres scalables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from . import settings


@dataclass(frozen=True)
class LevelConfig:
    """Paramètres d'un niveau."""

    name: str
    pacman_speed_multiplier: float = 1.0
    ghost_speed_multiplier: float = 1.0
    frightened_speed_multiplier: float = 1.0
    power_duration_multiplier: float = 1.0
    score_multiplier: float = 1.0
    lives: int | None = None
    auto_replan: bool = False

    def apply(self) -> None:
        """Applique les multiplicateurs au module settings."""
        settings.PACMAN_SPEED = settings.BASE_PACMAN_SPEED * self.pacman_speed_multiplier
        settings.GHOST_SPEED = settings.BASE_GHOST_SPEED * self.ghost_speed_multiplier
        settings.FRIGHTENED_SPEED = (
            settings.BASE_FRIGHTENED_SPEED * self.frightened_speed_multiplier
        )
        settings.POWER_MODE_DURATION = (
            settings.BASE_POWER_MODE_DURATION * self.power_duration_multiplier
        )
        if self.lives is not None:
            settings.PACMAN_LIVES = self.lives


LEVELS: List[LevelConfig] = [
    LevelConfig(
        name="Niveau 1 - Classique",
        pacman_speed_multiplier=1.0,
        ghost_speed_multiplier=0.9,
        frightened_speed_multiplier=1.1,
        power_duration_multiplier=1.2,
        score_multiplier=1.0,
        lives=4,
    ),
    LevelConfig(
        name="Niveau 2 - Dynamique",
        pacman_speed_multiplier=1.0,
        ghost_speed_multiplier=1.0,
        frightened_speed_multiplier=1.0,
        power_duration_multiplier=1.0,
        score_multiplier=1.1,
    ),
    LevelConfig(
        name="Niveau 3 - Rapide",
        pacman_speed_multiplier=1.1,
        ghost_speed_multiplier=1.2,
        frightened_speed_multiplier=1.0,
        power_duration_multiplier=0.9,
        score_multiplier=1.2,
    ),
    LevelConfig(
        name="Niveau 4 - Expert",
        pacman_speed_multiplier=1.1,
        ghost_speed_multiplier=1.35,
        frightened_speed_multiplier=0.9,
        power_duration_multiplier=0.8,
        score_multiplier=1.3,
        lives=2,
        auto_replan=True,
    ),
]


def get_level(index: int) -> LevelConfig:
    """Retourne la configuration d'un niveau (avec clamp)."""
    if index < 0:
        index = 0
    if index >= len(LEVELS):
        index = len(LEVELS) - 1
    return LEVELS[index]
