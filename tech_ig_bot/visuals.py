from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Callable

from PIL import Image, ImageDraw

from .headline import technology_topic
from .models import Article

Color = tuple[int, int, int, int]
Box = tuple[int, int, int, int]


PALETTES: dict[str, tuple[Color, Color, Color]] = {
    "ai": ((0, 245, 212, 190), (124, 58, 237, 165), (255, 255, 255, 210)),
    "battery": ((34, 197, 94, 190), (250, 204, 21, 175), (255, 255, 255, 210)),
    "biotech": ((45, 212, 191, 185), (244, 114, 182, 165), (255, 255, 255, 210)),
    "chip": ((96, 165, 250, 190), (0, 245, 212, 165), (255, 255, 255, 210)),
    "energy": ((250, 204, 21, 190), (34, 197, 94, 165), (255, 255, 255, 210)),
    "quantum": ((125, 92, 255, 190), (0, 245, 212, 165), (255, 255, 255, 210)),
    "robot": ((56, 189, 248, 190), (148, 163, 184, 170), (255, 255, 255, 210)),
    "space": ((96, 165, 250, 190), (251, 113, 133, 150), (255, 255, 255, 210)),
    "default": ((0, 245, 212, 175), (124, 58, 237, 150), (255, 255, 255, 205)),
}


def draw_story_visual(image: Image.Image, article: Article, headline: str) -> str:
    """Draw deterministic, topic-related artwork behind the headline."""

    topic = technology_topic(article)
    visual_key = _visual_key(topic, headline)
    seed = _seed(article, headline)
    rng = random.Random(seed)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    box = (565, 190, 1038, 690)

    _draw_glow(draw, box, PALETTES[visual_key], rng)
    drawers: dict[str, Callable[[ImageDraw.ImageDraw, Box, random.Random, tuple[Color, Color, Color]], None]] = {
        "ai": _draw_ai_network,
        "battery": _draw_battery,
        "biotech": _draw_dna,
        "chip": _draw_chip,
        "energy": _draw_energy,
        "quantum": _draw_quantum,
        "robot": _draw_robot_arm,
        "space": _draw_space,
        "default": _draw_ai_network,
    }
    drawers[visual_key](draw, box, rng, PALETTES[visual_key])

    image.alpha_composite(overlay) if image.mode == "RGBA" else image.paste(
        Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    )
    return visual_key


def _visual_key(topic: str, headline: str) -> str:
    text = f"{topic} {headline}".lower()
    if any(term in text for term in ("battery", "energy storage")):
        return "battery"
    if any(term in text for term in ("fusion", "solar", "renewable", "clean energy")):
        return "energy"
    if any(term in text for term in ("quantum", "qubit")):
        return "quantum"
    if any(term in text for term in ("robot", "humanoid", "manipulation")):
        return "robot"
    if any(term in text for term in ("gene", "biotech", "biology", "dna", "crispr")):
        return "biotech"
    if any(term in text for term in ("chip", "semiconductor", "processor")):
        return "chip"
    if any(term in text for term in ("space", "rocket", "satellite", "propulsion")):
        return "space"
    if any(term in text for term in ("ai", "artificial intelligence", "machine learning")):
        return "ai"
    return "default"


def _seed(article: Article, headline: str) -> int:
    digest = hashlib.sha256(f"{article.url}|{article.title}|{headline}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def _draw_glow(
    draw: ImageDraw.ImageDraw,
    box: Box,
    palette: tuple[Color, Color, Color],
    rng: random.Random,
) -> None:
    left, top, right, bottom = box
    for _ in range(4):
        cx = rng.randint(left + 40, right - 40)
        cy = rng.randint(top + 40, bottom - 40)
        radius = rng.randint(80, 170)
        color = palette[rng.randrange(2)]
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            fill=(color[0], color[1], color[2], 28),
        )


def _draw_ai_network(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    nodes = [
        (rng.randint(left + 25, right - 25), rng.randint(top + 25, bottom - 25))
        for _ in range(15)
    ]
    for index, start in enumerate(nodes):
        distances = sorted(
            ((abs(start[0] - end[0]) + abs(start[1] - end[1]), end) for end in nodes[index + 1 :]),
            key=lambda item: item[0],
        )
        for _, end in distances[:2]:
            draw.line((*start, *end), fill=(palette[0][0], palette[0][1], palette[0][2], 75), width=2)
    for x, y in nodes:
        radius = rng.randint(6, 13)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=palette[rng.randrange(3)])


def _draw_battery(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    width = right - left
    height = bottom - top
    body = (left + 75, top + 145, right - 95, bottom - 145)
    terminal = (body[2], body[1] + height // 12, body[2] + 34, body[3] - height // 12)
    draw.rounded_rectangle(body, radius=26, outline=palette[2], width=5, fill=(5, 20, 35, 92))
    draw.rounded_rectangle(terminal, radius=10, fill=palette[2])
    charge_bars = rng.randint(3, 5)
    bar_width = (body[2] - body[0] - 55) // 5
    for index in range(charge_bars):
        x0 = body[0] + 24 + index * (bar_width + 9)
        draw.rounded_rectangle(
            (x0, body[1] + 22, x0 + bar_width, body[3] - 22),
            radius=14,
            fill=palette[index % 2],
        )
    bolt = [
        (left + width // 2 + 20, top + 65),
        (left + width // 2 - 45, top + height // 2),
        (left + width // 2 + 20, top + height // 2),
        (left + width // 2 - 22, bottom - 48),
        (left + width // 2 + 88, top + height // 2 - 42),
        (left + width // 2 + 23, top + height // 2 - 42),
    ]
    draw.polygon(bolt, fill=(palette[1][0], palette[1][1], palette[1][2], 210))


def _draw_dna(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    center = (left + right) // 2
    amplitude = rng.randint(58, 78)
    points_a: list[tuple[int, int]] = []
    points_b: list[tuple[int, int]] = []
    for step in range(34):
        y = top + 35 + step * ((bottom - top - 70) / 33)
        angle = step * 0.55
        points_a.append((int(center + math.sin(angle) * amplitude), int(y)))
        points_b.append((int(center - math.sin(angle) * amplitude), int(y)))
    draw.line(points_a, fill=palette[0], width=5)
    draw.line(points_b, fill=palette[1], width=5)
    for index in range(0, len(points_a), 3):
        draw.line((*points_a[index], *points_b[index]), fill=(255, 255, 255, 95), width=2)


def _draw_chip(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    chip = (left + 130, top + 110, right - 130, bottom - 110)
    draw.rounded_rectangle(chip, radius=34, fill=(6, 24, 43, 150), outline=palette[2], width=4)
    for side in ("top", "bottom"):
        y = chip[1] if side == "top" else chip[3]
        for x in range(chip[0] + 24, chip[2], 34):
            draw.line((x, y, x, y - 34 if side == "top" else y + 34), fill=palette[0], width=3)
    for side in ("left", "right"):
        x = chip[0] if side == "left" else chip[2]
        for y in range(chip[1] + 24, chip[3], 34):
            draw.line((x, y, x - 34 if side == "left" else x + 34, y), fill=palette[1], width=3)
    for _ in range(10):
        x0 = rng.randint(chip[0] + 30, chip[2] - 90)
        y0 = rng.randint(chip[1] + 30, chip[3] - 30)
        draw.line((x0, y0, x0 + rng.randint(25, 85), y0), fill=(255, 255, 255, 85), width=2)


def _draw_energy(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    sun = (right - 170, top + 40, right - 55, top + 155)
    draw.ellipse(sun, fill=palette[0])
    for angle in range(0, 360, 30):
        cx = (sun[0] + sun[2]) // 2
        cy = (sun[1] + sun[3]) // 2
        draw.line(
            (
                cx,
                cy,
                int(cx + math.cos(math.radians(angle)) * 92),
                int(cy + math.sin(math.radians(angle)) * 92),
            ),
            fill=(palette[0][0], palette[0][1], palette[0][2], 90),
            width=2,
        )
    for x in (left + 120, left + 235):
        base_y = bottom - 70
        draw.line((x, base_y, x, top + 205), fill=palette[2], width=5)
        blade_center = (x, top + 205)
        for angle in (rng.randint(-10, 10), 120 + rng.randint(-10, 10), 240 + rng.randint(-10, 10)):
            draw.line(
                (
                    *blade_center,
                    int(blade_center[0] + math.cos(math.radians(angle)) * 72),
                    int(blade_center[1] + math.sin(math.radians(angle)) * 72),
                ),
                fill=palette[1],
                width=7,
            )


def _draw_quantum(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    cx = (left + right) // 2 + rng.randint(-20, 20)
    cy = (top + bottom) // 2 + rng.randint(-20, 20)
    for radius in (70, 125, 180):
        draw.ellipse((cx - radius, cy - radius // 2, cx + radius, cy + radius // 2), outline=palette[0], width=4)
        draw.ellipse((cx - radius // 2, cy - radius, cx + radius // 2, cy + radius), outline=palette[1], width=3)
    for angle in range(0, 360, 72):
        x = int(cx + math.cos(math.radians(angle + rng.randint(-12, 12))) * 150)
        y = int(cy + math.sin(math.radians(angle + rng.randint(-12, 12))) * 82)
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=palette[2])
    draw.ellipse((cx - 25, cy - 25, cx + 25, cy + 25), fill=palette[0])


def _draw_robot_arm(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    base = (left + 105, bottom - 105)
    joint1 = (left + 205 + rng.randint(-20, 20), top + 305)
    joint2 = (left + 340 + rng.randint(-20, 20), top + 205)
    claw = (right - 80, top + 245 + rng.randint(-20, 20))
    for start, end in ((base, joint1), (joint1, joint2), (joint2, claw)):
        draw.line((*start, *end), fill=palette[1], width=24)
        draw.line((*start, *end), fill=palette[0], width=8)
    for x, y in (base, joint1, joint2):
        draw.ellipse((x - 30, y - 30, x + 30, y + 30), fill=(8, 20, 35, 210), outline=palette[2], width=5)
    draw.line((claw[0], claw[1], claw[0] + 55, claw[1] - 38), fill=palette[2], width=8)
    draw.line((claw[0], claw[1], claw[0] + 58, claw[1] + 36), fill=palette[2], width=8)


def _draw_space(
    draw: ImageDraw.ImageDraw,
    box: Box,
    rng: random.Random,
    palette: tuple[Color, Color, Color],
) -> None:
    left, top, right, bottom = box
    planet = (left + 150, top + 140, left + 360, top + 350)
    draw.ellipse(planet, fill=palette[0])
    draw.arc((planet[0] - 70, planet[1] + 40, planet[2] + 70, planet[3] - 40), 8, 172, fill=palette[2], width=5)
    for _ in range(36):
        x = rng.randint(left + 20, right - 20)
        y = rng.randint(top + 20, bottom - 20)
        radius = rng.choice((1, 2, 3))
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255, rng.randint(80, 210)))
    rocket = [(right - 150, bottom - 140), (right - 82, bottom - 230), (right - 62, bottom - 105)]
    draw.polygon(rocket, fill=palette[1])
