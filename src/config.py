"""Visual and runtime configuration shared by the Pico and simulator."""

DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 128

BACKGROUND_PATH = "/Background/background.bmp"
BACKGROUND_NIGHT_PATH = "/Background/background_night.bmp"

MENU_BAR_HEIGHT = 16
MENU_CELL_SIZE = 16
MENU_ICON_SIZE = 14
MENU_ICON_Y = 1
MENU_SELECTOR_COLOR = 0xFFD700
MENU_ICON_PATHS = [
    "/UIIcons/Status.bmp",
    "/UIIcons/Feed.bmp",
    "/UIIcons/Training.bmp",
    "/UIIcons/Battle.bmp",
    "/UIIcons/Rest.bmp",
    "/UIIcons/Items.bmp",
    "/UIIcons/Pedia.bmp",
    "/UIIcons/Options.bmp",
]
MENU_ICON_X = [index * MENU_CELL_SIZE + 1 for index in range(8)]
MENU_STATUS_INDEX = 0
MENU_FEED_INDEX = 1
MENU_TRAINING_INDEX = 2
MENU_BATTLE_INDEX = 3
MENU_REST_INDEX = 4
MENU_INVENTORY_INDEX = 5
MENU_PEDIA_INDEX = 6
MENU_OPTIONS_INDEX = 7
MENU_ACTIONS = {1: 0, 2: 2, 4: 3}

CARE_TIME_SCALE = 600

EVOLUTION_REGISTRY = {
    "baby": {
        "evolves_to": "rookie",
        "automatic": True,
        "requirements_pending": False,
        "min_stage_age_seconds": 43800,
        "max_care_mistakes": 1,
        "battles_required": 0,
        "requirements": {},
    },
    "rookie": {
        "evolves_to": "champion",
        "automatic": True,
        "requirements_pending": False,
        "min_stage_age_seconds": 86400,
        "battles_required": 0,
        "requirements": {"h": 55, "e": 55, "p": 55, "hp": 75},
    },
    "champion": {
        "evolves_to": "ultimate",
        "automatic": True,
        "requirements_pending": False,
        "min_stage_age_seconds": 129600,
        "battles_required": 15,
        "requirements": {},
    },
}
EVOLVED_SPECIES = "champion"
ULTIMATE_SPECIES = "ultimate"
EGG_SPECIES = "egg"
BABY_SPECIES = "baby"
ROOKIE_SPECIES = "rookie"

EGG_IDLE_IMAGE_PATH = "/digimon1/Egg/egg_idle_atlas.bmp"
EGG_HATCH_IMAGE_PATH = "/digimon1/Egg/egg_hatch_atlas.bmp"
SPARKMON_IDLE_IMAGE_PATH = "/digimon1/Baby/sparkmon_idle_atlas.bmp"
SPARKMON_WALK_IMAGE_PATH = "/digimon1/Baby/sparkmon_walk_atlas.bmp"
SPARKMON_EAT_IMAGE_PATH = "/digimon1/Baby/sparkmon_eat_atlas.bmp"
SPARKMON_SLEEP_IMAGE_PATH = "/digimon1/Baby/sparkmon_sleep_atlas.bmp"
SPARKMON_EVOLUTION_IMAGE_PATH = "/digimon1/Baby/sparkmon_evolution_atlas.bmp"
EGG_IDLE_FRAME_COUNT = 16
EGG_HATCH_FRAME_COUNT = 10
SPARKMON_FRAME_COUNT = 25
SPARKMON_EVOLUTION_FRAME_COUNT = 16
HATCH_DURATION_SECONDS = 2
EGG_HATCH_DURATION_SECONDS = 0.8

PET_IDLE_IMAGE_PATH = "/digimon1/Rookie/firemon_idle_atlas.bmp"
PET_WALK_IMAGE_PATH = "/digimon1/Rookie/firemon_walk_atlas.bmp"
PET_EAT_IMAGE_PATH = "/digimon1/Rookie/firemon_eat_atlas.bmp"
PET_PUNCH_IMAGE_PATH = "/digimon1/Rookie/firemon_punch_atlas.bmp"
PET_SLEEP_IMAGE_PATH = "/digimon1/Rookie/firemon_sleep_atlas.bmp"
PET_CAST_IMAGE_PATH = "/digimon1/Rookie/firemon_cast_atlas.bmp"
PET_EVOLUTION_IMAGE_PATH = "/digimon1/Rookie/firemon_evolution_atlas.bmp"
FLAMEMON_IDLE_IMAGE_PATH = "/digimon1/Champion/flamemon_idle_atlas.bmp"
FLAMEMON_WALK_IMAGE_PATH = "/digimon1/Champion/flamemon_walk_atlas.bmp"
FLAMEMON_EAT_IMAGE_PATH = "/digimon1/Champion/flamemon_eat_atlas.bmp"
FLAMEMON_PUNCH_IMAGE_PATH = "/digimon1/Champion/flamemon_punch_atlas.bmp"
FLAMEMON_SLEEP_IMAGE_PATH = "/digimon1/Champion/flamemon_sleep_atlas.bmp"
FLAMEMON_CAST_IMAGE_PATH = "/digimon1/Champion/flamemon_cast_atlas.bmp"
FLAMEMON_EVOLUTION_IMAGE_PATH = "/digimon1/Champion/flamemon_evolution_atlas.bmp"
DRAGFIREMON_IDLE_IMAGE_PATH = "/digimon1/Ultimate/dragfiremon_idle_atlas.bmp"
DRAGFIREMON_FLY_IMAGE_PATH = "/digimon1/Ultimate/dragfiremon_fly_atlas.bmp"
DRAGFIREMON_EAT_IMAGE_PATH = "/digimon1/Ultimate/dragfiremon_eat_atlas.bmp"
DRAGFIREMON_PUNCH_IMAGE_PATH = "/digimon1/Ultimate/dragfiremon_punch_atlas.bmp"
DRAGFIREMON_SLEEP_IMAGE_PATH = "/digimon1/Ultimate/dragfiremon_sleep_atlas.bmp"
DRAGFIREMON_CAST_IMAGE_PATH = "/digimon1/Ultimate/dragfiremon_cast_atlas.bmp"
FIREMON_EVOLUTION_THUMB_PATH = "/UIEvolution/Firemon.bmp"
EGG_EVOLUTION_THUMB_PATH = "/UIEvolution/Egg.bmp"
SPARKMON_EVOLUTION_THUMB_PATH = "/UIEvolution/Sparkmon.bmp"
FLAMEMON_EVOLUTION_THUMB_PATH = "/UIEvolution/Flamemon.bmp"
DRAGFIREMON_EVOLUTION_THUMB_PATH = "/UIEvolution/Dragfiremon.bmp"
EVOLUTION_THUMB_SIZE = 32
EVOLUTION_FIREMON_THUMB_X = 5
EVOLUTION_FLAMEMON_THUMB_X = 48
EVOLUTION_DRAGFIREMON_THUMB_X = 91
EVOLUTION_THUMB_Y = 48
PET_X = 32
PET_Y = 46
PET_SIZE = 64
PET_IDLE_FRAME_COUNT = 19
PET_WALK_FRAME_COUNT = 22
PET_EAT_FRAME_COUNT = 25
PET_PUNCH_FRAME_COUNT = 15
PET_SLEEP_FRAME_COUNT = 15
PET_CAST_FRAME_COUNT = 15
PET_COMBAT_FRAME_COUNT = 15
PET_EVOLUTION_FRAME_COUNT = 15
FLAMEMON_IDLE_FRAME_COUNT = 15
FLAMEMON_WALK_FRAME_COUNT = 15
DRAGFIREMON_IDLE_FRAME_COUNT = 25
DRAGFIREMON_FLY_FRAME_COUNT = 25
DRAGFIREMON_SLEEP_FRAME_COUNT = 25
PET_IDLE_FRAME_INTERVAL = 0.12
PET_WALK_FRAME_INTERVAL = 0.09
PET_EAT_FRAME_INTERVAL = 0.10
PET_PUNCH_FRAME_INTERVAL = 0.08
PET_SLEEP_FRAME_INTERVAL = 0.14
PET_CAST_FRAME_INTERVAL = 0.09
PET_COMBAT_FRAME_INTERVAL = 0.09
PET_EVOLUTION_FRAME_INTERVAL = 0.12
FLAMEMON_IDLE_FRAME_INTERVAL = 0.12
FLAMEMON_WALK_FRAME_INTERVAL = 0.09
PET_EVOLUTION_SIZE = 112
PET_EVOLUTION_X = 8
PET_EVOLUTION_Y = MENU_BAR_HEIGHT
PET_MIN_X = 0
PET_MAX_X = DISPLAY_WIDTH - PET_SIZE
PET_WALK_SPEED = 13
PET_IDLE_DURATION_MS = (1500, 4500)
PET_WALK_DURATION_MS = (2000, 5000)

SAVE_INTERVAL = 30
