#!/usr/bin/env python3
"""vPet simulator: render the app UI to a pygame window.

This is a standalone simulator that does NOT use displayio — it renders
the same UI layout using pure pygame, reading the same BMPs. Goal is to
let you preview the screen on the Mac without flashing the Pico.

It's not 1:1 with the real app (no state machine, no real pet), but it
shows the same visual: background + sprite + bars + buttons + selection
ring, and reacts to the same keyboard keys.

Install:
    /usr/bin/python3 -m pip install --user pygame pillow

Run:
    make sim
"""
import argparse
import os
import sys
import time
from pathlib import Path

import pygame
from PIL import Image

ROOT = Path(__file__).parent.parent
BUILD = ROOT / "build"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--scale", type=int, default=4, help="window scale (default 4 → 512x512)")
    p.add_argument("--record", type=str, default=None, help="output dir for PNG frames")
    p.add_argument("--pet", choices=["egg", "baby", "rookie", "champion", "ultimate", "mega"],
                   default="egg", help="which digimon to show")
    return p.parse_args()


def load_bmp_pygame(path):
    """Load a BMP and return a pygame.Surface with per-pixel alpha."""
    img = Image.open(path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return pygame.image.fromstring(img.tobytes(), img.size, "RGBA")


def make_solid_surface(w, h, rgb, transparent=False):
    surf = pygame.Surface((w, h), pygame.SRCALPHA if transparent else 0)
    if not transparent:
        surf.fill(rgb)
    return surf


def main():
    args = parse_args()
    if args.record:
        Path(args.record).mkdir(parents=True, exist_ok=True)

    SCALE = args.scale
    WIN_W, WIN_H = 128 * SCALE, 128 * SCALE

    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption(f"vPet simulator [{args.pet}] — n=NEXT, a=ACTION, q=quit")

    # Build the 128x128 framebuffer
    fb = pygame.Surface((128, 128))

    # Load assets
    bg = load_bmp_pygame(BUILD / "Background" / "jungle.bmp")
    sprite = load_bmp_pygame(BUILD / "digimon1" / args.pet.capitalize() / "hatch_atlas.bmp")
    # sprite is 256x64 (4 frames of 64x64) for egg, or 320x64 (5 frames) for others
    sprite_w, sprite_h = sprite.get_size()
    n_frames = sprite_w // 64
    sprite_frame = 0

    # Bar colors (must match src/core/pet.py STAT_COLORS)
    BAR_COLORS = {
        "h": 0xff5050,  # health (placeholder, real value from pet.py)
        "s": 0x50ff50,
        "a": 0x5050ff,
        "e": 0xffff50,
    }
    BAR_VALUES = [80, 60, 90, 50]  # mock stat values

    BTN_COLORS = [0xf0b41e, 0xd03030, 0x32c850, 0x2850a0]
    BTN_LABELS = ["F", "H", "P", "E"]
    BTN_X = [8 + i * 29 for i in range(4)]
    BTN_Y = 92

    # Selection ring surface (24x24, white border, transparent inside)
    ring = pygame.Surface((24, 24), pygame.SRCALPHA)
    pygame.draw.rect(ring, (255, 255, 255), ring.get_rect(), 1)

    menu_idx = 0
    last_idle = time.monotonic()
    running = True
    frame = 0

    print(f"vPet simulator running. Window: {WIN_W}x{WIN_H}px")
    print("Keys: n = NEXT, a = ACTION, q/ESC = quit")

    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif ev.key == pygame.K_n:
                    menu_idx = (menu_idx + 1) % 4
                elif ev.key == pygame.K_a:
                    BAR_VALUES[menu_idx] = min(100, BAR_VALUES[menu_idx] + 10)
                elif ev.key == pygame.K_r:
                    BAR_VALUES = [80, 60, 90, 50]
                elif ev.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                pygame.K_5, pygame.K_6):
                    args.pet = ["egg", "baby", "rookie", "champion", "ultimate", "mega"][ev.key - pygame.K_1]
                    sprite = load_bmp_pygame(BUILD / "digimon1" / args.pet.capitalize() / "hatch_atlas.bmp")
                    n_frames = sprite.get_size()[0] // 64
                    sprite_frame = 0
                    pygame.display.set_caption(f"vPet simulator [{args.pet}] — n=NEXT, a=ACTION, q=quit")

        # Render
        fb.blit(bg, (0, 0))

        # Sprite (one frame at a time, animated)
        now = time.monotonic()
        if now - last_idle > 0.15:
            sprite_frame = (sprite_frame + 1) % n_frames
            last_idle = now
        fb.blit(sprite, (32, 4), area=pygame.Rect(sprite_frame * 64, 0, 64, 64))

        # 4 stat bars
        for i in range(4):
            x = 6 + i * 29
            y = 78
            # empty bar (dark gray)
            pygame.draw.rect(fb, (40, 40, 40), (x, y, 26, 5))
            # filled portion
            color = list(BAR_COLORS.values())[i]
            w = int(26 * BAR_VALUES[i] / 100)
            if w > 0:
                pygame.draw.rect(fb, color, (x, y, w, 5))

        # 4 buttons
        for i in range(4):
            x, y, color, label = BTN_X[i], BTN_Y, BTN_COLORS[i], BTN_LABELS[i]
            # background square
            pygame.draw.rect(fb, color, (x, y, 24, 24))
            # letter label (centered)
            font = pygame.font.SysFont("monospace", 14, bold=True)
            text = font.render(label, True, (0, 0, 0))
            text_rect = text.get_rect(center=(x + 12, y + 12))
            fb.blit(text, text_rect)

        # Selection ring on selected button
        fb.blit(ring, (BTN_X[menu_idx], BTN_Y))

        # Scale to window
        scaled = pygame.transform.scale(fb, (WIN_W, WIN_H))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        if args.record:
            pygame.image.save(screen, f"{args.record}/frame_{frame:05d}.png")
            frame += 1

        time.sleep(0.05)

    pygame.quit()


if __name__ == "__main__":
    main()
