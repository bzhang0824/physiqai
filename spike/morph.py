#!/usr/bin/env python3
"""PhysiqAI poke-tool: run the NEW physiology engine on any profile, print the
defensible projection, and (optionally) generate the visual morph from a photo.

Demo/exploration harness (not production) — the engine it calls is TDD-tested.

Examples:
  # numbers only (free, instant):
  spike/.venv/bin/python spike/morph.py --age 24 --sex M --height 72 --weight 192 \
      --bf 11 --years 5 --goal fat_loss --weeks 26 --no-image

  # with the visual morph from a photo:
  spike/.venv/bin/python spike/morph.py --photo spike/photos/bz02_IMG_7520.png \
      --age 24 --sex M --height 72 --weight 192 --bf 11 --years 5 \
      --goal muscle_gain --lean-pref lean_bulk --weeks 26
"""
import argparse, os, sys, time, pathlib, urllib.request, logging
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from models.governor.schemas import UserProfile, GoalSpec, NutritionSpec, TrainingSpec
from models.governor.simulator import simulate_weekly
from models.governor.predictor import predict

KG = 0.453592
M = 0.0254


def load_fal_key():
    for line in pathlib.Path("/Users/brianzhang/Projects/PhysiqAI/.env").read_text().splitlines():
        if line.startswith("FAL_KEY="):
            os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")


def summarize(tl, p, goal, weeks):
    s, f = tl[0], tl[-1]
    print(f"\n{'='*64}")
    print(f"  PROJECTION — {goal.primary}"
          + (f"/{goal.lean_preference}" if goal.primary == 'muscle_gain' else "")
          + f", {weeks//4} months")
    print(f"{'='*64}")
    print(f"  Weight   {s.weight_kg/KG:6.1f} lb  ->  {f.weight_kg/KG:6.1f} lb   ({(f.weight_kg-s.weight_kg)/KG:+.1f})")
    print(f"  Body fat {s.bf_pct:6.1f} %   ->  {f.bf_pct:6.1f} %    ({f.bf_pct-s.bf_pct:+.1f})")
    print(f"  Lean     {s.lean_mass_kg/KG:6.1f} lb  ->  {f.lean_mass_kg/KG:6.1f} lb   ({(f.lean_mass_kg-s.lean_mass_kg)/KG:+.1f})")
    print(f"  FFMI     {s.normalized_ffmi:6.1f}     ->  {f.normalized_ffmi:6.1f}      (natural ceiling 25.0)")
    mile = {4: '1mo', 12: '3mo', 26: '6mo', 52: '1yr'}
    pts = [w for w in (4, 12, 26, 52) if w <= weeks]
    print("  Trajectory: " + "  ".join(f"{mile[w]}:{tl[w].weight_kg/KG:.0f}lb/{tl[w].bf_pct:.1f}%" for w in pts))
    print(f"  Min body fat ever reached: {min(x.bf_pct for x in tl):.1f}%  (floor enforced)")
    return s, f


def build_prompt(p, s, f, weeks):
    dlb = (f.weight_kg - s.weight_kg) / KG
    dlean = (f.lean_mass_kg - s.lean_mass_kg) / KG
    mo = weeks // 4
    if f.bf_pct < s.bf_pct - 0.5:  # cut
        return (f"Edit this exact photo of a person to show the SAME person after a realistic {mo}-month "
                f"fat-loss program: body fat from ~{s.bf_pct:.0f}% down to ~{f.bf_pct:.0f}% "
                f"({abs(dlb):.0f} lb change), tighter waist, more visible muscle definition, "
                f"keeping muscle size (lean mass change {dlean:+.0f} lb). Natural and realistic, NOT a "
                f"stage bodybuilder, no exaggeration. CRITICAL: keep the face, hair, skin tone and identity "
                f"EXACTLY the same; keep the same pose, clothing, background, lighting, camera and image quality. Photorealistic.")
    else:  # gain / recomp
        return (f"Edit this exact photo to show the SAME person after {mo} months of training: add about "
                f"{dlean:+.0f} lb of lean muscle (fuller chest, shoulders, arms, back), body fat ~{s.bf_pct:.0f}% "
                f"to ~{f.bf_pct:.0f}%. NATURAL natural-lifter result, NOT a pro bodybuilder, no exaggeration. "
                f"CRITICAL: keep the face, hair, skin tone and identity EXACTLY the same; keep the same pose, "
                f"clothing, background, lighting, camera and image quality. Photorealistic.")


def generate(photo, prompt, out_stem, meta=None):
    import fal_client, json
    logging.getLogger("httpx").setLevel(logging.WARNING)
    url = fal_client.upload_file(photo)
    t = time.time()
    res = fal_client.subscribe("fal-ai/nano-banana-pro/edit",
                               arguments={"image_urls": [url], "prompt": prompt}, with_logs=False)
    u = (res.get("images") or [{}])[0].get("url")
    outdir = pathlib.Path("spike/output/morph"); outdir.mkdir(parents=True, exist_ok=True)
    after = outdir / f"{out_stem}_after.jpg"
    if u:
        urllib.request.urlretrieve(u, after)
    from PIL import Image, ImageDraw
    b = Image.open(photo).convert("RGB"); a = Image.open(after).convert("RGB")
    H = 900; rs = lambda im: im.resize((int(im.width * H / im.height), H)); b, a = rs(b), rs(a)
    c = Image.new("RGB", (b.width + a.width + 22, H + 40), (18, 18, 18))
    c.paste(b, (0, 40)); c.paste(a, (b.width + 22, 40))
    d = ImageDraw.Draw(c); d.text((8, 12), "BEFORE", fill=(120, 200, 255))
    d.text((b.width + 30, 12), "AFTER (new engine)", fill=(0, 255, 120))
    cmp = outdir / f"{out_stem}_compare.png"; c.save(cmp)
    if meta is not None:
        json.dump(meta, open(outdir / f"{out_stem}_compare.json", "w"), indent=2)
    print(f"  morph generated in {time.time()-t:.0f}s -> {cmp}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo"); ap.add_argument("--no-image", action="store_true")
    # defaults = Brian's stats, so quick pokes need almost no args
    ap.add_argument("--age", type=int, default=24); ap.add_argument("--sex", default="M")
    ap.add_argument("--height", type=float, default=72, help="inches")
    ap.add_argument("--weight", type=float, default=192, help="lb")
    ap.add_argument("--bf", type=float, default=11); ap.add_argument("--years", type=float, default=5)
    ap.add_argument("--goal", default="fat_loss", choices=["fat_loss", "muscle_gain", "recomp", "maintenance"])
    ap.add_argument("--lean-pref", default="standard", choices=["standard", "lean_bulk", "aggressive_bulk"])
    ap.add_argument("--days", type=int, default=5); ap.add_argument("--sleep", type=float, default=7.5)
    ap.add_argument("--protein", type=float, default=None); ap.add_argument("--weeks", type=int, default=26)
    a = ap.parse_args()

    p = UserProfile(age=a.age, sex=a.sex.upper(), height_m=a.height * M, weight_kg=a.weight * KG,
                    bf_pct=a.bf, years_training=a.years, sleep_hrs_per_night=a.sleep)
    goal = GoalSpec(primary=a.goal, lean_preference=a.lean_pref)
    nut = NutritionSpec(protein_g=a.protein); trn = TrainingSpec(days_per_week=a.days)
    result = predict(p, goal, nut, trn, a.weeks)
    tl = result.weekly_timeline
    s, f = summarize(tl, p, goal, a.weeks)
    lo, hi = result.confidence_range_lbs()
    print(f"  Confidence {result.confidence_score*100:.0f}%  |  likely weight-change range: "
          f"{min(lo,hi):+.1f} to {max(lo,hi):+.1f} lb")
    md = result.measurement_deltas
    print(f"  Measurements (cm): waist {md['waist_cm']:+.1f}  chest {md['chest_cm']:+.1f}  "
          f"arms {md['arms_cm']:+.1f}  thighs {md['thighs_cm']:+.1f}")
    for w in result.warnings: print(f"  ⚠ {w}")
    for ins in result.insights: print(f"  ✓ {ins}")

    if a.photo and not a.no_image:
        load_fal_key()
        stem = pathlib.Path(a.photo).stem + f"_{a.goal}_{a.weeks}w"
        meta = {
            "scenario": f"{a.goal}" + (f"/{a.lean_pref}" if a.goal == "muscle_gain" else ""),
            "months": a.weeks // 4, "photo": pathlib.Path(a.photo).name,
            "profile": f"{a.age}{a.sex} {a.weight:.0f}lb {a.bf:.0f}% {a.years}yr",
            "weight": f"{s.weight_kg/KG:.0f} -> {f.weight_kg/KG:.0f} lb",
            "bodyfat": f"{s.bf_pct:.0f} -> {f.bf_pct:.1f} %",
            "lean": f"{(f.lean_mass_kg-s.lean_mass_kg)/KG:+.1f} lb",
            "ffmi": f"{f.normalized_ffmi:.1f}",
        }
        generate(a.photo, build_prompt(p, s, f, a.weeks), stem, meta)


if __name__ == "__main__":
    main()
