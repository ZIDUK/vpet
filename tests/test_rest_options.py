from core.options import OptionsSession
from core.pet import Pet
import core.options as options


class Services:
    def __init__(self, accepted=True):
        self.accepted=accepted
        self.saved=None

    def save(self, pet):
        if self.accepted: self.saved=pet.to_dict()
        return self.accepted


def test_pause_is_reachable_before_back_without_renumbering_old_options():
    assert options.OPTION_BACK==8
    assert getattr(options,'OPTION_PAUSE',None)==9
    session=OptionsSession()
    seen=[]
    for _ in range(10):
        seen.append(session.index)
        session.next()
    assert seen==[0,1,2,3,4,5,6,7,9,8]
    assert session.index==0


def test_pause_is_saved_and_failed_save_rolls_back():
    pet=Pet(species='rookie',state='live')
    session=OptionsSession(); session.index=9
    service=Services()
    assert session.action(pet,service)
    assert pet.cold and service.saved['cold']
    assert session.action(pet,service)
    assert not pet.cold and not service.saved['cold']
    assert session.action(pet,Services(False))
    assert not pet.cold and session.message=='SAVE ERROR'


def test_pause_roundtrip_and_legacy_default():
    pet=Pet(species='rookie',state='live'); pet.cold=True
    saved=pet.to_dict()
    restored=Pet(); restored.load_from_dict(saved)
    assert restored.cold
    del saved['cold']; restored.load_from_dict(saved)
    assert not restored.cold
