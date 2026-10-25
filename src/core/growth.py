"""Portable growth profile: adult ranks, per-gene potential and EV headroom."""
ADULT_RANKS = 3
MAX_STAT = 320
MAX_BATTLE_STAT = 448
ADULT_RANK_BY_ROLE = {"rookie": 1, "champion": 2, "ultimate": 3}


def adult_rank(species):
    return ADULT_RANK_BY_ROLE.get(species, 0)


def ev_limit(species):
    rank = adult_rank(species)
    return 252 * rank // ADULT_RANKS if rank else 252


def stat_limit(iv, rank):
    return ((200 + 8 * iv) * rank * 2 + ADULT_RANKS) // (2 * ADULT_RANKS)


def stat_value(iv, ev, rank):
    base = ((10 + 3 * iv) * (rank + 4) * 2 + 5) // 10
    cap = stat_limit(iv, rank)
    cap_ev = 252 * rank // ADULT_RANKS
    return base + (cap - base) * min(ev, cap_ev) // cap_ev


def projected_ev(current, delta, species):
    return max(current, min(ev_limit(species), current + max(0, int(delta))))
