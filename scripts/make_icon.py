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

    # -- Background: rounded dark rectangle --
    bg_color = (16, 31, 48, 255)  # Anlan (#101f30)
    radius = size // 6
    draw.rounded_rectangle(
        [(0, 0), (size - 1, size - 1)],
        radius=radius,
        fill=bg_color,
    )

    # -- Layer stack: 3 offset rectangles representing PSD layers --
    # Colors from lettepa: teal, blue, then solid white for "P"
    layer_colors = [
        (87, 195, 194, 100),   # Shilv teal, translucent
        (102, 169, 201, 160),  # Jianshilan blue, semi-opaque
        (248, 244, 237, 255),  # Hanbaiyu white, opaque (the "P")
    ]

    margin = size * 0.18
    layer_w = size - 2 * margin
    layer_h = size * 0.22
    offset_step = size * 0.06

    for i, color in enumerate(layer_colors):
        y_top = margin + i * offset_step
        y_bot = y_top + layer_h
        x_left = margin + (2 - i) * offset_step * 0.5
        x_right = x_left + layer_w - (2 - i) * offset_step
        draw.rounded_rectangle(
            [(x_left, y_top), (x_right, y_bot)],
            radius=max(2, size // 32),
            fill=color,
        )

    # -- Letter "P" on the top (white) layer --
    # Try to use a bold system font, fall back to default.
    font_size = int(layer_h * 0.85)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except (OSError, IOError):
        try:
            font = ImageFont.truetype("Arial Bold", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()

    # Center the "P" on the top layer.
    p_color = (16, 31, 48, 255)  # dark on white
    text = "P"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) / 2
    # Place vertically centered within the top layer rectangle.
    top_layer_y = margin + 2 * offset_step
    ty = top_layer_y + (layer_h - th) / 2 - bbox[1]
    draw.text((tx, ty), text, fill=p_color, font=font)

    return img


def main():
    # Generate multiple sizes for .ico
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [create_icon(s) for s in sizes]

    # Save as .ico (Windows icon)
    ico_path = "icon.ico"
    images[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"Saved {ico_path}")

    # Also save a PNG preview at 256px
    png_path = "icon.png"
    images[-1].save(png_path)
    print(f"Saved {png_path}")


if __name__ == "__main__":
    main()
