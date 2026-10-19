import subprocess
from pathlib import Path

import pytest
from core.sleep import SleepRoutine

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'firmware/t-display/lib/vpet_core/src'


@pytest.fixture(scope='module')
def sleep_board(tmp_path_factory):
    binary = tmp_path_factory.mktemp('sleep-board') / 'board'
    subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra',
                    '-I'+str(ROOT/'tests/app_stubs'), '-I'+str(ROOT/'firmware/t-display/include'),
                    '-I'+str(CORE), str(ROOT/'tests/sleep_board.cpp'),
                    str(ROOT/'firmware/t-display/src/App.cpp'),
                    *[str(CORE/'vpet'/(name+'.cpp')) for name in
                      ('PetState','Nutrition','SettingsStore','PracticeBattle','Motion','Navigation','Evolution','DateTimeMenu')],
                    '-o', str(binary)], check=True, capture_output=True, text=True)
    return binary


def test_actual_app_sleep_reboot_rewards_and_legacy_storage(sleep_board):
    subprocess.run([str(sleep_board)], check=True)


def test_actual_app_pause_freezes_sleep_checkpoints(sleep_board):
    subprocess.run([str(sleep_board),'paused'], check=True)


def test_actual_app_rest_and_pause_menu_preserve_saved_pet_and_reserve(sleep_board):
    subprocess.run([str(sleep_board),'menus'], check=True)


@pytest.mark.parametrize('hour', [0, 6, 12, 18, 22, 23])
@pytest.mark.parametrize('trait', [0, 1, 2])
@pytest.mark.parametrize('milliseconds', [300001, 43200000])
def test_board_python_exact_sleep_parity(sleep_board, hour, trait, milliseconds):
    routine = SleepRoutine()
    energy, expected = 0, []
    for day in range(5):
        routine.start((20000+day)*86400+hour*3600,trait)
        energy, _, reward = routine.advance_ms(milliseconds, energy)
        expected.append(f'{routine.encode()} {energy} {int(reward)}')
        if routine.asleep:
            routine.stop()
    result = subprocess.check_output([str(sleep_board), str(hour), str(trait), str(milliseconds)], text=True)
    assert result.splitlines() == expected
