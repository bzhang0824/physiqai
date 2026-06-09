#!/usr/bin/env python3
"""PhysiqAI spike: dense PHOTOREAL turntable — the realistic-looking rotation.

FLUX multiple-angles, fixed seed, N frames around the subject. Played back as a
scrubbable spin, this is the most photoreal "rotation" achievable with no GPU.
Key thing to eyeball: frame-to-frame JITTER (each frame is generated
independently; fixed seed should minimize drift, but fine steps may flicker).

Usage:
  spike/.venv/bin/python spike/dense_spin.py --photo output/bz_trackA/bz02_IMG_7520_after.jpg --step 30
"""
import argparse, logging, os, pathlib, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "spike" / "output" / "spin" / "dense"
OUT.mkdir(parents=True, exist_ok=True)
SEED = 777


def load_fal_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("FAL_KEY="):
            os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    raise SystemExit("FAL_KEY not found in .env")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    ap.add_argument("--step", type=int, default=30)
    a = ap.parse_args()
    photo = a.photo if os.path.isabs(a.photo) else str(ROOT / a.photo)
    if not os.path.exists(photo):
        photo = str(ROOT / "spike" / a.photo)
    load_fal_key()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    import fal_client

    print(f"[upload] {photo}")
    url = fal_client.upload_file(photo)
    azs = list(range(0, 360, a.step))
    print(f"[dense] {len(azs)} frames every {a.step}deg, seed {SEED}")
    for az in azs:
        t = time.time()
        print(f"[dense] az {az:3d} ...", end=" ", flush=True)
        res = fal_client.subscribe(
            "fal-ai/flux-2-lora-gallery/multiple-angles",
            arguments={
                "image_urls": [url],
                "horizontal_angle": az,
                "vertical_angle": 0,
                "zoom": 4,
                "image_size": "portrait_4_3",
                "seed": SEED,
                "output_format": "jpeg",
            },
            with_logs=False,
        )
        u = (res.get("images") or [{}])[0].get("url")
        if u:
            urllib.request.urlretrieve(u, OUT / f"frame_{az:03d}.jpg")
            print(f"ok ({time.time()-t:.0f}s)")
        else:
            print("NO IMAGE")
    print(f"\nDONE -> {OUT}")


if __name__ == "__main__":
    main()
