#!/usr/bin/env python3
"""Run the vPet framebuffer in a scaled pygame window."""
import argparse
import sys
import time
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
    EGG_HATCH_DURATION_SECONDS,
    EGG_HATCH_FRAME_COUNT,
    EGG_SPECIES,
    HATCH_DURATION_SECONDS,
    CARE_TIME_SCALE,
    EVOLUTION_REGISTRY,
    MENU_ICON_PATHS,
    MENU_INVENTORY_INDEX,
    MENU_OPTIONS_INDEX,
    MENU_PEDIA_INDEX,
    MENU_STATUS_INDEX,
    MENU_TRAINING_INDEX,
    MENU_BATTLE_INDEX,
    MENU_FEED_INDEX,
    MENU_REST_INDEX,
    ROOKIE_SPECIES,
    SPARKMON_EVOLUTION_FRAME_COUNT,
    TDISPLAY_MENU_ICON_PATHS,
)
from display_profiles import get_display_profile
from core.dna import STATUS_PAGE_COUNT
from core.evolution import (
    EVOLUTION_NODE_COUNT,
    Evolution,
    evolution_current_stage,
    evolution_hidden,
    evolution_tree_node,
)
from core.evolution_progress import next_detail_index
from scripts.exploration_session import ExplorationSession
from core.inventory import (
    clamp_visible_inventory_index,
    next_visible_inventory_index,
    use_inventory_item,
)
from core.menu import activate_menu_item, next_tdisplay_menu
from core.motion import MOTION_IDLE, MOTION_SLEEP, PetMotion
from core.pet import Pet
from core.options import OptionsSession
from scripts.sim_renderer import render_frame
from scripts.sim_services import SimulatorServices, clock_hour
from scripts.practice_session import PracticeSession
from scripts.practice_renderer import render_practice
from scripts.training_session import TrainingSession
from scripts.training_renderer import render_training


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scale", type=int, default=4)
    parser.add_argument("--record", type=str)
    parser.add_argument("--profile", choices=("tdisplay", "pico"), default="pico")
    parser.add_argument("--build-dir", type=str)
    parser.add_argument("--max-frames", type=int, help=argparse.SUPPRESS)
    preview = parser.add_mutually_exclusive_group()
    preview.add_argument("--practice", action="store_true", help="Start an isolated Firemon practice preview")
    preview.add_argument("--training", action="store_true", help="Start the isolated Firemon dumbbell preview")
    return parser.parse_args()


def main():
    args = parse_args()
    profile = get_display_profile(args.profile)
    menu_icons = TDISPLAY_MENU_ICON_PATHS if profile.name == "tdisplay" else MENU_ICON_PATHS
    explore_index = menu_icons.index("/UIIcons/Explore.bmp") if "/UIIcons/Explore.bmp" in menu_icons else None
    battle_index = menu_icons.index("/UIIcons/Battle.bmp")
    inventory_menu_index = menu_icons.index("/UIIcons/Backpack.bmp")
    pedia_index = menu_icons.index("/UIIcons/Pedia.bmp")
    options_index = menu_icons.index("/UIIcons/Options.bmp")
    rest_index = menu_icons.index("/UIIcons/Rest.bmp")
    legacy_menu = {
        menu_icons.index("/UIIcons/Feed.bmp"): MENU_FEED_INDEX,
        menu_icons.index("/UIIcons/Training.bmp"): MENU_TRAINING_INDEX,
        battle_index: MENU_BATTLE_INDEX,
        rest_index: MENU_REST_INDEX,
    }
    build_dir = Path(args.build_dir) if args.build_dir else ROOT / "build"
    record_dir = Path(args.record) if args.record else None
    if record_dir:
        record_dir.mkdir(parents=True, exist_ok=True)

    pygame.init()
    window_size = (profile.width * args.scale, profile.height * args.scale)
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("vPet simulator - n=NEXT, a=ACTION, b=BACK, e=EVOLVE")
    clock = pygame.time.Clock()

    pet = Pet()
    pet.start_hatch()
    menu_index = 0
    panel_mode = None
    inventory_index = 0
    motion_kwargs = {
        "min_x": 0,
        "max_x": profile.width - profile.pet_size,
        "start_x": (profile.width - profile.pet_size) / 2,
    }
    if profile.name == "tdisplay":
        from scripts.content_loader import definition_for
        motion_kwargs["definition"] = definition_for(build_dir)
    motion = PetMotion(pygame.time.get_ticks() / 1000, **motion_kwargs)
    evolution = Evolution(EVOLUTION_REGISTRY)
    services = SimulatorServices(ROOT)
    if profile.name == "tdisplay" and not (args.practice or args.training):
        if not services.start(pet):
            pygame.quit()
            raise RuntimeError("Simulator storage blocked; original save preserved")
    practice = None
    training = None
    exploration_menu = None
    if args.practice or args.training:
        if profile.name != "tdisplay":
            raise ValueError("Firemon previews require --profile tdisplay")
        pet.complete_hatch("rookie", entropy=12345)
        motion = PetMotion(pygame.time.get_ticks() / 1000, **motion_kwargs)
        # Preview saves are isolated from the ordinary simulator save.
        services.save_path = ROOT / "out" / "sim_practice_save.json"
        if not services.start(pet):
            pygame.quit()
            raise RuntimeError("Simulator preview storage blocked; original save preserved")
        if pet.species != "rookie":
            pet.complete_hatch("rookie", entropy=12345)
        if args.training:
            training = TrainingSession(pet, services.save)
            menu_index = MENU_TRAINING_INDEX
        else:
            practice = PracticeSession(pet, services.save)
            menu_index = battle_index
    options_session = None
    frame_number = 0
    rendered_frames = 0
    boot_started = time.monotonic() - (3 if args.practice or args.training else 0)

    running = True
    practice_keys = set()
    last_interaction_ms = pygame.time.get_ticks()
    last_sleep_tick_ms = last_interaction_ms
    if profile.name == "tdisplay" and pet.sleep.asleep:
        motion.start_sleep(last_sleep_tick_ms / 1000)
    while running:
        sleep_now_ms = pygame.time.get_ticks()
        sleep_elapsed_ms = sleep_now_ms - last_sleep_tick_ms
        last_sleep_tick_ms = sleep_now_ms
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYUP:
                practice_keys.discard(event.key)
            elif event.type == pygame.KEYDOWN:
                last_interaction_ms = pygame.time.get_ticks()
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key in practice_keys:
                    # Require release even when an activity has just returned to Home.
                    continue
                elif practice is not None or training is not None:
                    practice_keys.add(event.key)
                    command = {pygame.K_n: "next", pygame.K_a: "action", pygame.K_b: "back"}.get(event.key)
                    activity = training if training is not None else practice
                    accepted = activity.input(command, pygame.time.get_ticks()) if command else True
                    if command and not accepted:
                        # Return to the same home icon that opened the activity.
                        menu_index = MENU_TRAINING_INDEX if training is not None else battle_index
                        training = None
                        practice = None
                        pet.last_decay = time.monotonic()
                        motion = PetMotion(pygame.time.get_ticks() / 1000, **motion_kwargs)
                elif event.key == pygame.K_n:
                    if panel_mode == "inventory":
                        inventory_index = next_visible_inventory_index(pet, inventory_index)
                    elif panel_mode == "feeding":
                        inventory_index = (inventory_index + 1) % 3
                    elif panel_mode == "rest":
                        inventory_index = (inventory_index + 1) % 2
                    elif panel_mode == "status":
                        inventory_index = (inventory_index + 1) % STATUS_PAGE_COUNT
                    elif panel_mode == "evolution_detail" and profile.name == "tdisplay":
                        inventory_index = next_detail_index(pet, EVOLUTION_REGISTRY, inventory_index)
                    elif panel_mode in ("evolution", "evolution_detail"):
                        inventory_index = (inventory_index + 1) % EVOLUTION_NODE_COUNT
                    elif panel_mode == "explore" and exploration_menu is not None:
                        practice_keys.add(event.key)
                        exploration_menu.input("next")
                    elif panel_mode == "options":
                        options_session.next()
                    else:
                        panel_mode = None
                        menu_index = (next_tdisplay_menu(pet.species, menu_index)
                                      if profile.name == "tdisplay"
                                      else (menu_index + 1) % len(menu_icons))
                elif event.key == pygame.K_a and pet.is_live:
                    if profile.name == "tdisplay" and pet.sleep.asleep and panel_mode is None and menu_index == rest_index:
                        panel_mode = "rest"
                        inventory_index = 0
                        continue
                    if profile.name == "tdisplay" and pet.sleep.asleep and menu_index not in (MENU_STATUS_INDEX, options_index, pedia_index, rest_index):
                        continue
                    if getattr(pet,'cold',False) and menu_index not in (MENU_STATUS_INDEX, options_index):
                        continue
                    if pet.exploration.away and panel_mode not in ("explore", "status") and menu_index not in (explore_index, MENU_STATUS_INDEX):
                        exploration_menu = ExplorationSession(pet, services.save, services.exploration_time)
                        menu_index = explore_index
                        panel_mode = "explore"
                        practice_keys.add(event.key)
                        continue
                    if panel_mode == "feeding":
                        if inventory_index == 2:
                            panel_mode = None
                        else:
                            snapshot = pet.to_dict()
                            food = ("meat", "protein")[inventory_index]
                            result = pet.use_food(food, asleep=motion.state == MOTION_SLEEP)
                            if result["applied"]:
                                if services.save(pet):
                                    motion.start_eat(pygame.time.get_ticks() / 1000)
                                    panel_mode = None
                                else:
                                    pet.load_from_dict(snapshot)
                    elif panel_mode == "rest":
                        if inventory_index==1:
                            panel_mode=None
                        elif services.toggle_sleep(pet):
                            if pet.sleep.asleep: motion.start_sleep(pygame.time.get_ticks()/1000)
                            else: motion.wake(pygame.time.get_ticks()/1000)
                            panel_mode=None
                    elif panel_mode == "inventory":
                        inventory_index = clamp_visible_inventory_index(pet, inventory_index)
                        snapshot = pet.to_dict()
                        result = use_inventory_item(pet, inventory_index)
                        if result == "used":
                            if services.save(pet):
                                inventory_index = clamp_visible_inventory_index(pet, inventory_index)
                            else:
                                pet.load_from_dict(snapshot)
                        if result == "back":
                            panel_mode = None
                        elif result == "train" and motion.state != MOTION_SLEEP:
                            training = TrainingSession(pet, services.save)
                            panel_mode = None
                            practice_keys.add(event.key)
                    elif panel_mode == "evolution":
                        stage, dark = evolution_tree_node(inventory_index)
                        if not evolution_hidden(stage, dark, evolution_current_stage(pet)):
                            panel_mode = "evolution_detail"
                    elif panel_mode == "evolution_detail":
                        panel_mode = "evolution"
                        inventory_index %= EVOLUTION_NODE_COUNT
                    elif panel_mode == "explore" and exploration_menu is not None:
                        practice_keys.add(event.key)
                        was_away = pet.exploration.away
                        if not exploration_menu.input("action"):
                            panel_mode = None
                            exploration_menu = None
                        if pet.exploration.away != was_away:
                            motion = PetMotion(pygame.time.get_ticks() / 1000, **motion_kwargs)
                    elif panel_mode == "options":
                        staying = options_session.action(pet, services)
                        if options_session.message == "EVOLVED":
                            motion.start_evolution(
                                pygame.time.get_ticks() / 1000,
                                SPARKMON_EVOLUTION_FRAME_COUNT
                                if pet.species == ROOKIE_SPECIES
                                else None,
                            )
                            panel_mode = None
                        elif not staying:
                            panel_mode = None
                    elif panel_mode is not None:
                        panel_mode = None
                    elif menu_index == MENU_STATUS_INDEX:
                        panel_mode = "status"
                        inventory_index = 0
                    elif menu_index == inventory_menu_index:
                        panel_mode = "inventory"
                        inventory_index = clamp_visible_inventory_index(pet, 0)
                    elif menu_index == MENU_FEED_INDEX:
                        panel_mode = "feeding"
                        inventory_index = 0
                    elif menu_index == pedia_index:
                        panel_mode = "evolution"
                        inventory_index = evolution_current_stage(pet)
                    elif menu_index == options_index:
                        options_session = OptionsSession()
                        panel_mode = "options"
                    elif menu_index == rest_index and profile.name == "tdisplay":
                        panel_mode = "rest"
                        inventory_index = 0
                    elif menu_index == explore_index and profile.name == "tdisplay":
                        exploration_menu = ExplorationSession(pet, services.save, services.exploration_time)
                        panel_mode = "explore"
                        practice_keys.add(event.key)
                    elif menu_index == MENU_TRAINING_INDEX and profile.name == "tdisplay" and pet.species not in ("egg", "baby") and motion.state != MOTION_SLEEP:
                        training = TrainingSession(pet, services.save)
                        practice_keys.add(event.key)
                    elif menu_index == battle_index and profile.name == "tdisplay" and pet.species in ("rookie", "champion", "ultimate") and motion.state != MOTION_SLEEP and not pet.dead and not getattr(pet, "cold", False):
                        practice = PracticeSession(pet, services.save)
                        practice_keys.add(event.key)
                    else:
                        activate_menu_item(
                            pet,
                            motion,
                            legacy_menu.get(menu_index, menu_index),
                            pygame.time.get_ticks() / 1000,
                            hour=clock_hour(services.get_datetime()),
                        )
                elif event.key == pygame.K_e and pet.is_live and not pet.exploration.away and not pet.sleep.asleep:
                    if evolution.force(pet):
                        motion.start_evolution(
                            pygame.time.get_ticks() / 1000,
                            SPARKMON_EVOLUTION_FRAME_COUNT
                            if pet.species == ROOKIE_SPECIES
                            else None,
                        )
                elif event.key == pygame.K_b:
                    if panel_mode == "evolution_detail":
                        panel_mode = "evolution"
                        inventory_index %= EVOLUTION_NODE_COUNT
                    elif panel_mode == "explore" and exploration_menu is not None:
                        practice_keys.add(event.key)
                        if not exploration_menu.input("back"):
                            panel_mode = None
                            exploration_menu = None
                    else:
                        panel_mode = None
                        exploration_menu = None
                elif event.key == pygame.K_r:
                    pet = Pet()
                    pet.start_hatch()
                    motion = PetMotion(pygame.time.get_ticks() / 1000, **motion_kwargs)
                    panel_mode = None
                    inventory_index = 0

        boot_progress = min(1.0, (time.monotonic() - boot_started) / 2.2)
        if boot_progress < 1.0:
            from scripts.sim_renderer import render_boot_intro
            frame = render_boot_intro(boot_progress)
            surface = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
            scaled = pygame.transform.scale(surface, window_size)
            screen.blit(scaled, (0, 0))
            pygame.display.flip()
            rendered_frames += 1
            if args.record:
                frame.save(record_dir / f"frame_{frame_number:05d}.png")
                frame_number += 1
            if args.max_frames and rendered_frames >= args.max_frames:
                running = False
            clock.tick(20)
            continue

        now_ms = pygame.time.get_ticks()
        if practice is not None:
            practice.tick(now_ms)
        busy = ((training is not None and training.state == "session")
                or (practice is not None and practice.busy))
        if busy:
            last_interaction_ms = now_ms
        elif now_ms - last_interaction_ms >= 10000:
            if practice is not None or training is not None or panel_mode is not None:
                practice = training = options_session = exploration_menu = None
                panel_mode = None
                pet.last_decay = time.monotonic()
                motion = PetMotion(now_ms / 1000, **motion_kwargs)

        if practice is not None or training is not None:
            if training is not None:
                training.input(None, pygame.time.get_ticks())
            frame = (render_training(build_dir, training, pygame.time.get_ticks()) if training is not None
                     else render_practice(build_dir, practice, pygame.time.get_ticks()))
            surface = pygame.image.fromstring(frame.tobytes(), frame.size, frame.mode)
            screen.blit(pygame.transform.scale(surface, window_size), (0, 0))
            pygame.display.flip()
            if record_dir:
                frame.save(record_dir / f"frame_{frame_number:05d}.png")
                frame_number += 1
            rendered_frames += 1
            if args.max_frames and rendered_frames >= args.max_frames:
                running = False
            clock.tick(20)
            continue

        if profile.name == "tdisplay" and pet.sleep.asleep:
            if motion.state != MOTION_SLEEP:
                motion.start_sleep(now_ms / 1000)
            if pet.call_reason:
                pet.call_started_ms += sleep_elapsed_ms
            if services.advance_sleep(pet, sleep_elapsed_ms):
                motion.wake(now_ms / 1000)
        elif profile.name == "tdisplay" and motion.state == MOTION_SLEEP:
            motion.wake(now_ms / 1000)
        if not pet.exploration.away and not pet.sleep.asleep and not getattr(pet,'cold',False):
            pet.decay_if_due()
        else:
            pet.last_decay = time.monotonic()
        now = pygame.time.get_ticks() / 1000
        if pet.is_live and not pet.exploration.away and not pet.sleep.asleep and not getattr(pet,'cold',False):
            hour = clock_hour(services.get_datetime())
            pet.update_call(
                int(now * 1000),
                CARE_TIME_SCALE,
                hour,
                motion.state == MOTION_SLEEP,
                lights_enabled=profile.name != "tdisplay",
            )
        if getattr(pet,'cold',False):
            paused_seconds=sleep_elapsed_ms/1000
            pet.born_at+=paused_seconds
            if pet.hatch_started_at is not None: pet.hatch_started_at+=paused_seconds
            if pet.call_reason: pet.call_started_ms+=sleep_elapsed_ms
            motion.last_update=motion.last_frame=now
            motion.state_until+=paused_seconds
        if not getattr(pet,'cold',False) and pet.is_hatching and pet.hatch_progress(HATCH_DURATION_SECONDS) >= 1:
            pet.complete_hatch("baby")
            motion = PetMotion(now, **motion_kwargs)
        if not pet.exploration.away and motion.state == MOTION_IDLE and services.evolve_and_save(pet, evolution):
            motion.start_evolution(
                now,
                SPARKMON_EVOLUTION_FRAME_COUNT
                if pet.species == ROOKIE_SPECIES
                else None,
            )
        if profile.name == "tdisplay":
            dt = services.get_datetime()
            minute = dt[3]*60+dt[4] if dt and dt[0]>=2024 else None
            motion.set_tired(not pet.dead and not pet.injured and not getattr(pet,'cold',False) and
                             pet.sleep.tired(pet.stats['e'], pet.dna[3], minute), now)
        if profile.name == "tdisplay": motion.species = pet.species
        if not getattr(pet,'cold',False): motion.update(now)
        sprite_frame = motion.frame
        egg_motion = motion.state
        if pet.species == EGG_SPECIES and pet.hatch_started_at is not None:
            elapsed = max(0.0, time.monotonic() - pet.hatch_started_at)
            break_at = HATCH_DURATION_SECONDS - EGG_HATCH_DURATION_SECONDS
            if elapsed >= break_at:
                egg_motion = "hatch"
                sprite_frame = min(
                    EGG_HATCH_FRAME_COUNT - 1,
                    int((elapsed - break_at) / EGG_HATCH_DURATION_SECONDS * EGG_HATCH_FRAME_COUNT),
                )
        frame = render_frame(
            build_dir,
            pet,
            menu_index,
            sprite_frame,
            egg_motion,
            motion.x,
            motion.direction,
            panel_mode == "status",
            panel_mode,
            inventory_index,
            options_session,
            services.get_datetime(),
            profile=profile,
            now_ms=int(now * 1000),
            exploration_menu=exploration_menu,
            exploration_now=services.exploration_time(),
            evolution_scale=CARE_TIME_SCALE,
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
