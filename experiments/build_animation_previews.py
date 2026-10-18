#!/usr/bin/env python3
"""Render candidate GIFs from four PNG states; publication is a separate command."""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ANIMATION_DIR = ROOT / "static/animation"
EXPRESSIONS = (
    "neutral",
    "happy",
    "shocked",
    "pouty",
    "angry",
    "embarrassed",
    "sad",
    "strained_smile",
)
SIZES = (1086, 1448)
BG = "#f0f0f0"
BLINK = ("idle", "blink", "idle", "blink", "idle")
TALK = ("idle", "talking", "idle", "talking", "idle")
COMBINED = ("idle", "talking", "idle", "blink", "idle", "talking", "blink_talking", "talking", "idle")
BLINK_DURATIONS = (1050, 130, 1250, 130, 1050)
TALK_DURATIONS = (260, 220, 220, 250, 900)
COMBINED_DURATIONS = (450, 220, 300, 130, 430, 220, 130, 240, 1100)
ALL_DURATIONS = (500, 260, 250, 130, 420, 260, 130, 900)
FACE_BOX = (434, 64, 640, 268)
FACE_SCALE = 2
LABEL_HEIGHT = 48
GAP = 12


def load_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def read_png(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        if image.size != SIZES or image.mode != "RGBA":
            raise AssertionError(f"{path}: expected {SIZES} RGBA, got {image.size} {image.mode}")
        return image.copy()


def read_state(slug: str, state: str) -> Image.Image:
    return read_png(ANIMATION_DIR / slug / f"{state}.png")


def flatten(image: Image.Image) -> Image.Image:
    matte = Image.new("RGBA", image.size, BG)
    matte.alpha_composite(image)
    return matte.convert("RGB")


def save_gif(path: Path, frames: list[Image.Image], durations: tuple[int, ...]) -> None:
    if not frames or len(frames) != len(durations):
        raise ValueError(f"{path}: frames and durations do not match")
    size = frames[0].size
    if any(frame.size != size for frame in frames):
        raise AssertionError(f"{path}: frames do not share a canvas size")

    # One shared palette keeps color stable between frames without dithering noise.
    sheet = Image.new("RGB", (size[0], size[1] * len(frames)), BG)
    for index, frame in enumerate(frames):
        sheet.paste(frame.convert("RGB"), (0, index * size[1]))
    palette = sheet.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indexed = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]

    temporary = path.with_suffix(path.suffix + ".tmp")
    indexed[0].save(
        temporary,
        format="GIF",
        save_all=True,
        append_images=indexed[1:],
        duration=list(durations),
        loop=0,
        disposal=2,
        optimize=False,
    )
    with Image.open(temporary) as check:
        check.verify()
    with Image.open(temporary) as check:
        if check.size != size or check.n_frames != len(frames):
            raise AssertionError(f"{path}: bad GIF output {check.size}, {check.n_frames} frames")
    temporary.replace(path)
    display = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
    print(f"{display}: {size[0]}×{size[1]}, {len(frames)} frames")


def render_state_gifs(source: Path, folder: Path) -> None:
    """Render one set without changing its PNGs or any publication record."""
    folder.mkdir(parents=True, exist_ok=True)
    states = {name: flatten(read_png(source / f"{name}.png")) for name in ("idle", "blink", "talking", "blink_talking")}
    save_gif(folder / "blink.gif", [states[name] for name in BLINK], BLINK_DURATIONS)
    save_gif(folder / "talk.gif", [states[name] for name in TALK], TALK_DURATIONS)
    save_gif(folder / "combined.gif", [states[name] for name in COMBINED], COMBINED_DURATIONS)


def make_face_tile(slug: str, state: str) -> Image.Image:
    source = flatten(read_state(slug, state))
    face = source.crop(FACE_BOX).resize(
        ((FACE_BOX[2] - FACE_BOX[0]) * FACE_SCALE, (FACE_BOX[3] - FACE_BOX[1]) * FACE_SCALE),
        Image.Resampling.NEAREST,
    )
    tile = Image.new("RGB", (face.width, face.height + LABEL_HEIGHT), BG)
    tile.paste(face, (0, LABEL_HEIGHT))
    label = slug.replace("_", " ").title()
    ImageDraw.Draw(tile).text((16, 10), label, fill="#161616", font=load_font(28))
    return tile


def make_title_tile(size: tuple[int, int]) -> Image.Image:
    tile = Image.new("RGB", size, "#e5e5e5")
    draw = ImageDraw.Draw(tile)
    font = load_font(38)
    title = "ALL EIGHT\nEXPRESSIONS"
    bounds = draw.multiline_textbbox((0, 0), title, font=font, spacing=12, align="center")
    x = (size[0] - (bounds[2] - bounds[0])) // 2
    y = (size[1] - (bounds[3] - bounds[1])) // 2 - 20
    draw.multiline_text((x, y), title, fill="#171717", font=font, spacing=12, align="center")
    subtitle = "Blink · speech · both"
    subfont = load_font(22)
    sb = draw.textbbox((0, 0), subtitle, font=subfont)
    draw.text(((size[0] - (sb[2] - sb[0])) // 2, size[1] - 52), subtitle, fill="#444444", font=subfont)
    return tile


def build_all_expressions_gif(destination: Path) -> None:
    face_w = (FACE_BOX[2] - FACE_BOX[0]) * FACE_SCALE
    face_h = (FACE_BOX[3] - FACE_BOX[1]) * FACE_SCALE
    tile_size = (face_w, face_h + LABEL_HEIGHT)
    canvas_size = (tile_size[0] * 3 + GAP * 4, tile_size[1] * 3 + GAP * 4)
    title = make_title_tile(tile_size)
    frames = []
    for state in ("idle", "talking", "idle", "blink", "idle", "talking", "blink_talking", "idle"):
        canvas = Image.new("RGB", canvas_size, "#d8d8d8")
        for index, slug in enumerate(EXPRESSIONS):
            x = GAP + (index % 3) * (tile_size[0] + GAP)
            y = GAP + (index // 3) * (tile_size[1] + GAP)
            canvas.paste(make_face_tile(slug, state), (x, y))
        canvas.paste(title, (GAP + 2 * (tile_size[0] + GAP), GAP + 2 * (tile_size[1] + GAP)))
        frames.append(canvas)
    save_gif(destination / "all_expressions.gif", frames, ALL_DURATIONS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, help='Folder containing four candidate PNG states')
    parser.add_argument('--output', type=Path, default=ROOT/'experiments/preview_output')
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(ROOT/'static'):
        parser.error('Render to a candidate folder; use publish_artwork.py for static assets')
    if args.source:
        render_state_gifs(args.source, args.output)
    else:
        for slug in EXPRESSIONS:
            render_state_gifs(ANIMATION_DIR/slug, args.output/slug)
        build_all_expressions_gif(args.output)


if __name__ == "__main__":
    main()
