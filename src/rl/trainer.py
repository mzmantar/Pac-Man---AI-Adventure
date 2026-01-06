"""Script d'entraînement pour les agents RL."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import torch
from torch.utils.tensorboard import SummaryWriter

from .rl_agent import RLGhostAgent, RLPacmanAgent
from .rl_environment import PacManEnv
from .adaptive_difficulty import DifficultyManager


class RLTrainer:
    """Gestionnaire d'entraînement pour les agents RL."""

    def __init__(
        self,
        env: PacManEnv,
        agent: RLGhostAgent | RLPacmanAgent,
        save_dir: Path,
        log_dir: Optional[Path] = None,
    ):
        self.env = env
        self.agent = agent
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)

        # TensorBoard
        if log_dir:
            self.writer = SummaryWriter(log_dir=str(log_dir))
        else:
            self.writer = SummaryWriter(log_dir=str(save_dir / "logs"))

        # Statistiques
        self.episode_rewards = []
        self.episode_lengths = []
        self.losses = []

    def train(
        self,
        num_episodes: int = 1000,
        max_steps_per_episode: int = 1000,
        save_freq: int = 100,
        eval_freq: int = 50,
    ):
        """Entraîne l'agent."""
        print(f"🎮 Démarrage de l'entraînement pour {num_episodes} épisodes...")
        print(f"📁 Modèles sauvegardés dans: {self.save_dir}")

        best_reward = float("-inf")

        for episode in range(1, num_episodes + 1):
            episode_reward, episode_length, avg_loss = self._run_episode(
                max_steps_per_episode
            )

            # Enregistrer les statistiques
            self.episode_rewards.append(episode_reward)
            self.episode_lengths.append(episode_length)
            if avg_loss > 0:
                self.losses.append(avg_loss)

            # TensorBoard
            self.writer.add_scalar("train/reward", episode_reward, episode)
            self.writer.add_scalar("train/length", episode_length, episode)
            self.writer.add_scalar("train/loss", avg_loss, episode)
            self.writer.add_scalar("train/epsilon", self.agent.config.epsilon, episode)

            # Afficher les progrès
            if episode % 10 == 0:
                avg_reward = np.mean(self.episode_rewards[-10:])
                avg_length = np.mean(self.episode_lengths[-10:])
                print(
                    f"Épisode {episode}/{num_episodes} | "
                    f"Récompense: {episode_reward:.1f} (moy: {avg_reward:.1f}) | "
                    f"Longueur: {episode_length} (moy: {avg_length:.1f}) | "
                    f"ε: {self.agent.config.epsilon:.3f}"
                )

            # Sauvegarder le meilleur modèle
            if episode_reward > best_reward:
                best_reward = episode_reward
                self.agent.save(self.save_dir / "best_model.pt")
                print(f"💾 Nouveau meilleur modèle sauvegardé (récompense: {best_reward:.1f})")

            # Sauvegarder périodiquement
            if episode % save_freq == 0:
                self.agent.save(self.save_dir / f"model_ep{episode}.pt")

            # Évaluer périodiquement
            if episode % eval_freq == 0:
                eval_reward, eval_length = self.evaluate(num_episodes=5)
                self.writer.add_scalar("eval/reward", eval_reward, episode)
                self.writer.add_scalar("eval/length", eval_length, episode)
                print(f"📊 Évaluation: Récompense={eval_reward:.1f}, Longueur={eval_length:.1f}")

        # Sauvegarder le modèle final
        self.agent.save(self.save_dir / "final_model.pt")
        print("✅ Entraînement terminé!")
        
        self.writer.close()

    def _run_episode(self, max_steps: int) -> tuple[float, int, float]:
        """Exécute un épisode d'entraînement."""
        state, _ = self.env.reset()
        total_reward = 0.0
        total_loss = 0.0
        steps = 0
        loss_count = 0

        for step in range(max_steps):
            # Sélectionner une action
            action = self.agent.select_action(state)

            # Exécuter l'action
            next_state, reward, terminated, truncated, _ = self.env.step(action)
            done = terminated or truncated

            # Stocker l'expérience
            self.agent.remember(state, action, reward, next_state, done)

            # Entraîner le réseau
            if len(self.agent.memory) >= self.agent.config.batch_size:
                loss = self.agent.replay()
                total_loss += loss
                loss_count += 1

            total_reward += reward
            steps += 1
            state = next_state

            if done:
                break

        avg_loss = total_loss / loss_count if loss_count > 0 else 0.0
        return total_reward, steps, avg_loss

    def evaluate(self, num_episodes: int = 10) -> tuple[float, float]:
        """Évalue l'agent sans exploration."""
        old_epsilon = self.agent.config.epsilon
        self.agent.config.epsilon = 0.0  # Pas d'exploration

        rewards = []
        lengths = []

        for _ in range(num_episodes):
            state, _ = self.env.reset()
            episode_reward = 0.0
            episode_length = 0

            done = False
            while not done and episode_length < 1000:
                action = self.agent.select_action(state)
                state, reward, terminated, truncated, _ = self.env.step(action)
                done = terminated or truncated
                episode_reward += reward
                episode_length += 1

            rewards.append(episode_reward)
            lengths.append(episode_length)

        self.agent.config.epsilon = old_epsilon

        return np.mean(rewards), np.mean(lengths)


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(description="Entraîner un agent RL pour Pac-Man")
    parser.add_argument(
        "--agent",
        type=str,
        choices=["pacman", "ghost"],
        default="pacman",
        help="Type d'agent à entraîner",
    )
    parser.add_argument(
        "--episodes",
        type=int,
        default=1000,
        help="Nombre d'épisodes d'entraînement",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1000,
        help="Nombre maximum de steps par épisode",
    )
    parser.add_argument(
        "--save-dir",
        type=str,
        default="models",
        help="Répertoire pour sauvegarder les modèles",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Afficher le jeu pendant l'entraînement",
    )
    parser.add_argument(
        "--load",
        type=str,
        default=None,
        help="Chemin vers un modèle à charger",
    )

    args = parser.parse_args()

    # Créer l'environnement
    render_mode = "human" if args.render else None
    env = PacManEnv(render_mode=render_mode, max_steps=args.steps)

    # Créer l'agent
    if args.agent == "pacman":
        agent = RLPacmanAgent()
        print("🟡 Entraînement de l'agent Pac-Man")
    else:
        agent = RLGhostAgent()
        print("👻 Entraînement de l'agent fantôme")

    # Charger un modèle existant si spécifié
    if args.load:
        agent.load(Path(args.load))
        print(f"📂 Modèle chargé depuis {args.load}")

    # Créer le trainer
    save_dir = Path(args.save_dir) / args.agent
    trainer = RLTrainer(env, agent, save_dir)

    # Entraîner
    try:
        trainer.train(
            num_episodes=args.episodes,
            max_steps_per_episode=args.steps,
        )
    except KeyboardInterrupt:
        print("\n⏸️  Entraînement interrompu par l'utilisateur")
        agent.save(save_dir / "interrupted_model.pt")
        print(f"💾 Modèle sauvegardé dans {save_dir}")
    finally:
        env.close()


if __name__ == "__main__":
    main()
