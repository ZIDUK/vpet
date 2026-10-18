"""Board-oriented consumable catalog; legacy save slots are not reassigned.

This is the adopted content contract, not a declaration of UI availability.
Amounts are vPet rules, never the original game's raw stat magnitudes.
"""

VERSION = 2


def _item(item_id, name, reference, category, effects, duration='instant'):
    return dict(id=item_id, name=name, reference=reference, category=category,
                effects=effects, duration=duration, unlimited=category == 'feeding',
                stack_max=0 if category == 'feeding' else 1 if item_id == 'training_manual' else 99,
                sprite='assets/ui/items/adopted/' + item_id + '.png',
                acquisition='feeding' if category == 'feeding' else 'practice_victory_rotation',
                ui_available=True)


def effect(kind, target, amount):
    return dict(kind=kind, target=target, amount=amount)


_items = [
    _item('meat', 'Carne', 'Meat', 'feeding',
          [effect('restore_care', 'h', 20), effect('weight', 'weight', 1)]),
    _item('protein', 'Proteina', 'vPet Protein', 'feeding',
          [effect('restore_care', 'e', 20), effect('weight', 'weight', 2)]),
]
for target, names in (
    ('hp', [('small_recovery', 'Recuperador pequeno', 'sm.recovery'),
            ('medium_recovery', 'Recuperador mediano', 'med.recovery'),
            ('large_recovery', 'Recuperador grande', 'lrg.recovery'),
            ('super_recovery', 'Recuperador completo', 'sup.recovery')]),
    ('mp', [('mp_floppy', 'Disco MP pequeno', 'MP Floppy'),
            ('medium_mp', 'Disco MP mediano', 'Medium MP'),
            ('large_mp', 'Disco MP grande', 'Large MP'),
            ('super_veggy', 'Verdura MP', 'Super veggy')]),
):
    for (item_id, name, reference), percent in zip(names, (20, 50, 90, 100)):
        _items.append(_item(item_id, name, reference, 'combat_recovery',
                            [effect('restore_percent', target, percent)]))
_items += [
    _item('double_floppy', 'Disco doble', 'Double flop', 'combat_recovery',
          [effect('restore_percent', 'hp', 50), effect('restore_percent', 'mp', 50)]),
    _item('sweet_nut', 'Nuez vital', 'Sweet Nut', 'combat_recovery', [effect('restore_percent', 'hp', 100)]),
    _item('orange_banana', 'Banana restauradora', 'Orange bana', 'combat_recovery',
          [effect('restore_percent', 'hp', 100), effect('restore_percent', 'mp', 100)]),
    _item('bandage', 'Venda', 'Bandage', 'condition', [effect('cure', 'injured', 1)]),
    _item('medicine', 'Medicina', 'Medicine', 'condition',
          [effect('cure', 'injured', 1), effect('restore_care', 'hp', 20)]),
]
for item_id, name, reference, targets, percent in (
    ('off_disk', 'Disco de ataque', 'Off. Disk', ('off',), 20),
    ('def_disk', 'Disco de defensa', 'Def. Disk', ('def',), 20),
    ('speed_disk', 'Disco de velocidad', 'Hispeed dsk', ('spd',), 20),
    ('omni_disk', 'Disco integral', 'Omni Disk', ('off', 'def', 'spd', 'brn'), 20),
    ('super_off_disk', 'Superdisco de ataque', 'S.Off.disk', ('off',), 40),
    ('super_def_disk', 'Superdisco de defensa', 'S.Def.disk', ('def',), 40),
    ('super_speed_disk', 'Superdisco de velocidad', 'S.speed.disk', ('spd',), 40),
):
    _items.append(_item(item_id, name, reference, 'battle_boost',
                        [effect('boost_percent', target, percent) for target in targets], 'one_battle'))
for stat, chip_name, food_id, food_name, reference in (
    ('off', 'Off. Chip', 'power_fruit', 'Fruta de fuerza', 'Power fruit'),
    ('def', 'Def. Chip', 'power_ice', 'Hielo defensivo', 'Power Ice'),
    ('spd', 'Quick Chip', 'speed_leaf', 'Hoja veloz', 'Speed Leaf'),
    ('brn', 'Brain Chip', 'sage_fruit', 'Fruta sabia', 'Sage Fruit'),
    ('hp', 'HP Chip', 'muscle_yam', 'Tuberculo vital', 'Muscle Yam'),
    ('mp', 'MP Chip', 'calm_berry', 'Baya serena', 'Calm berry'),
):
    _items.append(_item(stat + '_chip', 'Chip ' + stat.upper(), chip_name,
                        'permanent', [effect('ev', stat, 4)]))
    _items.append(_item(food_id, food_name, reference, 'permanent', [effect('ev', stat, 2)]))
_items += [
    _item('giant_meat', 'Carne grande', 'Giant Meat', 'care',
          [effect('restore_care', 'h', 40), effect('weight', 'weight', 2)]),
    _item('sirloin', 'Solomillo', 'Sirloin', 'care',
          [effect('restore_care', 'h', 60), effect('weight', 'weight', 3)]),
    _item('digimushroom', 'Champinon', 'Digimushrm', 'care',
          [effect('restore_care', 'h', 15), effect('weight', 'weight', 1)]),
    _item('blue_apple', 'Manzana azul', 'Blue apple', 'care', [effect('restore_care', 'p', 20)]),
    _item('prickly_pear', 'Pera ligera', 'Pricklypear', 'care', [effect('weight', 'weight', -2)]),
    _item('training_manual', 'Manual de entrenamiento', 'Trn. manual', 'training_boost',
          [effect('training_ev_bonus', 'trained_stat', 1)], 'next_completed_training'),
]
ITEMS = tuple(_items)
BY_ID = {i['id']: i for i in ITEMS}
STAT_INDEX = dict(zip(('hp', 'mp', 'off', 'def', 'spd', 'brn'), range(6)))
STARTER_STOCK = {'small_recovery': 2, 'mp_floppy': 2, 'bandage': 1,
                 'off_disk': 1, 'blue_apple': 1}
MENU_OFFSET = 8
COMBAT_CATEGORIES = ('combat_recovery', 'battle_boost')


def menu_index(item_id):
    return MENU_OFFSET + next(i for i, item in enumerate(ITEMS) if item['id'] == item_id)


def menu_item(index):
    index -= MENU_OFFSET
    return ITEMS[index] if 0 <= index < len(ITEMS) else None


def empty_stock():
    return {i['id']: 0 for i in ITEMS if not i['unlimited']}


def load_stock(data, missing=False):
    counts = empty_stock()
    if missing:
        counts.update(STARTER_STOCK)
        return counts, 0
    if not isinstance(data, dict) or data.get('version') != 1:
        return counts, 0
    raw = data.get('counts', {})
    raw = raw if isinstance(raw, dict) else {}
    for key in counts:
        try:
            counts[key] = max(0, min(BY_ID[key]['stack_max'], int(raw.get(key, 0))))
        except (ValueError, TypeError, OverflowError):
            pass
    try:
        cursor = max(0, int(data.get('reward_cursor', 0))) % len(ITEMS)
    except (ValueError, TypeError, OverflowError):
        cursor = 0
    return counts, cursor


def award_victory_item(pet):
    for offset in range(len(ITEMS)):
        idx = (pet.item_reward_cursor + offset) % len(ITEMS)
        item = ITEMS[idx]
        if item['unlimited'] or pet.adopted_inventory[item['id']] >= item['stack_max']:
            continue
        if item['id'] == 'training_manual' and pet.exploration.guide:
            continue
        pet.adopted_inventory[item['id']] += 1
        pet.item_reward_cursor = (idx + 1) % len(ITEMS)
        return item['id']
    return None


def has_training_bonus(pet):
    return pet.exploration.guide or pet.adopted_inventory.get('training_manual', 0) > 0


def consume_training_bonus(pet, stat):
    if pet.exploration.away or stat not in STAT_INDEX or pet.ev_at(stat) >= 252:
        return 0
    if pet.exploration.guide:
        return pet.exploration.use_guide(pet, stat)
    if pet.adopted_inventory.get('training_manual', 0):
        pet.gain_ev(stat, 1)
        pet.adopted_inventory['training_manual'] -= 1
        return 1
    return 0


def item_name(item, spanish=False):
    name = item['name'] if spanish else item['reference'].replace('vPet ', '')
    return name.upper()


def short_name(item, spanish=False):
    key = item['id']
    recovery = {'small_recovery': ('HP PEQ.', 'SMALL HP'), 'medium_recovery': ('HP MED.', 'MED. HP'),
                'large_recovery': ('HP GRANDE', 'LARGE HP'), 'super_recovery': ('HP TOTAL', 'FULL HP'),
                'mp_floppy': ('MP PEQ.', 'SMALL MP'), 'medium_mp': ('MP MED.', 'MED. MP'),
                'large_mp': ('MP GRANDE', 'LARGE MP'), 'super_veggy': ('VERDURA MP', 'MP VEGGY'),
                'double_floppy': ('DISCO DOBLE', 'DUAL DISK'), 'training_manual': ('MANUAL', 'MANUAL')}
    if key in recovery:
        return recovery[key][0 if spanish else 1]
    if item['category'] == 'battle_boost':
        target = item['effects'][0]['target'].upper()
        target = 'OMNI' if key == 'omni_disk' else target
        return ('S.' if key.startswith('super_') else '') + target + (' DISCO' if spanish else ' DISK')
    return item_name(item, spanish)


def item_blurb(item, spanish=False):
    first = item['effects'][0]
    kind, target, amount = first['kind'], first['target'], first['amount']
    if kind == 'restore_percent':
        return 'BAT +%d%% %s' % (amount, target.upper())
    if kind == 'boost_percent':
        return 'BAT +%d%% %s' % (amount, target.upper())
    if kind == 'ev':
        return '%s +%d EV' % (target.upper(), amount)
    if kind == 'training_ev_bonus':
        return '+1 EV/SESION' if spanish else '+1 EV/TRAIN'
    if kind == 'cure':
        return 'CURA LESION' if spanish else 'HEAL INJURY'
    if kind == 'weight':
        return '%+d %s' % (amount, 'PESO' if spanish else 'WEIGHT')
    return '%+d %s' % (amount, {'h': 'HAM' if spanish else 'HUN', 'p': 'ANIMO' if spanish else 'MOOD', 'e': 'ENE'}.get(target, target.upper()))


def recovered(current, maximum, percent):
    if maximum <= 0 or not 0 < percent <= 100:
        raise ValueError('Invalid recovery')
    return min(maximum, max(0, current) + max(1, maximum * percent // 100))


def use_combat_item(fighter, stock, item_id):
    """Apply once to a live fighter. No stock consumed for a zero effect.

    Boosts use the original fighter stats, replace weaker boosts and never stack.
    The owning battle must block calls after its result has been established.
    """
    item = BY_ID.get(item_id)
    if not item or stock.get(item_id, 0) <= 0 or fighter.hp <= 0:
        return False
    if item['category'] not in ('combat_recovery', 'battle_boost'):
        return False
    hp, mp = fighter.hp, fighter.mp
    stats = list(fighter.stats)
    base = getattr(fighter, 'item_base_stats', fighter.stats)
    boosts = list(getattr(fighter, 'item_boosts', (0,) * 6))
    for e in item['effects']:
        target, amount = e['target'], e['amount']
        if e['kind'] == 'restore_percent':
            if target == 'hp':
                hp = recovered(hp, fighter.max_hp, amount)
            else:
                mp = recovered(mp, fighter.max_mp, amount)
        else:
            idx = STAT_INDEX[target]
            if amount > boosts[idx]:
                boosts[idx] = amount
                stats[idx] = min(99, base[idx] + max(1, base[idx] * amount // 100))
    if (hp, mp, tuple(stats)) == (fighter.hp, fighter.mp, fighter.stats):
        return False
    fighter.hp, fighter.mp = hp, mp
    fighter.item_base_stats, fighter.item_boosts = tuple(base), boosts
    fighter.stats = tuple(stats)
    stock[item_id] -= 1
    return True


def use_care_item(pet, stock, item_id):
    """Consume home items only if something changes; no feeding stock involved."""
    item = BY_ID.get(item_id)
    if (not item or item['category'] not in ('care', 'condition', 'permanent')
            or stock.get(item_id, 0) <= 0 or pet.is_egg or pet.dead
            or getattr(pet, 'cold', False)
            or pet.exploration.away):
        return False
    if item['category'] == 'condition' and not pet.injured:
        return False
    before = (dict(pet.stats), dict(pet.ev), pet.weight, pet.injured)
    for e in item['effects']:
        target, amount = e['target'], e['amount']
        if e['kind'] == 'ev':
            pet.gain_ev(target, amount)
        elif e['kind'] == 'restore_care':
            pet.stats[target] = min(100, pet.stats[target] + amount)
        elif e['kind'] == 'weight':
            pet.weight = min(99, max(1, pet.weight + amount))
        elif e['kind'] == 'cure':
            pet.injured = False
            pet.injured_ms = 0
    if before == (pet.stats, pet.ev, pet.weight, pet.injured):
        return False
    stock[item_id] -= 1
    return True
