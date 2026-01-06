"""Agents de Reinforcement Learning pour Pac-Man et les fantômes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from pygame.math import Vector2


class DQNetwork(nn.Module):
    """Réseau de neurones Deep Q-Network pour l'agent."""

    def __init__(self, state_size: int, action_size: int, hidden_size: int = 128):
        super().__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, action_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


@dataclass
class RLConfig:
    """Configuration pour l'agent RL."""

    learning_rate: float = 0.001
    gamma: float = 0.99  # Facteur de discount
    epsilon: float = 1.0  # Exploration rate
    epsilon_min: float = 0.01
    epsilon_decay: float = 0.995
    batch_size: int = 32
    memory_size: int = 10000
    target_update_freq: int = 10


class RLAgent:
    """Agent de base utilisant Deep Q-Learning."""

    def __init__(
        self,
        state_size: int,
        action_size: int,
        config: Optional[RLConfig] = None,
    ):
        self.state_size = state_size
        self.action_size = action_size
        self.config = config or RLConfig()

        # Réseau principal et réseau cible
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.policy_net = DQNetwork(state_size, action_size).to(self.device)
        self.target_net = DQNetwork(state_size, action_size).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = torch.optim.Adam(
            self.policy_net.parameters(), lr=self.config.learning_rate
        )

        # Mémoire de replay
        self.memory: List[Tuple[np.ndarray, int, float, np.ndarray, bool]] = []
        self.steps = 0

    def get_state_representation(
        self, maze_state: np.ndarray, entity_pos: Vector2, target_pos: Vector2
    ) -> np.ndarray:
        """Convertit l'état du jeu en représentation pour le réseau."""
        # Position relative de l'entité
        pos = np.array([entity_pos.x, entity_pos.y])

        # Position relative de la cible
        target = np.array([target_pos.x, target_pos.y])
        relative_target = target - pos

        # Distance et direction vers la cible
        distance = np.linalg.norm(relative_target)
        direction = relative_target / (distance + 1e-8)

        # État local du labyrinthe (5x5 autour de l'entité)
        local_maze = self._extract_local_maze(maze_state, entity_pos)

        # Combiner toutes les features
        state = np.concatenate(
            [pos, relative_target, [distance], direction, local_maze.flatten()]
        )
        return state.astype(np.float32)

    def _extract_local_maze(
        self, maze_state: np.ndarray, pos: Vector2, radius: int = 2
    ) -> np.ndarray:
        """Extrait une vue locale du labyrinthe."""
        x, y = int(pos.x), int(pos.y)
        h, w = maze_state.shape
        local = np.zeros((2 * radius + 1, 2 * radius + 1))

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    local[dy + radius, dx + radius] = maze_state[ny, nx]

        return local

    def select_action(
        self, state: np.ndarray, valid_actions: Optional[List[int]] = None
    ) -> int:
        """Sélectionne une action avec epsilon-greedy."""
        # Exploration
        if np.random.random() < self.config.epsilon:
            if valid_actions:
                return np.random.choice(valid_actions)
            return np.random.randint(self.action_size)

        # Exploitation
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)

            # Masquer les actions invalides
            if valid_actions:
                mask = torch.full((self.action_size,), float("-inf"))
                mask[valid_actions] = 0
                q_values = q_values + mask.to(self.device)

            return q_values.argmax().item()

    def remember(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
    ):
        """Stocke l'expérience dans la mémoire de replay."""
        if len(self.memory) >= self.config.memory_size:
            self.memory.pop(0)
        self.memory.append((state, action, reward, next_state, done))

    def replay(self) -> float:
        """Entraîne le réseau sur un batch d'expériences."""
        if len(self.memory) < self.config.batch_size:
            return 0.0

        # Échantillonner un batch
        indices = np.random.choice(len(self.memory), self.config.batch_size, replace=False)
        batch = [self.memory[i] for i in indices]

        states = torch.FloatTensor([s for s, _, _, _, _ in batch]).to(self.device)
        actions = torch.LongTensor([a for _, a, _, _, _ in batch]).to(self.device)
        rewards = torch.FloatTensor([r for _, _, r, _, _ in batch]).to(self.device)
        next_states = torch.FloatTensor([ns for _, _, _, ns, _ in batch]).to(self.device)
        dones = torch.FloatTensor([d for _, _, _, _, d in batch]).to(self.device)

        # Q-values actuelles
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)

        # Q-values cibles
        next_q = self.target_net(next_states).max(1)[0]
        target_q = rewards + (1 - dones) * self.config.gamma * next_q

        # Calculer la perte
        loss = F.mse_loss(current_q, target_q.detach())

        # Backpropagation
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        # Mettre à jour epsilon
        self.config.epsilon = max(
            self.config.epsilon_min, self.config.epsilon * self.config.epsilon_decay
        )

        # Mettre à jour le réseau cible
        self.steps += 1
        if self.steps % self.config.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        return loss.item()

    def save(self, path: Path):
        """Sauvegarde le modèle."""
        torch.save(
            {
                "policy_net": self.policy_net.state_dict(),
                "target_net": self.target_net.state_dict(),
                "optimizer": self.optimizer.state_dict(),
                "config": self.config,
            },
            path,
        )

    def load(self, path: Path):
        """Charge le modèle."""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint["policy_net"])
        self.target_net.load_state_dict(checkpoint["target_net"])
        self.optimizer.load_state_dict(checkpoint["optimizer"])
        self.config = checkpoint["config"]


class RLGhostAgent(RLAgent):
    """Agent RL spécialisé pour contrôler un fantôme."""

    def __init__(self):
        # État: position ghost (2), position pacman (2), direction (2),
        #       labyrinthe local (5x5), mode (4)
        state_size = 2 + 2 + 2 + 25 + 4
        # Actions: 4 directions
        action_size = 4
        super().__init__(state_size, action_size)

    def calculate_reward(
        self,
        old_dist: float,
        new_dist: float,
        caught_pacman: bool,
        was_eaten: bool,
        is_frightened: bool,
    ) -> float:
        """Calcule la récompense pour le fantôme."""
        reward = 0.0

        if caught_pacman:
            reward += 100.0  # Grande récompense pour attraper Pac-Man
        elif was_eaten:
            reward -= 50.0  # Pénalité pour être mangé

        if is_frightened:
            # En mode frightened, récompenser l'éloignement
            if new_dist > old_dist:
                reward += 1.0
        else:
            # En mode normal, récompenser le rapprochement
            if new_dist < old_dist:
                reward += 1.0

        return reward


class RLPacmanAgent(RLAgent):
    """Agent RL pour contrôler Pac-Man."""

    def __init__(self):
        # État: position (2), ghosts positions (8), pellets proches (25),
        #       power mode (1), labyrinthe local (25)
        state_size = 2 + 8 + 25 + 1 + 25
        # Actions: 4 directions
        action_size = 4
        super().__init__(state_size, action_size)

    def calculate_reward(
        self,
        pellets_eaten: int,
        power_pellet_eaten: bool,
        ghosts_eaten: int,
        died: bool,
        score_delta: int,
    ) -> float:
        """Calcule la récompense pour Pac-Man."""
        reward = 0.0

        # Récompenses pour pellets
        reward += pellets_eaten * 10.0

        # Bonus pour power pellet
        if power_pellet_eaten:
            reward += 50.0

        # Récompenses pour manger des fantômes
        reward += ghosts_eaten * 200.0

        # Pénalité pour mort
        if died:
            reward -= 500.0

        # Bonus basé sur le score
        reward += score_delta * 0.1

        return reward
