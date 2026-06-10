"""TDD for pipeline.avatar: orchestration, rebake logic, and pure frame helpers.

Stages (still/orbit/matte/extract) are dependency-injected fakes — no fal, no
network, no ffmpeg in this suite.  The extract pure helpers (extract_crop_box,
write_frame_pair) are tested with tiny synthetic RGBA arrays.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from pipeline.avatar import (
    AvatarResult,
    AvatarStages,
    extract_crop_box,
    run_avatar_pipeline,
    should_rebake,
    write_frame_pair,
)
from pipeline.engine_bridge import MorphSpec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _spec():
    return MorphSpec(
        direction="cut", months=6, weight_before_lb=192, weight_after_lb=182,
        weight_delta_lb=-10, bf_before=14, bf_after=9, bf_delta=-5,
        lean_delta_lb=-0.5, measurements_cm={"waist_cm": -4.0}, confidence_score=0.7,
        confidence_lo_lb=-12, confidence_hi_lb=-8,
    )


def _rgba_frame(H: int = 10, W: int = 10, body_slice=None, alpha: int = 255) -> np.ndarray:
    """Return an RGBA array with the body_slice rows/cols set to opaque."""
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    if body_slice is not None:
        r0, r1, c0, c1 = body_slice
        arr[r0:r1, c0:c1, :] = [200, 150, 100, alpha]
    return arr


# ---------------------------------------------------------------------------
# FakeAvatarStages
# ---------------------------------------------------------------------------

class FakeAvatarStages:
    """Records calls; returns scripted values; no I/O."""

    def __init__(
        self,
        after_img=None,
        orbit_raises=None,
        matte_raises=None,
        extract_raises=None,
        frame_count=96,
    ):
        # after_img: if None we fabricate a tiny 3-channel numpy array
        self._after_img = after_img if after_img is not None else np.zeros((4, 4, 3), dtype=np.uint8)
        self._orbit_raises = orbit_raises
        self._matte_raises = matte_raises
        self._extract_raises = extract_raises
        self._frame_count = frame_count
        self.calls: dict = {"still": 0, "orbit": 0, "matte": 0, "extract": 0}
        self.n_passed: list = []

    def still(self, photo_path: str, spec) -> np.ndarray:
        self.calls["still"] += 1
        return self._after_img

    def orbit(self, after_jpg_path: str) -> str:
        self.calls["orbit"] += 1
        if self._orbit_raises:
            raise self._orbit_raises
        return "/fake/orbit.mp4"

    def matte(self, orbit_mp4_path: str) -> str:
        self.calls["matte"] += 1
        if self._matte_raises:
            raise self._matte_raises
        return "/fake/master.webm"

    def extract(self, webm_path: str, n: int) -> int:
        self.calls["extract"] += 1
        self.n_passed.append(n)
        if self._extract_raises:
            raise self._extract_raises
        return self._frame_count

    def as_stages(self) -> AvatarStages:
        return AvatarStages(
            still=self.still,
            orbit=self.orbit,
            matte=self.matte,
            extract=self.extract,
        )


# ---------------------------------------------------------------------------
# run_avatar_pipeline — happy path
# ---------------------------------------------------------------------------

def test_happy_path_returns_ok(tmp_path):
    fs = FakeAvatarStages()
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages())
    assert result.ok is True
    assert result.error is None
    assert result.frame_count == 96
    assert fs.calls == {"still": 1, "orbit": 1, "matte": 1, "extract": 1}


def test_happy_path_emits_statuses_in_order(tmp_path):
    fs = FakeAvatarStages()
    events: list = []
    run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages(),
                        on_status=lambda s, p: events.append((s, p)))
    statuses = [e[0] for e in events]
    pcts = [e[1] for e in events]
    assert statuses == ["after_still", "orbiting", "matting", "extracting", "done"]
    # pcts must be strictly increasing
    assert pcts == sorted(pcts)
    assert pcts[-1] == 100


def test_happy_path_after_jpg_written(tmp_path):
    fs = FakeAvatarStages()
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages())
    assert (tmp_path / "after.jpg").exists()
    assert result.after_path == str(tmp_path / "after.jpg")


def test_n_frames_passed_through(tmp_path):
    fs = FakeAvatarStages()
    run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages(), n_frames=48)
    assert fs.n_passed == [48]


def test_result_paths_populated(tmp_path):
    fs = FakeAvatarStages()
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages())
    assert result.after_path is not None
    assert result.orbit_path == "/fake/orbit.mp4"
    assert result.master_path == "/fake/master.webm"


# ---------------------------------------------------------------------------
# run_avatar_pipeline — failure paths
# ---------------------------------------------------------------------------

def test_orbit_failure_returns_not_ok(tmp_path):
    boom = RuntimeError("seedance timeout")
    fs = FakeAvatarStages(orbit_raises=boom)
    events: list = []
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages(),
                                 on_status=lambda s, p: events.append((s, p)))
    assert result.ok is False
    assert "seedance timeout" in result.error
    assert result.frame_count == 0
    # last status emitted is "failed"
    assert events[-1][0] == "failed"
    # still stage did run (after.jpg written), orbit did not
    assert fs.calls["orbit"] == 1
    assert fs.calls["matte"] == 0
    assert fs.calls["extract"] == 0


def test_still_failure_returns_not_ok_no_after(tmp_path):
    class _BadStages(FakeAvatarStages):
        def still(self, photo_path, spec):
            raise RuntimeError("fal down")
    fs = _BadStages()
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages())
    assert result.ok is False
    assert result.after_path is None
    assert not (tmp_path / "after.jpg").exists()


def test_matte_failure_after_orbit_still_populated(tmp_path):
    fs = FakeAvatarStages(matte_raises=RuntimeError("bria 500"))
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages())
    assert result.ok is False
    assert result.after_path is not None
    assert result.orbit_path == "/fake/orbit.mp4"
    assert result.master_path is None


def test_extract_failure_after_matte_still_populated(tmp_path):
    fs = FakeAvatarStages(extract_raises=RuntimeError("no frames"))
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages())
    assert result.ok is False
    assert result.master_path == "/fake/master.webm"
    assert result.frame_count == 0


def test_failed_status_emitted_on_each_stage_failure(tmp_path):
    for raises_kwarg in ("orbit_raises", "matte_raises", "extract_raises"):
        events: list = []
        fs = FakeAvatarStages(**{raises_kwarg: RuntimeError("boom")})
        run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages(),
                            on_status=lambda s, p: events.append((s, p)))
        assert events[-1][0] == "failed", f"no failed event for {raises_kwarg}"


def test_on_status_none_does_not_crash(tmp_path):
    fs = FakeAvatarStages()
    result = run_avatar_pipeline("photo.jpg", _spec(), tmp_path, fs.as_stages(),
                                 on_status=None)
    assert result.ok is True


# ---------------------------------------------------------------------------
# should_rebake
# ---------------------------------------------------------------------------

def _proj(weight_after=180.0, bf_after=10.0, direction="cut"):
    return {"weight_after_lb": weight_after, "bf_after": bf_after, "direction": direction}


def test_no_rebake_under_all_thresholds():
    ok, reasons = should_rebake(_proj(180.0, 10.0, "cut"), _proj(181.9, 10.9, "cut"))
    assert ok is False
    assert reasons == []


def test_rebake_on_weight_exactly_threshold():
    ok, reasons = should_rebake(_proj(180.0), _proj(182.0))
    assert ok is True
    assert any("weight" in r for r in reasons)


def test_rebake_on_weight_above_threshold():
    ok, reasons = should_rebake(_proj(180.0), _proj(183.5))
    assert ok is True
    assert any("3.5" in r for r in reasons)


def test_no_rebake_on_weight_below_threshold():
    ok, _ = should_rebake(_proj(180.0), _proj(181.9))
    assert ok is False


def test_rebake_on_bf_exactly_threshold():
    ok, reasons = should_rebake(_proj(bf_after=10.0), _proj(bf_after=11.0))
    assert ok is True
    assert any("fat" in r for r in reasons)


def test_rebake_on_bf_above_threshold():
    ok, reasons = should_rebake(_proj(bf_after=10.0), _proj(bf_after=12.5))
    assert ok is True
    assert any("fat" in r for r in reasons)


def test_no_rebake_on_bf_below_threshold():
    ok, _ = should_rebake(_proj(bf_after=10.0), _proj(bf_after=10.9))
    assert ok is False


def test_rebake_on_direction_change():
    ok, reasons = should_rebake(_proj(direction="cut"), _proj(direction="gain"))
    assert ok is True
    assert any("direction" in r for r in reasons)


def test_no_rebake_same_direction():
    ok, _ = should_rebake(_proj(direction="recomp"), _proj(direction="recomp"))
    assert ok is False


def test_multiple_reasons_accumulate():
    ok, reasons = should_rebake(
        _proj(180.0, 10.0, "cut"),
        _proj(183.0, 12.0, "gain"),
    )
    assert ok is True
    assert len(reasons) == 3  # weight + bf + direction


# ---------------------------------------------------------------------------
# extract_crop_box — pure geometry
# ---------------------------------------------------------------------------

def test_crop_box_single_frame_tight():
    arr = _rgba_frame(20, 20, body_slice=(5, 15, 4, 16))
    x0, y0, x1, y1 = extract_crop_box([arr], pad_x_frac=0.0, pad_y_frac=0.0)
    assert x0 == 4
    assert y0 == 5
    assert x1 == 16   # xs.max()=15 inclusive -> +1 = exclusive PIL crop bound
    assert y1 == 15   # ys.max()=14 inclusive -> +1


def test_crop_box_union_across_frames():
    # frame 0 has pixels in left half, frame 1 in right half
    f0 = _rgba_frame(20, 20, body_slice=(2, 18, 0, 10))
    f1 = _rgba_frame(20, 20, body_slice=(2, 18, 10, 20))
    x0, y0, x1, y1 = extract_crop_box([f0, f1], pad_x_frac=0.0, pad_y_frac=0.0)
    assert x0 == 0
    assert x1 == 20   # xs.max()=19 across both frames -> +1 exclusive


def test_crop_box_adds_padding():
    arr = _rgba_frame(100, 100, body_slice=(10, 90, 10, 90))
    x0, y0, x1, y1 = extract_crop_box([arr], pad_x_frac=0.06, pad_y_frac=0.04)
    # bbox width = 79 (90-10-1 = 79 px), pad_x = int(79 * 0.06) = 4
    # bbox height = 79, pad_y = int(79 * 0.04) = 3
    assert x0 < 10   # padded inward from left
    assert y0 < 10


def test_crop_box_clamps_to_image_bounds():
    arr = _rgba_frame(10, 10, body_slice=(0, 10, 0, 10))
    x0, y0, x1, y1 = extract_crop_box([arr])
    assert x0 >= 0
    assert y0 >= 0
    assert x1 <= 10
    assert y1 <= 10


def test_crop_box_all_transparent_returns_full_frame():
    arr = np.zeros((20, 30, 4), dtype=np.uint8)
    x0, y0, x1, y1 = extract_crop_box([arr])
    assert (x0, y0, x1, y1) == (0, 0, 30, 20)


def test_crop_box_requires_at_least_one_frame():
    with pytest.raises(ValueError):
        extract_crop_box([])


# ---------------------------------------------------------------------------
# write_frame_pair — frame writing helper (no ffmpeg needed)
# ---------------------------------------------------------------------------

def test_write_frame_pair_creates_png_and_webp(tmp_path):
    from PIL import Image as PILImage
    frames_dir = tmp_path / "frames"
    frames_mobile_dir = tmp_path / "frames_mobile"
    frames_dir.mkdir()
    frames_mobile_dir.mkdir()

    # 40×40 solid magenta RGBA image
    img = PILImage.new("RGBA", (40, 40), (255, 0, 255, 255))
    crop_box = (0, 0, 40, 40)
    write_frame_pair(img, crop_box, 0, frames_dir, frames_mobile_dir)

    png = frames_dir / "f000.png"
    webp = frames_mobile_dir / "f000.webp"
    assert png.exists()
    assert webp.exists()


def test_write_frame_pair_correct_heights(tmp_path):
    from PIL import Image as PILImage
    frames_dir = tmp_path / "frames"
    frames_mobile_dir = tmp_path / "frames_mobile"
    frames_dir.mkdir()
    frames_mobile_dir.mkdir()

    img = PILImage.new("RGBA", (200, 400), (100, 200, 50, 255))
    crop_box = (0, 0, 200, 400)
    write_frame_pair(img, crop_box, 3, frames_dir, frames_mobile_dir)

    full = PILImage.open(frames_dir / "f003.png")
    mob = PILImage.open(frames_mobile_dir / "f003.webp")
    assert full.height == 1280
    assert mob.height == 800


def test_write_frame_pair_crops_before_resize(tmp_path):
    from PIL import Image as PILImage
    frames_dir = tmp_path / "frames"
    frames_mobile_dir = tmp_path / "frames_mobile"
    frames_dir.mkdir()
    frames_mobile_dir.mkdir()

    # 200×100 image; crop the left 100×100 half
    img = PILImage.new("RGBA", (200, 100), (0, 128, 255, 255))
    # Draw a red rectangle in the right half (should not appear after crop)
    for x in range(100, 200):
        for y in range(100):
            img.putpixel((x, y), (255, 0, 0, 255))

    crop_box = (0, 0, 100, 100)
    write_frame_pair(img, crop_box, 0, frames_dir, frames_mobile_dir)

    full = PILImage.open(frames_dir / "f000.png")
    # the full image should be square (100×100 -> 1280×1280)
    assert full.height == 1280
    assert full.width == 1280
    # no red pixels should be present (the right half was cropped away)
    arr = np.asarray(full.convert("RGBA"))
    red_pixels = np.sum((arr[:, :, 0] > 200) & (arr[:, :, 1] < 50) & (arr[:, :, 2] < 50))
    assert red_pixels == 0


def test_write_frame_pair_index_naming(tmp_path):
    from PIL import Image as PILImage
    frames_dir = tmp_path / "frames"
    frames_mobile_dir = tmp_path / "frames_mobile"
    frames_dir.mkdir()
    frames_mobile_dir.mkdir()

    img = PILImage.new("RGBA", (10, 10), (0, 0, 0, 255))
    for i in [0, 5, 95]:
        write_frame_pair(img, (0, 0, 10, 10), i, frames_dir, frames_mobile_dir)

    assert (frames_dir / "f000.png").exists()
    assert (frames_dir / "f005.png").exists()
    assert (frames_dir / "f095.png").exists()
    assert (frames_mobile_dir / "f000.webp").exists()
    assert (frames_mobile_dir / "f095.webp").exists()
