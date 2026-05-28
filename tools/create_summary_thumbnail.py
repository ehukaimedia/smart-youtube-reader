#!/usr/bin/env python3
"""
Create a Smart YouTube Reader teaching thumbnail from a project archive.

Usage:
  python3 tools/create_summary_thumbnail.py data/jobs/my-project_folder
  python3 tools/create_summary_thumbnail.py e68163e9-7141-49bc-b61f-12fe741784a6
"""

from __future__ import annotations

import argparse
import json
import math
import re
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PROJECT_ROOT / "data" / "jobs"
DEFAULT_OUTPUT = "generated/summary.webp"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an AI-teaching summary thumbnail from Smart YouTube Reader archive text and frame images."
    )
    parser.add_argument(
        "project",
        help="Project folder path, data/jobs folder name, or job_id from manifest.json.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Relative output path inside the project folder. Default: {DEFAULT_OUTPUT}",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1600,
        help="Thumbnail width in pixels. Default: 1600",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=900,
        help="Thumbnail height in pixels. Default: 900",
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=12,
        help="Maximum archive frame images to inspect/use. Default: 12",
    )
    parser.add_argument(
        "--title",
        help="Override the rendered title. Defaults to manifest title or archive concepts.",
    )
    args = parser.parse_args()

    project_dir = resolve_project(args.project)
    archive_path = project_dir / "archive.json"
    manifest_path = project_dir / "manifest.json"
    if not archive_path.exists():
        raise SystemExit(f"Archive not found: {archive_path}")
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    archive = read_json(archive_path)
    manifest = read_json(manifest_path)
    chapters = archive.get("archive", [])
    if not chapters:
        raise SystemExit("Archive has no chapters.")

    output_rel = Path(args.output)
    if output_rel.is_absolute() or ".." in output_rel.parts:
        raise SystemExit("--output must be a safe relative path inside the project folder.")

    output_path = project_dir / output_rel
    output_path.parent.mkdir(parents=True, exist_ok=True)

    frame_items = collect_frame_items(project_dir, chapters, args.max_frames)
    if not frame_items:
        raise SystemExit("No usable archive frame images found.")

    title = clean_title(args.title or manifest.get("title") or archive.get("title") or "Smart YouTube Reader Summary")
    subtitle = build_subtitle(chapters)
    flow = build_learning_flow(chapters)
    cards = build_teaching_cards(chapters)

    image = render_thumbnail(
        project_dir=project_dir,
        title=title,
        subtitle=subtitle,
        frame_items=frame_items,
        flow=flow,
        cards=cards,
        width=args.width,
        height=args.height,
    )
    save_thumbnail(image, output_path)

    attach_metadata(archive_path, manifest_path, str(output_rel))

    print(f"Created {output_path}")
    print(f"Updated {archive_path}")
    print(f"Updated {manifest_path}")
    return 0


def resolve_project(value: str) -> Path:
    candidate = Path(value).expanduser()
    if candidate.exists():
        return candidate.resolve()

    candidate = DATA_ROOT / value
    if candidate.exists():
        return candidate.resolve()

    if DATA_ROOT.exists():
        for manifest_path in DATA_ROOT.glob("*/manifest.json"):
            try:
                manifest = read_json(manifest_path)
            except Exception:
                continue
            if manifest.get("job_id") == value:
                return manifest_path.parent.resolve()

    raise SystemExit(f"Project not found: {value}")


def read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_thumbnail(image: Image.Image, output_path: Path) -> None:
    suffix = output_path.suffix.lower()
    if suffix == ".webp":
        image.save(output_path, format="WEBP", quality=82, method=6)
        return
    image.save(output_path)


def collect_frame_items(project_dir: Path, chapters: list[dict[str, Any]], max_frames: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()

    for index, chapter in enumerate(chapters):
        for image_path in chapter.get("images", []) or []:
            if image_path in seen:
                continue
            path = project_dir / image_path
            if not path.exists() or not path.is_file():
                continue
            if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            seen.add(image_path)
            items.append({
                "chapter_index": index,
                "concept": chapter.get("concept") or f"Chapter {index + 1}",
                "summary": chapter.get("summary") or "",
                "path": path,
                "relative_path": image_path,
            })
            break

        if len(items) >= max_frames:
            break

    return items


def clean_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\b(ai digest|youtube|complete guide|ultimate)\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip(" -:|")
    return title[:76] or "Smart YouTube Reader Summary"


def build_subtitle(chapters: list[dict[str, Any]]) -> str:
    concepts = [str(ch.get("concept", "")) for ch in chapters[:8]]
    joined = " ".join(concepts).lower()
    if "volume" in joined and ("profile" in joined or "poc" in joined):
        return "A visual learning map of price context, volume zones, entries, and risk."
    if "agent" in joined or "ai" in joined:
        return "A compact visual map of the core ideas, workflow, and decision points."
    return "A compact visual map of the video's durable concepts and key visual evidence."


def build_learning_flow(chapters: list[dict[str, Any]]) -> list[tuple[str, str]]:
    concepts = " ".join(str(ch.get("concept", "")) for ch in chapters).lower()
    if "volume" in concepts and ("profile" in concepts or "poc" in concepts):
        return [
            ("POC", "Max traded price zone"),
            ("HVN / Value Area", "Institutional activity cluster"),
            ("First Retest", "Highest-quality reaction point"),
            ("Boundary Entry", "Enter before center-line misses"),
            ("Risk Barrier", "Stop behind wall, TP before next wall"),
        ]

    selected = select_distinct_chapters(chapters, 5)
    flow = []
    for chapter in selected:
        concept = short_label(str(chapter.get("concept") or "Concept"), 24)
        summary = short_sentence(str(chapter.get("summary") or chapter.get("content") or ""), 58)
        flow.append((concept, summary))

    while len(flow) < 5:
        flow.append((f"Step {len(flow) + 1}", "Key lesson from the archive"))
    return flow[:5]


def build_teaching_cards(chapters: list[dict[str, Any]]) -> list[tuple[str, str]]:
    concepts = " ".join(str(ch.get("concept", "")) for ch in chapters).lower()
    if "volume" in concepts and ("profile" in concepts or "poc" in concepts):
        return [
            ("Read the Market", "Volume profile turns random candles into a map of where serious participation happened."),
            ("Plan the Trade", "Wait for price to leave the defended zone, then evaluate the first return."),
            ("Manage Risk", "Place stops beyond the barrier and take profit before the next opposing zone."),
        ]

    selected = select_distinct_chapters(chapters, 3)
    cards = []
    for chapter in selected:
        cards.append((
            short_label(str(chapter.get("concept") or "Lesson"), 24),
            short_sentence(str(chapter.get("summary") or chapter.get("content") or ""), 92),
        ))
    while len(cards) < 3:
        cards.append(("Use the Archive", "Read the text and frames together to preserve the video's visual context."))
    return cards[:3]


def select_distinct_chapters(chapters: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if len(chapters) <= count:
        return chapters
    indexes = [round(i * (len(chapters) - 1) / (count - 1)) for i in range(count)]
    seen: set[int] = set()
    selected = []
    for index in indexes:
        if index not in seen:
            selected.append(chapters[index])
            seen.add(index)
    return selected


def short_label(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].strip()


def short_sentence(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.split(r"(?<=[.!?])\s+", text)[0] if text else ""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].strip() + "."


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend([
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ])
    else:
        candidates.extend([
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        ])

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            pass
    return ImageFont.load_default()


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    start_size: int,
    min_size: int,
    max_width: int,
    bold: bool = False,
) -> ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        candidate = font(size, bold)
        if draw.textbbox((0, 0), text, font=candidate)[2] <= max_width:
            return candidate
    return font(min_size, bold)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=text_font)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    text_font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    max_width: int,
    max_lines: int,
    line_gap: int = 6,
) -> None:
    x, y = xy
    for line in wrap_text(draw, text, text_font, max_width)[:max_lines]:
        draw.text((x, y), line, fill=fill, font=text_font)
        y += getattr(text_font, "size", 16) + line_gap


def render_thumbnail(
    project_dir: Path,
    title: str,
    subtitle: str,
    frame_items: list[dict[str, Any]],
    flow: list[tuple[str, str]],
    cards: list[tuple[str, str]],
    width: int,
    height: int,
) -> Image.Image:
    if width <= 0 or height <= 0:
        raise SystemExit("Width and height must be positive.")

    image = Image.new("RGB", (width, height), (7, 9, 12))
    draw = ImageDraw.Draw(image)

    scale = width / 1600
    def s(value: int) -> int:
        return max(1, round(value * scale))

    colors = {
        "white": (243, 246, 250),
        "muted": (156, 166, 178),
        "blue": (56, 189, 248),
        "yellow": (250, 204, 21),
        "red": (248, 113, 113),
        "green": (52, 211, 153),
        "panel": (14, 18, 25),
        "panel2": (18, 24, 33),
        "border": (42, 55, 72),
    }
    accents = [colors["blue"], colors["yellow"], colors["red"], colors["green"], colors["yellow"]]

    subtitle_font = font(s(25))
    heading_font = font(s(25), True)
    body_font = font(s(20))
    small_font = font(s(16))
    tag_font = font(s(18), True)

    for x in range(0, width, s(40)):
        draw.line((x, 0, x, height), fill=(11, 15, 20), width=1)
    for y in range(0, height, s(40)):
        draw.line((0, y, width, y), fill=(11, 15, 20), width=1)

    margin = s(54)
    title_font = fit_font(draw, title, s(52), s(34), width - margin * 2 - s(220), True)
    draw.text((margin, s(42)), title, fill=colors["white"], font=title_font)
    draw_wrapped(draw, subtitle, (margin, s(108)), subtitle_font, colors["muted"], width - margin * 2, 2)

    top_frames = select_frame_layout(frame_items, 3)
    frame_y1 = s(175)
    frame_y2 = s(453)
    gap = s(38)
    frame_w = (width - margin * 2 - gap * 2) // 3
    frame_h = frame_y2 - frame_y1
    for index, item in enumerate(top_frames):
        x1 = margin + index * (frame_w + gap)
        x2 = x1 + frame_w
        label = f"{index + 1}. {short_label(item['concept'], 42)}"
        paste_frame(image, draw, item["path"], (x1, frame_y1, x2, frame_y2), label, accents[index], small_font)

    flow_box = (margin, s(490), width - margin, s(674))
    draw.rounded_rectangle(flow_box, radius=s(22), fill=colors["panel"], outline=(38, 52, 68), width=s(2))
    step_width = (flow_box[2] - flow_box[0] - s(60)) // 5
    for index, (label, description) in enumerate(flow):
        x = flow_box[0] + s(30) + index * step_width
        y = flow_box[1] + s(30)
        color = accents[index % len(accents)]
        draw.ellipse((x, y, x + s(46), y + s(46)), fill=color)
        draw.text((x + s(16), y + s(10)), str(index + 1), fill=(5, 8, 12), font=tag_font)
        draw_wrapped(draw, label, (x, y + s(62)), heading_font, colors["white"], step_width - s(35), 2, s(3))
        draw_wrapped(draw, description, (x, y + s(118)), small_font, colors["muted"], step_width - s(35), 1, s(4))
        if index < 4:
            ax = x + step_width - s(78)
            ay = y + s(24)
            draw.line((ax, ay, ax + s(54), ay), fill=(70, 82, 100), width=s(3))
            draw.polygon([(ax + s(54), ay), (ax + s(42), ay - s(8)), (ax + s(42), ay + s(8))], fill=(70, 82, 100))

    card_gap = s(40)
    card_w = (width - margin * 2 - card_gap * 2) // 3
    card_y1 = s(714)
    card_y2 = s(842)
    for index, (card_title, body) in enumerate(cards):
        x1 = margin + index * (card_w + card_gap)
        x2 = x1 + card_w
        accent = accents[index % len(accents)]
        draw.rounded_rectangle((x1, card_y1, x2, card_y2), radius=s(18), fill=colors["panel2"], outline=accent, width=s(2))
        draw.rectangle((x1 + s(20), card_y1 + s(24), x1 + s(28), card_y2 - s(24)), fill=accent)
        draw.text((x1 + s(46), card_y1 + s(24)), card_title, fill=colors["white"], font=heading_font)
        draw_wrapped(draw, body, (x1 + s(46), card_y1 + s(62)), body_font, colors["muted"], card_w - s(84), 2)

    note = "Smart YouTube Reader summary built from archive frames and chapter text"
    note_width = draw.textbbox((0, 0), note, font=small_font)[2]
    draw.text((width - note_width - margin, height - s(42)), note, fill=(95, 105, 118), font=small_font)

    for index, length in enumerate([118, 82, 154, 65, 188, 122, 92]):
        y = s(52 + index * 12)
        scaled_length = s(length)
        fill = (18, 158, 190) if index % 2 else (230, 185, 32)
        draw.rectangle((width - margin - scaled_length, y, width - margin, y + s(5)), fill=fill)

    return image


def select_frame_layout(frame_items: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if len(frame_items) <= count:
        return frame_items
    indexes = [0, len(frame_items) // 2, len(frame_items) - 1]
    selected = []
    seen = set()
    for index in indexes:
        if index not in seen:
            selected.append(frame_items[index])
            seen.add(index)
    return selected[:count]


def paste_frame(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    path: Path,
    box: tuple[int, int, int, int],
    label: str,
    accent: tuple[int, int, int],
    label_font: ImageFont.ImageFont,
) -> None:
    x1, y1, x2, y2 = box
    target_size = (x2 - x1, y2 - y1)
    frame = Image.open(path).convert("RGB")
    frame = ImageOps.fit(frame, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))

    overlay = Image.new("RGBA", target_size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((0, target_size[1] - 46, target_size[0], target_size[1]), fill=(0, 0, 0, 165))
    frame = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

    canvas.paste(frame, (x1, y1))
    draw.rounded_rectangle((x1, y1, x2, y2), radius=14, outline=accent, width=3)
    draw.text((x1 + 14, y2 - 36), label, fill=(243, 246, 250), font=label_font)


def attach_metadata(archive_path: Path, manifest_path: Path, output_rel: str) -> None:
    for path in [archive_path, manifest_path]:
        data = read_json(path)
        data["summary_image"] = output_rel
        data["summary_image_source"] = "cli_archive_frame_synthesis"
        data.pop("summary_image_error", None)
        write_json(path, data)


if __name__ == "__main__":
    raise SystemExit(main())
