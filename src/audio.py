"""Gestion audio (musique + effets) avec repli si fichiers manquants."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

import pygame

from . import settings


class AudioManager:
    """Charge et joue la musique/les effets. Tolère l'absence de fichiers."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir or Path(settings.SOUND_DIR))
        self.enabled = bool(settings.SOUND_ENABLED)
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_loaded = False
        self._mixer_ready = False
        self._init_mixer()
        if self.enabled and self._mixer_ready:
            self.load()

    def _init_mixer(self) -> None:
        if not self.enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self._mixer_ready = True
        except Exception as exc:  # pragma: no cover
            print(f"[Audio] Mixer init failed: {exc}")
            self.enabled = False
            self._mixer_ready = False

    def _resolve(self, filename: str) -> Path:
        return self.base_dir / filename

    def load(self) -> None:
        if not (self.enabled and self._mixer_ready):
            return

        mapping = {
            "pellet": settings.SOUND_PELLET,
            "power": settings.SOUND_POWER,
            "eat_ghost": settings.SOUND_EAT_GHOST,
            "death": settings.SOUND_DEATH,
            "win": settings.SOUND_WIN,
        }
        for key, fname in mapping.items():
            path = self._resolve(fname)
            if path.exists():
                try:
                    snd = pygame.mixer.Sound(str(path))
                    snd.set_volume(settings.SOUND_VOLUME)
                    self.sounds[key] = snd
                except Exception as exc:  # pragma: no cover
                    print(f"[Audio] Cannot load {path}: {exc}")

        music_path = self._resolve(settings.SOUND_MUSIC)
        if music_path.exists():
            try:
                pygame.mixer.music.load(str(music_path))
                pygame.mixer.music.set_volume(settings.MUSIC_VOLUME)
                self.music_loaded = True
            except Exception as exc:  # pragma: no cover
                print(f"[Audio] Cannot load music {music_path}: {exc}")

    def play_music(self, loop: bool = True) -> None:
        if not (self.enabled and self._mixer_ready and self.music_loaded):
            return
        loops = -1 if loop else 0
        try:
            pygame.mixer.music.play(loops)
        except Exception as exc:  # pragma: no cover
            print(f"[Audio] Music play failed: {exc}")

    def stop_music(self) -> None:
        if not (self.enabled and self._mixer_ready):
            return
        pygame.mixer.music.stop()

    def play(self, key: str) -> None:
        if not (self.enabled and self._mixer_ready):
            return
        snd = self.sounds.get(key)
        if snd:
            try:
                snd.play()
            except Exception as exc:  # pragma: no cover
                print(f"[Audio] Play failed for {key}: {exc}")

    def teardown(self) -> None:
        if pygame.mixer.get_init():
            pygame.mixer.quit()


def ensure_audio_manager() -> Optional[AudioManager]:
    """Helper pour créer un AudioManager en toute sécurité."""
    mgr = AudioManager()
    if not mgr.enabled:
        return None
    return mgr
