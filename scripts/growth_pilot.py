"""Reproducible offline growth experiment. Never loads a user's save."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from core.dna import COMBAT_STATS, legacy_combat_stat as combat_stat, iv_at
from core.growth_pilot import point
from core.practice import Fighter, PracticeBattle
from core.techniques import technique_stage

ROLES = ("rookie", "champion", "ultimate")
LOADOUTS = ((0, 1), (0, 1, 2), (0, 2, 3, 4))


def matrix_rows():
    for rank, role in enumerate(ROLES, 1):
        for iv in range(16):
            for ev in range(253):
                p = point(iv, ev, rank)
                legacy = combat_stat((iv, 0, 0, 1), {"hp": ev}, "hp", role)
                yield dict(p, legacy=legacy, delta=p["stat"] - legacy)


def audit_pet(pet):
    """Read-only comparison; no migration, rank fallback or DNA reroll."""
    rank = technique_stage(pet.species)
    if not rank:
        raise ValueError("Pilot only evaluates adult ranks")
    return [dict(point(iv_at(pet.dna, stat), pet.ev_at(stat), rank), name=stat,
                 legacy=combat_stat(pet.dna,pet.ev,stat,pet.species),
                 runtime=pet.combat_stat(stat)) for stat in COMBAT_STATS]


def sandbox_fighter(stats, equipped=(0, 1, 2, 3, 4)):
    """Host-only wider stats, explicitly bypassing the live Fighter clamp."""
    stats = tuple(stats)
    if len(stats) != 6 or any(type(v) is not int or not 1 <= v <= 320 for v in stats):
        raise ValueError("Invalid pilot fighter")
    fighter = Fighter(stats, equipped=equipped, element="fire")
    fighter.stats = stats
    fighter.hp = fighter.max_hp = 40 + 2 * stats[0]
    fighter.mp = fighter.max_mp = 10 + stats[1]
    return fighter


def run_battle(player_stats, rival_stats, equipped=(0, 1, 2, 3, 4), candidate=True):
    factory = sandbox_fighter if candidate else lambda stats, eq: Fighter(stats, equipped=eq, element="fire")
    player, rival = factory(player_stats, equipped), factory(rival_stats, equipped)
    battle = PracticeBattle(player, rival)
    trace = []
    while battle.step():
        trace.append([battle.round, player.hp, rival.hp, player.mp, rival.mp,
                      *[-1 if a is None else a for a in battle.actions], *battle.damage])
    return {"rounds": battle.round, "result": battle.result, "max_hp": player.max_hp,
            "max_mp": player.max_mp, "player_stats": list(player.stats),
            "rival_stats": list(rival.stats), "trace": trace,
            "scheduled_ms": 500 + (battle.round - 1) * 1450}


def battle_cases():
    for rank, role in enumerate(ROLES, 1):
        for iv in (0, 8, 10, 15):
            cap_ev = point(iv, 0, rank)["cap_ev"]
            for ev in (0, cap_ev // 2, cap_ev):
                for model in ("legacy", "pilot"):
                    value = (point(iv, ev, rank)["stat"] if model == "pilot" else
                             combat_stat((iv, 0, 0, 1), {"hp": ev}, "hp", role))
                    player = (value,) * 6
                    for match, rival in (("equal", player), ("fixed_arena", (25, 20, 24, 20, 22, 20)),
                                         ("stronger", (min(320 if model == "pilot" else 99, value * 2),) * 6)):
                        row = run_battle(player, rival, LOADOUTS[rank - 1], candidate=model == "pilot")
                        row.pop("trace")
                        yield dict(row, model=model, rank=rank, iv=iv, ev=ev, match=match)
    for model, maximum in (("legacy", 99), ("pilot", 320)):
        stats = (maximum, maximum, 1, maximum, 1, 1)
        row = run_battle(stats, stats, (0, 2), candidate=model == "pilot")
        row.pop("trace")
        yield dict(row, model=model, rank=3, iv=None, ev=None, match="defensive_extreme")


def training_budget(start, cap):
    # Ten seconds per attribute rep; recovery, menus and care are not modeled.
    reps = (max(0, cap - start) + 5) // 6
    return {"reps": reps, "energy": reps * 8, "active_ms": reps * 10000}


def item_probe():
    from core.adopted_items import BY_ID, use_combat_item
    boost = next(i for i, item in BY_ID.items() if item["category"] == "battle_boost"
                 and any(e["target"] == "off" for e in item["effects"]))
    fighter = sandbox_fighter((264,) * 6)
    stock = {boost: 2}
    before = fighter.stats[2]
    consumed = use_combat_item(fighter, stock, boost)
    recovery_ok = True
    for item_id, item in BY_ID.items():
        if item["category"] != "combat_recovery":
            continue
        target = sandbox_fighter((320,) * 6)
        target.hp = target.mp = 1
        units = {item_id: 1}
        use_combat_item(target, units, item_id)
        recovery_ok &= 1 <= target.hp <= target.max_hp and 1 <= target.mp <= target.max_mp
    return {"boost_item": boost, "before": before, "after": fighter.stats[2],
            "consumed": consumed, "boost_reduces_candidate": fighter.stats[2] < before,
            "recovery_stays_bounded": bool(recovery_ok)}


def build_report():
    rows = list(matrix_rows())
    battles = list(battle_cases())
    evolution_losses, maximum_jump, plateaus = 0, 0, 0
    for p in rows:
        if p["rank"] < 3:
            following = point(p["iv"], p["stored_ev"], p["rank"] + 1)["stat"]
            evolution_losses += following < p["stat"]
            maximum_jump = max(maximum_jump, following - p["stat"])
        if p["stored_ev"] < p["cap_ev"]:
            plateaus += point(p["iv"], p["stored_ev"] + 1, p["rank"])["stat"] == p["stat"]
    training = []
    for rank in (1, 2, 3):
        cap = point(0, 0, rank)["cap_ev"]
        previous = point(0, 0, rank - 1)["cap_ev"] if rank > 1 else 0
        zero = training_budget(0, cap)
        training.append({"rank": rank, "cap_ev": cap, "from_zero": zero,
                         "from_previous_cap": training_budget(previous, cap),
                         "all_six_from_zero": {k: v * 6 for k, v in zero.items()}})
    summary = []
    for model in ("legacy", "pilot"):
        for match in ("equal", "fixed_arena", "stronger", "defensive_extreme"):
            group = [b for b in battles if b["model"] == model and b["match"] == match]
            summary.append({"model": model, "match": match, "count": len(group),
                            "min_rounds": min(b["rounds"] for b in group),
                            "median_rounds": statistics.median(b["rounds"] for b in group),
                            "max_rounds": max(b["rounds"] for b in group),
                            "draws": sum(b["result"] == "EMPATE" for b in group)})
    sources = ("src/core/dna.py", "src/core/growth.py", "src/core/growth_pilot.py", "src/core/practice.py",
               "src/core/techniques.py", "src/core/adopted_items.py", "scripts/growth_pilot.py")
    return {"profile": "growth-200-8-v1", "activated": True,
            "activation_scope": "local-code-not-board",
            "assumptions": {"adult_ranks": 3, "iv_range": [0, 15], "ev_range": [0, 252],
                            "round_ms": 1450, "first_round_ms": 500,
                            "battle_limit": 30, "items_in_battles": False,
                            "wall_clock_training_measured": False,
                            "weight_and_care_penalties": False},
            "matrix": {"points": len(rows), "legacy_stat_losses": sum(p["delta"] < 0 for p in rows),
                       "evolution_losses": evolution_losses, "max_evolution_jump": maximum_jump,
                       "one_ev_plateaus": plateaus,
                       "above_99": sum(p["stat"] > 99 for p in rows),
                       "legacy_99": sum(p["legacy"] == 99 for p in rows)},
            "training": training, "item_probe": item_probe(),
            "battle_summary": summary, "battles": battles,
            "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}}


def write_report(destination):
    report = build_report()
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    for filename, rows in (("stats.csv", list(matrix_rows())), ("battles.csv", report["battles"])):
        with (destination / filename).open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "out/growth-pilot")
    args = parser.parse_args()
    result = write_report(args.out)
    print(json.dumps({"matrix": result["matrix"], "item_probe": result["item_probe"],
                      "battle_summary": result["battle_summary"]}, indent=2))
