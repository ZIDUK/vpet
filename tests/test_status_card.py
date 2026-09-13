"""T-Display Status card: pet stays left, NEXT only pages the right fiche."""

from core.pet import Pet, STATE_LIVE
from core.status_card import (
    HELIX_HEIGHT,
    HELIX_RUNGS,
    HELIX_WIDTH,
    HELIX_Y,
    STATUS_CARD_H,
    STATUS_CARD_ROW,
    STATUS_CARD_Y,
    STATUS_PAGE_COUNT,
    STATUS_SPLIT_X,
    battle_rows,
    care_rows,
    dna_stat_rows,
    pin_pet_x,
    vital_rows,
)


def _pet(**kwargs):
    pet = Pet(species="rookie", state=STATE_LIVE)
    pet.stage_age_seconds = 12
    pet.overfeeds = 2
    pet.care_mistakes = 1
    pet.training_sessions = 8
    pet.battles_this_form = 3
    pet.weight = 7
    pet.dp = 2
    pet.protein = 1
    pet.battles_won = 4
    pet.battles_lost = 1
    pet.restore_dna((0x12, 0x34, 0x56, 0x78))
    pet.restore_ev({"hp": 24, "off": 12})
    for key, value in kwargs.items():
        setattr(pet, key, value)
    return pet


def test_status_keeps_four_pages_and_pins_pet_in_left_half():
    assert STATUS_PAGE_COUNT == 4
    assert STATUS_SPLIT_X == 100
    assert pin_pet_x(88) == 6


def test_status_cards_clear_the_title_bar():
    assert STATUS_CARD_Y >= 54
    assert STATUS_CARD_H == 24
    assert STATUS_CARD_ROW - STATUS_CARD_H >= 3


def test_helix_is_thin_and_clears_the_title():
    assert HELIX_Y >= 56
    assert HELIX_WIDTH <= 36
    assert HELIX_HEIGHT >= 74
    assert HELIX_RUNGS <= 6


def test_vital_page_is_three_care_bars():
    labels = [row[1] for row in vital_rows(_pet(), spanish=False)]
    assert labels == ["HP", "HUN", "ENE"]
    assert [row[1] for row in vital_rows(_pet(language="ES"), spanish=True)] == ["PV", "HAM", "ENE"]


def test_care_page_uses_one_clock_and_overfeed_label():
    rows = care_rows(_pet(), spanish=False, clock_text="09/12 19:56", call_text="")
    labels = [row[1] for row in rows]
    icons = [row[0] for row in rows]
    assert labels == ["AGE", "OF", "CM", "EFF", "BAT"]
    assert icons.count("Clock") == 1
    assert rows[0][2] == "12s"
    assert rows[0][3] == "09/12 19:56"
    assert rows[1][2] == 2
    call_rows = care_rows(_pet(), spanish=False, clock_text="09/12 19:56", call_text="CALL HUN")
    assert call_rows[0][3] == "CALL HUN"


def test_battle_page_does_not_reuse_the_sword_for_win_ratio():
    rows = battle_rows(_pet(), spanish=False)
    labels = [row[1] for row in rows]
    icons = [row[0] for row in rows]
    assert labels == ["WT", "DP", "WR", "PR", "W-L"]
    assert icons == ["Weight", "Battle", "Trophy", "Protein", "Versus"]
    assert icons[1] != icons[2]
    assert rows[2][2] == "80%"
    assert rows[3][2] == "1/7"
    empty = battle_rows(_pet(battles_won=0, battles_lost=0), spanish=False)
    assert empty[2][2] == "--"


def test_dna_rows_show_visible_stat_without_iv_ev_text():
    rows = dna_stat_rows(_pet())
    assert [row[0] for row in rows] == ["HP", "MP", "OFF", "DEF", "SPD", "BRN"]
    assert rows[0][1] == _pet().combat_stat("hp")
    assert all("IV" not in str(row) and "EV" not in str(row) for row in rows)
    assert dna_stat_rows(_pet(dna=[0, 0, 0, 0])) == []
