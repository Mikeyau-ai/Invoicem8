"""Generate assets/icon.ico for the exe and the window/taskbar.

One source of truth for both: PyInstaller stamps this into InvoiceM8.exe and
the GUI calls iconbitmap() with the same file, so the taskbar and the
executable never drift apart.

Drawn in the shared RamBo palette (see gui/theme.py). Run after changing the
artwork:  python make_icon.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "assets" / "icon.ico"

# Matches gui.theme.C - the family palette these tools share.
BG = (26, 26, 26)          # panel  #1a1a1a
PAGE = (220, 220, 220)     # text   #dcdcdc
ACCENT = (76, 175, 80)     # green  #4caf50
LINE = (107, 107, 107)     # dim    #6b6b6b

#: Windows picks the nearest size; 16 and 32 are what the taskbar actually uses.
SIZES = [16, 24, 32, 48, 64, 128, 256]


def _draw(size: int = 1024) -> Image.Image:
    """Render the icon at a large size for clean downscaling."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size / 1024.0                      # scale helper: coords authored at 1024

    # Rounded dark tile.
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(180 * u), fill=BG)

    # Invoice page with a folded top-right corner.
    left, top, right, bottom = int(250 * u), int(190 * u), int(774 * u), int(834 * u)
    fold = int(150 * u)
    d.rounded_rectangle([left, top, right, bottom], radius=int(40 * u), fill=PAGE)
    d.polygon([(right - fold, top), (right, top + fold), (right - fold, top + fold)],
              fill=BG)

    # Text lines on the page - the top one accented so it reads as a document
    # even at 16px, where finer detail disappears.
    x0, x1 = left + int(70 * u), right - int(90 * u)
    for i, y in enumerate(range(int(330 * u), int(620 * u), int(90 * u))):
        end = x1 if i else x1 - int(120 * u)
        d.rounded_rectangle([x0, y, end, y + int(46 * u)],
                            radius=int(23 * u),
                            fill=ACCENT if i == 0 else LINE)

    # Green tick badge, bottom-right: "processed".
    cx, cy, r = int(735 * u), int(760 * u), int(190 * u)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT, outline=BG,
              width=int(34 * u))
    d.line([(cx - int(85 * u), cy), (cx - int(20 * u), cy + int(65 * u)),
            (cx + int(95 * u), cy - int(70 * u))],
           fill=BG, width=int(60 * u), joint="curve")
    return img


def main() -> int:
    """Write the multi-resolution .ico."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    master = _draw()
    frames = [master.resize((s, s), Image.LANCZOS) for s in SIZES]
    frames[-1].save(OUT, format="ICO",
                    sizes=[(s, s) for s in SIZES], append_images=frames[:-1])
    print(f"Wrote {OUT} ({', '.join(f'{s}x{s}' for s in SIZES)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
