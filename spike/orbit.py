#!/usr/bin/env python3
"""PhysiqAI spike: VIDEO-ORBIT spin — does temporal consistency beat 2D drift?

Seedance 2.0 image-to-video enforces frame-to-frame coherence, so a prompted
turntable orbit should rotate the SAME person smoothly (no flicker/identity
drift) — the thing independently-generated FLUX frames couldn't do.

Eyes-on real output. 720p / 8s / portrait keeps it ~$1.

Usage:
  spike/.venv/bin/python spike/orbit.py --photo output/bz_trackA/bz02_IMG_7520_after.jpg
"""
import argparse, json, logging, os, pathlib, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "spike" / "output" / "spin"
OUT.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Smooth cinematic turntable. The camera slowly orbits a full circle around the "
    "muscular man, revealing his physique from the front, then the side, then the back, "
    "and continuing around to the front again. He stands completely still in a relaxed "
    "neutral standing pose with arms at his sides. His face, hair, skin, body shape and "
    "the locker-room background stay perfectly consistent the entire time. "
    "Photorealistic, steady continuous rotation, no warping, no morphing."
)


def load_fal_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("FAL_KEY="):
            os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    raise SystemExit("FAL_KEY not found in .env")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    ap.add_argument("--duration", default="8")
    ap.add_argument("--resolution", default="720p")
    a = ap.parse_args()
    photo = a.photo if os.path.isabs(a.photo) else str(ROOT / a.photo)
    if not os.path.exists(photo):
        photo = str(ROOT / "spike" / a.photo)
    load_fal_key()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    import fal_client

    stem = pathlib.Path(photo).stem
    print(f"[upload] {photo}")
    url = fal_client.upload_file(photo)
    print(f"[orbit] seedance-2.0 i2v · {a.resolution} · {a.duration}s · portrait ...")
    t = time.time()
    res = fal_client.subscribe(
        "bytedance/seedance-2.0/image-to-video",
        arguments={
            "prompt": PROMPT,
            "image_url": url,
            "resolution": a.resolution,
            "duration": a.duration,
            "aspect_ratio": "9:16",
            "generate_audio": False,
            "seed": 777,
        },
        with_logs=False,
    )
    dt = time.time() - t
    tag = f"_orbit_{a.resolution}"
    (OUT / f"{stem}{tag}_raw.json").write_text(json.dumps(res, indent=2))
    v = (res.get("video") or {}).get("url") or (res.get("videos") or [{}])[0].get("url")
    print(f"[orbit] done in {dt:.0f}s. keys={list(res.keys())}")
    if v:
        dest = OUT / f"{stem}{tag}.mp4"
        urllib.request.urlretrieve(v, dest)
        print(f"[orbit] video -> {dest.name} ({dest.stat().st_size//1024} KB)")
    else:
        print("[orbit] NO video url — inspect _orbit_raw.json")


if __name__ == "__main__":
    main()
