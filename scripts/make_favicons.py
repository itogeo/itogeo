#!/usr/bin/env python
"""Generate the browser-tab icon set from data/logo.jpg (actually a transparent PNG).

The full lockup is unusable as a favicon: at 16px the "ITO GEOSPATIAL" wordmark
collapses into a grey smudge. So the icon is the *mark* only -- the orbit ellipse
with the satellite crossing it -- which is what the logo is recognised by anyway.

Two things here only matter at 16px, and both mirror robigus-bio/app/icon.svg:
  * a filled navy ground, so the icon is a solid tile on any tab strip rather
    than a few floating cyan pixels;
  * the orbit stroke is dilated ~18px in the 805px source, because at its native
    ~12px it rasterises to under a fifth of a pixel and disappears entirely.

The letters are removed by colour separation: the orbit is cyan, everything else
is black, and the satellite is the set of black connected components sitting in
the upper right (ids 1,2,3,4,5,9) -- the rest of the black is the wordmark.

Run:  /Users/ianvandusen/anaconda3/envs/geodata/bin/python scripts/make_favicons.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "logo.jpg"

NAVY = (22, 44, 77, 255)      # --navy-900
ORBIT = (110, 200, 232)       # brand cyan, lifted for contrast on navy
SATELLITE = (255, 255, 255)
SAT_COMPONENTS = [1, 2, 3, 4, 5, 9]
ORBIT_DILATE = 18
SAT_DILATE = 6


def masks():
    im = Image.open(SRC).convert("RGBA")
    a = np.array(im)
    r, g, b, alpha = (a[..., i].astype(int) for i in range(4))
    ink = alpha > 60
    blue = ink & (b > 120) & ((b - r) > 40)
    dark = ink & (r < 110) & (g < 110) & (b < 110)
    labels, _ = ndimage.label(dark)
    sat = np.isin(labels, SAT_COMPONENTS)
    st = ndimage.generate_binary_structure(2, 2)
    return (
        ndimage.binary_dilation(blue, st, iterations=ORBIT_DILATE),
        ndimage.binary_dilation(sat, st, iterations=SAT_DILATE),
    )


def render(orbit_m, sat_m, size, rounded=True, pad=0.08):
    h, w = orbit_m.shape
    c = np.zeros((h, w, 4), np.uint8)
    c[orbit_m] = (*ORBIT, 255)
    c[sat_m] = (*SATELLITE, 255)
    mark = Image.fromarray(c)
    mark = mark.crop(mark.getchannel("A").getbbox())

    inner = int(size * (1 - 2 * pad))
    mw, mh = mark.size
    s = min(inner / mw, inner / mh)
    mark = mark.resize((max(1, int(mw * s)), max(1, int(mh * s))), Image.LANCZOS)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    if rounded:
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.1875), fill=NAVY)
    else:
        d.rectangle([0, 0, size - 1, size - 1], fill=NAVY)
    out.alpha_composite(mark, ((size - mark.size[0]) // 2, (size - mark.size[1]) // 2))
    return out


def main():
    orbit_m, sat_m = masks()
    # Pillow builds every ICO entry by downsampling this one base image, so render
    # it large; passing a list via append_images silently keeps only the first.
    render(orbit_m, sat_m, 256).save(
        ROOT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)]
    )
    render(orbit_m, sat_m, 32).save(ROOT / "favicon-32.png")
    render(orbit_m, sat_m, 192).save(ROOT / "icon-192.png")
    render(orbit_m, sat_m, 512).save(ROOT / "icon-512.png")
    # iOS applies its own corner mask, so ship this one square and full-bleed.
    render(orbit_m, sat_m, 180, rounded=False).save(ROOT / "apple-touch-icon.png")
    print("wrote favicon.ico, favicon-32.png, icon-192.png, icon-512.png, apple-touch-icon.png")


if __name__ == "__main__":
    main()
