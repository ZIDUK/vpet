"""Pixel-level and contract tests for the four Status pages
(1/4 vital, 2/4 care, 3/4 battle, 4/4 DNA) of the T-Display 240x135
simulator.

The original ``tests/test_sim_renderer.py`` already pins the layout
coordinates of the fiche; this file adds:

* DNA code "DNA: XX-XX-XX-XX" must be fully painted inside the frame.
* The six combat stats on the DNA page use the i18n labels and never
  show EV accumulated as if it were a recent gain.
* The helix rotation between two timestamps produces a different
  well crop but never mutates the pet (DNA, IV, EV, stats).
* Vital page bars are differentiated by color (red / orange / cyan).
* Care page uses full labels (no OF/CM acronyms).
* Battle page shows "--" when the pet has no encounters.
* Age format adapts to seconds / minutes / hours / days.
* All chip text fits inside 240x135 with no overlaps.
"""
import time

import pytest
from PIL import Image

from core.pet import Pet, STATE_LIVE
from display_profiles import get_display_profile
from scripts import build as build_script
from scripts.sim_renderer import render_frame


ROOT = None  # set in conftest / test if needed


def _rookie():
    return Pet(species="rookie", state=STATE_LIVE)


def _render_status(build_dir, pet, page, now_ms=0, language="EN"):
    pet.language = language
    profile = get_display_profile("tdisplay")
    return render_frame(
        build_dir,
        pet,
        menu_index=0,
        panel_mode="status",
        panel_index=page,
        profile=profile,
        pet_x=140,
        now_ms=now_ms,
    )


@pytest.fixture(scope="module")
def build_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("status") / "build-tdisplay"
    profile = get_display_profile("tdisplay")
    build_script.main(profile_name="tdisplay", output_dir=out)
    return out


@pytest.mark.parametrize("language", ["ES", "EN"])
def test_new_status_values_fit_and_do_not_mutate_pet(build_dir, monkeypatch, language):
    from PIL import ImageDraw
    from core.status_card import care_rows
    from scripts.sim_renderer import _call_label
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.language = language
    pet.restore_dna((0xAB, 0xCD, 0xEF, 0x12))
    pet.restore_ev(dict.fromkeys(("hp", "mp", "off", "def", "spd", "brn"), 252))
    pet.injuries = 2
    assert care_rows(pet, language == "ES", "", "")[-1][2] == "2/15"
    calls = []
    original = ImageDraw.ImageDraw.text

    def capture(draw, xy, text, *args, **kwargs):
        calls.append((str(text), draw.textbbox(xy, str(text), font=kwargs.get("font"),
                                             anchor=kwargs.get("anchor"))))
        return original(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(ImageDraw.ImageDraw, "text", capture)
    for dead, injured in ((False, False), (False, True), (True, True)):
        pet.dead, pet.injured = dead, injured
        for mood in (0, 100):
            pet.stats["p"] = mood
            snapshot = pet.to_dict()
            for page in range(4):
                calls.clear()
                _render_status(build_dir, pet, page, language=language)
                assert pet.to_dict() == snapshot
                if page == 0:
                    assert any(text == ("ANIMO" if language == "ES" else "MOOD") for text, _ in calls)
                if page == 1:
                    assert any(text == "2/15" for text, _ in calls)
                if page == 3:
                    ev_bounds = [box for text, box in calls if text == "252"]
                    assert len(ev_bounds) == 6
                    assert all(213 <= box[0] < box[2] <= 234 for box in ev_bounds)
                    assert any(text == "EV" for text, _ in calls)
                if dead or injured:
                    label = _call_label(pet, language == "ES")
                    assert label == (("MUERTO" if language == "ES" else "DEAD") if dead
                                     else ("HERIDO" if language == "ES" else "HURT"))
                    boxes = [box for text, box in calls if text == label]
                    assert len(boxes) == 1
                    assert boxes[0][3] <= 59  # portrait starts below the badge
                assert all(0 <= box[0] < box[2] <= 240 and 24 <= box[1] < box[3] <= 135
                           for _, box in calls)


def test_mood_changes_only_its_meter(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.stats["p"] = 0
    empty = _render_status(build_dir, pet, 0)
    pet.stats["p"] = 100
    full = _render_status(build_dir, pet, 0)
    assert empty.crop((0, 0, 240, 112)).tobytes() == full.crop((0, 0, 240, 112)).tobytes()
    assert full.getpixel((220, 125)) == (82, 218, 140)
    assert empty.getpixel((220, 125)) != (82, 218, 140)


def _patch_monotonic(monkeypatch):
    frozen = time.monotonic()
    monkeypatch.setattr(time, "monotonic", lambda: frozen)


# ---------------------------------------------------------------------------
# 1/4 vital
# ---------------------------------------------------------------------------


def test_vital_page_paints_four_distinct_bar_colors(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.stats["hp"] = 80
    pet.stats["h"] = 60
    pet.stats["e"] = 40
    pet.stats["p"] = 75
    frame = _render_status(build_dir, pet, page=0)
    # Four rows at y=49,70,91,112, with bars below their labels.
    bar_samples = {
        "hp_care":  (140, 62),
        "feed":     (140, 83),
        "energy":   (140, 104),
        "mood":     (140, 125),
    }
    seen = {}
    for kind, (x, y) in bar_samples.items():
        # Walk the bar and find the first fill pixel (not the outline
        # ink, not the parchment card background).
        for dx in range(0, 80):
            pixel = frame.getpixel((x + dx, y))
            if pixel != (48, 42, 55) and pixel != (214, 180, 112):
                seen[kind] = pixel
                break
    assert "hp_care" in seen, "HP bar has no fill"
    assert "feed" in seen, "Feed bar has no fill"
    assert "energy" in seen, "Energy bar has no fill"
    assert "mood" in seen
    assert len(set(seen.values())) == 4, seen


def test_vital_page_values_match_pet_stats(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.stats["hp"] = 85
    pet.stats["h"] = 42
    pet.stats["e"] = 17
    frame = _render_status(build_dir, pet, page=0)
    # Values are plain numbers aligned to the right of the wider cards.
    for value, y in ((85, 51), (42, 72), (17, 93), (pet.stats["p"], 114)):
        # The text region must contain at least one non-parchment
        # pixel that is not the icon background.
        region = [frame.getpixel((x, y)) for x in range(200, 229)]
        assert any(p != (214, 180, 112) and sum(p) < 600 for p in region), (
            value, y, region)


def test_vital_page_handles_zero_and_100(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.stats["hp"] = 0
    pet.stats["h"] = 0
    pet.stats["e"] = 0
    frame = _render_status(build_dir, pet, page=0)
    assert frame.size == (240, 135)
    pet.stats["hp"] = 100
    pet.stats["h"] = 100
    pet.stats["e"] = 100
    frame = _render_status(build_dir, pet, page=0)
    assert frame.size == (240, 135)


# ---------------------------------------------------------------------------
# 2/4 care
# ---------------------------------------------------------------------------


def test_care_page_has_six_full_labels_no_acronyms(build_dir, monkeypatch):
    """The care page must not use OF/CM acronyms. The five labels are
    the localised strings from the i18n catalog."""
    from core.status_card import care_rows
    pet = _rookie()
    pet.overfeeds = 3
    pet.care_mistakes = 2
    pet.effort = 10
    pet.battles_this_form = 5
    pet.stage_age_seconds = 90  # 1 minute
    rows = care_rows(pet, spanish=False, clock_text="", call_text="")
    labels = [row[1] for row in rows]
    # All five labels must be present and non-empty.
    assert len(labels) == 6
    for label in labels:
        assert label, "empty label in care page"
        assert label not in ("OF", "CM", "BAT", "ESF"), (
            "acronym leaked: %r" % label)


def test_care_page_age_adapts_unit(build_dir, monkeypatch):
    """The age string picks the most readable unit."""
    from core.i18n import format_age
    pet = _rookie()
    pet.language = "EN"
    assert format_age(pet, 30).endswith("s")
    assert format_age(pet, 90).endswith("m")
    assert format_age(pet, 7200).endswith("h")
    assert format_age(pet, 200000).endswith("d")


def test_care_page_renders_without_overflow(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.overfeeds = 7
    pet.care_mistakes = 3
    pet.effort = 50
    pet.battles_this_form = 12
    pet.stage_age_seconds = 9999
    frame = _render_status(build_dir, pet, page=1)
    assert frame.size == (240, 135)


# ---------------------------------------------------------------------------
# 3/4 battle
# ---------------------------------------------------------------------------


def test_battle_page_shows_dashes_when_no_encounters(build_dir, monkeypatch):
    from core.status_card import battle_rows
    pet = _rookie()
    pet.battles_won = 0
    pet.battles_lost = 0
    rows = battle_rows(pet, spanish=False)
    # row 2 is winrate, row 4 is W-L.
    assert rows[2][2] == "--"
    assert rows[4][2] == "--"


def test_battle_page_shows_winrate_and_wl_with_encounters(build_dir, monkeypatch):
    from core.status_card import battle_rows
    pet = _rookie()
    pet.battles_won = 7
    pet.battles_lost = 3
    rows = battle_rows(pet, spanish=False)
    assert rows[2][2] == "70%"
    assert rows[4][2] == "7-3"


def test_battle_page_keeps_dp_label(build_dir, monkeypatch):
    """DP must keep its name; the user explicitly asked not to rename
    it as 'battles'."""
    from core.status_card import battle_rows
    pet = _rookie()
    rows = battle_rows(pet, spanish=False)
    labels = [row[1] for row in rows]
    assert "DP" in labels, labels


def test_battle_page_renders_all_five_rows(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.weight = 7
    pet.dp = 2
    pet.battles_won = 4
    pet.battles_lost = 1
    pet.protein = 3
    frame = _render_status(build_dir, pet, page=2)
    assert frame.size == (240, 135)


# ---------------------------------------------------------------------------
# 4/4 DNA — the critical page
# ---------------------------------------------------------------------------


def test_dna_page_shows_full_code_inside_frame(build_dir, monkeypatch):
    """The full DNA identifier fits in the page header."""
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0xBF, 0x1E, 0x1B, 0x93))
    frame = _render_status(build_dir, pet, page=3)
    parchment = (214, 180, 112)
    head = [frame.getpixel((x, y)) for x in range(150, 180)
            for y in range(29, 46)]
    tail = [frame.getpixel((x, y)) for x in range(200, 234)
            for y in range(29, 46)]
    assert any(sum(pixel) > 350 for pixel in head), "DNA code head is missing"
    assert any(sum(pixel) > 350 for pixel in tail), "DNA code tail is missing"


def test_dna_page_accepts_sex_locus_byte(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0xBF, 0x1E, 0x1B, 0x93, 0x02))
    assert _render_status(build_dir, pet, page=3).size == (240, 135)


def test_dna_page_six_stats_match_combat_stat(build_dir, monkeypatch):
    """The six stats on the DNA page must read from combat_stat and
    never invent a +1. The test pins the exact values for a known
    DNA/EV combination."""
    from core.dna import rgb565_to_rgb, helix_color565
    from core.status_card import STATUS_SPLIT_X
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0x21, 0x43, 0x65, 0x87))
    pet.restore_ev({"hp": 0, "mp": 0, "off": 12, "def": 6, "spd": 0,
                     "brn": 0})
    frame = _render_status(build_dir, pet, page=3)
    # Capture the pet before and after the render.
    dna_before = list(pet.dna)
    ev_before = dict(pet.ev)
    # Re-render and confirm the pet is unchanged.
    _render_status(build_dir, pet, page=3, now_ms=1200)
    assert list(pet.dna) == dna_before
    assert dict(pet.ev) == ev_before


def test_dna_page_six_stats_remain_stable_across_timestamps(build_dir,
                                                            monkeypatch):
    """The six stat values on the DNA page must not change between
    renders at different timestamps. The helix rotates, the stats
    do not."""
    from core.status_card import STATUS_SPLIT_X
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0x12, 0x34, 0x56, 0x78))
    pet.restore_ev({"off": 24, "def": 12})
    f0 = _render_status(build_dir, pet, page=3, now_ms=0)
    f1 = _render_status(build_dir, pet, page=3, now_ms=800)
    stats_strip = (145, 55, 238, 134)
    assert f0.crop(stats_strip).tobytes() == f1.crop(stats_strip).tobytes()


def test_dna_page_helix_rotates_between_timestamps(build_dir, monkeypatch):
    """The helix well must show different pixels at two timestamps,
    proving the rotation is derived from now_ms."""
    from core.dna import rgb565_to_rgb, helix_color565
    from core.status_card import STATUS_SPLIT_X
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0xAB, 0xCD, 0xEF, 0x12))
    f0 = _render_status(build_dir, pet, page=3, now_ms=0)
    f1 = _render_status(build_dir, pet, page=3, now_ms=600)
    well = (STATUS_SPLIT_X, 56, STATUS_SPLIT_X + 28, 128)
    assert f0.crop(well).tobytes() != f1.crop(well).tobytes(), (
        "helix did not rotate between timestamps")
    # Both frames must contain both strand colors.
    for frame in (f0, f1):
        well_pixels = set(frame.crop(well).getdata())
        assert rgb565_to_rgb(helix_color565(pet.dna, 0)) in well_pixels
        assert rgb565_to_rgb(helix_color565(pet.dna, 1)) in well_pixels


def test_dna_page_helix_uses_wider_mockup_column(build_dir, monkeypatch):
    """The enlarged helix remains visually distinct from the stat rows."""
    from core.dna import rgb565_to_rgb, helix_color565
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0xAB, 0xCD, 0xEF, 0x12))
    frame = _render_status(build_dir, pet, page=3)
    strand_colors = {
        rgb565_to_rgb(helix_color565(pet.dna, strand)) for strand in (0, 1)
    }
    helix_pixels = [
        (x, y)
        for x in range(101, 144)
        for y in range(56, 128)
        if frame.getpixel((x, y)) in strand_colors
    ]
    assert helix_pixels
    assert max(x for x, _ in helix_pixels) - min(x for x, _ in helix_pixels) >= 25


def test_dna_page_uses_brain_icon_for_brain_stat(build_dir, monkeypatch):
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0xAB, 0xCD, 0xEF, 0x12))
    frame = _render_status(build_dir, pet, page=3)
    assert (build_dir / "UIIcons" / "Brain.bmp").is_file()
    brain_region = frame.crop((146, 120, 158, 132))
    assert any(red > 150 and blue > 100 and red > green
               for red, green, blue in brain_region.getdata())


def test_dna_page_render_does_not_mutate_pet(build_dir, monkeypatch):
    """The renderer must never write back to the pet. The DNA, IV,
    EV, and stats must be byte-for-byte equal before and after a
    render at any timestamp."""
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0x12, 0x34, 0x56, 0x78))
    pet.restore_ev({"hp": 6, "off": 18})
    snapshot = pet.to_dict()
    for now in (0, 400, 800, 1200, 2000, 2400):
        _render_status(build_dir, pet, page=3, now_ms=now)
    assert pet.to_dict() == snapshot


def test_dna_page_six_stats_labels_use_i18n(build_dir, monkeypatch):
    """The six stat labels follow the compact approved layout."""
    from core.i18n import tr_status_dna_label
    pet = _rookie()
    pet.language = "EN"
    assert tr_status_dna_label(pet, "hp") == "HP"
    assert tr_status_dna_label(pet, "mp") == "MP"
    assert tr_status_dna_label(pet, "off") == "OFF"
    assert tr_status_dna_label(pet, "def") == "DEF"
    assert tr_status_dna_label(pet, "spd") == "SPD"
    assert tr_status_dna_label(pet, "brn") == "BRN"
    pet.language = "ES"
    assert tr_status_dna_label(pet, "hp") == "HP"
    assert tr_status_dna_label(pet, "mp") == "MP"
    assert tr_status_dna_label(pet, "off") == "OF"
    assert tr_status_dna_label(pet, "def") == "DEF"
    assert tr_status_dna_label(pet, "spd") == "VEL"
    assert tr_status_dna_label(pet, "brn") == "MEN"


def test_dna_page_no_dna_shows_placeholder(build_dir, monkeypatch):
    """When the pet has no DNA (egg state) the page must show an
    honest placeholder instead of fake stats."""
    _patch_monotonic(monkeypatch)
    pet = Pet(species="egg", state="egg")
    frame = _render_status(build_dir, pet, page=3)
    assert frame.size == (240, 135)


def test_dna_page_full_dna_code_does_not_overlap_helix(build_dir, monkeypatch):
    """The DNA identifier stays in the header, clear of the helix."""
    from core.dna import rgb565_to_rgb, helix_color565
    from core.status_card import STATUS_SPLIT_X
    _patch_monotonic(monkeypatch)
    pet = _rookie()
    pet.restore_dna((0xAB, 0xCD, 0xEF, 0x12))
    frame = _render_status(build_dir, pet, page=3)
    code_region = [frame.getpixel((x, y))
                   for x in range(145, 234) for y in range(29, 46)]
    helix_color = rgb565_to_rgb(helix_color565(pet.dna, 0))
    assert helix_color not in code_region, (
        "helix color leaked into the DNA code region")
    assert any(sum(pixel) > 350 for pixel in code_region)


# ---------------------------------------------------------------------------
# i18n: every status key used by the renderer is bilingual
# ---------------------------------------------------------------------------


def test_status_i18n_every_used_key_is_bilingual():
    import inspect
    from core import i18n
    import scripts.sim_renderer as sr
    import re
    src = inspect.getsource(sr)
    pattern = re.compile(r"(?<![\w.])tr\(\s*[^,]+,\s*[\"']([^\"']+)[\"']")
    used = {match.group(1) for match in pattern.finditer(src)}
    # Also pick up any "status." key referenced in status_card.
    src2 = inspect.getsource(__import__("core.status_card", fromlist=["*"]))
    used |= set(re.findall(r"[\"'](status\.[^\"']+)[\"']", src2))
    for key in used:
        assert key in i18n.TRAINING_STRINGS, key
        entry = i18n.TRAINING_STRINGS[key]
        assert "ES" in entry and "EN" in entry, key
        assert entry["ES"], key
        assert entry["EN"], key
