#!/usr/bin/env python3
"""PhysiqAI spike: A+B HYBRID — does the face/back survive the round-trip into 3D?

Pipeline:
  1. FLUX multiple-angles synthesizes clean back / left / right / 45° views
     of the SAME person (fixed seed for cross-angle consistency).
  2. Those views feed Hunyuan3D Pro's named multi-view slots, with PBR on and
     a high face_count — so the mesh's back/sides/face are built from real-ish
     views instead of being hallucinated from a front-only photo.
  3. Download the new GLB. Compare against the single-view mesh in the viewer.

Eyes-on real output only. ~$0.55 total ( ~5x $0.02 FLUX + ~$0.45 Hunyuan Pro ).

Usage:
  spike/.venv/bin/python spike/hybrid.py --photo output/bz_trackA/bz02_IMG_7520_after.jpg
"""
import argparse, json, logging, os, pathlib, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "spike" / "output" / "spin"
OUT.mkdir(parents=True, exist_ok=True)

# FLUX horizontal_angle -> Hunyuan multi-view slot
VIEWS = [
    (90,  "right_image_url",       "right"),
    (270, "left_image_url",        "left"),
    (180, "back_image_url",        "back"),
    (45,  "right_front_image_url", "rfront"),
    (315, "left_front_image_url",  "lfront"),
]
SEED = 777  # fixed -> same person across all synthesized angles


def load_fal_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("FAL_KEY="):
            os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    raise SystemExit("FAL_KEY not found in .env")


def _download(url, dest):
    urllib.request.urlretrieve(url, dest)
    return dest


def synth_views(front_url, stem):
    """Path B: synthesize the missing angles. Returns {slot: fal_url} for Hunyuan."""
    import fal_client
    slots = {}
    for az, slot, tag in VIEWS:
        t = time.time()
        print(f"[flux] {tag:6s} (az {az:3d}) ...", end=" ", flush=True)
        res = fal_client.subscribe(
            "fal-ai/flux-2-lora-gallery/multiple-angles",
            arguments={
                "image_urls": [front_url],
                "horizontal_angle": az,
                "vertical_angle": 0,
                "zoom": 4,                       # slightly wide -> keep full body in frame
                "image_size": "portrait_4_3",
                "seed": SEED,
                "output_format": "jpeg",
            },
            with_logs=False,
        )
        u = (res.get("images") or [{}])[0].get("url")
        if not u:
            print(f"NO IMAGE keys={list(res.keys())}")
            continue
        slots[slot] = u
        _download(u, OUT / f"{stem}_view_{tag}.jpg")
        print(f"ok ({time.time()-t:.0f}s)")
    return slots


def build_mesh(front_url, slots, stem):
    """Path A with multi-view + PBR + high detail."""
    import fal_client
    args = {
        "input_image_url": front_url,
        "generate_type": "Normal",
        "enable_pbr": True,
        "face_count": 1_000_000,
        **slots,
    }
    print(f"[hunyuan] multi-view ({len(slots)} extra views), PBR on, 1M faces ...")
    t = time.time()
    res = fal_client.subscribe(
        "fal-ai/hunyuan-3d/v3.1/pro/image-to-3d",
        arguments=args,
        with_logs=False,
    )
    dt = time.time() - t
    (OUT / f"{stem}_hybrid_raw.json").write_text(json.dumps(res, indent=2))
    glb = (res.get("model_glb") or {}).get("url") or (res.get("model_urls") or {}).get("glb")
    print(f"[hunyuan] done in {dt:.0f}s. keys={list(res.keys())}")
    if glb:
        dest = OUT / f"{stem}_hybrid.glb"
        _download(glb, dest)
        print(f"[hunyuan] GLB -> {dest.name} ({dest.stat().st_size//1024} KB)")
        return dest
    print("[hunyuan] NO GLB url — inspect _hybrid_raw.json")
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", required=True)
    a = ap.parse_args()
    photo = a.photo if os.path.isabs(a.photo) else str(ROOT / a.photo)
    if not os.path.exists(photo):
        photo = str(ROOT / "spike" / a.photo)
    if not os.path.exists(photo):
        raise SystemExit(f"photo not found: {a.photo}")
    load_fal_key()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    import fal_client

    stem = pathlib.Path(photo).stem
    print(f"[upload] {photo}")
    front_url = fal_client.upload_file(photo)

    slots = synth_views(front_url, stem)
    build_mesh(front_url, slots, stem)
    print("\nDONE. New mesh: spike/output/spin/%s_hybrid.glb" % stem)


if __name__ == "__main__":
    main()
