import pygame
from src.game import Game
from src.menu import Menu, MenuState


def main():
    """Main entry point with menu system."""
    pygame.init()
    screen = pygame.display.set_mode((672, 744))  # SCREEN_WIDTH x SCREEN_HEIGHT
    pygame.display.set_caption("Pac-Man Deluxe Edition")
    clock = pygame.time.Clock()
    
    while True:
        # Show menu
        menu = Menu(screen, clock)
        state = menu.run()
        
        if state == MenuState.QUIT:
            break
        elif state == MenuState.START_GAME:
            # Start the game
            game = Game.create()
            game.run()
            # After game ends, return to menu
    
    pygame.quit()


if __name__ == "__main__":
    main()

