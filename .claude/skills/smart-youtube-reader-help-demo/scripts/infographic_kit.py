#!/usr/bin/env python3
"""Reusable HTML/CSS kit for brand-spec AI-digest teaching cards (Claude image path).

Bakes in the docs/impeccable/DESIGN.md Section 7 art direction so generated cards
pass the acceptance checklist by construction: Inter type, Operator Blue (#3b82f6)
as the only accent, committed light (simple) or dark (premium) theme, generous
whitespace, no decorative shadows, no rainbow, no fake UI controls.

Use it to author content fast, then render with render_to_webp.py:

    from infographic_kit import simple_page, premium_page, node, arrow, glyph, write_pages
    pages = {
        "chapter-01-foo": simple_page("Capture", "Headline here", "One supporting line.",
            [("Start","Card title","Short body.","play"), ...]),       # 5 cards
        "chapter-01-foo-premium": premium_page("Capture", "Headline here", "Sub line.",
            node("play","Source","one link",300) + arrow() + node("folder","Archive","",300)),
    }
    write_pages(pages, "html")   # writes html/*.html (+ copies fonts/ in)
    # then: python3 render_to_webp.py html ../out/generated

Run this file directly to emit a 2-page smoke example into ./_kit_example/.
"""
import pathlib
import shutil

# ---- theme tokens (DESIGN.md Section 7) ----
ACCENT = "#3b82f6"
ACCENT_DEEP = "#2563eb"


def fonts_css(font_dir: str = "fonts") -> str:
    weights = (400, 500, 600, 700, 800)
    return "".join(
        f"@font-face{{font-family:Inter;src:url('{font_dir}/inter-{w}.woff2') format('woff2');font-weight:{w}}}"
        for w in weights
    )


GLYPHS = {
    "play": '<rect x="5" y="9" width="30" height="22" rx="5"/><path d="M17 16v8l7-4z" fill="#3b82f6" stroke="none"/>',
    "folder": '<path d="M5 13a3 3 0 0 1 3-3h7l3 4h14a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3z"/>',
    "chapters": '<rect x="6" y="9" width="28" height="6" rx="3"/><rect x="6" y="19" width="28" height="6" rx="3"/><rect x="6" y="29" width="18" height="6" rx="3"/>',
    "clock": '<circle cx="20" cy="20" r="14"/><path d="M20 12v8.5l5.5 3.3"/>',
    "image": '<rect x="6" y="9" width="28" height="22" rx="4"/><circle cx="14" cy="17" r="2.6" fill="#3b82f6" stroke="none"/><path d="M9 30l8-8 6 5 4-3.5 4 3.5"/>',
    "text": '<path d="M8 11h24M8 18h24M8 25h16"/>',
    "index": '<rect x="6" y="8" width="28" height="24" rx="4"/><path d="M15 8v24"/><path d="M19 15h10M19 21h10"/>',
    "doc": '<path d="M11 6h12l6 6v22a2 2 0 0 1-2 2H11a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z"/><path d="M23 6v6h6"/><path d="M14 20h12M14 26h9"/>',
    "send": '<path d="M7 20l26-11-7 26-6-11z"/><path d="M20 24l6-11"/>',
    "search": '<circle cx="18" cy="18" r="10"/><path d="M26 26l8 8"/>',
    "filter": '<path d="M7 9h26l-10 12v9l-6 3V21z"/>',
    "layers": '<path d="M20 6 6 14l14 8 14-8z"/><path d="M6 22l14 8 14-8"/>',
    "card": '<rect x="6" y="8" width="28" height="24" rx="4"/><rect x="11" y="13" width="18" height="7" rx="2"/><path d="M11 25h12"/>',
    "hash": '<path d="M15 7l-3 26M28 7l-3 26M9 16h24M7 26h24"/>',
    "check": '<circle cx="20" cy="20" r="14"/><path d="M13 20.5l5 5 9-11"/>',
    "venn": '<circle cx="16" cy="20" r="10"/><circle cx="24" cy="20" r="10"/>',
    "flag": '<path d="M11 7v26"/><path d="M11 9h17l-3 6 3 6H11z"/>',
    "bookmark": '<path d="M12 7h16v27l-8-6-8 6z"/>',
    "teach": '<rect x="6" y="8" width="28" height="19" rx="3"/><path d="M20 27v6M13 33h14"/>',
    "laptop": '<rect x="9" y="10" width="22" height="15" rx="2"/><path d="M5 31h30l-2-4H7z"/>',
    "network": '<circle cx="20" cy="9" r="4"/><circle cx="9" cy="30" r="4"/><circle cx="31" cy="30" r="4"/><path d="M18 12l-7 15M22 12l7 15M13 30h14"/>',
    "devices": '<rect x="6" y="11" width="19" height="13" rx="2"/><path d="M4 28h21"/><rect x="27" y="16" width="9" height="16" rx="2"/>',
    "link": '<path d="M17 23a6 6 0 0 1 0-8l4-4a6 6 0 0 1 9 9l-2 2"/><path d="M23 17a6 6 0 0 1 0 8l-4 4a6 6 0 0 1-9-9l2-2"/>',
    "shield": '<path d="M20 6l12 4v9c0 8-5 13-12 15-7-2-12-7-12-15v-9z"/><path d="M14 20l5 5 8-10"/>',
}


def glyph(name: str, size: int = 40, stroke: str = ACCENT, sw: float = 2.4) -> str:
    inner = GLYPHS[name]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{inner}</svg>')


# ---- simple (committed light) ----
_SIMPLE_CSS = """
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1280px;height:720px}
.stage{width:1280px;height:720px;background:#f5f5f7;font-family:Inter;padding:70px 80px;color:#1d1d1f;position:relative}
.eyebrow{font-weight:700;font-size:16px;letter-spacing:.16em;text-transform:uppercase;color:#2563eb}
.headline{font-weight:800;font-size:50px;line-height:1.05;letter-spacing:-.022em;margin-top:14px}
.sub{font-weight:400;font-size:20px;line-height:1.4;color:#6e6e73;margin-top:16px;max-width:820px}
.cards{position:absolute;left:80px;right:80px;bottom:70px;display:grid;grid-template-columns:repeat(5,1fr);gap:20px;height:316px}
.card{background:#fff;border:1px solid #e6e6ea;border-radius:18px;padding:24px 22px;display:flex;flex-direction:column}
.card.tint{background:#e8f0fb;border-color:#dbe7fb}
.step{font-weight:700;font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:#9a9aa1}
.card.tint .step{color:#5b7fc4}
.ct{font-weight:700;font-size:20px;line-height:1.15;letter-spacing:-.01em;margin-top:10px}
.cb{font-weight:400;font-size:15px;line-height:1.4;color:#6e6e73;margin-top:8px}
.gl{margin-top:auto;align-self:flex-start}svg{display:block}
"""

# ---- premium (committed dark) ----
_PREMIUM_CSS = """
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1280px;height:720px}
.stage{width:1280px;height:720px;background:#0c0d10;font-family:Inter;position:relative;padding:74px 80px 70px;color:#f5f5f7;overflow:hidden}
.eyebrow{font-weight:700;font-size:16px;letter-spacing:.16em;text-transform:uppercase;color:#3b82f6}
.headline{font-weight:800;font-size:52px;line-height:1.05;letter-spacing:-.022em;color:#f5f5f7;margin-top:16px;max-width:1010px}
.sub{font-weight:400;font-size:21px;line-height:1.45;color:#a1a1a6;margin-top:18px;max-width:820px}
.flow{position:absolute;left:80px;right:80px;bottom:70px;height:300px;display:flex;align-items:center}
.panel{border:1px solid rgba(255,255,255,.10);border-radius:22px;background:#14161b;height:300px}
.ptitle{display:flex;align-items:center;gap:12px;padding-bottom:16px;border-bottom:1px solid rgba(255,255,255,.08)}
.ptitle b{font-weight:700;font-size:18px;letter-spacing:-.01em}
.ptitle span{font-weight:500;font-size:14px;color:#6f7178;margin-left:auto}
.nodelabel{font-weight:600;font-size:19px;color:#f5f5f7;text-align:center}
.nodemeta{font-weight:500;font-size:13px;color:#80838b;text-align:center;margin-top:4px}
.arrow{flex:0 0 auto;display:flex;align-items:center;justify-content:center}
.pill{display:inline-flex;align-items:center;font-weight:600;font-size:14px;color:#cfe0fb;background:rgba(59,130,246,.16);border:1px solid rgba(59,130,246,.45);border-radius:999px;padding:5px 12px}
svg{display:block}
"""


def _doc(css: str, body: str, font_dir: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{fonts_css(font_dir)}{css}</style>'
            f'</head><body>{body}</body></html>')


def simple_page(eyebrow: str, headline: str, sub: str, cards, tint_index: int = 2, font_dir: str = "fonts") -> str:
    """cards: list of (step, title, body, glyph_name). 4-6 cards; one tinted for rhythm."""
    items = []
    for i, (step, title, body, gname) in enumerate(cards):
        cls = "card tint" if i == tint_index else "card"
        items.append(
            f'<div class="{cls}"><div class="step">{step}</div><div class="ct">{title}</div>'
            f'<div class="cb">{body}</div><div class="gl">{glyph(gname)}</div></div>')
    body = (f'<div class="stage"><div class="eyebrow">{eyebrow}</div><div class="headline">{headline}</div>'
            f'<div class="sub">{sub}</div><div class="cards">{"".join(items)}</div></div>')
    return _doc(_SIMPLE_CSS, body, font_dir)


def premium_page(eyebrow: str, headline: str, sub: str, flow_html: str, font_dir: str = "fonts") -> str:
    """flow_html: the focal composition; compose with node()/arrow()/panel markup."""
    body = (f'<div class="stage"><div class="eyebrow">{eyebrow}</div><div class="headline">{headline}</div>'
            f'<div class="sub">{sub}</div><div class="flow">{flow_html}</div></div>')
    return _doc(_PREMIUM_CSS, body, font_dir)


def node(glyph_name: str, label: str, meta: str = "", width: int = 300) -> str:
    return (f'<div class="panel" style="width:{width}px;flex:0 0 auto;display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;gap:22px"><div>{glyph(glyph_name, size=58, sw=2.2)}</div>'
            f'<div><div class="nodelabel">{label}</div><div class="nodemeta">{meta}</div></div></div>')


def arrow(width: int = 78) -> str:
    return ('<div class="arrow" style="width:%dpx;height:300px"><svg width="%d" height="40" viewBox="0 0 %d 40" fill="none">'
            '<path d="M2 20H%d" stroke="#3b82f6" stroke-width="2.6" stroke-linecap="round"/>'
            '<path d="M%d 13l8 7-8 7" stroke="#3b82f6" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
            '</svg></div>') % (width, width, width, width - 10, width - 12)


def write_pages(pages: dict, out_dir: str = "html", font_dir: str = "fonts") -> None:
    """Write {name: html} to out_dir/*.html and copy a sibling fonts/ dir in if present."""
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    src_fonts = pathlib.Path(font_dir)
    if src_fonts.is_dir():
        dst_fonts = out / "fonts"
        dst_fonts.mkdir(exist_ok=True)
        for f in src_fonts.glob("*.woff2"):
            shutil.copy2(f, dst_fonts / f.name)
    for name, html in pages.items():
        (out / f"{name}.html").write_text(html)
    print(f"wrote {len(pages)} html files to {out}")


if __name__ == "__main__":
    example = {
        "example-simple": simple_page(
            "Capture", "Video becomes structured context",
            "One supporting line that stays calm and concrete.",
            [("Start", "Paste a video link", "From one source URL.", "play"),
             ("Archive", "Save local evidence", "Files stay local.", "folder"),
             ("Chapters", "Split into topics", "Find the blocks.", "chapters"),
             ("Transcript", "Keep timestamps", "Jump to the moment.", "clock"),
             ("Frames", "Store visual proof", "Images as evidence.", "image")]),
        "example-premium": premium_page(
            "Capture", "Video becomes structured context",
            "An image-led editorial card on a committed dark theme.",
            node("play", "Source video", "one link", 300) + arrow(96)
            + node("folder", "Local archive", "read again", 300)),
    }
    write_pages(example, "_kit_example/html")
    print("now render: python3 render_to_webp.py _kit_example/html _kit_example/out")
