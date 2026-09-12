"""vPet application entrypoint for CircuitPython."""
import time

import displayio

import hal
from config import (
    BACKGROUND_PATH,
    BACKGROUND_NIGHT_PATH,
    DISPLAY_WIDTH,
    DRAGFIREMON_CAST_IMAGE_PATH,
    DRAGFIREMON_EAT_IMAGE_PATH,
    DRAGFIREMON_EVOLUTION_THUMB_PATH,
    DRAGFIREMON_FLY_FRAME_COUNT,
    DRAGFIREMON_FLY_IMAGE_PATH,
    DRAGFIREMON_IDLE_FRAME_COUNT,
    DRAGFIREMON_IDLE_IMAGE_PATH,
    DRAGFIREMON_PUNCH_IMAGE_PATH,
    DRAGFIREMON_SLEEP_IMAGE_PATH,
    EVOLUTION_DRAGFIREMON_THUMB_X,
    EVOLUTION_FIREMON_THUMB_X,
    EVOLUTION_FLAMEMON_THUMB_X,
    EVOLUTION_THUMB_SIZE,
    EVOLUTION_THUMB_Y,
    EVOLVED_SPECIES,
    EVOLUTION_REGISTRY,
    FLAMEMON_CAST_IMAGE_PATH,
    FLAMEMON_EAT_IMAGE_PATH,
    FLAMEMON_EVOLUTION_IMAGE_PATH,
    FLAMEMON_EVOLUTION_THUMB_PATH,
    FLAMEMON_IDLE_FRAME_COUNT,
    FLAMEMON_IDLE_IMAGE_PATH,
    FLAMEMON_PUNCH_IMAGE_PATH,
    FLAMEMON_SLEEP_IMAGE_PATH,
    FLAMEMON_WALK_FRAME_COUNT,
    FLAMEMON_WALK_IMAGE_PATH,
    MENU_BAR_HEIGHT,
    MENU_ICON_PATHS,
    MENU_ICON_X,
    MENU_ICON_Y,
    MENU_INVENTORY_INDEX,
    MENU_OPTIONS_INDEX,
    MENU_PEDIA_INDEX,
    MENU_SELECTOR_COLOR,
    MENU_STATUS_INDEX,
    PET_CAST_FRAME_COUNT,
    PET_CAST_IMAGE_PATH,
    PET_EAT_FRAME_COUNT,
    PET_EAT_IMAGE_PATH,
    PET_EVOLUTION_FRAME_COUNT,
    PET_EVOLUTION_IMAGE_PATH,
    PET_EVOLUTION_SIZE,
    PET_EVOLUTION_X,
    PET_EVOLUTION_Y,
    PET_IDLE_FRAME_COUNT,
    PET_IDLE_IMAGE_PATH,
    PET_PUNCH_FRAME_COUNT,
    PET_PUNCH_IMAGE_PATH,
    PET_SLEEP_FRAME_COUNT,
    PET_SLEEP_IMAGE_PATH,
    PET_SIZE,
    PET_WALK_FRAME_COUNT,
    PET_WALK_IMAGE_PATH,
    PET_X,
    PET_Y,
    FIREMON_EVOLUTION_THUMB_PATH,
    SAVE_INTERVAL,
    ULTIMATE_SPECIES,
)
from core.evolution import Evolution
from core.device_services import DeviceServices
from core.inventory import (
    clamp_visible_inventory_index,
    next_visible_inventory_index,
    use_inventory_item,
)
from core.menu import activate_menu_item
from core.motion import (
    MOTION_CAST,
    MOTION_EAT,
    MOTION_EVOLUTION,
    MOTION_IDLE,
    MOTION_PUNCH,
    MOTION_SLEEP,
    MOTION_WALK,
    PetMotion,
)
from core.pet import Pet, STATE_LIVE
from core.options import OptionsSession
from core.save import load_pet, save_pet
from ui.sprites import load_bmp, make_tile_grid
from ui.status import (
    STATUS_COLORS,
    STATUS_HEIGHT,
    STATUS_WIDTH,
    draw_evolution_guide,
    draw_datetime_editor,
    draw_inventory,
    draw_options,
    draw_status,
)


def _make_menu_bar():
    bitmap = displayio.Bitmap(DISPLAY_WIDTH, MENU_BAR_HEIGHT, 1)
    palette = displayio.Palette(1)
    palette[0] = 0x000000
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=0, y=0)


def _make_menu_selector():
    bitmap = displayio.Bitmap(16, MENU_BAR_HEIGHT, 2)
    for x in range(16):
        bitmap[x, 0] = 1
        bitmap[x, MENU_BAR_HEIGHT - 1] = 1
    for y in range(MENU_BAR_HEIGHT):
        bitmap[0, y] = 1
        bitmap[15, y] = 1

    palette = displayio.Palette(2)
    palette[0] = 0x000000
    palette[1] = MENU_SELECTOR_COLOR
    palette.make_transparent(0)
    return displayio.TileGrid(bitmap, pixel_shader=palette, x=0, y=0)


def _make_panel(pet, draw_panel):
    bitmap = displayio.Bitmap(STATUS_WIDTH, STATUS_HEIGHT, len(STATUS_COLORS))
    palette = displayio.Palette(len(STATUS_COLORS))
    for index, color in enumerate(STATUS_COLORS):
        palette[index] = color
    draw_panel(bitmap, pet)
    return bitmap, displayio.TileGrid(
        bitmap,
        pixel_shader=palette,
        x=-STATUS_WIDTH,
        y=MENU_BAR_HEIGHT,
    )


def run():
    """Initialize hardware and run the vPet event loop forever."""
    display = hal.init_display()
    next_button, action_button = hal.init_buttons()

    pet = Pet(species="rookie", state=STATE_LIVE)
    load_pet(pet)

    group = displayio.Group()
    display.root_group = group

    background = load_bmp(BACKGROUND_PATH, transparent_index=None)
    background_grid = make_tile_grid(background, x=0, y=0)
    night_background = load_bmp(BACKGROUND_NIGHT_PATH, transparent_index=None)
    night_background_grid = make_tile_grid(night_background, x=-DISPLAY_WIDTH, y=0)
    group.append(background_grid)
    group.append(night_background_grid)
    group.append(_make_menu_bar())

    for index, path in enumerate(MENU_ICON_PATHS):
        icon = load_bmp(path, transparent_index=None)
        group.append(make_tile_grid(icon, x=MENU_ICON_X[index], y=MENU_ICON_Y))

    menu_selector = _make_menu_selector()
    group.append(menu_selector)

    idle_bitmap = load_bmp(PET_IDLE_IMAGE_PATH, transparent_index=0)
    idle_grid = make_tile_grid(
        idle_bitmap,
        x=PET_X,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    walk_bitmap = load_bmp(PET_WALK_IMAGE_PATH, transparent_index=0)
    walk_grid = make_tile_grid(
        walk_bitmap,
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    eat_bitmap = load_bmp(PET_EAT_IMAGE_PATH, transparent_index=0)
    eat_grid = make_tile_grid(
        eat_bitmap,
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    punch_bitmap = load_bmp(PET_PUNCH_IMAGE_PATH, transparent_index=0)
    punch_grid = make_tile_grid(
        punch_bitmap,
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    sleep_bitmap = load_bmp(PET_SLEEP_IMAGE_PATH, transparent_index=0)
    sleep_grid = make_tile_grid(
        sleep_bitmap,
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    cast_bitmap = load_bmp(PET_CAST_IMAGE_PATH, transparent_index=0)
    cast_grid = make_tile_grid(
        cast_bitmap,
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    evolution_bitmap = load_bmp(PET_EVOLUTION_IMAGE_PATH, transparent_index=0)
    evolution_grid = make_tile_grid(
        evolution_bitmap,
        x=-PET_EVOLUTION_SIZE,
        y=PET_EVOLUTION_Y,
        tile_width=PET_EVOLUTION_SIZE,
        tile_height=PET_EVOLUTION_SIZE,
    )
    flamemon_idle_bitmap = load_bmp(FLAMEMON_IDLE_IMAGE_PATH, transparent_index=0)
    flamemon_idle_grid = make_tile_grid(
        flamemon_idle_bitmap,
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    flamemon_walk_bitmap = load_bmp(FLAMEMON_WALK_IMAGE_PATH, transparent_index=0)
    flamemon_walk_grid = make_tile_grid(
        flamemon_walk_bitmap,
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    flamemon_eat_grid = make_tile_grid(
        load_bmp(FLAMEMON_EAT_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    flamemon_sleep_grid = make_tile_grid(
        load_bmp(FLAMEMON_SLEEP_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    flamemon_punch_grid = make_tile_grid(
        load_bmp(FLAMEMON_PUNCH_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    flamemon_cast_grid = make_tile_grid(
        load_bmp(FLAMEMON_CAST_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    flamemon_evolution_grid = make_tile_grid(
        load_bmp(FLAMEMON_EVOLUTION_IMAGE_PATH, transparent_index=0),
        x=-PET_EVOLUTION_SIZE,
        y=PET_EVOLUTION_Y,
        tile_width=PET_EVOLUTION_SIZE,
        tile_height=PET_EVOLUTION_SIZE,
    )
    dragfiremon_idle_grid = make_tile_grid(
        load_bmp(DRAGFIREMON_IDLE_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    dragfiremon_fly_grid = make_tile_grid(
        load_bmp(DRAGFIREMON_FLY_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    dragfiremon_eat_grid = make_tile_grid(
        load_bmp(DRAGFIREMON_EAT_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    dragfiremon_punch_grid = make_tile_grid(
        load_bmp(DRAGFIREMON_PUNCH_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    dragfiremon_sleep_grid = make_tile_grid(
        load_bmp(DRAGFIREMON_SLEEP_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    dragfiremon_cast_grid = make_tile_grid(
        load_bmp(DRAGFIREMON_CAST_IMAGE_PATH, transparent_index=0),
        x=-PET_SIZE,
        y=PET_Y,
        tile_width=PET_SIZE,
        tile_height=PET_SIZE,
    )
    group.append(evolution_grid)
    group.append(flamemon_evolution_grid)
    group.append(dragfiremon_cast_grid)
    group.append(dragfiremon_sleep_grid)
    group.append(dragfiremon_punch_grid)
    group.append(dragfiremon_eat_grid)
    group.append(dragfiremon_fly_grid)
    group.append(dragfiremon_idle_grid)
    group.append(flamemon_cast_grid)
    group.append(flamemon_sleep_grid)
    group.append(flamemon_punch_grid)
    group.append(flamemon_eat_grid)
    group.append(flamemon_walk_grid)
    group.append(flamemon_idle_grid)
    group.append(cast_grid)
    group.append(sleep_grid)
    group.append(punch_grid)
    group.append(eat_grid)
    group.append(walk_grid)
    group.append(idle_grid)

    panel_bitmap, panel_grid = _make_panel(pet, draw_status)
    group.append(panel_grid)
    firemon_thumb_grid = make_tile_grid(
        load_bmp(FIREMON_EVOLUTION_THUMB_PATH, transparent_index=0),
        x=-EVOLUTION_THUMB_SIZE,
        y=EVOLUTION_THUMB_Y,
    )
    flamemon_thumb_grid = make_tile_grid(
        load_bmp(FLAMEMON_EVOLUTION_THUMB_PATH, transparent_index=0),
        x=-EVOLUTION_THUMB_SIZE,
        y=EVOLUTION_THUMB_Y,
    )
    dragfiremon_thumb_grid = make_tile_grid(
        load_bmp(DRAGFIREMON_EVOLUTION_THUMB_PATH, transparent_index=0),
        x=-EVOLUTION_THUMB_SIZE,
        y=EVOLUTION_THUMB_Y,
    )
    group.append(firemon_thumb_grid)
    group.append(flamemon_thumb_grid)
    group.append(dragfiremon_thumb_grid)

    menu_index = 0
    panel_mode = None
    inventory_index = 0
    panel_snapshot = None
    now = time.monotonic()
    motion = PetMotion(now)
    evolution = Evolution(EVOLUTION_REGISTRY)
    services = DeviceServices()
    options_session = None
    last_save = now

    while True:
        if display.root_group is not group:
            display.root_group = group

        next_button.update()
        action_button.update()
        if next_button.fell:
            if panel_mode == "inventory":
                inventory_index = next_visible_inventory_index(pet, inventory_index)
            elif panel_mode == "status":
                inventory_index = 1 - inventory_index
            elif panel_mode == "options":
                options_session.next()
            else:
                panel_mode = None
                menu_index = (menu_index + 1) % len(MENU_ICON_PATHS)
                menu_selector.x = menu_index * 16
        if action_button.fell:
            if panel_mode == "inventory":
                inventory_index = clamp_visible_inventory_index(pet, inventory_index)
                result = use_inventory_item(pet, inventory_index)
                if result == "used":
                    inventory_index = clamp_visible_inventory_index(pet, inventory_index)
                if result == "back":
                    panel_mode = None
            elif panel_mode == "options":
                staying = options_session.action(pet, services)
                if options_session.message == "EVOLVED":
                    motion.start_evolution(time.monotonic())
                    panel_mode = None
                elif not staying:
                    panel_mode = None
            elif panel_mode is not None:
                panel_mode = None
            elif menu_index == MENU_STATUS_INDEX:
                panel_mode = "status"
                inventory_index = 0
            elif menu_index == MENU_INVENTORY_INDEX:
                panel_mode = "inventory"
                inventory_index = clamp_visible_inventory_index(pet, 0)
            elif menu_index == MENU_PEDIA_INDEX:
                panel_mode = "evolution"
            elif menu_index == MENU_OPTIONS_INDEX:
                options_session = OptionsSession()
                panel_mode = "options"
            else:
                activate_menu_item(pet, motion, menu_index, time.monotonic())

        pet.decay_if_due()
        now = time.monotonic()
        if motion.state == MOTION_IDLE and evolution.evolve(pet):
            motion.start_evolution(now)
        motion.update(now)
        sleeping = motion.state == MOTION_SLEEP
        background_grid.x = -DISPLAY_WIDTH if sleeping else 0
        night_background_grid.x = 0 if sleeping else -DISPLAY_WIDTH
        idle_grid.x = -PET_SIZE
        walk_grid.x = -PET_SIZE
        eat_grid.x = -PET_SIZE
        punch_grid.x = -PET_SIZE
        sleep_grid.x = -PET_SIZE
        cast_grid.x = -PET_SIZE
        flamemon_idle_grid.x = -PET_SIZE
        flamemon_walk_grid.x = -PET_SIZE
        flamemon_eat_grid.x = -PET_SIZE
        flamemon_punch_grid.x = -PET_SIZE
        flamemon_sleep_grid.x = -PET_SIZE
        flamemon_cast_grid.x = -PET_SIZE
        flamemon_evolution_grid.x = -PET_EVOLUTION_SIZE
        dragfiremon_idle_grid.x = -PET_SIZE
        dragfiremon_fly_grid.x = -PET_SIZE
        dragfiremon_eat_grid.x = -PET_SIZE
        dragfiremon_punch_grid.x = -PET_SIZE
        dragfiremon_sleep_grid.x = -PET_SIZE
        dragfiremon_cast_grid.x = -PET_SIZE
        evolution_grid.x = -PET_EVOLUTION_SIZE
        if motion.state == MOTION_EVOLUTION:
            active_grid = (
                flamemon_evolution_grid
                if pet.species == ULTIMATE_SPECIES
                else evolution_grid
            )
            active_frame_count = PET_EVOLUTION_FRAME_COUNT
        elif motion.state == MOTION_WALK:
            if pet.species == ULTIMATE_SPECIES:
                active_grid = dragfiremon_fly_grid
                active_frame_count = DRAGFIREMON_FLY_FRAME_COUNT
            elif pet.species == EVOLVED_SPECIES:
                active_grid = flamemon_walk_grid
                active_frame_count = FLAMEMON_WALK_FRAME_COUNT
            else:
                active_grid = walk_grid
                active_frame_count = PET_WALK_FRAME_COUNT
        elif motion.state == MOTION_EAT:
            active_grid = (
                dragfiremon_eat_grid
                if pet.species == ULTIMATE_SPECIES
                else flamemon_eat_grid if pet.species == EVOLVED_SPECIES else eat_grid
            )
            active_frame_count = PET_EAT_FRAME_COUNT
        elif motion.state == MOTION_PUNCH:
            active_grid = (
                dragfiremon_punch_grid
                if pet.species == ULTIMATE_SPECIES
                else flamemon_punch_grid if pet.species == EVOLVED_SPECIES else punch_grid
            )
            active_frame_count = PET_PUNCH_FRAME_COUNT
        elif motion.state == MOTION_SLEEP:
            active_grid = (
                dragfiremon_sleep_grid
                if pet.species == ULTIMATE_SPECIES
                else flamemon_sleep_grid if pet.species == EVOLVED_SPECIES else sleep_grid
            )
            active_frame_count = PET_SLEEP_FRAME_COUNT
        elif motion.state == MOTION_CAST:
            active_grid = (
                dragfiremon_cast_grid
                if pet.species == ULTIMATE_SPECIES
                else flamemon_cast_grid if pet.species == EVOLVED_SPECIES else cast_grid
            )
            active_frame_count = PET_CAST_FRAME_COUNT
        else:
            if pet.species == ULTIMATE_SPECIES:
                active_grid = dragfiremon_idle_grid
                active_frame_count = DRAGFIREMON_IDLE_FRAME_COUNT
            elif pet.species == EVOLVED_SPECIES:
                active_grid = flamemon_idle_grid
                active_frame_count = FLAMEMON_IDLE_FRAME_COUNT
            else:
                active_grid = idle_grid
                active_frame_count = PET_IDLE_FRAME_COUNT
        if motion.state == MOTION_EVOLUTION:
            active_grid.x = PET_EVOLUTION_X
            active_grid.flip_x = False
        else:
            active_grid.x = int(motion.x)
            active_grid.flip_x = motion.direction < 0
        active_grid[0] = motion.frame % active_frame_count
        panel_grid.x = 0 if panel_mode is not None else -STATUS_WIDTH
        firemon_thumb_grid.x = (
            EVOLUTION_FIREMON_THUMB_X if panel_mode == "evolution" else -EVOLUTION_THUMB_SIZE
        )
        flamemon_thumb_grid.x = (
            EVOLUTION_FLAMEMON_THUMB_X if panel_mode == "evolution" else -EVOLUTION_THUMB_SIZE
        )
        dragfiremon_thumb_grid.x = (
            EVOLUTION_DRAGFIREMON_THUMB_X
            if panel_mode == "evolution"
            else -EVOLUTION_THUMB_SIZE
        )
        if panel_mode == "status":
            next_snapshot = (
                "status",
                int(now),
                pet.species,
                pet.battles_won,
                pet.stats["hp"],
                pet.stats["h"],
                pet.stats["e"],
                pet.stats["p"],
            )
            if next_snapshot != panel_snapshot:
                draw_status(panel_bitmap, pet)
                panel_snapshot = next_snapshot
        elif panel_mode == "inventory":
            next_snapshot = (
                "inventory",
                inventory_index,
                pet.inventory.get("meat", 0),
                pet.inventory.get("energy", 0),
                pet.inventory.get("exp", 0),
                pet.inventory.get("ring", 0),
            )
            if next_snapshot != panel_snapshot:
                draw_inventory(panel_bitmap, pet, inventory_index)
                panel_snapshot = next_snapshot
        elif panel_mode == "evolution":
            next_snapshot = ("evolution", pet.species)
            if next_snapshot != panel_snapshot:
                draw_evolution_guide(panel_bitmap, pet)
                panel_snapshot = next_snapshot
        elif panel_mode == "options":
            current_datetime = services.get_datetime()
            next_snapshot = (
                "options",
                options_session.mode,
                options_session.index,
                options_session.field,
                tuple(options_session.values),
                options_session.bluetooth_status,
                options_session.message,
                pet.language,
                pet.sound_enabled,
                current_datetime,
            )
            if next_snapshot != panel_snapshot:
                if options_session.mode in ("date", "time"):
                    draw_datetime_editor(panel_bitmap, pet, options_session)
                else:
                    draw_options(panel_bitmap, pet, options_session, current_datetime)
                panel_snapshot = next_snapshot
        if now - last_save > SAVE_INTERVAL:
            save_pet(pet)
            last_save = now
        time.sleep(0.05)
