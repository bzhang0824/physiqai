#!/usr/bin/env python3
"""Live E2E smoke test for the production pipeline (pipeline/).

Runs the real stages on a real photo: engine -> bounded prompt -> Nano Banana Pro
-> face-lock, for a cut and a lean-bulk. Saves a 3-panel (BEFORE | AFTER raw |
AFTER face-locked) per scenario for eyes-on review, plus a sidecar JSON.

Identity is verified by eye here (the facenet auto-gate needs torch; its decision
policy is already unit-tested). Run:
    spike/.venv/bin/python spike/smoke_pipeline.py --photo spike/photos/bz02_IMG_7520.png
"""
import argparse
import json
import pathlib
import sys
import time

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from models.governor.schemas import GoalSpec, NutritionSpec, TrainingSpec, UserProfile
from pipeline.engine_bridge import build_morph_spec
from pipeline.facelock import apply_facelock
from pipeline.prompt import build_prompt
from pipeline.stages import generate_nano_banana

KG, INCH = 0.453592, 0.0254
NANO_COST = 0.15  # $/generation

SCENARIOS = [
    ("cut_6mo", GoalSpec(primary="fat_loss"), TrainingSpec(days_per_week=5), 26),
    ("leanbulk_6mo", GoalSpec(primary="muscle_gain", lean_preference="lean_bulk"),
     TrainingSpec(days_per_week=5), 26),
]


def panel(before_rgb, after_rgb, locked_rgb, locked_flag, caption, out_png):
    H = 820
    def rs(a):
        im = Image.fromarray(a)
        return im.resize((int(im.width * H / im.height), H))
    imgs = [rs(before_rgb), rs(after_rgb), rs(locked_rgb)]
    labels = ["BEFORE", "AFTER (engine-bounded)",
              "AFTER + FACE-LOCK" + ("" if locked_flag else " (no face found)")]
    gap = 18
    W = sum(i.width for i in imgs) + gap * (len(imgs) + 1)
    c = Image.new("RGB", (W, H + 80), (16, 16, 16))
    x = gap
    d = ImageDraw.Draw(c)
    colors = [(120, 200, 255), (255, 210, 120), (0, 255, 140)]
    for im, lab, col in zip(imgs, labels, colors):
        c.paste(im, (x, 56))
        d.text((x, 18), lab, fill=col)
        x += im.width + gap
    d.text((gap, H + 58), caption, fill=(180, 180, 180))
    c.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", default="spike/photos/bz02_IMG_7520.png")
    ap.add_argument("--age", type=int, default=24)
    ap.add_argument("--sex", default="M")
    ap.add_argument("--height", type=float, default=72)
    ap.add_argument("--weight", type=float, default=192)
    ap.add_argument("--bf", type=float, default=11)
    ap.add_argument("--years", type=float, default=5)
    args = ap.parse_args()

    profile = UserProfile(age=args.age, sex=args.sex.upper(), height_m=args.height * INCH,
                          weight_kg=args.weight * KG, bf_pct=args.bf, years_training=args.years)
    before = np.array(Image.open(args.photo).convert("RGB"))
    outdir = pathlib.Path("spike/output/pipeline")
    outdir.mkdir(parents=True, exist_ok=True)

    spend = 0.0
    print(f"photo: {args.photo}")
    for name, goal, training, weeks in SCENARIOS:
        spec = build_morph_spec(profile, goal, NutritionSpec(), training, weeks)
        prompt = build_prompt(spec)
        print(f"\n[{name}] {spec.direction}  "
              f"{spec.weight_before_lb:.0f}->{spec.weight_after_lb:.0f}lb  "
              f"bf {spec.bf_before:.0f}->{spec.bf_after:.0f}%  lean {spec.lean_delta_lb:+.1f}lb")
        t = time.time()
        after = generate_nano_banana(args.photo, prompt, None)
        spend += NANO_COST
        locked, locked_flag = apply_facelock(before, after)
        dt = time.time() - t

        stem = pathlib.Path(args.photo).stem + f"_{name}"
        Image.fromarray(after).save(outdir / f"{stem}_after.jpg")
        Image.fromarray(locked).save(outdir / f"{stem}_locked.jpg")
        caption = (f"{spec.direction} {weeks // 4}mo | {spec.weight_before_lb:.0f}->"
                   f"{spec.weight_after_lb:.0f}lb, bf {spec.bf_before:.0f}->{spec.bf_after:.0f}%, "
                   f"lean {spec.lean_delta_lb:+.1f}lb | conf {spec.confidence_score * 100:.0f}% | "
                   f"facelock={'yes' if locked_flag else 'NO FACE'}")
        panel(before, after, locked, locked_flag, caption, outdir / f"{stem}_3panel.png")
        json.dump({
            "scenario": name, "direction": spec.direction,
            "weight": f"{spec.weight_before_lb:.0f}->{spec.weight_after_lb:.0f} lb",
            "bodyfat": f"{spec.bf_before:.0f}->{spec.bf_after:.0f} %",
            "lean_delta_lb": round(spec.lean_delta_lb, 1),
            "confidence": round(spec.confidence_score, 2),
            "facelocked": locked_flag, "seconds": round(dt, 1), "prompt": prompt,
        }, open(outdir / f"{stem}_3panel.json", "w"), indent=2)
        print(f"  -> {stem}_3panel.png   ({dt:.0f}s, face-lock={'yes' if locked_flag else 'NO FACE'})")

    print(f"\ntotal spend this run: ~${spend:.2f}  (outputs in {outdir})")


if __name__ == "__main__":
    main()
