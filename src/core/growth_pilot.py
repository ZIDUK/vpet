"""Unactivated growth candidate. No runtime model imports this module."""


def _integer(value, minimum, maximum, label):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("%s outside pilot profile" % label)


def _half_up(numerator, denominator):
    return (2 * numerator + denominator) // (2 * denominator)


def point(iv, ev, rank, ranks=3):
    """Evaluate one stat without consuming, clamping or rewriting stored EV."""
    _integer(ranks, 1, 3, "adult ranks")
    _integer(rank, 1, ranks, "rank")
    _integer(iv, 0, 15, "IV")
    _integer(ev, 0, 252, "EV")
    cap = _half_up((200 + 8 * iv) * rank, ranks)
    cap_ev = 6 * ((252 * rank) // (6 * ranks))
    base = _half_up((10 + 3 * iv) * (rank + 4), 5)
    active_ev = min(ev, cap_ev)
    return {"iv": iv, "rank": rank, "ranks": ranks, "base": base,
            "cap": cap, "cap_ev": cap_ev, "stored_ev": ev, "active_ev": active_ev,
            "headroom": max(0, cap_ev - ev),
            "stat": base + (cap - base) * active_ev // cap_ev}


def project_training(iv, ev, rank, requested=6, ranks=3):
    """Single attribute-rep projection, not a transaction or eligibility rule."""
    _integer(requested, 1, 252, "requested EV")
    before = point(iv, ev, rank, ranks)
    added = min(requested, before["headroom"])
    return {"before": before, "after": point(iv, ev + added, rank, ranks),
            "ev_added": added, "energy_cost": 8 if added else 0}
