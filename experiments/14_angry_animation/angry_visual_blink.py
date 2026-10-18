#!/usr/bin/env python3
"""Eye-only Angry blink reconstruction using a source-matched donor crop."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "static/sprites/05_angry.png"
DONOR = HERE / "assets/eyes_closed_angry_patch.png"
OUT = HERE / "output"
DONOR_BOX = (460, 112, 606, 176)

LEFT_REGION = [[(474,143),(478,140),(485,140),(493,141),(502,142),(510,143),(516,146),(517,151),(514,156),(507,160),(497,161),(487,159),(479,156),(475,151)]]
RIGHT_REGION = [[(537,140),(541,137),(547,135),(554,133),(562,131),(570,129),(578,128),(584,130),(588,134),(590,141),(589,148),(584,152),(575,154),(565,153),(555,151),(546,148),(540,145)]]
BROW_POLYGONS = [
    [(476,135),(482,135),(489,136),(497,137),(505,138),(513,139),(519,141),(520,143),(515,142),(507,141),(498,140),(490,139),(482,138),(477,138)],
    [(531,134),(538,132),(546,130),(554,127),(563,124),(572,121),(580,118),(585,119),(585,122),(578,124),(569,127),(560,130),(552,133),(544,136),(537,138),(533,137)],
]
HAIR_POLYGONS = [
    [(514,129),(519,131),(521,137),(524,143),(528,149),(533,157),(532,164),(527,158),(523,151),(519,145),(516,139)],
    [(583,121),(588,121),(590,128),(590,140),(589,151),(586,156),(583,151),(584,140)],
]
LID_POLYGONS = [
    [(475,147),(478,147),(484,149),(490,150),(497,150),(503,149),(507,150),(505,154),(500,156),(493,157),(486,156),(480,154),(476,151)],
    [(549,139),(553,138),(559,137),(566,136),(573,135),(580,135),(585,137),(586,140),(582,143),(575,145),(567,146),(560,146),(553,144),(550,142)],
]


def polygon_mask(size, polygons):
    layer = Image.new("L", size, 0)
    draw = ImageDraw.Draw(layer)
    for polygon in polygons:
        draw.polygon(polygon, fill=255)
    return np.asarray(layer) > 0


def skin(rgb):
    r, g, b = [rgb[:, :, i].astype(np.int16) for i in range(3)]
    return ((r > 120) & (g > 70) & (b > 45) & (r-g > 12) &
            (g-b > 3) & (r-g < 100))


def make_closed_blink() -> np.ndarray:
    source = np.asarray(Image.open(SOURCE).convert("RGBA"))
    donor = source.copy()
    donor_crop = np.asarray(Image.open(DONOR).convert("RGB"))
    x0, y0, x1, y1 = DONOR_BOX
    if donor_crop.shape != (y1-y0, x1-x0, 3):
        raise ValueError(f"Unexpected donor crop size: {donor_crop.shape}")
    donor[y0:y1, x0:x1, :3] = donor_crop

    def transfer_skin(base, region):
        hard = region.astype(np.float32)
        alpha = np.minimum(hard, cv2.GaussianBlur(hard, (3, 3), 0.6))
        ring = cv2.dilate(region.astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        ring &= ~region
        valid = ring & skin(source[:, :, :3]) & skin(donor[:, :, :3])
        if int(valid.sum()) < 8:
            raise ValueError("Not enough nearby skin pixels for donor color correction")
        delta = np.median(source[:, :, :3][valid].astype(np.int16) -
                          donor[:, :, :3][valid].astype(np.int16), axis=0)
        delta = np.clip(delta, -8, 8).astype(np.float32)
        adjusted = donor[:, :, :3].astype(np.float32).copy()
        adjusted[skin(donor[:, :, :3])] += delta
        a = alpha[:, :, None]
        out = base.copy()
        out[:, :, :3] = np.rint(source[:, :, :3].astype(np.float32) * (1-a) +
                                np.clip(adjusted, 0, 255) * a).clip(0, 255).astype(np.uint8)
        return out

    left = polygon_mask(source.shape[1::-1], LEFT_REGION)
    right = polygon_mask(source.shape[1::-1], RIGHT_REGION)
    result = transfer_skin(source, left)
    result = transfer_skin(result, right)

    # Keep exact source brow and hair strokes as foreground layers.
    for polygons, threshold in ((BROW_POLYGONS, 225), (HAIR_POLYGONS, 230)):
        traced = polygon_mask(source.shape[1::-1], polygons)
        dark = np.max(source[:, :, :3], axis=2) < threshold
        core = traced & dark
        grown = cv2.dilate(core.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        restore = grown & cv2.dilate(traced.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        result[restore, :3] = source[restore, :3]

    # Place the closed lid lines over the repaired skin, while retaining crossing hair.
    lids = polygon_mask(source.shape[1::-1], LID_POLYGONS)
    hair = polygon_mask(source.shape[1::-1], HAIR_POLYGONS)
    lids &= ~hair
    alpha = np.minimum(lids.astype(np.float32),
                       cv2.GaussianBlur(lids.astype(np.float32), (3, 3), 0.55))
    a = alpha[:, :, None]
    result[:, :, :3] = np.rint(result[:, :, :3].astype(np.float32) * (1-a) +
                               donor[:, :, :3].astype(np.float32) * a).clip(0, 255).astype(np.uint8)
    result[:, :, 3] = source[:, :, 3]
    return result


def apply_to_states() -> None:
    blink = make_closed_blink()
    source = np.asarray(Image.open(SOURCE).convert("RGBA"))
    idle = np.asarray(Image.open(OUT / "idle.png").convert("RGBA"))
    changed = np.any(blink[:, :, :3] != source[:, :, :3], axis=2)
    blink_talking = idle.copy()
    blink_talking[changed] = blink[changed]
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(blink, "RGBA").save(OUT / "angry_visual_blink.png")
    Image.fromarray(blink_talking, "RGBA").save(OUT / "angry_visual_blink_talking.png")
    Image.fromarray(blink, "RGBA").save(OUT / "blink.png")
    Image.fromarray(blink_talking, "RGBA").save(OUT / "blink_talking.png")
    # Regenerate the experiment previews after replacing the generic blink.
    from animation_builder import save_gif
    talking = np.asarray(Image.open(OUT / "talking.png").convert("RGBA"))
    save_gif(OUT / "blink.gif", [idle, blink, idle, blink, idle],
             [1050, 130, 1250, 130, 1050])
    save_gif(OUT / "talk.gif", [idle, talking, idle, talking, idle],
             [260, 220, 220, 250, 900])
    save_gif(OUT / "combined.gif",
             [idle, talking, idle, blink, idle, talking, blink_talking, talking, idle],
             [450, 220, 300, 130, 430, 220, 130, 240, 1100])


if __name__ == "__main__":
    apply_to_states()
