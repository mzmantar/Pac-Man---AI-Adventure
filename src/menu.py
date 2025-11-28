from __future__ import annotations

import math
from enum import Enum, auto
from typing import Tuple

import pygame

from . import settings


class MenuState(Enum):
    MAIN = auto()
    INSTRUCTIONS = auto()
    QUIT = auto()
    START_GAME = auto()


class Menu:
    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock) -> None:
        self.screen = screen
        self.clock = clock
        self.state = MenuState.MAIN
        self.selected_option = 0
        self.options = ["Jouer", "Instructions", "Quitter"]
        
        # Fonts
        self.title_font = pygame.font.SysFont("arialroundedmtbold", 72)
        self.option_font = pygame.font.SysFont("arialroundedmtbold", 36)
        self.text_font = pygame.font.SysFont("arialroundedmtbold", 24)
        self.small_font = pygame.font.SysFont("arialroundedmtbold", 20)
        
        # Animation
        self.animation_time = 0.0
        self.ghost_offset = 0

    def run(self) -> MenuState:
        """Run the menu loop and return the selected state."""
        running = True
        while running:
            dt = self.clock.tick(settings.FRAMES_PER_SECOND) / 1000.0
            self.animation_time += dt
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return MenuState.QUIT
                elif event.type == pygame.KEYDOWN:
                    if self.state == MenuState.MAIN:
                        if event.key == pygame.K_UP:
                            self.selected_option = (self.selected_option - 1) % len(self.options)
                        elif event.key == pygame.K_DOWN:
                            self.selected_option = (self.selected_option + 1) % len(self.options)
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            if self.selected_option == 0:  # Jouer
                                return MenuState.START_GAME
                            elif self.selected_option == 1:  # Instructions
                                self.state = MenuState.INSTRUCTIONS
                            elif self.selected_option == 2:  # Quitter
                                return MenuState.QUIT
                    elif self.state == MenuState.INSTRUCTIONS:
                        if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                            self.state = MenuState.MAIN
            
            if self.state == MenuState.MAIN:
                self.draw_main_menu()
            elif self.state == MenuState.INSTRUCTIONS:
                self.draw_instructions()
            
            pygame.display.flip()
        
        return MenuState.QUIT

    def draw_main_menu(self) -> None:
        """Draw the main menu screen."""
        # Background with gradient effect
        self.draw_enhanced_background()
        
        # Draw decorative border
        self.draw_border()
        
        # Title with glow effect and animation - centered and larger
        title_y = 100
        title_color = self.pulse_color(settings.AMBER, settings.FUCHSIA, 2.0)
        
        # Title shadow for depth
        shadow_offset = 5
        shadow = self.title_font.render("PAC-MAN", True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(settings.SCREEN_WIDTH // 2 + shadow_offset, title_y + shadow_offset))
        self.screen.blit(shadow, shadow_rect)
        
        # Main title with pulse
        title = self.title_font.render("PAC-MAN", True, title_color)
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, title_y))
        self.screen.blit(title, title_rect)
        
        # Animated decorative line under title
        line_y = title_y + 55
        line_width = 400
        line_x = settings.SCREEN_WIDTH // 2 - line_width // 2
        for i in range(5):
            alpha = 150 - i * 30
            thickness = max(1, 3 - i)
            color = (*settings.SKY_BLUE, alpha)
            line_surf = pygame.Surface((line_width, thickness), pygame.SRCALPHA)
            line_surf.fill(color)
            self.screen.blit(line_surf, (line_x, line_y + i * 2))
        
        # Subtitle with style
        subtitle_y = line_y + 30
        subtitle = self.text_font.render("~ AI Adventure Deluxe ~", True, settings.SKY_BLUE)
        subtitle_rect = subtitle.get_rect(center=(settings.SCREEN_WIDTH // 2, subtitle_y))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Animated ghosts with better positioning
        ghost_y = subtitle_y + 60
        # Draw ghosts at custom position
        ghost_colors = [settings.GHOST_RED, settings.GHOST_PINK, settings.GHOST_TEAL, settings.GHOST_ORANGE]
        center_x = settings.SCREEN_WIDTH // 2
        spacing = 100
        
        for i, color in enumerate(ghost_colors):
            x = center_x - (len(ghost_colors) - 1) * spacing // 2 + i * spacing
            y = ghost_y + int(12 * pygame.math.Vector2(1, 0).rotate(
                self.animation_time * 180 + i * 90
            ).y)
            self.draw_ghost(x, y, color)
        
        # Menu options with enhanced styling - more space
        start_y = ghost_y + 100
        option_spacing = 80
        
        for i, option in enumerate(self.options):
            if i == self.selected_option:
                # Selected option - draw box and glow
                box_width = 320
                box_height = 55
                box_x = settings.SCREEN_WIDTH // 2 - box_width // 2
                box_y = start_y + i * option_spacing - box_height // 2
                
                # Glow effect
                glow_surf = pygame.Surface((box_width + 20, box_height + 20), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*settings.AMBER, 40), 
                               glow_surf.get_rect(), border_radius=15)
                self.screen.blit(glow_surf, (box_x - 10, box_y - 10))
                
                # Box
                pygame.draw.rect(self.screen, settings.AMBER, 
                               (box_x, box_y, box_width, box_height), 3, border_radius=12)
                
                color = settings.AMBER
                prefix = "▶  "
                
                # Pulse size for selected
                scale = 1.0 + math.sin(self.animation_time * 5) * 0.05
                scaled_font = pygame.font.SysFont("arialroundedmtbold", int(36 * scale))
                text = scaled_font.render(prefix + option, True, color)
            else:
                color = settings.WHITE
                prefix = "   "
                font = self.option_font
                text = font.render(prefix + option, True, color)
            
            text_rect = text.get_rect(center=(settings.SCREEN_WIDTH // 2, start_y + i * option_spacing))
            self.screen.blit(text, text_rect)
        
        # Footer with icons - at bottom
        footer_y = settings.SCREEN_HEIGHT - 60
        footer = self.small_font.render("↑↓ Naviguer  •  ENTRÉE Sélectionner  •  ÉCHAP Quitter", True, settings.SKY_BLUE)
        footer_rect = footer.get_rect(center=(settings.SCREEN_WIDTH // 2, footer_y))
        
        # Footer background
        footer_bg = pygame.Surface((footer_rect.width + 40, footer_rect.height + 10), pygame.SRCALPHA)
        footer_bg.fill((*settings.NIGHT_BLUE, 120))
        self.screen.blit(footer_bg, (footer_rect.x - 20, footer_rect.y - 5))
        self.screen.blit(footer, footer_rect)
        
        # Score indicator
        score_text = self.small_font.render("Meilleur Score: 0", True, (200, 200, 200))
        self.screen.blit(score_text, (30, settings.SCREEN_HEIGHT - 40))

    def draw_instructions(self) -> None:
        """Draw the instructions screen."""
        self.draw_enhanced_background()
        self.draw_border()
        
        # Title with shadow - centered at top
        title_y = 50
        shadow = self.title_font.render("INSTRUCTIONS", True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(settings.SCREEN_WIDTH // 2 + 3, title_y + 3))
        self.screen.blit(shadow, shadow_rect)
        
        title = self.title_font.render("INSTRUCTIONS", True, settings.AMBER)
        title_rect = title.get_rect(center=(settings.SCREEN_WIDTH // 2, title_y))
        self.screen.blit(title, title_rect)
        
        # Decorative line
        line_y = title_y + 45
        line_width = 500
        line_x = settings.SCREEN_WIDTH // 2 - line_width // 2
        for i in range(3):
            alpha = 120 - i * 30
            thickness = max(1, 2 - i)
            color = (*settings.SKY_BLUE, alpha)
            line_surf = pygame.Surface((line_width, thickness), pygame.SRCALPHA)
            line_surf.fill(color)
            self.screen.blit(line_surf, (line_x, line_y + i * 2))
        
        # Content in two columns
        start_y = line_y + 40
        left_x = 80
        right_x = settings.SCREEN_WIDTH // 2 + 40
        current_y_left = start_y
        current_y_right = start_y
        line_spacing = 35
        
        # Left column - CONTRÔLES
        section_title = self.option_font.render("CONTRÔLES", True, settings.AMBER)
        self.screen.blit(section_title, (left_x, current_y_left))
        current_y_left += 50
        
        controls = [
            ("←→↑↓", "Déplacer Pac-Man"),
            ("C", "Activer/Désactiver l'IA"),
            ("Clic", "Définir une destination"),
            ("ÉCHAP", "Pause / Retour"),
        ]
        
        for key, desc in controls:
            # Key box
            key_surf = self.text_font.render(key, True, settings.AMBER)
            key_width = key_surf.get_width() + 20
            key_box = pygame.Surface((key_width, 30), pygame.SRCALPHA)
            pygame.draw.rect(key_box, (*settings.AMBER, 60), key_box.get_rect(), border_radius=5)
            pygame.draw.rect(key_box, settings.AMBER, key_box.get_rect(), 2, border_radius=5)
            self.screen.blit(key_box, (left_x, current_y_left - 5))
            self.screen.blit(key_surf, (left_x + 10, current_y_left))
            
            # Description
            desc_surf = self.text_font.render(desc, True, settings.WHITE)
            self.screen.blit(desc_surf, (left_x + key_width + 15, current_y_left))
            current_y_left += line_spacing
        
        current_y_left += 20
        
        # OBJECTIF section
        section_title = self.option_font.render("OBJECTIF", True, settings.AMBER)
        self.screen.blit(section_title, (left_x, current_y_left))
        current_y_left += 50
        
        objectives = [
            ("Mangez TOUS les fantômes!", settings.AMBER),
            ("Évitez les fantômes normaux", settings.WHITE),
            ("Gros points → fantômes bleus", settings.SKY_BLUE),
            ("Fantômes bleus = +200 points", settings.GREEN),
            ("Points se régénèrent", settings.CYAN),
        ]
        
        for text, color in objectives:
            bullet = self.text_font.render("●", True, color)
            self.screen.blit(bullet, (left_x, current_y_left))
            text_surf = self.text_font.render(text, True, color)
            self.screen.blit(text_surf, (left_x + 25, current_y_left))
            current_y_left += line_spacing
        
        # Right column - FANTÔMES
        section_title = self.option_font.render("FANTÔMES", True, settings.AMBER)
        self.screen.blit(section_title, (right_x, current_y_right))
        current_y_right += 50
        
        ghost_info = [
            ("Blinky", settings.GHOST_RED, "Agressif et rapide"),
            ("Pinky", settings.GHOST_PINK, "Embusque devant vous"),
            ("Inky", settings.GHOST_TEAL, "Imprévisible"),
            ("Clyde", settings.GHOST_ORANGE, "Timide mais rusé"),
        ]
        
        for name, color, desc in ghost_info:
            # Draw mini ghost
            ghost_y = current_y_right + 15
            self.draw_ghost(right_x + 15, ghost_y, color)
            
            # Ghost name and description
            name_surf = self.text_font.render(name, True, color)
            self.screen.blit(name_surf, (right_x + 45, current_y_right))
            
            desc_surf = self.small_font.render(desc, True, settings.WHITE)
            self.screen.blit(desc_surf, (right_x + 45, current_y_right + 22))
            
            current_y_right += 55
        
        current_y_right += 30
        
        # ASTUCES section
        section_title = self.option_font.render("ASTUCES", True, settings.AMBER)
        self.screen.blit(section_title, (right_x, current_y_right))
        current_y_right += 50
        
        tips = [
            "L'IA peut vous aider!",
            "Coins = refuges sûrs",
            "Planifiez votre route",
            "Mode bleu limité!",
        ]
        
        for tip in tips:
            bullet = self.text_font.render("💡", True, settings.AMBER)
            self.screen.blit(bullet, (right_x, current_y_right))
            text_surf = self.small_font.render(tip, True, settings.SKY_BLUE)
            self.screen.blit(text_surf, (right_x + 30, current_y_right))
            current_y_right += 32
        
        # Back instruction with style - at bottom
        footer_y = settings.SCREEN_HEIGHT - 50
        back_bg = pygame.Surface((600, 45), pygame.SRCALPHA)
        back_bg.fill((*settings.NIGHT_BLUE, 150))
        pygame.draw.rect(back_bg, settings.AMBER, back_bg.get_rect(), 2, border_radius=10)
        back_rect = back_bg.get_rect(center=(settings.SCREEN_WIDTH // 2, footer_y))
        self.screen.blit(back_bg, back_rect)
        
        back_text = self.text_font.render("▶ Appuyez sur ENTRÉE ou ÉCHAP pour revenir", True, settings.AMBER)
        back_text_rect = back_text.get_rect(center=(settings.SCREEN_WIDTH // 2, footer_y))
        self.screen.blit(back_text, back_text_rect)

    def draw_enhanced_background(self) -> None:
        """Draw enhanced animated background with gradient."""
        # Gradient background
        for y in range(settings.SCREEN_HEIGHT):
            progress = y / settings.SCREEN_HEIGHT
            color = (
                int(settings.NIGHT_BLUE[0] + (settings.BLACK[0] - settings.NIGHT_BLUE[0]) * progress),
                int(settings.NIGHT_BLUE[1] + (settings.BLACK[1] - settings.NIGHT_BLUE[1]) * progress),
                int(settings.NIGHT_BLUE[2] + (settings.BLACK[2] - settings.NIGHT_BLUE[2]) * progress),
            )
            pygame.draw.line(self.screen, color, (0, y), (settings.SCREEN_WIDTH, y))
        
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Animated particles
        for i in range(100):
            size = 12 + (i % 7) * 4
            alpha = 15 + (i * 2) % 50
            color = (*settings.SKY_BLUE, alpha)
            x = (i * 53 + int(self.animation_time * 25)) % settings.SCREEN_WIDTH
            y = (i * 97 + int(self.animation_time * 15)) % settings.SCREEN_HEIGHT
            pygame.draw.circle(overlay, color, (x, y), size, 1)
        
        # Add dots pattern
        dot_spacing = 40
        for x in range(0, settings.SCREEN_WIDTH, dot_spacing):
            for y in range(0, settings.SCREEN_HEIGHT, dot_spacing):
                offset_x = int(5 * math.sin(self.animation_time + x * 0.01))
                offset_y = int(5 * math.cos(self.animation_time + y * 0.01))
                pygame.draw.circle(overlay, (*settings.SKY_BLUE, 10), 
                                 (x + offset_x, y + offset_y), 2)
        
        self.screen.blit(overlay, (0, 0))
    
    def draw_border(self) -> None:
        """Draw decorative border around screen."""
        border_color = settings.SKY_BLUE
        border_width = 8
        
        # Outer glow
        for i in range(3):
            alpha = 50 - i * 15
            surf = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*border_color, alpha), 
                           surf.get_rect().inflate(-border_width * i, -border_width * i), 
                           border_width)
            self.screen.blit(surf, (0, 0))
        
        # Main border
        pygame.draw.rect(self.screen, border_color, 
                        self.screen.get_rect(), border_width, border_radius=10)
        
        # Corner decorations
        corner_size = 20
        corners = [
            (border_width, border_width),
            (settings.SCREEN_WIDTH - border_width - corner_size, border_width),
            (border_width, settings.SCREEN_HEIGHT - border_width - corner_size),
            (settings.SCREEN_WIDTH - border_width - corner_size, 
             settings.SCREEN_HEIGHT - border_width - corner_size),
        ]
        
        for corner in corners:
            pygame.draw.circle(self.screen, settings.AMBER, corner, 6)

    def draw_background(self) -> None:
        """Draw animated background."""
        self.screen.fill(settings.BACKGROUND_COLOUR)
        overlay = pygame.Surface((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Animated circles
        for i in range(80):
            size = 18 + (i % 5) * 6
            alpha = 20 + (i * 3) % 60
            color = (*settings.SKY_BLUE, alpha)
            x = (i * 47 + int(self.animation_time * 30)) % settings.SCREEN_WIDTH
            y = (i * 91 + int(self.animation_time * 20)) % settings.SCREEN_HEIGHT
            pygame.draw.circle(overlay, color, (x, y), size, 1)
        
        self.screen.blit(overlay, (0, 0))

    def draw_animated_ghosts_at(self, y_position: int) -> None:
        """Draw animated ghosts at specific y position."""
        ghost_colors = [settings.GHOST_RED, settings.GHOST_PINK, settings.GHOST_TEAL, settings.GHOST_ORANGE]
        center_x = settings.SCREEN_WIDTH // 2
        spacing = 100
        
        for i, color in enumerate(ghost_colors):
            # Calculate position with wave animation
            x = center_x - (len(ghost_colors) - 1) * spacing // 2 + i * spacing
            y = y_position + int(12 * pygame.math.Vector2(1, 0).rotate(
                self.animation_time * 180 + i * 90
            ).y)
            
            self.draw_ghost(x, y, color)

    def draw_ghost(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        """Draw a single ghost."""
        size = 32
        body = pygame.Surface((size, size), pygame.SRCALPHA)
        radius = size // 2 - 2
        
        # Body
        pygame.draw.circle(body, color, (size // 2, size // 2), radius)
        pygame.draw.rect(body, color, pygame.Rect(4, size // 2, size - 8, size // 2))
        
        # Wave bottom
        wave_height = size // 6
        for i in range(4):
            pygame.draw.circle(
                body,
                color,
                (4 + i * (size - 8) // 3, size - wave_height),
                wave_height,
            )
        
        # Eyes
        eye_direction = pygame.math.Vector2(
            math.cos(self.animation_time * 2),
            math.sin(self.animation_time * 2)
        ) * 2
        
        for offset_x in (-6, 6):
            eye_center = pygame.math.Vector2(size // 2 + offset_x, size // 3)
            pygame.draw.circle(body, settings.WHITE, eye_center, 4)
            pygame.draw.circle(
                body,
                settings.NIGHT_BLUE,
                eye_center + eye_direction,
                2,
            )
        
        rect = body.get_rect(center=(x, y))
        self.screen.blit(body, rect)

    def pulse_color(
        self, 
        color1: Tuple[int, int, int], 
        color2: Tuple[int, int, int], 
        speed: float
    ) -> Tuple[int, int, int]:
        """Interpolate between two colors based on time."""
        t = (math.sin(self.animation_time * speed) + 1) / 2
        return (
            int(color1[0] * (1 - t) + color2[0] * t),
            int(color1[1] * (1 - t) + color2[1] * t),
            int(color1[2] * (1 - t) + color2[2] * t),
        )
