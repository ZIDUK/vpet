from pathlib import Path

from scripts.practice_renderer import _practice_species_label, _species_atlas

ROOT = Path(__file__).resolve().parents[1]


def test_training_sprite_paths_follow_the_current_evolution():
    assert _species_atlas("champion", "idle").endswith(
        "/Champion/flamemon_idle_atlas.bmp"
    )
    assert _species_atlas("ultimate", "walk").endswith(
        "/Ultimate/dragfiremon_fly_atlas.bmp"
    )


def test_unsupported_action_uses_current_species_idle_sprite():
    assert _species_atlas("baby", "punch").endswith(
        "/Baby/sparkmon_idle_atlas.bmp"
    )


def test_battle_sprites_resolve_to_each_combat_evolution():
    expected = {
        "rookie": ("Rookie/firemon", "firemon_punch", "firemon_cast", "firemon_hit", "firemon_hurt"),
        "champion": ("Champion/flamemon", "flamemon_punch", "flamemon_cast", "flamemon_punch", "flamemon_hurt"),
        "ultimate": ("Ultimate/dragfiremon", "dragfiremon_punch", "dragfiremon_cast", "dragfiremon_punch", "dragfiremon_hurt"),
    }
    for species, (stage, punch, cast, hit, hurt) in expected.items():
        name = stage.split("/")[1]
        assert _species_atlas(species, "idle").endswith(f"/{name}_idle_atlas.bmp")
        assert _species_atlas(species, "punch").endswith(f"/{punch}_atlas.bmp")
        assert _species_atlas(species, "cast").endswith(f"/{cast}_atlas.bmp")
        assert _species_atlas(species, "hit").endswith(f"/{hit}_atlas.bmp")
        assert _species_atlas(species, "hurt").endswith(f"/{hurt}_atlas.bmp")


def test_outcome_reactions_follow_the_current_species():
    assert _species_atlas("rookie", "happy").endswith("/firemon_happy_atlas.bmp")
    assert _species_atlas("rookie", "sad").endswith("/firemon_sad_atlas.bmp")
    assert _species_atlas("champion", "happy").endswith("/flamemon_happy_atlas.bmp")
    assert _species_atlas("champion", "sad").endswith("/flamemon_sad_atlas.bmp")
    assert _species_atlas("ultimate", "happy").endswith("/dragfiremon_happy_atlas.bmp")
    assert _species_atlas("ultimate", "sad").endswith("/dragfiremon_sad_atlas.bmp")


def test_dragfiremon_guard_uses_its_own_block_animation():
    assert _species_atlas("ultimate", "block").endswith("/dragfiremon_block_atlas.bmp")


def test_flamemon_has_dedicated_guard_and_dodge():
    for action in ("block", "dodge", "hurt", "hit_react"):
        assert _species_atlas("champion", action).endswith(f"/flamemon_{action}_atlas.bmp")


def test_flamemon_received_hit_reaction_is_not_used_as_attacker_hit():
    assert _species_atlas("champion", "hit").endswith("/flamemon_punch_atlas.bmp")


def test_tdisplay_has_idle_punch_and_cast_assets_for_every_combat_evolution():
    assets = {
        "rookie": ("rookie", "firemon"),
        "champion": ("champion", "flamemon"),
        "ultimate": ("ultimate", "dragfiremon"),
    }
    for folder, name in assets.values():
        for action in ("idle", "punch", "cast"):
            path = ROOT / "firmware/t-display/data/animations" / folder / f"{name}_{action}.vpa"
            assert path.is_file(), f"Missing battle sprite: {path}"


def test_battle_header_names_follow_the_current_evolution():
    assert [_practice_species_label(species) for species in
            ("rookie", "champion", "ultimate")] == [
                "FIREMON", "FLAMEMON", "DRAGFIRE"]
