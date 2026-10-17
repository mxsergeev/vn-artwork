#!/usr/bin/env python3
"""Build expression-specific blink/talk states from source-anchored donor crops."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def polygon_mask(size: tuple[int, int], polygons: list[list[list[int]]],
                 protects: list[list[list[int]]], feather: float) -> np.ndarray:
    w, h = size
    raw = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(raw)
    for poly in polygons:
        draw.polygon([tuple(p) for p in poly], fill=255)
    for poly in protects:
        draw.polygon([tuple(p) for p in poly], fill=0)
    binary = (np.asarray(raw) > 0).astype(np.uint8)
    if not np.any(binary):
        raise ValueError("Empty feature mask")
    distance = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    return np.clip(distance / feather, 0.0, 1.0).astype(np.float32)


def skin_color_offset(base: np.ndarray, donor: np.ndarray, mask: np.ndarray,
                      region: tuple[int, int, int, int]) -> tuple[np.ndarray, int]:
    """Estimate a small RGB correction from nearby skin-only pixels."""
    h, w = mask.shape
    x0, y0, x1, y1 = region
    local = np.zeros((h, w), dtype=bool)
    local[y0:y1, x0:x1] = True
    excluded = cv2.dilate((mask > 0).astype(np.uint8), np.ones((11, 11), np.uint8)) > 0

    def skin(rgb: np.ndarray) -> np.ndarray:
        r, g, b = [rgb[:, :, c].astype(np.int16) for c in range(3)]
        return ((r > 120) & (g > 70) & (b > 45) & (r - g > 12) &
                (g - b > 3) & (r - g < 100) & (r < 250))

    valid = local & ~excluded & skin(base[:, :, :3]) & skin(donor[:, :, :3])
    if int(valid.sum()) < 8:
        raise ValueError(f"Only {int(valid.sum())} nearby skin pixels for color correction")
    delta = base[:, :, :3].astype(np.int16) - donor[:, :, :3].astype(np.int16)
    offset = np.median(delta[valid], axis=0)
    offset = np.clip(offset, -22, 22).astype(np.float32)
    return offset, int(valid.sum())


def feature_donor(base: np.ndarray, patch: np.ndarray, box: list[int],
                  mask: np.ndarray, sample_region: list[int]) -> tuple[np.ndarray, dict]:
    x0, y0, x1, y1 = box
    if patch.shape[:2] != (y1 - y0, x1 - x0):
        raise ValueError(f"Donor crop size {patch.shape[:2]} does not match box {box}")
    donor = base.copy()
    donor[y0:y1, x0:x1, :3] = patch[:, :, :3]
    offset, samples = skin_color_offset(base, donor, mask, tuple(sample_region))
    donor[:, :, :3] = np.clip(donor[:, :, :3].astype(np.float32) + offset, 0, 255).astype(np.uint8)
    out = base.copy()
    out[:, :, :3] = np.rint(base[:, :, :3].astype(np.float32) * (1 - mask[:, :, None]) +
                            donor[:, :, :3].astype(np.float32) * mask[:, :, None]).clip(0, 255).astype(np.uint8)
    out[:, :, 3] = base[:, :, 3]
    return out, {"skin_rgb_offset": [round(float(v), 2) for v in offset], "skin_sample_pixels": samples}


def apply_feature(bottom: np.ndarray, donor: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = bottom.copy()
    active = mask > 0
    out[:, :, :3][active] = donor[:, :, :3][active]
    out[:, :, 3] = bottom[:, :, 3]
    return out


def flatten(frame: np.ndarray, bg: str = "#f0f0f0") -> Image.Image:
    im = Image.fromarray(frame, "RGBA")
    matte = Image.new("RGBA", im.size, bg)
    matte.alpha_composite(im)
    return matte.convert("RGB")


def face(frame: np.ndarray, box: tuple[int, int, int, int], scale: int = 4) -> Image.Image:
    im = Image.fromarray(frame, "RGBA").crop(box)
    bg = Image.new("RGBA", im.size, "#f0f0f0")
    bg.alpha_composite(im)
    return bg.convert("RGB").resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)


def save_gif(path: Path, frames: list[np.ndarray], durations: list[int], size=(272, 362)) -> None:
    flattened = [flatten(a).resize(size, Image.Resampling.BILINEAR) for a in frames]
    montage = Image.new("RGB", (size[0], size[1] * len(flattened)))
    for i, im in enumerate(flattened):
        montage.paste(im, (0, i * size[1]))
    palette = montage.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    indexed = [im.quantize(palette=palette, dither=Image.Dither.NONE) for im in flattened]
    indexed[0].save(path, save_all=True, append_images=indexed[1:], duration=durations,
                    loop=0, disposal=2, optimize=False)
    with Image.open(path) as check:
        check.verify()
    with Image.open(path) as check:
        if check.n_frames != len(frames):
            raise AssertionError(f"{path.name}: expected {len(frames)} frames, got {check.n_frames}")


def save_png_atomic(path: Path, frame: np.ndarray) -> None:
    buffer = io.BytesIO()
    Image.fromarray(frame, "RGBA").save(buffer, format="PNG", optimize=False)
    payload = buffer.getvalue()
    if not payload.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82"):
        raise AssertionError(f"{path.name}: encoder returned an incomplete PNG")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(payload)
    with Image.open(tmp) as check:
        check.load()
        if check.size != (1086, 1448) or check.mode != "RGBA":
            raise AssertionError(f"{path.name}: invalid temporary PNG")
    tmp.replace(path)
    with Image.open(path) as check:
        check.load()


def review_images(out: Path, base: np.ndarray, eye_frame: np.ndarray, mouth_frame: np.ndarray,
                  frames: dict[str, np.ndarray], eye_mask: np.ndarray, mouth_mask: np.ndarray,
                  source_mouth: str) -> None:
    full_box = (434, 64, 640, 268)
    labels = list(frames)
    canvas = Image.new("RGB", (206 * 3 * len(labels), 204 * 3 + 28), "#f7f7f7")
    d = ImageDraw.Draw(canvas)
    for i, key in enumerate(labels):
        im = face(frames[key], full_box, 3)
        x = i * im.width
        canvas.paste(im, (x, 28))
        d.text((x + 6, 6), key, fill="#111")
    canvas.save(out / "four_states_face_comparison.png", optimize=True)

    eye_box = (454, 112, 608, 170)
    eye_views = [face(base, eye_box, 8), face(eye_frame, eye_box, 8)]
    eye = Image.new("RGB", (eye_views[0].width * 2, eye_views[0].height + 28), "#f7f7f7")
    eye.paste(eye_views[0], (0, 28)); eye.paste(eye_views[1], (eye_views[0].width, 28))
    e = ImageDraw.Draw(eye); e.text((4, 6), "Source", fill="#111"); e.text((eye_views[0].width + 4, 6), "Blink transplant", fill="#111")
    eye.save(out / "eyes_8x_inspection.png", optimize=True)

    mouth_box = (505, 172, 582, 220)
    mouth_views = [face(base, mouth_box, 8), face(mouth_frame, mouth_box, 8)]
    mouth = Image.new("RGB", (mouth_views[0].width * 2, mouth_views[0].height + 28), "#f7f7f7")
    mouth.paste(mouth_views[0], (0, 28)); mouth.paste(mouth_views[1], (mouth_views[0].width, 28))
    m = ImageDraw.Draw(mouth); m.text((4, 6), "Source", fill="#111"); m.text((mouth_views[0].width + 4, 6), "Mouth transplant", fill="#111")
    mouth.save(out / "mouth_8x_inspection.png", optimize=True)

    bg = flatten(base).convert("RGBA")
    overlay = np.asarray(bg).copy()
    for c, value in enumerate((45, 225, 70)):
        active = eye_mask > 0
        overlay[:, :, c][active] = np.uint8(overlay[:, :, c][active] * .55 + value * .45)
    for c, value in enumerate((50, 125, 240)):
        active = mouth_mask > 0
        overlay[:, :, c][active] = np.uint8(overlay[:, :, c][active] * .55 + value * .45)
    Image.fromarray(overlay, "RGBA").crop((450, 110, 610, 222)).resize((960, 672), Image.Resampling.NEAREST).save(out / "feature_masks.png", optimize=True)

    allowed = (eye_mask > 0) | (mouth_mask > 0)
    changed = np.any(frames["blink_talking"][:, :, :3] != base[:, :, :3], axis=2)
    boundary = changed & ~(cv2.erode(changed.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    edge = np.asarray(bg).copy()
    edge[boundary] = [0, 255, 0, 255]
    Image.fromarray(edge, "RGBA").crop((450, 110, 610, 222)).resize((960, 672), Image.Resampling.NEAREST).save(out / "changed_boundary.png", optimize=True)


def build(config: dict) -> dict:
    here = Path(__file__).resolve().parent / config["experiment"]
    root = ROOT
    out = here / "output"
    out.mkdir(exist_ok=True)
    src_path = root / config["source"]
    base = np.asarray(Image.open(src_path).convert("RGBA"))
    if base.shape != (1448, 1086, 4):
        raise AssertionError(f"Unexpected source dimensions: {base.shape}")
    h, w = base.shape[:2]

    eye = polygon_mask((w, h), config["eye_polygons"], config.get("eye_protect", []), config.get("eye_feather", 1.1))
    mouth = polygon_mask((w, h), [config["mouth_polygon"]], config.get("mouth_protect", []), config.get("mouth_feather", 1.2))
    if np.any((eye > 0) & (mouth > 0)):
        raise AssertionError("Eye and mouth masks overlap")

    eye_patch = np.asarray(Image.open(here / "assets/eyes_closed_patch.png").convert("RGB"))
    mouth_patch = np.asarray(Image.open(here / "assets/mouth_variant_patch.png").convert("RGB"))
    eye_donor, eye_color = feature_donor(base, eye_patch, config["eye_box"], eye,
                                        config.get("eye_sample_region", [455, 115, 607, 174]))
    mouth_donor, mouth_color = feature_donor(base, mouth_patch, config["mouth_box"], mouth,
                                             config.get("mouth_sample_region", [505, 174, 582, 221]))

    eye_frame = apply_feature(base, eye_donor, eye)
    mouth_frame = apply_feature(base, mouth_donor, mouth)
    both_frame = apply_feature(eye_frame, mouth_donor, mouth)
    if config["source_mouth_state"] == "closed":
        frames = {"idle": base.copy(), "blink": eye_frame, "talking": mouth_frame, "blink_talking": both_frame}
    elif config["source_mouth_state"] == "open":
        frames = {"idle": mouth_frame, "blink": both_frame, "talking": base.copy(), "blink_talking": eye_frame}
    else:
        raise ValueError(config["source_mouth_state"])

    allowed_masks = {"eye": eye > 0, "mouth": mouth > 0, "both": (eye > 0) | (mouth > 0)}
    reports = {}
    for name, frame in frames.items():
        changed = np.any(frame[:, :, :3] != base[:, :, :3], axis=2)
        if not np.array_equal(frame[:, :, 3], base[:, :, 3]):
            raise AssertionError(f"{name}: source alpha changed")
        allowed = (eye > 0) if name == "blink_talking" and config["source_mouth_state"] == "open" else None
        if name == "blink":
            allowed = allowed_masks["both"] if config["source_mouth_state"] == "open" else allowed_masks["eye"]
        elif name == "talking":
            allowed = np.zeros((h, w), dtype=bool) if config["source_mouth_state"] == "open" else allowed_masks["mouth"]
        elif name == "idle":
            allowed = allowed_masks["mouth"] if config["source_mouth_state"] == "open" else np.zeros((h, w), dtype=bool)
        elif name == "blink_talking":
            allowed = allowed_masks["eye"] if config["source_mouth_state"] == "open" else allowed_masks["both"]
        outside = int(np.count_nonzero(changed & ~allowed))
        if outside:
            raise AssertionError(f"{name}: {outside} changed pixels outside feature masks")
        reports[name] = {"changed_rgb_pixels": int(changed.sum()), "outside_feature_mask_pixels": outside,
                         "alpha_identical": True}
        path = out / f"{name}.png"
        save_png_atomic(path, frame)

    prefix = config["slug"]
    base_mouth = base if config["source_mouth_state"] == "closed" else mouth_frame
    blink_closed = eye_frame if config["source_mouth_state"] == "closed" else both_frame
    talk_frames = [frames["idle"], frames["talking"], frames["idle"], frames["talking"], frames["idle"]]
    save_gif(out / "blink.gif", [base_mouth, blink_closed, base_mouth, blink_closed, base_mouth], [1050, 130, 1250, 130, 1050])
    save_gif(out / "talk.gif", talk_frames, [260, 220, 220, 250, 900])
    save_gif(out / "combined.gif", [frames[k] for k in ["idle", "talking", "idle", "blink", "idle", "talking", "blink_talking", "talking", "idle"]],
             [450, 220, 300, 130, 430, 220, 130, 240, 1100])

    review_images(out, base, eye_frame, mouth_frame, frames, eye, mouth, config["source_mouth_state"])
    report = {
        "expression": config["slug"],
        "source": config["source"],
        "source_git_blob_sha": git_blob_sha(src_path),
        "source_mouth_state": config["source_mouth_state"],
        "dimensions": [w, h],
        "source_alpha_preserved_for_all_states": True,
        "eye_mask_pixels": int(np.count_nonzero(eye)),
        "mouth_mask_pixels": int(np.count_nonzero(mouth)),
        "eye_donor_color": eye_color,
        "mouth_donor_color": mouth_color,
        "states": reports,
        "gifs": ["blink.gif", "talk.gif", "combined.gif"],
        "notes": config.get("notes", "")
    }
    (out / "QA.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report
