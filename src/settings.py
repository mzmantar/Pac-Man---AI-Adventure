from __future__ import annotations

# Display --------------------------------------------------------------------
WINDOW_TITLE = "Pac-Man Deluxe"
FRAMES_PER_SECOND = 60

TILE_SIZE = 24
GRID_WIDTH = 28
GRID_HEIGHT = 31

SCREEN_WIDTH = GRID_WIDTH * TILE_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * TILE_SIZE

# Colours --------------------------------------------------------------------
BLACK = (6, 6, 20)
NIGHT_BLUE = (8, 12, 48)
SKY_BLUE = (64, 172, 255)
FUCHSIA = (255, 92, 196)
AMBER = (255, 198, 46)
GHOST_RED = (255, 84, 84)
GHOST_TEAL = (84, 237, 255)
GHOST_ORANGE = (255, 157, 74)
GHOST_PINK = (255, 146, 247)
WHITE = (240, 244, 255)

BACKGROUND_COLOUR = NIGHT_BLUE
MAZE_WALL_COLOUR = (22, 56, 180)
MAZE_BORDER_COLOUR = SKY_BLUE
PELLET_COLOUR = (255, 229, 153)
POWER_PELLET_COLOUR = WHITE

# Gameplay -------------------------------------------------------------------
PACMAN_SPEED = 5 * TILE_SIZE / 1.0
PACMAN_LIVES = 3
GHOST_SPEED = 4.2 * TILE_SIZE / 1.0
FRIGHTENED_SPEED = 3.2 * TILE_SIZE / 1.0
POWER_MODE_DURATION = 8  # seconds
RESPAWN_DELAY = 3  # seconds
