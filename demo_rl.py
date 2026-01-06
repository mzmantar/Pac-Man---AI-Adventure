"""Exemple d'utilisation du module RL."""

import pygame

from src.rl.dynamic_maze import DynamicMaze
from src.rl.adaptive_difficulty import DifficultyManager
from src.maze import MAZE_BLUEPRINT
from src.entities import Pacman, Ghost
from src import settings


def demo_dynamic_maze():
    """Démo du labyrinthe dynamique."""
    print("🎮 Démo : Labyrinthe Dynamique")
    print("=" * 50)
    
    pygame.init()
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption("Pac-Man - Labyrinthe Dynamique")
    clock = pygame.time.Clock()
    
    # Créer le labyrinthe dynamique
    maze = DynamicMaze.from_blueprint(MAZE_BLUEPRINT)
    
    # Activer un motif (changer pour tester différents motifs)
    print("🌊 Activation du motif en vague...")
    maze.enable_wave_movement()
    # maze.enable_spiral_movement()  # Décommenter pour tester
    # maze.enable_random_movements()  # Décommenter pour tester
    
    # Créer Pac-Man
    pacman = Pacman(maze, start_pos=(13, 23))
    
    running = True
    paused = False
    pattern_index = 0
    patterns = ["wave", "spiral", "random"]
    
    while running:
        dt = clock.tick(settings.FRAMES_PER_SECOND) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    print(f"{'⏸️  Pause' if paused else '▶️  Reprise'}")
                elif event.key == pygame.K_m:
                    # Changer de motif
                    pattern_index = (pattern_index + 1) % len(patterns)
                    pattern = patterns[pattern_index]
                    print(f"🔄 Changement de motif : {pattern}")
                    
                    if pattern == "wave":
                        maze.enable_wave_movement()
                    elif pattern == "spiral":
                        maze.enable_spiral_movement()
                    elif pattern == "random":
                        maze.enable_random_movements()
                elif event.key == pygame.K_d:
                    # Désactiver les mouvements
                    maze.disable_movement()
                    print("⏹️  Mouvements désactivés")
        
        if not paused:
            # Mettre à jour le labyrinthe
            maze.update(dt)
            
            # Contrôler Pac-Man
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                pacman.desired_direction = pygame.math.Vector2(-1, 0)
            elif keys[pygame.K_RIGHT]:
                pacman.desired_direction = pygame.math.Vector2(1, 0)
            elif keys[pygame.K_UP]:
                pacman.desired_direction = pygame.math.Vector2(0, -1)
            elif keys[pygame.K_DOWN]:
                pacman.desired_direction = pygame.math.Vector2(0, 1)
            
            pacman.update(dt)
        
        # Dessiner
        screen.fill(settings.BACKGROUND_COLOUR)
        maze.draw(screen)
        pacman.draw(screen)
        
        # Instructions
        font = pygame.font.Font(None, 24)
        instructions = [
            "M: Changer motif",
            "D: Désactiver",
            "ESPACE: Pause",
            "ESC: Quitter",
        ]
        y = 10
        for text in instructions:
            surf = font.render(text, True, settings.WHITE)
            screen.blit(surf, (10, y))
            y += 25
        
        # Afficher le motif actuel
        pattern_text = font.render(
            f"Motif: {patterns[pattern_index]}",
            True,
            settings.AMBER,
        )
        screen.blit(pattern_text, (settings.SCREEN_WIDTH - 150, 10))
        
        pygame.display.flip()
    
    pygame.quit()
    print("✅ Démo terminée")


def demo_adaptive_difficulty():
    """Démo de la difficulté adaptative."""
    print("🎯 Démo : Difficulté Adaptative")
    print("=" * 50)
    
    manager = DifficultyManager(adaptation_speed=0.2)
    
    print("\n📊 Simulation de 20 parties...")
    print()
    
    # Simuler des parties
    for i in range(1, 21):
        # Simuler les performances (amélioration progressive)
        base_score = 500 + i * 50
        won = i > 5 and (i % 3 != 0)  # Gagner après 5 parties, sauf 1/3
        
        score = base_score if won else base_score // 2
        pellets = 50 + i * 2
        ghosts = (i // 5) if won else 0
        time_played = 60.0 + i * 5
        died = not won
        
        manager.update_after_game(
            score=score,
            pellets=pellets,
            ghosts=ghosts,
            died=died,
            time_played=time_played,
            won=won,
        )
        
        # Afficher les stats tous les 5 parties
        if i % 5 == 0:
            stats = manager.get_stats_summary()
            print(f"\n📈 Après {i} parties:")
            print(f"  Score moyen: {stats['average_score']:.0f}")
            print(f"  Win rate: {stats['win_rate']*100:.1f}%")
            print(f"  Vitesse fantômes: {stats['ghost_speed']:.2f}x")
            print(f"  Intelligence: {stats['ghost_intelligence']*100:.0f}%")
            print(f"  Win streak: {stats['win_streak']}")
            print(f"  Loss streak: {stats['loss_streak']}")
    
    print("\n✅ Simulation terminée")
    print(f"\n📊 Statistiques finales:")
    stats = manager.get_stats_summary()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Menu principal."""
    print("\n" + "=" * 50)
    print("🤖 DÉMONSTRATIONS MODULE RL")
    print("=" * 50)
    print()
    print("Choisissez une démo:")
    print("1. Labyrinthe Dynamique (interactif)")
    print("2. Difficulté Adaptative (simulation)")
    print("3. Quitter")
    print()
    
    choice = input("Votre choix (1-3): ").strip()
    
    if choice == "1":
        demo_dynamic_maze()
    elif choice == "2":
        demo_adaptive_difficulty()
    elif choice == "3":
        print("👋 Au revoir!")
    else:
        print("❌ Choix invalide")


if __name__ == "__main__":
    main()
