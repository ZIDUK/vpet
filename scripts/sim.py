#!/usr/bin/env python3
"""Run the vPet framebuffer in a scaled pygame window."""
import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
for import_root in (ROOT, SRC):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import pygame

from config import (
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    EVOLUTION_REGISTRY,
    MENU_ICON_PATHS,
    MENU_INVENTORY_INDEX,
    MENU_OPTIONS_INDEX,
    MENU_PEDIA_INDEX,
    MENU_STATUS_INDEX,
)
from display_profiles import get_display_profile
from core.evolution import Evolution
from core.inventory import INVENTORY_ENTRY_COUNT, use_inventory_item
from core.menu import activate_menu_item
from core.motion import MOTION_IDLE, PetMotion
from core.pet import Pet, STATE_LIVE
from core.options import OptionsSession
from scripts.sim_renderer import render_frame
from scripts.sim_services import SimulatorServices


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--record", type=str)
    parser.add_argument("--profile", choices=("tdisplay", "pico"), default="pico")
    parser.add_argument("--build-dir", type=str)
    parser.add_argument("--max-frames", type=int, help=argparse.SUPPRESS)
    return parser.parse_args()


def main():
    args = parse_args()
    profile = get_display_profile(args.profile)
    build_dir = Path(args.build_dir) if args.build_dir else ROOT / "build"
    record_dir = Path(args.record) if args.record else None
    if record_dir:
        record_dir.mkdir(parents=True, exist_ok=True)

    pygame.init()
    window_size = (profile.width * args.scale, profile.height * args.scale)
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("vPet simulator - n=NEXT, a=ACTION, b=BACK, e=EVOLVE")
    clock = pygame.time.Clock()

    pet = Pet(species="rookie", state=STATE_LIVE)
    menu_index = 0
    panel_mode = None
    inventory_index = 0
    motion_kwargs = {
        "min_x": 0,
        "max_x": profile.width - profile.pet_size,
        "start_x": (profile.width - profile.pet_size) / 2,
    }
    motion = PetMotion(pygame.time.get_ticks() / 1000, **motion_kwargs)
    evolution = Evolution(EVOLUTION_REGISTRY)
    services = SimulatorServices(ROOT)
    services.auto_connect()
    options_session = None
    frame_number = 0
    rendered_frames = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_n:
                    if panel_mode == "inventory":
                        inventory_index = (inventory_index + 1) % INVENTORY_ENTRY_COUNT
                    elif panel_mode == "evolution":
                        inventory_index = (inventory_index + 1) % 3
                    elif panel_mode == "options":
                        options_session.next()
                    else:
                        panel_mode = None
                        menu_index = (menu_index + 1) % len(MENU_ICON_PATHS)
                elif event.key == pygame.K_a and pet.is_live:
                    if panel_mode == "inventory":
                        if use_inventory_item(pet, inventory_index) == "back":
                            panel_mode = None
                    elif panel_mode == "options":
                        if not options_session.action(pet, services):
                            panel_mode = None
                    elif panel_mode is not None:
                        panel_mode = None
                    elif menu_index == MENU_STATUS_INDEX:
                        panel_mode = "status"
                    elif menu_index == MENU_INVENTORY_INDEX:
                        panel_mode = "inventory"
                        inventory_index = 0
                    elif menu_index == MENU_PEDIA_INDEX:
                        panel_mode = "evolution"
                    elif menu_index == MENU_OPTIONS_INDEX:
                        options_session = OptionsSession()
                        panel_mode = "options"
                    else:
                        activate_menu_item(
                            pet,
                            motion,
                            menu_index,
                            pygame.time.get_ticks() / 1000,
                        )
                elif event.key == pygame.K_e and pet.is_live:
                    if evolution.force(pet):
                        motion.start_evolution(pygame.time.get_ticks() / 1000)
                elif event.key == pygame.K_b:
                    panel_mode = None
                elif event.key == pygame.K_r:
                    pet = Pet(species="rookie", state=STATE_LIVE)
                    motion = PetMotion(pygame.time.get_ticks() / 1000, **motion_kwargs)
                    panel_mode = None
                    inventory_index = 0

        pet.decay_if_due()
        now = pygame.time.get_ticks() / 1000
        if motion.state == MOTION_IDLE and evolution.evolve(pet):
            motion.start_evolution(now)
        motion.update(now)
        frame = render_frame(
            build_dir,
            pet,
            menu_index,
            motion.frame,
            motion.state,
            motion.x,
            motion.direction,
            panel_mode == "status",
            panel_mode,
            inventory_index,
            options_session,
            services.get_datetime(),
            profile=profile,
        )
        surface = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
        scaled = pygame.transform.scale(surface, window_size)
        screen.blit(scaled, (0, 0))
        pygame.display.flip()

        if record_dir:
            frame.save(record_dir / f"frame_{frame_number:05d}.png")
            frame_number += 1
        rendered_frames += 1
        if args.max_frames and rendered_frames >= args.max_frames:
            running = False
        clock.tick(20)

    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
