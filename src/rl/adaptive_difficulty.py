"""Système de difficulté adaptative basé sur les performances du joueur."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np


@dataclass
class PlayerStats:
    """Statistiques du joueur."""

    games_played: int = 0
    total_score: int = 0
    total_pellets_eaten: int = 0
    total_ghosts_eaten: int = 0
    total_deaths: int = 0
    total_time_played: float = 0.0
    win_streak: int = 0
    loss_streak: int = 0
    
    # Stats par partie
    scores_history: List[int] = field(default_factory=list)
    survival_times: List[float] = field(default_factory=list)
    
    @property
    def average_score(self) -> float:
        """Score moyen par partie."""
        if not self.scores_history:
            return 0.0
        return np.mean(self.scores_history)
    
    @property
    def average_survival_time(self) -> float:
        """Temps de survie moyen."""
        if not self.survival_times:
            return 0.0
        return np.mean(self.survival_times)
    
    @property
    def win_rate(self) -> float:
        """Taux de victoire."""
        if self.games_played == 0:
            return 0.0
        wins = len([s for s in self.scores_history if s > 0])
        return wins / self.games_played
    
    def add_game(
        self,
        score: int,
        pellets: int,
        ghosts: int,
        died: bool,
        time_played: float,
        won: bool,
    ):
        """Ajoute une partie aux statistiques."""
        self.games_played += 1
        self.total_score += score
        self.total_pellets_eaten += pellets
        self.total_ghosts_eaten += ghosts
        if died:
            self.total_deaths += 1
        self.total_time_played += time_played
        
        # Historique
        self.scores_history.append(score)
        self.survival_times.append(time_played)
        
        # Limiter l'historique à 100 parties
        if len(self.scores_history) > 100:
            self.scores_history.pop(0)
        if len(self.survival_times) > 100:
            self.survival_times.pop(0)
        
        # Win/loss streak
        if won:
            self.win_streak += 1
            self.loss_streak = 0
        else:
            self.loss_streak += 1
            self.win_streak = 0


@dataclass
class DifficultyLevel:
    """Niveau de difficulté."""

    name: str
    ghost_speed_multiplier: float
    ghost_intelligence: float  # 0.0 = aléatoire, 1.0 = optimal
    frightened_duration_multiplier: float
    respawn_delay_multiplier: float
    num_active_ghosts: int
    pellet_score_multiplier: float
    
    @staticmethod
    def easy() -> DifficultyLevel:
        """Difficulté facile."""
        return DifficultyLevel(
            name="Facile",
            ghost_speed_multiplier=0.7,
            ghost_intelligence=0.3,
            frightened_duration_multiplier=1.5,
            respawn_delay_multiplier=1.5,
            num_active_ghosts=2,
            pellet_score_multiplier=1.2,
        )
    
    @staticmethod
    def normal() -> DifficultyLevel:
        """Difficulté normale."""
        return DifficultyLevel(
            name="Normal",
            ghost_speed_multiplier=1.0,
            ghost_intelligence=0.6,
            frightened_duration_multiplier=1.0,
            respawn_delay_multiplier=1.0,
            num_active_ghosts=3,
            pellet_score_multiplier=1.0,
        )
    
    @staticmethod
    def hard() -> DifficultyLevel:
        """Difficulté difficile."""
        return DifficultyLevel(
            name="Difficile",
            ghost_speed_multiplier=1.3,
            ghost_intelligence=0.85,
            frightened_duration_multiplier=0.7,
            respawn_delay_multiplier=0.7,
            num_active_ghosts=4,
            pellet_score_multiplier=0.8,
        )
    
    @staticmethod
    def expert() -> DifficultyLevel:
        """Difficulté experte."""
        return DifficultyLevel(
            name="Expert",
            ghost_speed_multiplier=1.5,
            ghost_intelligence=1.0,
            frightened_duration_multiplier=0.5,
            respawn_delay_multiplier=0.5,
            num_active_ghosts=4,
            pellet_score_multiplier=0.7,
        )


class DifficultyManager:
    """Gestionnaire de difficulté adaptative."""

    def __init__(self, adaptation_speed: float = 0.1):
        """
        Args:
            adaptation_speed: Vitesse d'adaptation (0.0 = lent, 1.0 = rapide)
        """
        self.adaptation_speed = adaptation_speed
        self.stats = PlayerStats()
        self.current_difficulty = DifficultyLevel.normal()
        
        # Seuils pour ajuster la difficulté
        self.easy_threshold = 0.3  # Win rate < 30% -> plus facile
        self.hard_threshold = 0.7  # Win rate > 70% -> plus difficile
        self.min_games_before_adjust = 5
    
    def update_after_game(
        self,
        score: int,
        pellets: int,
        ghosts: int,
        died: bool,
        time_played: float,
        won: bool,
    ):
        """Met à jour les statistiques après une partie."""
        self.stats.add_game(score, pellets, ghosts, died, time_played, won)
        
        # Adapter la difficulté si nécessaire
        if self.stats.games_played >= self.min_games_before_adjust:
            self._adapt_difficulty()
    
    def _adapt_difficulty(self):
        """Adapte la difficulté en fonction des performances."""
        win_rate = self.stats.win_rate
        recent_scores = self.stats.scores_history[-10:]  # 10 dernières parties
        
        if len(recent_scores) < 5:
            return
        
        avg_recent_score = np.mean(recent_scores)
        score_trend = self._calculate_trend(recent_scores)
        
        # Déterminer s'il faut ajuster
        should_decrease = False
        should_increase = False
        
        # Trop difficile ?
        if win_rate < self.easy_threshold or self.stats.loss_streak >= 5:
            should_decrease = True
        
        # Trop facile ?
        if win_rate > self.hard_threshold or self.stats.win_streak >= 5:
            should_increase = True
        
        # Tendance des scores
        if score_trend < -0.2 and avg_recent_score < self.stats.average_score * 0.8:
            should_decrease = True
        elif score_trend > 0.2 and avg_recent_score > self.stats.average_score * 1.2:
            should_increase = True
        
        # Appliquer l'ajustement
        if should_decrease:
            self._decrease_difficulty()
        elif should_increase:
            self._increase_difficulty()
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calcule la tendance d'une série de valeurs (-1 à 1)."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Régression linéaire simple
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        # Normaliser la pente
        y_range = np.max(y) - np.min(y)
        if y_range == 0:
            return 0.0
        
        normalized_slope = slope / (y_range / len(values))
        return np.clip(normalized_slope, -1.0, 1.0)
    
    def _decrease_difficulty(self):
        """Diminue la difficulté graduellement."""
        d = self.current_difficulty
        
        # Ajuster les paramètres progressivement
        d.ghost_speed_multiplier = max(0.5, d.ghost_speed_multiplier - 0.1 * self.adaptation_speed)
        d.ghost_intelligence = max(0.1, d.ghost_intelligence - 0.1 * self.adaptation_speed)
        d.frightened_duration_multiplier = min(2.0, d.frightened_duration_multiplier + 0.1 * self.adaptation_speed)
        d.respawn_delay_multiplier = min(2.0, d.respawn_delay_multiplier + 0.1 * self.adaptation_speed)
        d.pellet_score_multiplier = min(1.5, d.pellet_score_multiplier + 0.05 * self.adaptation_speed)
        
        # Réduire le nombre de fantômes actifs si nécessaire
        if d.num_active_ghosts > 2 and np.random.random() < 0.3:
            d.num_active_ghosts -= 1
        
        print(f"🔽 Difficulté diminuée: {d.name}")
    
    def _increase_difficulty(self):
        """Augmente la difficulté graduellement."""
        d = self.current_difficulty
        
        # Ajuster les paramètres progressivement
        d.ghost_speed_multiplier = min(2.0, d.ghost_speed_multiplier + 0.1 * self.adaptation_speed)
        d.ghost_intelligence = min(1.0, d.ghost_intelligence + 0.1 * self.adaptation_speed)
        d.frightened_duration_multiplier = max(0.3, d.frightened_duration_multiplier - 0.1 * self.adaptation_speed)
        d.respawn_delay_multiplier = max(0.3, d.respawn_delay_multiplier - 0.1 * self.adaptation_speed)
        d.pellet_score_multiplier = max(0.5, d.pellet_score_multiplier - 0.05 * self.adaptation_speed)
        
        # Augmenter le nombre de fantômes actifs si nécessaire
        if d.num_active_ghosts < 4 and np.random.random() < 0.3:
            d.num_active_ghosts += 1
        
        print(f"🔼 Difficulté augmentée: {d.name}")
    
    def get_ghost_speed(self, base_speed: float) -> float:
        """Calcule la vitesse d'un fantôme selon la difficulté."""
        return base_speed * self.current_difficulty.ghost_speed_multiplier
    
    def should_use_ai_path(self) -> bool:
        """Détermine si le fantôme doit utiliser l'IA (selon l'intelligence)."""
        return np.random.random() < self.current_difficulty.ghost_intelligence
    
    def get_frightened_duration(self, base_duration: float) -> float:
        """Calcule la durée du mode frightened."""
        return base_duration * self.current_difficulty.frightened_duration_multiplier
    
    def get_respawn_delay(self, base_delay: float) -> float:
        """Calcule le délai de respawn."""
        return base_delay * self.current_difficulty.respawn_delay_multiplier
    
    def get_active_ghost_count(self) -> int:
        """Retourne le nombre de fantômes actifs."""
        return self.current_difficulty.num_active_ghosts
    
    def get_score_multiplier(self) -> float:
        """Retourne le multiplicateur de score."""
        return self.current_difficulty.pellet_score_multiplier
    
    def get_stats_summary(self) -> Dict[str, any]:
        """Retourne un résumé des statistiques."""
        return {
            "games_played": self.stats.games_played,
            "average_score": self.stats.average_score,
            "win_rate": self.stats.win_rate,
            "current_difficulty": self.current_difficulty.name,
            "ghost_speed": self.current_difficulty.ghost_speed_multiplier,
            "ghost_intelligence": self.current_difficulty.ghost_intelligence,
            "win_streak": self.stats.win_streak,
            "loss_streak": self.stats.loss_streak,
        }
