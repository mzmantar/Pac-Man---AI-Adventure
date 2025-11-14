# Pac-Man Deluxe - IA V1.0

Version française — clone/variation de Pac‑Man implémentée en Python avec `pygame` et une IA A* pour la navigation des fantômes (et un autopilot pour Pac‑Man).

## Aperçu
- Jeu inspiré de Pac‑Man avec comportements de fantômes (scatter / chase / frightened / eaten).
- IA basée sur A* (recherche de chemin), et logique de décision simple pour les fantômes située dans `src/ai/`.
- Projet modulaire : `src/game.py`, `src/maze.py`, `src/entities.py`, `src/ai/`.

## Caractéristiques
- Mouvement fluide des entités sur une grille.
- Autopilot (Pac‑Man peut suivre un chemin calculé automatiquement).
- Replanification automatique (touche `C`) pour recalculer la trajectoire A*.
- Affichage simple avec `pygame`.

## Prérequis
- Python 3.10+ recommandé
- `pygame==2.6.1` (déclaré dans `requirements.txt`)

## Installation (PowerShell)
```powershell
cd c:\Users\moham\pac_man
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancer le jeu
```powershell
python main.py
```

## Contrôles
- Flèches directionnelles : déplacer Pac‑Man manuellement.
- C : basculer le mode de replanification automatique (A*).
- Clic gauche : si vous cliquez sur une case valide, Pac‑Man calculera un chemin vers cette case.
- Échap / Entrée (à l'écran Game Over) : quitter l'écran Game Over.
- Fermer la fenêtre ou `Ctrl+C` dans la console pour arrêter le jeu.

## Structure du dépôt
- `main.py` — point d'entrée.
- `requirements.txt` — dépendances.
- `src/`
  - `game.py` — boucle du jeu, entrée/sortie, orchestration.
  - `maze.py` — blueprint du labyrinthe, pellets, dessin.
  - `entities.py` — Pac‑Man, Ghosts, logique de mouvement et dessin.
  - `ai/`
    - `pathfinding.py` — A* adapté à la grille.
    - `controller.py` — logique de décision des fantômes.
  - `settings.py` — constantes (taille, couleurs, vitesses).
---