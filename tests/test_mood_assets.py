from pathlib import Path
import shutil
from PIL import Image
from scripts.mood_assets import build_mood_assets

ROOT=Path(__file__).resolve().parents[1]


def test_mood_assets_are_small_transparent_and_deterministic(tmp_path):
    files=build_mood_assets(ROOT,tmp_path)
    assert len(files)==13
    before={p.name:p.read_bytes() for p in files}
    for path in files:
        with Image.open(path) as image:
            assert image.mode=='P' and image.getpixel((0,0))==0
            assert image.size==((20,20) if path.stem.startswith('face_') else (32,28))
            assert len(set(image.getdata()))>3
    assert before=={p.name:p.read_bytes() for p in build_mood_assets(ROOT,tmp_path)}
    assert before['energy.bmp']!=before['rest.bmp']
    assert before['energy_angry.bmp']!=before['energy.bmp']


def test_rest_bubbles_use_transparent_glyphs_not_menu_tiles(tmp_path):
    root=tmp_path/'sources'
    for relative in ('assets/ui/mood/mood-atlas-v1.png','assets/ui/mood/food-angry-v1.png',
                     'assets/ui/mood/fatigue-drops-v1.png','assets/ui/mood/sleepy-face-v1.png',
                     'assets/ui/items/meat.png','assets/ui/items/adopted/bandage.png'):
        target=root/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/relative,target)
    paths={p.stem:p for p in build_mood_assets(root,tmp_path/'output')}
    with Image.open(paths['energy']) as image:
        colors=image.convert('RGB').crop((7,2,25,21)).getdata()
        assert sum(1 for r,g,b in colors if r<70 and g>120 and b>120)>=8
    with Image.open(paths['rest']) as image:
        colors=image.convert('RGB').crop((7,2,25,21)).getdata()
        assert sum(1 for r,g,b in colors if r>150 and g>120 and b<80)>=8
