"""Render the exact notebook outputs as console-style PNG exhibits."""
from __future__ import annotations

import base64
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\Users\roshn\OneDrive\Desktop\Amrita\SEM 5\ML\Project")
NB = ROOT / "notebooks" / "CISCaRL_31_steps.ipynb"
OUT = ROOT / "paper" / "exhibits"
OUT.mkdir(parents=True, exist_ok=True)

cells = json.loads(NB.read_text(encoding="utf-8"))["cells"]
steps = [i for i, c in enumerate(cells)
         if c["cell_type"] == "markdown" and "".join(c.get("source", [])).startswith("## STEP")]

FONT_PATH = "C:/Windows/Fonts/consola.ttf"
FONT = ImageFont.truetype(FONT_PATH, 18)
LINE_H = 25
PAD = 22
WRAP = 168

for idx, start in enumerate(steps, 1):
    end = steps[idx] if idx < len(steps) else len(cells)
    chunks = []
    imgs = []
    for j in range(start + 1, end):
        c = cells[j]
        if c["cell_type"] != "code":
            continue
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream":
                text = "".join(o.get("text", [])).rstrip("\n")
                if text.strip():
                    chunks.append(text)
            elif o.get("output_type") == "display_data" and "image/png" in o.get("data", {}):
                imgs.append(o["data"]["image/png"])

    text = "\n\n".join(chunks)
    lines = []
    for raw in text.splitlines():
        if len(raw) <= WRAP:
            lines.append(raw)
        else:
            lines.extend(textwrap.wrap(raw, width=WRAP, break_long_words=False,
                                       break_on_hyphens=False, replace_whitespace=False))
    if not lines:
        lines = ["(no printed output at this step)"]

    probe = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(probe)
    char_w = draw.textlength("M", font=FONT)

    chunks_of = 30
    nparts = max(1, (len(lines) + chunks_of - 1) // chunks_of)
    size = (len(lines) + nparts - 1) // nparts
    for part, start in enumerate(range(0, len(lines), size), 1):
        block = lines[start:start + size]
        width = int(max(len(ln) for ln in block) * char_w) + 2 * PAD
        width = max(width, 900)
        height = len(block) * LINE_H + 2 * PAD
        img = Image.new("RGB", (width, height), (250, 250, 250))
        draw = ImageDraw.Draw(img)
        y = PAD
        for ln in block:
            draw.text((PAD, y), ln, font=FONT, fill=(20, 20, 20))
            y += LINE_H
        draw.rectangle([0, 0, width - 1, height - 1], outline=(80, 80, 80), width=2)
        img.save(OUT / f"console_{idx:02d}_{part}.png")

    for k, b64 in enumerate(imgs, 1):
        (OUT / f"nbimg_{idx:02d}_{k}.png").write_bytes(base64.b64decode(b64))

    print(f"{idx:02d}: {len(lines)} lines, {width}x{height}, images {len(imgs)}")

print("saved to", OUT)
