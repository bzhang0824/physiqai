"""Share card composer for PhysiqAI.

render_share_card(after_img, projection, *, before_img=None) -> PIL.Image

Canvas: 1080 x 1350 white (4:5 Instagram/social ratio).
Layout:
  - Headline (top)
  - Image area: after-only or before|after side-by-side in a rounded rect
  - Stat rows: weight before->after, bf before->after, lean gain, confidence
  - Footer: bold PHYSIQAI wordmark + URL + disclaimer

Font: Inter variable (OFL), vendored at server/assets/fonts/Inter.ttf.
      Uses set_variation_by_name('Bold') / ('Regular') for weight switching.
"""
from __future__ import annotations

import pathlib
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

_FONTS_DIR = pathlib.Path(__file__).resolve().parent / "assets" / "fonts"
_INTER_TTF = _FONTS_DIR / "Inter.ttf"

# Canvas dimensions
_W, _H = 1080, 1350

# Palette
_WHITE  = (255, 255, 255)
_BLACK  = (15,  15,  15)
_GRAY   = (120, 120, 120)
_ACCENT = (50,  100, 200)   # blue accent for headline
_BG     = (245, 246, 248)   # very light gray image area

# Layout constants (px)
_MARGIN   = 60
_IMG_TOP  = 140
_IMG_H    = 600
_STATS_TOP = _IMG_TOP + _IMG_H + 40
_FOOTER_Y  = _H - 80

_CORNER_RADIUS = 28


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Inter at the requested size and weight variation."""
    f = ImageFont.truetype(str(_INTER_TTF), size)
    try:
        f.set_variation_by_name("Bold" if bold else "Regular")
    except (AttributeError, OSError):
        pass  # fallback: single-weight TTF used as-is
    return f


def _rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill) -> None:
    """Draw a filled rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def _paste_fit(canvas: Image.Image, img: Image.Image, box: tuple) -> None:
    """Fit-and-centre `img` into `box` (x0, y0, x1, y1) on `canvas`.

    Maintains aspect ratio; blank area filled with _BG.
    """
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0

    # Scale to fit
    iw, ih = img.size
    scale = min(bw / iw, bh / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    resized = img.resize((nw, nh), Image.LANCZOS)

    # Centre in box
    ox = x0 + (bw - nw) // 2
    oy = y0 + (bh - nh) // 2
    canvas.paste(resized, (ox, oy))


def render_share_card(
    after_img: Image.Image,
    projection: dict,
    *,
    before_img: Optional[Image.Image] = None,
) -> Image.Image:
    """Compose a 1080x1350 share card and return it as a PIL Image.

    Args:
        after_img: The generated "after" photo (any size; will be fit-scaled).
        projection: Engine projection dict (same shape as /transform response).
        before_img: Optional "before" photo for side-by-side layout.

    Returns:
        A 1080x1350 RGB PIL Image ready to be saved as PNG.
    """
    canvas = Image.new("RGB", (_W, _H), _WHITE)
    draw = ImageDraw.Draw(canvas)

    months = projection.get("months", "?")

    # ── Headline ────────────────────────────────────────────────────────────
    headline_text = f"My {months}-month projection"
    h_font = _font(52, bold=True)
    draw.text((_MARGIN, 52), headline_text, font=h_font, fill=_ACCENT)

    # ── Image area ──────────────────────────────────────────────────────────
    img_box_x0 = _MARGIN
    img_box_x1 = _W - _MARGIN
    img_box_y0 = _IMG_TOP
    img_box_y1 = _IMG_TOP + _IMG_H

    # Background rounded rect
    _rounded_rect(draw, (img_box_x0, img_box_y0, img_box_x1, img_box_y1),
                  _CORNER_RADIUS, _BG)

    pad = 12
    if before_img is not None:
        # Side-by-side: before on left, after on right
        mid = (_W) // 2
        _paste_fit(canvas, before_img,
                   (img_box_x0 + pad, img_box_y0 + pad, mid - pad, img_box_y1 - pad))
        _paste_fit(canvas, after_img,
                   (mid + pad, img_box_y0 + pad, img_box_x1 - pad, img_box_y1 - pad))

        # Labels
        lbl_font = _font(26, bold=True)
        draw.text((img_box_x0 + pad + 8, img_box_y0 + pad + 8), "BEFORE",
                  font=lbl_font, fill=_GRAY)
        draw.text((mid + pad + 8, img_box_y0 + pad + 8), "AFTER",
                  font=lbl_font, fill=_GRAY)
    else:
        _paste_fit(canvas, after_img,
                   (img_box_x0 + pad, img_box_y0 + pad, img_box_x1 - pad, img_box_y1 - pad))

    # ── Stat rows ───────────────────────────────────────────────────────────
    stat_font_bold  = _font(34, bold=True)
    stat_font       = _font(30, bold=False)
    label_font      = _font(26, bold=False)

    def _stat_row(y: int, label: str, value: str) -> int:
        draw.text((_MARGIN, y), label, font=label_font, fill=_GRAY)
        draw.text((_MARGIN + 320, y), value, font=stat_font_bold, fill=_BLACK)
        return y + 52

    y = _STATS_TOP

    w_before = projection.get("weight_before_lb")
    w_after  = projection.get("weight_after_lb")
    if w_before is not None and w_after is not None:
        y = _stat_row(y, "Weight", f"{w_before:.0f} → {w_after:.0f} lb")

    bf_before = projection.get("bf_before")
    bf_after  = projection.get("bf_after")
    if bf_before is not None and bf_after is not None:
        y = _stat_row(y, "Body fat", f"{bf_before:.1f}% → {bf_after:.1f}%")

    lean = projection.get("lean_delta_lb")
    if lean is not None:
        sign = "+" if lean >= 0 else ""
        y = _stat_row(y, "Lean gain", f"{sign}{lean:.1f} lb")

    conf = projection.get("confidence_score")
    if conf is not None:
        y = _stat_row(y, "Confidence", f"{int(round(conf * 100))}%")

    # ── Footer ───────────────────────────────────────────────────────────────
    footer_bold_font = _font(30, bold=True)
    footer_sm_font   = _font(22, bold=False)
    disclaimer_font  = _font(18, bold=False)

    draw.text((_MARGIN, _FOOTER_Y - 30), "PHYSIQAI",
              font=footer_bold_font, fill=_BLACK)
    draw.text((_MARGIN + 150, _FOOTER_Y - 30), "dist-nine-kappa-20.vercel.app",
              font=footer_sm_font, fill=_GRAY)
    draw.text((_MARGIN, _FOOTER_Y + 8),
              "AI projection — estimate, not a guarantee",
              font=disclaimer_font, fill=_GRAY)

    return canvas
