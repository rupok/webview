"""Launcher-icon generation.

Given a single source PNG, emit the legacy mipmap sizes plus an adaptive
icon (foreground + flat background color). If the user provides no icon,
we generate a flat letter-tile from the app name.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# (mipmap directory suffix, edge in pixels)
LEGACY_SIZES: list[tuple[str, int]] = [
    ("mdpi", 48),
    ("hdpi", 72),
    ("xhdpi", 96),
    ("xxhdpi", 144),
    ("xxxhdpi", 192),
]

# Adaptive icons require a 108dp asset where the inner 72dp is "safe".
# We render a 432x432 foreground (xxxhdpi) leaving 25% padding on each side.
ADAPTIVE_FOREGROUND_PX = 432
ADAPTIVE_FOREGROUND_SAFE_PX = 288


def write_legacy_mipmaps(source: Image.Image, res_dir: Path) -> list[Path]:
    """Write ic_launcher and ic_launcher_round PNGs to mipmap-* dirs."""
    written: list[Path] = []
    for suffix, size in LEGACY_SIZES:
        out_dir = res_dir / f"mipmap-{suffix}"
        out_dir.mkdir(parents=True, exist_ok=True)
        square = _square_resize(source, size)
        square_path = out_dir / "ic_launcher.png"
        square.save(square_path)
        written.append(square_path)

        round_path = out_dir / "ic_launcher_round.png"
        _circle_mask(square).save(round_path)
        written.append(round_path)
    return written


def write_adaptive_icon(
    source: Image.Image,
    res_dir: Path,
    *,
    background_color: str,
) -> list[Path]:
    """Write the adaptive-icon foreground PNG and the XML wiring."""
    written: list[Path] = []

    foreground = Image.new("RGBA", (ADAPTIVE_FOREGROUND_PX, ADAPTIVE_FOREGROUND_PX), (0, 0, 0, 0))
    inner = _square_resize(source, ADAPTIVE_FOREGROUND_SAFE_PX)
    offset = (ADAPTIVE_FOREGROUND_PX - ADAPTIVE_FOREGROUND_SAFE_PX) // 2
    foreground.paste(inner, (offset, offset), inner if inner.mode == "RGBA" else None)

    fg_dir = res_dir / "mipmap-xxxhdpi"
    fg_dir.mkdir(parents=True, exist_ok=True)
    fg_path = fg_dir / "ic_launcher_foreground.png"
    foreground.save(fg_path)
    written.append(fg_path)

    values_dir = res_dir / "values"
    values_dir.mkdir(parents=True, exist_ok=True)
    colors_path = values_dir / "ic_launcher_background.xml"
    colors_path.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        f'    <color name="ic_launcher_background">{background_color}</color>\n'
        "</resources>\n"
    )
    written.append(colors_path)

    for filename in ("ic_launcher.xml", "ic_launcher_round.xml"):
        anyhdpi_dir = res_dir / "mipmap-anydpi-v26"
        anyhdpi_dir.mkdir(parents=True, exist_ok=True)
        path = anyhdpi_dir / filename
        path.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
            '    <background android:drawable="@color/ic_launcher_background" />\n'
            '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />\n'
            "</adaptive-icon>\n"
        )
        written.append(path)
    return written


def load_or_generate_source(icon_path: Path | None, *, app_name: str, color: str) -> Image.Image:
    """Load the user's icon or synthesize a letter tile from the app name."""
    if icon_path is not None:
        if not icon_path.exists():
            raise FileNotFoundError(f"icon not found: {icon_path}")
        img = Image.open(icon_path).convert("RGBA")
        return _square_resize(img, 512)
    return _letter_tile(app_name, color=color, size=512)


def _square_resize(img: Image.Image, size: int) -> Image.Image:
    img = img.convert("RGBA")
    if img.width != img.height:
        edge = max(img.width, img.height)
        canvas = Image.new("RGBA", (edge, edge), (0, 0, 0, 0))
        canvas.paste(img, ((edge - img.width) // 2, (edge - img.height) // 2))
        img = canvas
    return img.resize((size, size), Image.Resampling.LANCZOS)


def _circle_mask(img: Image.Image) -> Image.Image:
    size = img.size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0, *size), fill=255)
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def _letter_tile(name: str, *, color: str, size: int) -> Image.Image:
    bg = _hex_to_rgb(color)
    fg = (255, 255, 255, 255)
    img = Image.new("RGBA", (size, size), (*bg, 255))
    draw = ImageDraw.Draw(img)

    letter = (name.strip()[:1] or "W").upper()
    font = _best_font(int(size * 0.6))
    bbox = draw.textbbox((0, 0), letter, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
        letter,
        fill=fg,
        font=font,
    )
    return img


def _best_font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def encode_png(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
