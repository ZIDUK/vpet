"""Read-only Home needs and mood presentation; never starts a care call."""


def ui_cue(hunger, energy, mood, injured=False, tired=False, hunger_call=False, rest_call=False):
    need = ('hurt' if injured else 'food' if hunger<=20 or hunger_call else
            'rest' if energy<=20 or tired or rest_call else None)
    angry = mood<50 and need in ('food','rest')
    face = ('sad' if injured else 'angry' if mood<20 or angry else
            'sad' if mood<50 else 'neutral' if mood<75 else 'happy')
    if need is None and mood<50:
        need = face
    return need, face, angry


def pet_cue(pet, tired=False):
    need, face, angry = ui_cue(pet.stats['h'],pet.stats['e'],pet.stats['p'],
        pet.injured,tired,pet.call_reason=='hunger',pet.call_reason in ('strength','lights'))
    if pet.species=='egg' or pet.dead or getattr(pet,'cold',False) or pet.sleep.asleep or pet.exploration.away:
        need, angry = None, False
    return need, face, angry


def rest_detail(pet, tired=False, minute=None):
    """Explain the current Rest cue without advancing the sleep routine."""
    trait=pet.dna[3] % 3
    bedtime=pet.sleep.preferred(trait)
    detail={'kind':None,'current':pet.stats['e'],'target':0,'bedtime':bedtime}
    if pet_cue(pet,tired)[0]!='rest':
        return detail
    scheduled=minute is not None and 0<=minute<1440 and (minute>=bedtime or minute<360)
    detail.update(kind='bedtime' if scheduled else 'energy',target=30+trait*5)
    return detail


def rest_label_position(bubble_x):
    return (bubble_x-102 if bubble_x>=104 else bubble_x+34),25


def bubble_position(pet_x, pet_y, facing):
    anchor = int(pet_x)+(22 if facing<0 else 66)
    flip = facing<0
    x = anchor-34 if flip else anchor+2
    if x<0:
        x, flip = anchor+2, False
    elif x>208:
        x, flip = anchor-34, True
    return max(0,min(208,x)),max(25,min(107,int(pet_y)-16)),flip


def bubble_name(need, angry):
    return need+('_angry' if angry else '') if need else None
