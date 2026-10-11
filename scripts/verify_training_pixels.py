#!/usr/bin/env python3
"""Compare the production C++ Training renderer to Pillow at native resolution."""
import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from PIL import Image, ImageChops, ImageDraw
from core.pet import Pet
from core.training import TRAINING_TYPES, batch_apply, batch_block_reason
from scripts.training_session import TrainingSession
from scripts.training_renderer import render_training

STATES = ("select", "prepare", "session", "confirm", "result", "error", "cancel")


def compile_renderer(output, include_dir):
    subprocess.run(["c++", "-std=c++17", "-O2", "-I"+str(include_dir), "-I"+str(ROOT / "firmware/t-display/include"),
                    "-I"+str(ROOT / "firmware/t-display/lib/vpet_core/src"),
                    str(ROOT / "tests/training_pixels.cpp"),
                    str(ROOT / "firmware/t-display/lib/vpet_core/src/vpet/PetState.cpp"),
                    "-o", str(output)], check=True)


def sim_frame(build, state, lang, index, secondary, reps, ms, energy, ev):
    p = Pet()
    p.complete_hatch("rookie", entropy=42)
    p.restore_dna([0xab, 0xcd, 0xef, 0x12])
    p.restore_ev(dict(zip(("hp", "mp", "off", "def", "spd", "brn"), (60,24,30,12,18,0))))
    stat = TRAINING_TYPES[min(index,5)]["stat"]
    p.ev[stat] = ev
    p.stats = {"h":50, "e":energy, "p":80, "hp":80}
    p.effort = 0
    p.language = lang
    s = TrainingSession(p, lambda _: True)
    s.state = STATES[state]
    s.index = index
    s._chosen_index = min(index,5)
    s._chosen_stat = stat
    s._reps_completed = reps
    s._pending_ev = reps*6
    s._energy_reserved = reps*8
    s._focus = (("train", "finalize") if state == 2 else
                ("confirm", "follow") if state == 3 else
                ("follow", "discard") if state == 6 else
                ("retry", "discard") if state == 5 else ("start", "back"))[secondary]
    if state == 2 and ms < 10000 and reps:
        s._animation_started_ms = 0
        s._animation_index = min(index,5)
    if state == 4:
        s._result_snapshot = batch_apply(p, stat, reps)
        s._result_page = "stats" if secondary else "summary"
        s._focus = "back" if batch_block_reason(p, stat) else "repeat"
    return render_training(build, s, ms)


def quantized(image):
    result = Image.new("RGB", image.size)
    result.putdata([((r>>3)*255//31, (g>>2)*255//63, (b>>3)*255//31)
                    for r,g,b in image.convert("RGB").getdata()])
    return result


def verify(build, output, data_dir=None, include_dir=None):
    data_dir = data_dir or ROOT / "firmware/t-display/data"
    include_dir = include_dir or ROOT / "firmware/t-display/include"
    output.mkdir(parents=True, exist_ok=True)
    binary = output / "training-pixels"
    compile_renderer(binary, include_dir)
    report = []
    # Includes every stat, button focus, locale, active animation and failure screen.
    for lang in ("ES", "EN"):
        for state in range(7):
            for index in range(8 if state == 0 else 6):
                for secondary in range(1 if state == 0 else 2):
                    reps = 1 if state in (2,3,4,6) else 0
                    scenarios = [(1600,80,30)]
                    if state == 2:
                        scenarios += [(0,80,30),(300,80,30),(5000,80,30),
                                      (9999,80,30),(1600,8,30),(1600,80,246)]
                    if state == 4:
                        scenarios += [(1600,8,30),(1600,80,250)]
                    for ms,energy,ev in scenarios:
                        args=(state,lang,index,secondary,reps,ms,energy,ev)
                        raw=subprocess.check_output([str(binary),str(data_dir),*map(str,args)])
                        fw=Image.open(io.BytesIO(raw)).convert("RGB")
                        sim=quantized(sim_frame(build,*args))
                        different=sum(a!=b for a,b in zip(sim.getdata(),fw.getdata()))
                        slug=f"{lang}-{STATES[state]}-{index}-{secondary}-{ms}-{energy}-{ev}"
                        sim.save(output / (slug+"-sim.png"))
                        fw.save(output / (slug+"-firmware.png"))
                        report.append({"slug":slug,"different_pixels":different,"match":1-different/(240*135)})
    (output / "report.json").write_text(json.dumps(report,indent=2)+"\n")
    rows=[]
    for state,secondary in ((0,0),(1,0),(2,0),(2,1),(3,0),(6,0),(4,0),(4,1),(5,0)):
        row=Image.new("RGB",(980,154),(245,245,245))
        draw=ImageDraw.Draw(row)
        for col,(lang,kind) in enumerate((("ES","sim"),("ES","firmware"),("EN","sim"),("EN","firmware"))):
            slug=f"{lang}-{STATES[state]}-0-{secondary}-1600-80-30"
            draw.text((col*245,0),f"{lang} {kind} / {STATES[state]}",fill="black")
            row.paste(Image.open(output/(slug+f"-{kind}.png")),(col*245,18))
        rows.append(row)
    sheet=Image.new("RGB",(980,len(rows)*154),(245,245,245))
    for i,row in enumerate(rows): sheet.paste(row,(0,i*154))
    sheet.save(output / "training-parity.png")
    overview = Image.new("RGB", (480, 270))
    for position, state in enumerate(("select", "prepare", "session", "result")):
        path = output / f"ES-{state}-0-0-1600-80-30-firmware.png"
        overview.paste(Image.open(path), ((position % 2)*240, (position // 2)*135))
    overview.resize((960, 540), Image.Resampling.NEAREST).save(output / "training-firmware-overview.png")
    failures=[r for r in report if r["different_pixels"]]
    print(json.dumps({"frames":len(report),"exact":len(report)-len(failures),"worst":sorted(report,key=lambda r:r["match"])[:8]},indent=2))
    return not failures


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build",type=Path,default=ROOT/"build-tdisplay")
    parser.add_argument("--output",type=Path,default=ROOT/"out/training-parity")
    args=parser.parse_args()
    sys.exit(0 if verify(args.build,args.output) else 1)
