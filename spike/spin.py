#!/usr/bin/env python3
"""PhysiqAI Phase-0.5 spike: can we make a PHOTOREAL ROTATABLE future-self?

Tests the two most promising paths surfaced by the 2026-06 model re-survey:
  A) image-to-3D textured mesh  (fal-ai/hunyuan-3d/v3.1/pro/image-to-3d)
       -> a real GLB you can spin in any WebGL viewer; consistency is free.
  B) multi-angle 2D generation  (fal-ai/flux-2-lora-gallery/multiple-angles)
       -> discrete azimuths; tests cross-angle identity, and can synth the
          side/back views to feed A's multi-view input.

Eyes-on real output only. Reuses an existing Arch-A "after" still as input.

Usage:
  spike/.venv/bin/python spike/spin.py mesh   --photo output/bz_trackA/bz02_IMG_7520_after.jpg
  spike/.venv/bin/python spike/spin.py angles --photo output/bz_trackA/bz02_IMG_7520_after.jpg
"""
import argparse, json, logging, os, pathlib, sys, time, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "spike" / "output" / "spin"
OUT.mkdir(parents=True, exist_ok=True)


def load_fal_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("FAL_KEY="):
            os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    raise SystemExit("FAL_KEY not found in .env")


def _download(url, dest):
    urllib.request.urlretrieve(url, dest)
    return dest


def run_mesh(photo):
    """Path A: single image -> textured GLB."""
    import fal_client
    logging.getLogger("httpx").setLevel(logging.WARNING)
    stem = pathlib.Path(photo).stem
    print(f"[mesh] uploading {photo} ...")
    url = fal_client.upload_file(photo)
    t = time.time()
    print("[mesh] calling fal-ai/hunyuan-3d/v3.1/pro/image-to-3d (textured) ...")
    res = fal_client.subscribe(
        "fal-ai/hunyuan-3d/v3.1/pro/image-to-3d",
        arguments={"input_image_url": url, "generate_type": "Normal"},
        with_logs=False,
    )
    dt = time.time() - t
    (OUT / f"{stem}_mesh_raw.json").write_text(json.dumps(res, indent=2))
    glb = (res.get("model_glb") or {}).get("url") or \
          ((res.get("model_urls") or {}).get("glb"))
    print(f"[mesh] done in {dt:.0f}s. response keys: {list(res.keys())}")
    if glb:
        dest = OUT / f"{stem}.glb"
        _download(glb, dest)
        print(f"[mesh] GLB -> {dest} ({dest.stat().st_size//1024} KB)")
    else:
        print("[mesh] NO GLB url in response — inspect _mesh_raw.json")
    return res


def run_angles(photo, azimuths=(0, 90, 180, 270)):
    """Path B: discrete-angle 2D generations (identity-across-angles check)."""
    import fal_client
    logging.getLogger("httpx").setLevel(logging.WARNING)
    stem = pathlib.Path(photo).stem
    print(f"[angles] uploading {photo} ...")
    url = fal_client.upload_file(photo)
    saved = []
    for az in azimuths:
        t = time.time()
        print(f"[angles] azimuth {az} ...")
        res = fal_client.subscribe(
            "fal-ai/flux-2-lora-gallery/multiple-angles",
            arguments={"image_urls": [url], "horizontal_angle": az,
                       "vertical_angle": 0, "distance": 5},
            with_logs=False,
        )
        u = (res.get("images") or [{}])[0].get("url")
        if u:
            dest = OUT / f"{stem}_az{az:03d}.jpg"
            _download(u, dest)
            saved.append(dest)
            print(f"[angles] az{az} -> {dest.name} ({time.time()-t:.0f}s)")
        else:
            print(f"[angles] az{az}: no image. keys={list(res.keys())}")
    # contact sheet
    if saved:
        from PIL import Image, ImageDraw
        ims = [Image.open(p).convert("RGB") for p in saved]
        H = 700
        ims = [im.resize((int(im.width * H / im.height), H)) for im in ims]
        W = sum(im.width for im in ims) + 8 * (len(ims) - 1)
        sheet = Image.new("RGB", (W, H + 30), (18, 18, 18))
        x = 0
        d = ImageDraw.Draw(sheet)
        for im, az in zip(ims, azimuths):
            sheet.paste(im, (x, 30))
            d.text((x + 6, 8), f"{az}deg", fill=(0, 255, 120))
            x += im.width + 8
        sheet_path = OUT / f"{stem}_angles_sheet.png"
        sheet.save(sheet_path)
        print(f"[angles] contact sheet -> {sheet_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["mesh", "angles"])
    ap.add_argument("--photo", required=True)
    a = ap.parse_args()
    photo = a.photo if os.path.isabs(a.photo) else str(ROOT / "spike" / a.photo)
    if not os.path.exists(photo):
        photo = str(ROOT / a.photo)
    if not os.path.exists(photo):
        raise SystemExit(f"photo not found: {a.photo}")
    load_fal_key()
    (run_mesh if a.mode == "mesh" else run_angles)(photo)


if __name__ == "__main__":
    main()
