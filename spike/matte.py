#!/usr/bin/env python3
"""PhysiqAI spike: matte the orbit (remove background) + extract drag-spin frames.

  1. bria/video/background-removal on the 1080p orbit -> Transparent master (webm/alpha).
  2. ffmpeg (imageio-ffmpeg binary) -> RGBA PNG frames.
  3. Subsample to N, compute a SINGLE union alpha bounding-box across all frames,
     crop every frame to it (+pad) and resize -> subject is large, centered, and
     does not jiggle in scale while spinning. Writes spike/output/spin/scrub/f###.png.

Usage:
  spike/.venv/bin/python spike/matte.py --video spike/output/spin/bz02_IMG_7520_after_orbit_1080p.mp4 -n 96
"""
import argparse, json, logging, os, pathlib, subprocess, tempfile, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "spike" / "output" / "spin"


def load_fal_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("FAL_KEY="):
            os.environ["FAL_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")
            return
    raise SystemExit("FAL_KEY not found in .env")


def scrub_dir(tag):
    return OUT / "scrub" if tag == "bz02" else OUT / f"scrub_{tag}"


def matte(video_path, tag, video_url=None):
    import fal_client
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if video_url:
        url = video_url
        print(f"[matte] using hosted url (skip upload)")
    else:
        print(f"[matte] upload {pathlib.Path(video_path).name}")
        url = fal_client.upload_file(video_path)
    print("[matte] bria/video/background-removal (Transparent, webm_vp9) ...")
    res = fal_client.subscribe(
        "bria/video/background-removal",
        arguments={
            "video_url": url,
            "background_color": "Transparent",
            "output_container_and_codec": "webm_vp9",
            "preserve_audio": False,
        },
        with_logs=False,
    )
    (OUT / f"{tag}_matte_raw.json").write_text(json.dumps(res, indent=2))
    v = (res.get("video") or {}).get("url")
    if not v:
        raise SystemExit(f"[matte] no video url. keys={list(res.keys())}")
    dest = OUT / f"{tag}_orbit_transparent.webm"
    urllib.request.urlretrieve(v, dest)
    print(f"[matte] transparent master -> {dest.name} ({dest.stat().st_size//1024} KB)")
    return dest


def extract_frames(webm, n, tag):
    import imageio_ffmpeg
    from PIL import Image
    import numpy as np
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    tmp = pathlib.Path(tempfile.mkdtemp())
    print("[frames] decoding RGBA frames (vp9 alpha) ...")
    # -c:v libvpx-vp9 is REQUIRED to decode the webm alpha plane; the default
    # vp9 decoder silently drops it and every pixel comes back opaque.
    subprocess.run([ff, "-y", "-loglevel", "error", "-c:v", "libvpx-vp9", "-i", str(webm),
                    "-pix_fmt", "rgba", str(tmp / "raw_%04d.png")], check=True)
    raw = sorted(tmp.glob("raw_*.png"))
    if not raw:
        raise SystemExit("[frames] ffmpeg produced no frames")
    step = max(1, round(len(raw) / n))
    picks = raw[::step][:n]
    print(f"[frames] {len(raw)} decoded -> {len(picks)} kept (step {step})")

    # union alpha bbox across all kept frames (so scale/position is stable)
    ux0 = uy0 = 10**9; ux1 = uy1 = -1
    ims = []
    for p in picks:
        im = Image.open(p).convert("RGBA"); ims.append(im)
        a = np.asarray(im)[:, :, 3]
        ys, xs = np.where(a > 12)
        if len(xs):
            ux0 = min(ux0, xs.min()); ux1 = max(ux1, xs.max())
            uy0 = min(uy0, ys.min()); uy1 = max(uy1, ys.max())
    W, H = ims[0].size
    padx = int((ux1 - ux0) * 0.06); pady = int((uy1 - uy0) * 0.04)
    ux0 = max(0, ux0 - padx); uy0 = max(0, uy0 - pady)
    ux1 = min(W, ux1 + padx); uy1 = min(H, uy1 + pady)
    print(f"[frames] union bbox x[{ux0}:{ux1}] y[{uy0}:{uy1}] of {W}x{H}")

    SCRUB = scrub_dir(tag)
    SCRUB.mkdir(parents=True, exist_ok=True)
    for old in list(SCRUB.glob("*.jpg")) + list(SCRUB.glob("*.png")):
        old.unlink()
    target_h = 1280
    for i, im in enumerate(ims):
        c = im.crop((ux0, uy0, ux1, uy1))
        w = int(c.width * target_h / c.height)
        c = c.resize((w, target_h), Image.LANCZOS)
        c.save(SCRUB / f"f{i:03d}.png")
    print(f"[frames] wrote {len(ims)} PNGs -> {SCRUB} (each ~{w}x{target_h})")
    return len(ims)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--video-url", help="hosted video url -> skip the upload step")
    ap.add_argument("--from-master", help="skip API, extract from an existing transparent webm")
    ap.add_argument("--tag", default="bz02", help="subject id -> scrub_<tag>/ + <tag>_orbit_transparent.webm")
    ap.add_argument("-n", type=int, default=96)
    a = ap.parse_args()
    if a.from_master:
        master = pathlib.Path(a.from_master if os.path.isabs(a.from_master) else ROOT / a.from_master)
    else:
        load_fal_key()
        master = matte(a.video, a.tag, video_url=a.video_url)
    count = extract_frames(master, a.n, a.tag)
    print(f"\nDONE. {count} transparent frames + master webm in spike/output/spin/")


if __name__ == "__main__":
    main()
