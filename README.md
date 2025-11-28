# 🎮 Pac-Man AI Adventure

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Pygame](https://img.shields.io/badge/pygame-2.6.1-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

*Un clone moderne de Pac-Man avec intelligence artificielle avancée*

[Fonctionnalités](#-fonctionnalités) • [Installation](#-installation) • [Utilisation](#-utilisation) • [Architecture](#-architecture) • [Contrôles](#-contrôles)

</div>

---

## 📋 Description

**Pac-Man AI Adventure** est une implémentation professionnelle du jeu classique Pac-Man, développée en Python avec Pygame. Ce projet se distingue par son système d'intelligence artificielle sophistiqué utilisant l'algorithme A* pour la navigation autonome des fantômes et du joueur.

### 🎯 Objectifs du Projet

- Créer une version fidèle du jeu Pac-Man original
- Implémenter des comportements intelligents pour les fantômes
- Offrir un mode autopilote basé sur l'IA pour Pac-Man
- Démontrer l'utilisation de l'algorithme A* dans un jeu vidéo
- Fournir une architecture de code modulaire et maintenable

---

## ✨ Fonctionnalités

### 🤖 Intelligence Artificielle

- **Algorithme A*** : Pathfinding optimisé pour la navigation sur grille
- **Comportements multiples** des fantômes :
  - 🔴 **Scatter** : Patrouille des zones
  - 🎯 **Chase** : Poursuite agressive de Pac-Man
  - 💙 **Frightened** : Fuite aléatoire (mode vulnérable)
  - 👻 **Eaten** : Retour au spawn après capture
- **Autopilote intelligent** : Pac-Man peut naviguer automatiquement vers un objectif
- **Replanification dynamique** : Adaptation en temps réel aux changements du jeu

### 🎨 Interface & Graphismes

- Menu principal animé avec effets visuels
- Écran d'instructions détaillé
- Animations fluides des personnages
- Effets de particules et dégradés
- Interface utilisateur intuitive

### 🎮 Gameplay

- Mouvement fluide sur grille avec interpolation
- Système de collision précis
- Régénération automatique des pellets
- Condition de victoire : manger tous les fantômes
- Score et statistiques en temps réel
- Mode "power pellet" pour manger les fantômes

---

## 🚀 Installation

### Prérequis

- **Python 3.10+** (Python 3.11.0 recommandé)
- **pip** (gestionnaire de paquets Python)
- **Windows** PowerShell (ou terminal compatible)

### Étapes d'Installation

1. **Cloner le dépôt**
   ```powershell
   git clone https://github.com/mzmantar/Pac-Man---AI-Adventure.git
   cd Pac-Man---AI-Adventure
   ```

2. **Créer l'environnement virtuel**
   ```powershell
   python -m venv .venv
   ```

3. **Activer l'environnement virtuel**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   
   *Note : Si vous rencontrez une erreur de politique d'exécution, exécutez :*
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

4. **Installer les dépendances**
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🎯 Utilisation

### Lancer le Jeu

```powershell
python main.py
```

### 🕹️ Contrôles

#### Navigation du Menu
- **↑/↓** : Naviguer entre les options
- **ENTRÉE** : Sélectionner une option
- **ÉCHAP** : Quitter le jeu

#### Contrôles en Jeu

| Touche | Action |
|--------|--------|
| **←→↑↓** | Déplacer Pac-Man manuellement |
| **C** | Activer/Désactiver l'autopilote IA |
| **Clic gauche** | Définir une destination (calcul automatique du chemin) |
| **ÉCHAP** | Pause / Retour au menu |

#### Objectifs

- 🎯 **Objectif principal** : Mangez TOUS les fantômes pour gagner !
- 🔵 **Power Pellets** : Les gros points rendent les fantômes vulnérables (bleus)
- ⭐ **Points** : Fantômes bleus = +200 points
- ♻️ **Régénération** : Les pellets se régénèrent automatiquement

---

## 🏗️ Architecture

### Structure du Projet

```
pac_man/
│
├── main.py                 # Point d'entrée de l'application
├── requirements.txt        # Dépendances Python
├── README.md              # Documentation
│
└── src/
    ├── __init__.py
    ├── settings.py        # Configuration globale (constantes, couleurs)
    ├── menu.py            # Système de menus avec animations
    ├── game.py            # Boucle principale du jeu
    ├── maze.py            # Labyrinthe, pellets, génération
    ├── entities.py        # Pac-Man, Ghosts, entités du jeu
    │
    └── ai/
        ├── __init__.py
        ├── pathfinding.py # Implémentation de l'algorithme A*
        └── controller.py  # Logique de décision des fantômes
```

### Modules Principaux

#### 🎮 `game.py`
- Boucle principale du jeu
- Gestion des événements
- Détection des collisions
- Rendu des écrans (victoire/défaite)

#### 🗺️ `maze.py`
- Génération du labyrinthe à partir d'un blueprint
- Gestion des pellets et power pellets
- Système de régénération
- Affichage du terrain

#### 👾 `entities.py`
- Classe `Pacman` : Mouvement, animations, états
- Classe `Ghost` : 4 fantômes avec comportements distincts
  - Blinky (Rouge) : Agressif et direct
  - Pinky (Rose) : Embuscades stratégiques
  - Inky (Cyan) : Comportement imprévisible
  - Clyde (Orange) : Timide mais rusé
- Système d'escape pour fantômes bloqués

#### 🤖 `ai/pathfinding.py`
- Implémentation de l'algorithme A*
- Heuristique Manhattan
- Optimisé pour grilles de jeu
- Cache de chemins pour performance

#### 🧠 `ai/controller.py`
- Gestion des modes de fantômes
- Calcul des cibles (scatter/chase)
- Système de décision basé sur la distance
- Coordination multi-agents

#### 🎨 `menu.py`
- Menu principal avec animations
- Écran d'instructions interactif
- Effets visuels (gradients, particules)
- Gestion de la navigation

---

## 🛠️ Technologies Utilisées

- **Python 3.11.0** : Langage de programmation
- **Pygame 2.6.1** : Moteur de jeu 2D
- **Algorithme A*** : Pathfinding intelligent
- **Architecture MVC** : Séparation des responsabilités

---

## 📊 Système de Jeu

### Comportements des Fantômes

1. **Mode Scatter** : Les fantômes patrouillent leurs coins respectifs
2. **Mode Chase** : Poursuite active de Pac-Man avec stratégies uniques
3. **Mode Frightened** : Mouvement aléatoire, vulnérables aux attaques
4. **Mode Eaten** : Retour rapide à la zone de spawn

### Système de Score

- Petit pellet : +10 points
- Power pellet : +50 points
- Fantôme mangé : +200 points
- Victoire totale : Bonus supplémentaire

---

## 🐛 Dépannage

### Le jeu ne se lance pas

```powershell
# Vérifier la version de Python
python --version

# Réinstaller les dépendances
pip install --upgrade -r requirements.txt
```

### Erreur d'importation de module

```powershell
# S'assurer que l'environnement virtuel est activé
.\.venv\Scripts\Activate.ps1

# Vérifier l'installation de pygame
pip show pygame
```

### Performance lente

- Réduire le nombre de particules dans `menu.py`
- Vérifier que les pilotes graphiques sont à jour
- Fermer les applications gourmandes en ressources

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

---

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 👨‍💻 Auteur

**mzmantar**

- GitHub: [@mzmantar](https://github.com/mzmantar)
- Repository: [Pac-Man---AI-Adventure](https://github.com/mzmantar/Pac-Man---AI-Adventure)

---