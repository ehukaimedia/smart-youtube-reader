#!/usr/bin/env python3
"""Render infographic HTML to brand-spec WebP teaching images.

This is the Claude image path for the Smart YouTube Reader demo digest and any
AI-digest teaching image: author HTML/CSS/SVG, render it with headless Chrome at
2x for crisp type, then downsample to a 1280x720 WebP with cwebp.

Usage:
    python3 render_to_webp.py <input.html | input_dir> <output_dir>

Options:
    --size 1280x720     output WebP dimensions (default 1280x720)
    --scale 2           device scale factor for supersampling (default 2)
    --quality 82        cwebp quality (default 82)

Requirements (already present in this repo's environment):
    - Google Chrome installed (Playwright drives it via channel="chrome")
    - python3 -m pip install playwright   (the `playwright` package; no browser
      download needed when using channel="chrome")
    - cwebp on PATH (brew install webp)

Fonts: each HTML should reference Inter via @font-face from a `fonts/` dir next
to it (see setup_fonts.sh and infographic_kit.py). file:// rendering resolves
those relative paths. If Inter is absent, Chrome falls back to the system sans.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile


def render_html(html_path: pathlib.Path, png_path: pathlib.Path, w: int, h: int, scale: int) -> None:
    from playwright.sync_api import sync_playwright

    url = "file://" + str(html_path.resolve())
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", args=["--force-color-profile=srgb"])
        try:
            page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
            page.goto(url, wait_until="networkidle")
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(300)
            page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": w, "height": h})
        finally:
            browser.close()


def to_webp(png_path: pathlib.Path, webp_path: pathlib.Path, w: int, h: int, quality: int) -> None:
    subprocess.run(
        ["cwebp", "-q", str(quality), "-resize", str(w), str(h), str(png_path), "-o", str(webp_path)],
        check=True, capture_output=True,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="HTML file or directory of .html files")
    ap.add_argument("output_dir", help="directory to write .webp files into")
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--quality", type=int, default=82)
    args = ap.parse_args()

    if shutil.which("cwebp") is None:
        print("error: cwebp not found on PATH (try: brew install webp)", file=sys.stderr)
        return 2

    w, h = (int(x) for x in args.size.lower().split("x"))
    src = pathlib.Path(args.input)
    out_dir = pathlib.Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    htmls = sorted(src.glob("*.html")) if src.is_dir() else [src]
    if not htmls:
        print(f"error: no HTML found at {src}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = pathlib.Path(tmp)
        for html in htmls:
            name = html.stem
            png = tmp_dir / f"{name}.png"
            webp = out_dir / f"{name}.webp"
            render_html(html, png, w, h, args.scale)
            to_webp(png, webp, w, h, args.quality)
            print(f"OK {webp.name} ({webp.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
