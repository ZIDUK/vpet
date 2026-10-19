import copy
import itertools
from pathlib import Path
import subprocess
import pytest
from core.pet import Pet
from core import cues


def pet(h=80,e=80,p=80,**flags):
    value=Pet(species='rookie',state='live')
    value.stats.update(h=h,e=e,p=p)
    for key, val in flags.items(): setattr(value,key,val)
    return value


@pytest.mark.parametrize('h,e,p,tired,injured,need,face,angry',[
    (80,80,75,False,False,None,'happy',False),
    (80,80,74,False,False,None,'neutral',False),
    (80,80,50,False,False,None,'neutral',False),
    (80,80,49,False,False,'sad','sad',False),
    (80,80,19,False,False,'angry','angry',False),
    (20,80,80,False,False,'food','happy',False),
    (21,80,80,False,False,None,'happy',False),
    (20,80,49,False,False,'food','angry',True),
    (80,20,80,False,False,'rest','happy',False),
    (80,80,49,True,False,'rest','angry',True),
    (0,0,10,True,True,'hurt','sad',False),
    (0,0,80,True,False,'food','happy',False),
])
def test_need_and_mood_are_independent(h,e,p,tired,injured,need,face,angry):
    value=pet(h,e,p,injured=injured)
    before=copy.deepcopy(value.to_dict())
    assert cues.pet_cue(value,tired)==(need,face,angry)
    assert value.to_dict()==before


@pytest.mark.parametrize('flag',['dead','cold','away','asleep','egg'])
def test_hidden_needs_do_not_leak_to_home(flag):
    value=pet(h=0,p=10)
    if flag=='away': value.exploration.trip={'route':'patio','started':0}
    elif flag=='asleep': value.sleep.asleep=True
    elif flag=='egg': value.species='egg'
    else: setattr(value,flag,True)
    assert cues.pet_cue(value)[0] is None


def test_existing_calls_still_get_their_need():
    value=pet()
    for call,need in [('hunger','food'),('strength','rest'),('lights','rest')]:
        value.call_reason=call
        assert cues.pet_cue(value)[0]==need


def test_bubble_placement_bounds_and_facing():
    for x in range(153):
        for y in (24,43,47,100):
            for facing in (-1,1):
                bx,by,flip=cues.bubble_position(x,y,facing)
                assert 0<=bx<=208 and 25<=by<=107
                assert isinstance(flip,bool)
    assert cues.bubble_position(76,43,1)==(144,27,False)
    assert cues.bubble_position(152,43,1)==(184,27,True)


def test_cpp_python_cue_and_position_vectors(tmp_path):
    root=Path(__file__).resolve().parents[1]
    binary=tmp_path/'cues'
    subprocess.run(['c++','-std=c++11','-O2','-I'+str(root/'firmware/t-display/lib/vpet_core/src'),
                    str(root/'tests/mood_cue_vectors.cpp'),'-o',str(binary)],check=True)
    rows=[]; expected=[]
    for index,(h,e,p,inj,tired,call) in enumerate(itertools.product(
            (0,20,21,80),(0,20,21,80),(0,19,20,49,50,74,75,100),(0,1),(0,1),(0,1,2))):
        x=index%153; y=(24,43,100)[index%3]; facing=-1 if index%2 else 1
        rows.append(' '.join(map(str,(h,e,p,inj,tired,int(call==1),int(call==2),x,y,facing))))
        need,face,angry=cues.ui_cue(h,e,p,inj,tired,call==1,call==2)
        bx,by,flip=cues.bubble_position(x,y,facing)
        expected.append(' '.join(map(str,((None,'food','rest','hurt','sad','angry').index(need),
            ('happy','neutral','sad','angry').index(face),int(angry),bx,by,int(flip)))))
    output=subprocess.check_output([str(binary)],input='\n'.join(rows),text=True)
    assert output.splitlines()==expected
