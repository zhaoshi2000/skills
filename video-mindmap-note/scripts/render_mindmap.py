"""Render a compact, shareable mind map from a JSON outline."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path


WIDTH = 1600
CARD_WIDTH = 520
CARD_X = (75, WIDTH - 75 - CARD_WIDTH)
ROOT_WIDTH = 370
ROOT_HEIGHT = 130
COLORS = ("#2563eb", "#059669", "#ea580c", "#9333ea",
          "#be123c", "#0891b2", "#a16207", "#4f46e5")


def wrapped(value: str, max_chars: int) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    rows = []
    for paragraph in text.splitlines():
        while len(paragraph) > max_chars:
            rows.append(paragraph[:max_chars])
            paragraph = paragraph[max_chars:]
        rows.append(paragraph)
    return rows


def text_lines(rows: list[str], x: int, y: int, *, line_height: int,
               size: int, fill: str, weight: int = 400,
               anchor: str | None = None) -> str:
    align = f' text-anchor="{anchor}"' if anchor else ""
    parts = [f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
             f'fill="{fill}"{align} font-family="Microsoft YaHei,Noto Sans CJK SC,sans-serif">']
    for index, row in enumerate(rows):
        offset = 0 if index == 0 else line_height
        parts.append(f'<tspan x="{x}" dy="{offset}">{html.escape(row)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


def render(data: dict) -> str:
    title = str(data.get("title") or "").strip()
    branches = data.get("branches")
    if not title or not isinstance(branches, list) or not 1 <= len(branches) <= 8:
        raise ValueError("JSON needs a title and 1–8 branches")
    cleaned = []
    for branch in branches:
        if not isinstance(branch, dict):
            raise ValueError("each branch must be an object")
        label = str(branch.get("label") or "").strip()
        points = branch.get("points")
        if not label or not isinstance(points, list) or not 1 <= len(points) <= 5:
            raise ValueError("each branch needs a label and 1–5 points")
        points = [str(point).strip() for point in points if str(point).strip()]
        if not points:
            raise ValueError("branch points cannot be empty")
        cleaned.append({
            "label": label, "timestamp": str(branch.get("timestamp") or "").strip(),
            "points": points,
        })

    cards = []
    for index, branch in enumerate(cleaned):
        header = wrapped(branch["label"], 16)
        point_lines = [wrapped(point, 23) for point in branch["points"]]
        height = 86 + 31 * max(1, len(header)) + sum(30 * len(rows) + 14 for rows in point_lines)
        cards.append((branch, header, point_lines, height, COLORS[index % len(COLORS)]))
    per_side = math.ceil(len(cards) / 2)
    left = cards[:per_side]
    right = cards[per_side:]
    gap = 34
    left_height = sum(item[3] for item in left) + max(0, len(left) - 1) * gap
    right_height = sum(item[3] for item in right) + max(0, len(right) - 1) * gap
    height = max(900, max(left_height, right_height) + 160)
    root_y = height // 2 - ROOT_HEIGHT // 2
    root_x = (WIDTH - ROOT_WIDTH) // 2
    subtitle = str(data.get("subtitle") or "").strip()
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<rect x="20" y="20" width="1560" height="{height - 40}" rx="28" '
        'fill="#ffffff" stroke="#e2e8f0" stroke-width="2"/>',
    ]
    svg.append(f'<rect x="{root_x}" y="{root_y}" width="{ROOT_WIDTH}" '
               f'height="{ROOT_HEIGHT}" rx="24" fill="#0f172a"/>')
    svg.append(text_lines(wrapped(title, 11)[:2], WIDTH // 2, root_y + 54,
                          line_height=36, size=28, fill="#ffffff", weight=700,
                          anchor="middle"))
    if subtitle:
        svg.append(text_lines(wrapped(subtitle, 50)[:1], WIDTH // 2, height - 68,
                              line_height=24, size=17, fill="#64748b",
                              anchor="middle"))

    for side, group in enumerate((left, right)):
        total = sum(item[3] for item in group) + max(0, len(group) - 1) * gap
        cursor = (height - total) // 2
        x = CARD_X[side]
        for branch, header, point_lines, card_h, color in group:
            mid_y = cursor + card_h // 2
            start_x = root_x if side == 0 else root_x + ROOT_WIDTH
            end_x = x + CARD_WIDTH if side == 0 else x
            direction = -1 if side == 0 else 1
            c1 = start_x + direction * 86
            c2 = end_x - direction * 86
            svg.append(f'<path d="M {start_x} {height // 2} C {c1} {height // 2}, '
                       f'{c2} {mid_y}, {end_x} {mid_y}" fill="none" '
                       f'stroke="{color}" stroke-width="5" opacity=".7"/>')
            svg.append(f'<rect x="{x}" y="{cursor}" width="{CARD_WIDTH}" height="{card_h}" '
                       f'rx="20" fill="#ffffff" stroke="#cbd5e1" stroke-width="2"/>')
            svg.append(f'<rect x="{x}" y="{cursor}" width="10" height="{card_h}" '
                       f'rx="5" fill="{color}"/>')
            if branch["timestamp"]:
                svg.append(text_lines([branch["timestamp"]], x + CARD_WIDTH - 104, cursor + 40,
                                      line_height=20, size=18, fill=color, weight=700))
            svg.append(text_lines(header, x + 32, cursor + 42,
                                  line_height=31, size=23, fill="#0f172a", weight=700))
            point_y = cursor + 78 + 31 * max(1, len(header))
            for rows in point_lines:
                svg.append(f'<circle cx="{x + 39}" cy="{point_y - 6}" r="5" fill="{color}"/>')
                svg.append(text_lines(rows, x + 57, point_y,
                                      line_height=30, size=19, fill="#334155"))
                point_y += 30 * len(rows) + 14
            cursor += card_h + gap
    svg.append("</svg>")
    return "\n".join(svg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--png", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    svg = render(data)
    args.svg.parent.mkdir(parents=True, exist_ok=True)
    args.svg.write_text(svg, encoding="utf-8")
    if args.png:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise SystemExit("PNG rendering requires Playwright") from exc
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome", headless=True)
            page = browser.new_page(viewport={"width": WIDTH, "height": 900},
                                    device_scale_factor=1)
            page.set_content('<body style="margin:0">' + svg + "</body>")
            args.png.parent.mkdir(parents=True, exist_ok=True)
            page.locator("svg").screenshot(path=str(args.png))
            browser.close()
    print(args.svg)
    if args.png:
        print(args.png)


if __name__ == "__main__":
    main()
