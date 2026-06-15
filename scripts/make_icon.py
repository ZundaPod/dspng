"""
Generate dspng app icon.

Design concept:
  - The letter "P" is shared between PSD and PNG
  - Stacked layers represent PSD's layer structure
  - The bottom layer is solid = the final PNG output
  - Dark background matches the app's dark theme
  - Accent color from the lettepa palette (Jianshilan blue)
"""

from PIL import Image, ImageDraw, ImageFont


def create_icon(size: int) -> Image.Image:
    """Create a single icon at the given square size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # -- Background: dark rounded rectangle --
    bg_color = (16, 31, 48, 255)  # Anlan (#101f30)
    radius = size // 5
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=bg_color,
    )

    # -- Layer stack: 3 offset rectangles representing PSD layers --
    layer_colors = [
        (87, 195, 194, 130),   # Shilv teal
        (102, 169, 201, 190),  # Jianshilan blue
        (248, 244, 237, 255),  # Hanbaiyu white (the "P")
    ]

    # Tight margins — elements fill almost the entire canvas.
    m = size * 0.06
    layer_w = size - 2 * m
    layer_h = size * 0.32
    step = size * 0.09

    for i, color in enumerate(layer_colors):
        y_top = m + i * step
        y_bot = y_top + layer_h
        x_left = m + (2 - i) * step * 0.3
        x_right = x_left + layer_w - (2 - i) * step * 0.6
        draw.rounded_rectangle(
            [(x_left, y_top), (x_right, y_bot)],
            radius=max(2, size // 16),
            fill=color,
        )

    # -- Letter "P" on the top (white) layer, filling it --
    font_size = int(layer_h * 1.2)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("Arial Bold", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    p_color = (16, 31, 48, 255)
    text = "P"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) / 2
    top_layer_y = m + 2 * step
    ty = top_layer_y + (layer_h - th) / 2 - bbox[1]
    draw.text((tx, ty), text, fill=p_color, font=font)

    return img


def main():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]

    ico_path = "icon.ico"
    images[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"Saved {ico_path}")

    png_path = "icon.png"
    images[-1].save(png_path)
    print(f"Saved {png_path}")


if __name__ == "__main__":
    main()
