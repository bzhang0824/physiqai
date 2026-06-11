#!/usr/bin/env python3
"""A/B spike: does giving nano-banana-pro real side/back reference photos make
the morph match the user's actual physique better?

A = today's production behavior: image_urls=[front], production build_prompt().
B = image_urls=[front, back(, side)] + a multi-ref preamble before the same prompt.

Run (photos passed as absolute paths; fal key from env or repo .env):
  spike/.venv/bin/python spike/multiref_morph.py \
      --front "spike/photos/IMG_6378 (1).png" --back spike/photos/IMG_6387.png --seeds 3

Outputs spike/output/multiref/{i}_{a|b}.jpg + index.html (side-by-side review).
"""
import argparse, json, os, pathlib, sys, time, urllib.request, logging

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from models.governor.schemas import UserProfile, GoalSpec, NutritionSpec, TrainingSpec
from pipeline.engine_bridge import build_morph_spec
from pipeline.prompt import build_prompt

KG, M = 0.453592, 0.0254

PREAMBLE = (
    "You are given multiple photos of the SAME person. The FIRST image is the photo to "
    "edit - output exactly one edited version of it, keeping its pose, framing, background "
    "and lighting. The additional images show the person's real {angles} view(s): use them "
    "ONLY as ground truth for their true body proportions (back width, waist thickness, "
    "shoulder and arm size, leg size) so the edited physique matches their actual body. "
    "Do not blend poses, do not output a collage. "
)


def load_fal_key():
    if os.environ.get("FAL_KEY"):
        return
    env = pathlib.Path("/Users/brianzhang/Projects/PhysiqAI/.env")
    for line in env.read_text().splitlines():
        if line.startswith("FAL_KEY="):
            os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--front", required=True)
    ap.add_argument("--back", required=True)
    ap.add_argument("--side", default=None)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--age", type=int, default=24)
    ap.add_argument("--sex", default="M")
    ap.add_argument("--height", type=float, default=72)
    ap.add_argument("--weight", type=float, default=192)
    ap.add_argument("--bf", type=float, default=11)
    ap.add_argument("--years", type=float, default=5)
    ap.add_argument("--goal", default="muscle_gain")
    ap.add_argument("--lean-pref", default="lean_bulk")
    ap.add_argument("--weeks", type=int, default=26)
    a = ap.parse_args()

    load_fal_key()
    import fal_client
    logging.getLogger("httpx").setLevel(logging.WARNING)

    profile = UserProfile(age=a.age, sex=a.sex.upper(), height_m=a.height * M,
                          weight_kg=a.weight * KG, bf_pct=a.bf, years_training=a.years,
                          sleep_hrs_per_night=7.5)
    spec = build_morph_spec(profile, GoalSpec(primary=a.goal, lean_preference=a.lean_pref),
                            NutritionSpec(protein_g=None), TrainingSpec(days_per_week=5), a.weeks)
    prompt_a = build_prompt(spec)
    angles = "back" + (" and side" if a.side else "")
    prompt_b = PREAMBLE.format(angles=angles) + prompt_a

    out = pathlib.Path(__file__).resolve().parent / "output" / "multiref"
    out.mkdir(parents=True, exist_ok=True)

    print("uploading inputs once...")
    url_front = fal_client.upload_file(a.front)
    url_back = fal_client.upload_file(a.back)
    url_side = fal_client.upload_file(a.side) if a.side else None
    refs = [url_back] + ([url_side] if url_side else [])

    results = []
    for i in range(a.seeds):
        for tag, urls, prompt in (("a", [url_front], prompt_a),
                                  ("b", [url_front] + refs, prompt_b)):
            t = time.time()
            res = fal_client.subscribe("fal-ai/nano-banana-pro/edit",
                                       arguments={"image_urls": urls, "prompt": prompt},
                                       with_logs=False)
            u = (res.get("images") or [{}])[0].get("url")
            dest = out / f"{i}_{tag}.jpg"
            if u:
                urllib.request.urlretrieve(u, dest)
            dt = time.time() - t
            results.append({"seed": i, "variant": tag, "seconds": round(dt, 1), "ok": bool(u)})
            print(f"  seed {i} variant {tag.upper()}: {dt:.0f}s -> {dest.name}")

    # originals copied next to outputs for the review page
    from PIL import Image
    for src, name in ((a.front, "orig_front.jpg"), (a.back, "orig_back.jpg")):
        Image.open(src).convert("RGB").save(out / name, quality=90)

    rows = "".join(
        f"<tr><td>seed {i}</td>"
        f"<td><img src='{i}_a.jpg'><div>A — front only (production)</div></td>"
        f"<td><img src='{i}_b.jpg'><div>B — front + back refs</div></td></tr>"
        for i in range(a.seeds))
    (out / "index.html").write_text(f"""<!doctype html><meta charset=utf-8>
<title>multi-ref morph A/B</title>
<style>body{{font-family:-apple-system,sans-serif;background:#111;color:#eee;padding:20px}}
img{{height:520px;border-radius:8px}}td{{padding:10px;vertical-align:top;text-align:center}}
div{{margin-top:6px;font-size:13px;color:#9ca3af}}</style>
<h2>Multi-ref morph A/B — {a.goal}/{a.weeks}wk</h2>
<p>Inputs: <img src='orig_front.jpg' style='height:240px'> <img src='orig_back.jpg' style='height:240px'></p>
<table>{rows}</table>
<pre>{json.dumps(results, indent=2)}</pre>
<details><summary>prompt B</summary><pre style='white-space:pre-wrap'>{prompt_b}</pre></details>""")
    json.dump(results, open(out / "results.json", "w"), indent=2)
    print(f"\nreview: {out / 'index.html'}")


if __name__ == "__main__":
    main()
