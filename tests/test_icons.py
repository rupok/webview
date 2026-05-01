from __future__ import annotations

from pathlib import Path

from PIL import Image

from webview.icons import (
    LEGACY_SIZES,
    load_or_generate_source,
    write_adaptive_icon,
    write_legacy_mipmaps,
)


def test_letter_tile_when_no_icon_supplied():
    img = load_or_generate_source(None, app_name="Acme", color="#1976D2")
    assert img.size == (512, 512)
    assert img.mode == "RGBA"


def test_letter_tile_uses_first_letter():
    img = load_or_generate_source(None, app_name="zeta", color="#000000")
    assert img.size == (512, 512)


def test_load_supplied_icon_resizes(tmp_path: Path):
    src = tmp_path / "icon.png"
    Image.new("RGBA", (200, 400), (255, 0, 0, 255)).save(src)
    img = load_or_generate_source(src, app_name="X", color="#000000")
    assert img.size == (512, 512)


def test_legacy_mipmaps_written_at_each_density(tmp_path: Path):
    src = load_or_generate_source(None, app_name="A", color="#1976D2")
    written = write_legacy_mipmaps(src, tmp_path)
    for suffix, size in LEGACY_SIZES:
        path = tmp_path / f"mipmap-{suffix}/ic_launcher.png"
        assert path.exists()
        assert Image.open(path).size == (size, size)
    assert any("ic_launcher_round.png" in str(p) for p in written)


def test_adaptive_icon_written(tmp_path: Path):
    src = load_or_generate_source(None, app_name="A", color="#1976D2")
    write_adaptive_icon(src, tmp_path, background_color="#FFFFFF")
    fg = tmp_path / "mipmap-xxxhdpi/ic_launcher_foreground.png"
    assert fg.exists()
    assert Image.open(fg).size == (432, 432)
    xml = (tmp_path / "mipmap-anydpi-v26/ic_launcher.xml").read_text()
    assert "<adaptive-icon" in xml
