import copy
import itertools
from pathlib import Path
import subprocess
import pytest
from core import cues
from core.pet import Pet


def make_pet(energy=20,trait=0):
    pet=Pet(species='rookie',state='live')
    pet.stats.update(h=80,e=energy,p=80)
    pet.dna=tuple((*pet.dna[:3],trait))
    return pet


@pytest.mark.parametrize('trait,goal',[(0,30),(1,35),(2,40)])
def test_low_energy_detail_uses_real_recovery_goal_without_mutating(trait,goal):
    pet=make_pet(trait=trait)
    before=copy.deepcopy(pet.to_dict())
    sleep_before=copy.deepcopy(pet.sleep.__dict__)
    detail=cues.rest_detail(pet,tired=True,minute=720)
    assert detail['kind']=='energy'
    assert (detail['current'],detail['target'])==(20,goal)
    assert pet.to_dict()==before and pet.sleep.__dict__==sleep_before


@pytest.mark.parametrize('minute,kind',[(359,'bedtime'),(360,'energy'),(1109,'energy'),(1110,'bedtime'),(-1,'energy')])
def test_bedtime_and_dawn_boundaries_do_not_confuse_energy(minute,kind):
    pet=make_pet(); pet.sleep.bedtime=1110
    assert cues.rest_detail(pet,tired=True,minute=minute)['kind']==kind


def test_bedtime_has_priority_even_when_energy_is_full():
    pet=make_pet(100,2); pet.sleep.bedtime=1320
    detail=cues.rest_detail(pet,tired=True,minute=1320)
    assert detail['kind']=='bedtime' and detail['bedtime']==1320
    pet.stats['e']=0
    assert cues.rest_detail(pet,tired=True,minute=1320)['kind']=='bedtime'


@pytest.mark.parametrize('flag',['food','injured','cold','dead','away','asleep','egg','recovered'])
def test_rest_detail_does_not_override_other_needs_or_hidden_states(flag):
    pet=make_pet()
    if flag=='food': pet.stats['h']=0
    elif flag=='away': pet.exploration.trip={'route':'patio','started':0}
    elif flag=='asleep': pet.sleep.asleep=True
    elif flag=='egg': pet.species='egg'
    elif flag=='recovered': pet.stats['e']=80
    else: setattr(pet,flag,True)
    assert cues.rest_detail(pet,minute=720)['kind'] is None


def test_energy_latch_is_read_only_and_caption_never_covers_bubble_or_pet():
    pet=make_pet(32,1); pet.sleep.physical_tired=True
    assert cues.rest_detail(pet,tired=True,minute=720)['target']==35
    assert pet.sleep.physical_tired
    for x in range(209):
        lx,ly=cues.rest_label_position(x)
        assert 0<=lx and lx+100<=240 and ly>=24 and ly+18<=43
        assert lx+100<=x or lx>=x+32


def test_cpp_python_rest_details_share_boundaries_and_geometry(tmp_path):
    root=Path(__file__).resolve().parents[1]
    core=root/'firmware/t-display/lib/vpet_core/src'
    binary=tmp_path/'rest-vectors'
    subprocess.run(['c++','-std=c++17','-O2','-I'+str(core),str(root/'tests/rest_detail_vectors.cpp'),
                    str(core/'vpet/PetState.cpp'),str(core/'vpet/Nutrition.cpp'),'-o',str(binary)],check=True)
    rows=[]; expected=[]
    for i,(trait,energy,minute,bedtime,tired,hidden) in enumerate(itertools.product(
            range(3),(0,20,32,80),(-1,0,359,360,1080,1110,1320,1439),(0,1110,1320),range(2),range(5))):
        pet=make_pet(energy,trait); pet.sleep.bedtime=bedtime
        if hidden==1: pet.sleep.asleep=True
        if hidden==2: pet.cold=True
        if hidden==3: pet.injured=True
        if hidden==4: pet.stats['h']=0
        detail=cues.rest_detail(pet,tired,minute)
        x=i%209
        rows.append(' '.join(map(str,(trait,energy,minute,bedtime,tired,hidden,x))))
        expected.append(' '.join(map(str,((None,'energy','bedtime').index(detail['kind']),detail['current'],
                          detail['target'],detail['bedtime'],cues.rest_label_position(x)[0]))))
    output=subprocess.check_output([str(binary)],input='\n'.join(rows),text=True)
    assert output.splitlines()==expected
