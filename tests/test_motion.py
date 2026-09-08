"""Deterministic checks for autonomous idle/walk movement."""
import importlib.util


class MinimumRandom:
    def randint(self, minimum, maximum):
        del maximum
        return minimum

    def choice(self, values):
        return values[-1]


def _motion_module():
    assert importlib.util.find_spec("core.motion") is not None
    from core import motion

    return motion


def test_motion_varies_from_idle_to_walk_and_back():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(now=0, random_source=MinimumRandom())
    starting_x = subject.x

    subject.update(1.49)
    assert subject.state == motion_module.MOTION_IDLE

    subject.update(1.5)
    assert subject.state == motion_module.MOTION_WALK
    assert subject.x == starting_x

    subject.update(2.5)
    assert subject.x > starting_x

    subject.update(3.5)
    assert subject.state == motion_module.MOTION_IDLE


def test_walking_pet_reverses_at_screen_edges():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(now=0, random_source=MinimumRandom())
    subject.state = motion_module.MOTION_WALK
    subject.state_until = 100
    subject.x = motion_module.PET_MAX_X - 0.5
    subject.direction = 1

    subject.update(1)
    assert subject.x == motion_module.PET_MAX_X
    assert subject.direction == -1

    subject.update(2)
    assert subject.x < motion_module.PET_MAX_X


def test_motion_uses_profile_specific_horizontal_bounds():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(
        now=0,
        random_source=MinimumRandom(),
        min_x=0,
        max_x=152,
        start_x=76,
    )
    subject.state = motion_module.MOTION_WALK
    subject.state_until = 100
    subject.x = 151.5
    subject.direction = 1

    subject.update(1)

    assert subject.x == 152
    assert subject.direction == -1


def test_eat_action_plays_once_then_returns_to_idle():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(now=0, random_source=MinimumRandom())

    subject.start_eat(0.5)
    assert subject.state == motion_module.MOTION_EAT
    assert subject.frame == 0

    subject.update(0.5 + (motion_module.PET_EAT_FRAME_COUNT - 1) * 0.1)
    assert subject.state == motion_module.MOTION_EAT
    assert subject.frame == motion_module.PET_EAT_FRAME_COUNT - 1

    subject.update(0.5 + motion_module.PET_EAT_FRAME_COUNT * 0.1)
    assert subject.state == motion_module.MOTION_IDLE
    assert subject.frame == 0


def test_punch_action_plays_once_then_returns_to_idle():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(now=0, random_source=MinimumRandom())

    subject.start_punch(0.5)
    assert subject.state == motion_module.MOTION_PUNCH

    subject.update(0.5 + motion_module.PET_PUNCH_FRAME_COUNT * 0.08)
    assert subject.state == motion_module.MOTION_IDLE
    assert subject.frame == 0


def test_sleep_action_plays_once_then_returns_to_idle():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(now=0, random_source=MinimumRandom())

    subject.start_sleep(0.5)
    assert subject.state == motion_module.MOTION_SLEEP

    subject.update(0.5 + motion_module.PET_SLEEP_FRAME_COUNT * 0.14)
    assert subject.state == motion_module.MOTION_IDLE
    assert subject.frame == 0


def test_cast_action_plays_once_then_returns_to_idle():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(now=0, random_source=MinimumRandom())

    subject.start_cast(0.5)
    assert subject.state == motion_module.MOTION_CAST

    subject.update(0.5 + motion_module.PET_CAST_FRAME_COUNT * 0.09)
    assert subject.state == motion_module.MOTION_IDLE
    assert subject.frame == 0


def test_evolution_plays_once_then_returns_to_idle():
    motion_module = _motion_module()
    subject = motion_module.PetMotion(now=0, random_source=MinimumRandom())

    subject.start_evolution(0.5)
    assert subject.state == motion_module.MOTION_EVOLUTION

    subject.update(0.5 + motion_module.PET_EVOLUTION_FRAME_COUNT * 0.12)
    assert subject.state == motion_module.MOTION_IDLE
    assert subject.frame == 0
