"""
Generate dspng app icon.

Design:
  - Three stacked layers fill the canvas (PSD layer metaphor)
  - Letter "P" on the top white layer (shared between PSD and PNG)
  - Dark rounded background from lettepa palette
"""

from PIL import Image, ImageDraw, ImageFont


def create_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=size // 5,
        fill=(16, 31, 48, 255),
    )

    # Three layers: teal → blue → white
    colors = [
        (87, 195, 194, 130),
        (102, 169, 201, 190),
        (248, 244, 237, 255),
    ]

    # Layout: layers span from 5% to 95% of canvas.
    # Each layer is ~44% tall, with ~20% step between them.
    layer_h_frac = 0.44
    step_frac = 0.22
    top_margin_frac = 0.04

    for i, color in enumerate(colors):
        y0 = size * (top_margin_frac + i * step_frac)
        y1 = y0 + size * layer_h_frac
        # Each successive layer is slightly narrower (offset effect).
        indent = (2 - i) * size * 0.03
        x0 = 4 + indent
        x1 = size - 4 - indent
        draw.rounded_rectangle(
            [(x0, y0), (x1, y1)],
            radius=max(2, size // 14),
            fill=color,
        )

    # Letter "P" on the top layer, filling most of it.
    top_y = size * (top_margin_frac + 2 * step_frac)
    top_h = size * layer_h_frac
    font_size = int(top_h * 1.15)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("Arial Bold", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    text = "P"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) / 2
    ty = top_y + (top_h - th) / 2 - bbox[1]
    draw.text((tx, ty), text, fill=(16, 31, 48, 255), font=font)

    return img


def main():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]

    images[-1].save(
        "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print("Saved icon.ico")

    images[-1].save("icon.png")
    print("Saved icon.png")


if __name__ == "__main__":
    main()
