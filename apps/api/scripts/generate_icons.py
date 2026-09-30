"""Разовый скрипт: генерирует PNG-иконки PWA из простого геометрического
логотипа (раздел 16.1 SPEC.md), без внешних SVG-библиотек. Три узла и
линия маршрута — медицина/образование/соцзащита."""
from PIL import Image, ImageDraw

BG = (11, 13, 16, 255)
NODE_COLORS = [(79, 176, 255, 255), (127, 216, 143, 255), (255, 179, 92, 255)]
LINE_COLOR = (238, 241, 244, 255)

OUT_DIR = "/workspaces/medhub/apps/web/public/icons"


def draw_logo(size: int, padding_ratio: float, bg=True) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG if bg else (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size * padding_ratio
    inner = size - 2 * pad
    node_r = inner * 0.11
    y = size / 2
    xs = [pad + inner * 0.15, pad + inner * 0.5, pad + inner * 0.85]

    d.line([(xs[0], y), (xs[2], y)], fill=LINE_COLOR, width=max(2, int(size * 0.02)))
    for x, color in zip(xs, NODE_COLORS):
        d.ellipse([x - node_r, y - node_r, x + node_r, y + node_r], fill=color)
    return img


def rounded(img: Image.Image, radius_ratio: float) -> Image.Image:
    size = img.size[0]
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=size * radius_ratio, fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


if __name__ == "__main__":
    rounded(draw_logo(192, 0.18), 0.22).save(f"{OUT_DIR}/icon-192.png")
    rounded(draw_logo(512, 0.18), 0.22).save(f"{OUT_DIR}/icon-512.png")
    # maskable: без скругления/прозрачности, с запасом под safe zone (~40% от центра)
    draw_logo(512, 0.28).save(f"{OUT_DIR}/icon-512-maskable.png")
    rounded(draw_logo(180, 0.16), 0.22).convert("RGB").save(f"{OUT_DIR}/apple-touch-icon.png")
    print("icons written")
