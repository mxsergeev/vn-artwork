#!/usr/bin/env python3
"""Build expression-specific blink/talk states from source-anchored donor crops."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

from artwork_tools import compose_feature, align_feature, record_build, save_stage_review

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


def clip_mask_y(mask: np.ndarray, bounds: list[int | None], feather: float,
                name: str) -> np.ndarray:
    """Clip one expression's eye contour vertically, then feather the new edge."""
    if len(bounds) != 2:
        raise ValueError(f"{name}: clip_y must be [min_y, max_y]")
    min_y, max_y = bounds
    h = mask.shape[0]
    if min_y is not None and not 0 <= min_y < h:
        raise ValueError(f"{name}: invalid eye_clip_y minimum {min_y}")
    if max_y is not None and not 0 < max_y <= h:
        raise ValueError(f"{name}: invalid eye_clip_y maximum {max_y}")
    if min_y is not None and max_y is not None and min_y >= max_y:
        raise ValueError(f"{name}: empty eye_clip_y interval {bounds}")

    binary = (mask > 0).astype(np.uint8)
    if min_y is not None:
        binary[:min_y, :] = 0
    if max_y is not None:
        binary[max_y:, :] = 0
    if not np.any(binary):
        raise ValueError(f"{name}: eye_clip_y removed the entire expression-specific mask")
    distance = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    return np.clip(distance / feather, 0.0, 1.0).astype(np.float32)


def assert_mask_fits_donor(mask: np.ndarray, box: list[int], name: str) -> None:
    """A mask cannot transplant pixels that lie outside the actual donor crop."""
    x0, y0, x1, y1 = box
    active = mask > 0
    within = np.zeros_like(active)
    within[y0:y1, x0:x1] = True
    excess = int(np.count_nonzero(active & ~within))
    if excess:
        raise AssertionError(
            f"{name}: {excess} mask pixels are outside the donor crop {box}; "
            "these pixels cannot contain the requested donor feature"
        )


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
                  mask: np.ndarray, sample_region: list[int]) -> tuple[np.ndarray, np.ndarray, dict]:
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
    return out, donor, {"skin_rgb_offset": [round(float(v), 2) for v in offset], "skin_sample_pixels": samples}


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


def save_gif(path: Path, frames: list[np.ndarray], durations: list[int], size=(1086, 1448)) -> None:
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
    save_pil_png_atomic(path, Image.fromarray(frame, "RGBA"))


def save_pil_png_atomic(path: Path, image: Image.Image) -> None:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    payload = buffer.getvalue()
    if not payload.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82"):
        raise AssertionError(f"{path.name}: encoder returned an incomplete PNG")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(payload)
    with Image.open(tmp) as check:
        check.load()
        if check.format != "PNG" or check.size != image.size or check.mode != image.mode:
            raise AssertionError(f"{path.name}: invalid temporary PNG")
    tmp.replace(path)
    with Image.open(path) as check:
        check.load()


def review_images(out: Path, base: np.ndarray, eye_frame: np.ndarray, mouth_frame: np.ndarray,
                  frames: dict[str, np.ndarray], eye_mask: np.ndarray,
                  corrected_eye_donor: np.ndarray,
                  eye_components: dict[str, np.ndarray], eye_preserve_mask: np.ndarray,
                  mouth_mask: np.ndarray,
                  source_mouth: str, mouth_donor: np.ndarray,
                  eye_box: list[int], mouth_box: list[int]) -> None:
    full_box = (434, 64, 640, 268)
    labels = list(frames)
    canvas = Image.new("RGB", (206 * 3 * len(labels), 204 * 3 + 28), "#f7f7f7")
    d = ImageDraw.Draw(canvas)
    for i, key in enumerate(labels):
        im = face(frames[key], full_box, 3)
        x = i * im.width
        canvas.paste(im, (x, 28))
        d.text((x + 6, 6), key, fill="#111")
    save_pil_png_atomic(out / "four_states_face_comparison.png", canvas)

    overview_eye_box = (454, 112, 608, 170)
    eye_views = [face(base, overview_eye_box, 8), face(corrected_eye_donor, overview_eye_box, 8),
                 face(eye_frame, overview_eye_box, 8)]
    eye = Image.new("RGB", (eye_views[0].width * 3, eye_views[0].height + 28), "#f7f7f7")
    for i, view in enumerate(eye_views):
        eye.paste(view, (i * view.width, 28))
    e = ImageDraw.Draw(eye)
    for i, label in enumerate(("Source", "Closed-eye donor", "Blink result")):
        e.text((i * eye_views[0].width + 4, 6), label, fill="#111")
    save_pil_png_atomic(out / "eye_donor_result_8x.png", eye)
    save_pil_png_atomic(out / "eyes_8x_inspection.png", eye)

    overview_mouth_box = (505, 172, 582, 220)
    mouth_views = [face(base, overview_mouth_box, 8), face(mouth_frame, overview_mouth_box, 8)]
    mouth = Image.new("RGB", (mouth_views[0].width * 2, mouth_views[0].height + 28), "#f7f7f7")
    mouth.paste(mouth_views[0], (0, 28)); mouth.paste(mouth_views[1], (mouth_views[0].width, 28))
    m = ImageDraw.Draw(mouth); m.text((4, 6), "Source", fill="#111"); m.text((mouth_views[0].width + 4, 6), "Mouth transplant", fill="#111")
    save_pil_png_atomic(out / "mouth_8x_inspection.png", mouth)

    bg = flatten(base).convert("RGBA")
    overlay = np.asarray(bg).copy()
    for name, color in (("viewer_left", (45, 225, 70)), ("viewer_right", (245, 155, 35))):
        active = eye_components[name] > 0
        for c, value in enumerate(color):
            overlay[:, :, c][active] = np.uint8(overlay[:, :, c][active] * .45 + value * .55)
    for c, value in enumerate((255, 170, 0)):
        active = eye_preserve_mask
        overlay[:, :, c][active] = np.uint8(overlay[:, :, c][active] * .25 + value * .75)
    for c, value in enumerate((50, 125, 240)):
        active = mouth_mask > 0
        overlay[:, :, c][active] = np.uint8(overlay[:, :, c][active] * .55 + value * .45)
    save_pil_png_atomic(out / "feature_masks.png", Image.fromarray(overlay, "RGBA").crop((450, 110, 610, 222)).resize((960, 672), Image.Resampling.NEAREST))

    allowed = (eye_mask > 0) | (mouth_mask > 0)
    changed = np.any(frames["blink_talking"][:, :, :3] != base[:, :, :3], axis=2)
    boundary = changed & ~(cv2.erode(changed.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    edge = np.asarray(bg).copy()
    edge[boundary] = [0, 255, 0, 255]
    save_pil_png_atomic(out / "changed_boundary.png", Image.fromarray(edge, "RGBA").crop((450, 110, 610, 222)).resize((960, 672), Image.Resampling.NEAREST))

    eye_changed = np.any(eye_frame[:, :, :3] != base[:, :, :3], axis=2)
    eye_boundary = eye_changed & ~(cv2.erode(eye_changed.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    eye_edge = np.asarray(bg).copy()
    eye_edge[eye_boundary] = [0, 255, 0, 255]
    save_pil_png_atomic(out / "eye_changed_boundary.png", Image.fromarray(eye_edge, "RGBA").crop((450, 110, 610, 174)).resize((960, 384), Image.Resampling.NEAREST))

    # These comparisons are REVIEW MATERIAL, not an automatic quality certificate.
    # Show the donor, source, composite, and mask side by side at actual 20x zoom.
    # Mask containment checks cannot detect an eyelash or lid LEFT OUTSIDE the mask.
    def inspect_feature(label: str, donor: np.ndarray, result: np.ndarray,
                        mask: np.ndarray, box: tuple[int, int, int, int]) -> None:
        x0, y0, x1, y1 = box
        scale = 20
        views = [
            ("SOURCE", base),
            ("ALIGNED DONOR", donor),
            ("FINAL TRANSPLANT", result),
        ]
        width, height = (x1 - x0) * scale, (y1 - y0) * scale
        board = Image.new("RGB", (width * 5, height + 30), "#f7f7f7")
        draw = ImageDraw.Draw(board)
        for col, (title, frame) in enumerate(views):
            board.paste(face(frame, box, scale), (col * width, 30))
            draw.text((col * width + 5, 6), title, fill="#111111")

        mask_view = base.copy()
        active = mask > 0
        for channel, value in enumerate((25, 240, 65)):
            mask_view[:, :, channel][active] = np.uint8(
                mask_view[:, :, channel][active] * 0.55 + value * 0.45
            )
        board.paste(face(mask_view, box, scale), (3 * width, 30))
        draw.text((3 * width + 5, 6), "MASK ON SOURCE", fill="#111111")

        # Red: strong source/donor differences excluded by the mask.
        # These are CANDIDATES for missed lashes/lids, NOT verified defects:
        # unedited nearby hair or skin can legitimately differ in the donor.
        suspicious = (np.max(np.abs(donor[:, :, :3].astype(np.int16) -
                                     base[:, :, :3].astype(np.int16)), axis=2) >= 45) & ~active
        attention = base.copy()
        for channel, value in enumerate((255, 15, 25)):
            attention[:, :, channel][suspicious] = np.uint8(
                attention[:, :, channel][suspicious] * 0.35 + value * 0.65
            )
        board.paste(face(attention, box, scale), (4 * width, 30))
        draw.text((4 * width + 5, 6), "UNMASKED DONOR DIFFS: REVIEW", fill="#111111")
        save_pil_png_atomic(out / f"{label}_20x_review.png", board)

    ex0, ey0, ex1, ey1 = eye_box
    middle = (ex0 + ex1) // 2
    for label, crop in (
        ("left_eye", (max(0, ex0 - 8), max(0, ey0 - 10), middle + 8, min(base.shape[0], ey1 + 10))),
        ("right_eye", (middle - 8, max(0, ey0 - 10), min(base.shape[1], ex1 + 8), min(base.shape[0], ey1 + 10))),
    ):
        inspect_feature(label, corrected_eye_donor, eye_frame, eye_mask, crop)
    mx0, my0, mx1, my1 = mouth_box
    inspect_feature("mouth", mouth_donor, mouth_frame, mouth_mask,
                    (max(0, mx0 - 8), max(0, my0 - 8), min(base.shape[1], mx1 + 8), min(base.shape[0], my1 + 8)))


def build(config: dict, print_report: bool = True) -> dict:
    here = Path(__file__).resolve().parent / config["experiment"]
    root = ROOT
    out = here / "output"
    out.mkdir(exist_ok=True)
    src_path = root / config["source"]
    base = np.asarray(Image.open(src_path).convert("RGBA"))
    if base.shape != (1448, 1086, 4):
        raise AssertionError(f"Unexpected source dimensions: {base.shape}")
    h, w = base.shape[:2]

    # Selections describe actual source/donor geometry; uniqueness is not a gate.
    eye_components = {}
    protected_eye_components = {}
    global_eye_protect = config.get("eye_protect", [])
    for eye_name, region in config["eye_regions"].items():
        protect_polygons = [*global_eye_protect, *region.get("protect", [])]
        mask = polygon_mask(
            (w, h), region["polygons"],
            protect_polygons,
            region.get("feather", config.get("eye_feather", 1.1)),
        )
        if "clip_y" in region:
            mask = clip_mask_y(
                mask,
                region["clip_y"],
                region.get("feather", config.get("eye_feather", 1.1)),
                f"{config['slug']}/{eye_name}",
            )
        eye_components[eye_name] = mask
        if protect_polygons:
            protected_eye_components[eye_name] = polygon_mask(
                (w, h), protect_polygons, [], 1.0
            ) > 0
    eye = np.maximum.reduce(list(eye_components.values()))
    mouth = polygon_mask((w, h), [config["mouth_polygon"]], config.get("mouth_protect", []), config.get("mouth_feather", 1.2))
    if np.any((eye > 0) & (mouth > 0)):
        raise AssertionError("Eye and mouth masks overlap")
    assert_mask_fits_donor(eye, config["eye_box"], "eyes")
    assert_mask_fits_donor(mouth, config["mouth_box"], "mouth")

    eye_patch = np.asarray(Image.open(here / "assets/eyes_closed_patch.png").convert("RGB"))
    mouth_patch = np.asarray(Image.open(here / "assets/mouth_variant_patch.png").convert("RGB"))
    eye_donor, corrected_eye_donor, eye_color = feature_donor(
        base, eye_patch, config["eye_box"], eye,
        config.get("eye_sample_region", [455, 115, 607, 174]))
    mouth_donor, _, mouth_color = feature_donor(
        base, mouth_patch, config["mouth_box"], mouth,
        config.get("mouth_sample_region", [505, 174, 582, 221]))

    eye_frame = apply_feature(base, eye_donor, eye)
    eye_preserved = 0
    eye_preserve_mask = np.zeros((h, w), dtype=bool)
    preserve_rules = config.get("eye_preserve_similar", [])
    for rule in preserve_rules:
        region = polygon_mask((w, h), [rule["polygon"]], [], 1.0) > 0
        delta = np.abs(corrected_eye_donor[:, :, :3].astype(np.int16) - base[:, :, :3].astype(np.int16)).sum(axis=2)
        preserve = region & (eye > 0) & (delta <= int(rule.get("max_rgb_delta", 72)))
        eye_frame[preserve, :3] = base[preserve, :3]
        eye_preserve_mask |= preserve
        eye_preserved += int(preserve.sum())
    for rule in config.get("eye_preserve_dark", []):
        region = polygon_mask((w, h), [rule["polygon"]], [], 1.0) > 0
        rgb = base[:, :, :3].astype(np.uint16)
        dark = np.max(rgb, axis=2) <= int(rule.get("max_channel", 120))
        preserve = region & (eye > 0) & dark
        eye_frame[preserve, :3] = base[preserve, :3]
        eye_preserve_mask |= preserve
        eye_preserved += int(preserve.sum())
    eye_preserved = int(eye_preserve_mask.sum())
    mouth_frame = apply_feature(base, mouth_donor, mouth)
    eye_allowed, mouth_allowed = eye > 0, mouth > 0
    for feature, default_donor in (
        ('eye', corrected_eye_donor), ('mouth', mouth_donor)
    ):
        layers = config.get(f'{feature}_layers')
        if layers is None:
            continue  # Existing pipelines keep their exact historical arithmetic.
        donor = layers.get('donor', default_donor)
        insertion = layers['insertion']
        if 'alignment' in layers:
            donor, insertion = align_feature(donor, insertion, layers['alignment'], (w, h))
        final, declared, stages = compose_feature(
            base, donor, insertion, repair_image=layers.get('repair_image'),
            removal=layers.get('removal'), foreground=layers.get('foreground'),
            cleanup=layers.get('cleanup', ()),
        )
        save_stage_review(out/f'{feature}_stages.png', stages,
                          tuple(config[f'{feature}_box']), scale=8)
        if feature == 'eye':
            eye_frame, eye_allowed = final, declared
            corrected_eye_donor = donor
            eye = declared.astype(np.float32)
            split = (config['eye_box'][0] + config['eye_box'][2]) // 2
            left, right = eye.copy(), eye.copy()
            left[:, split:] = 0
            right[:, :split] = 0
            eye_components = {'viewer_left': left, 'viewer_right': right}
            eye_preserve_mask = np.asarray(layers.get('foreground', np.zeros((h, w)))) > 0
            eye_preserved = int(eye_preserve_mask.sum())
        else:
            mouth_frame, mouth_allowed = final, declared
            mouth_donor = donor
            mouth = declared.astype(np.float32)
    if np.any(eye_allowed & mouth_allowed):
        raise ValueError('Eye/mouth declared regions overlap; define their operation order in a custom builder')
    if not np.any(eye_frame[:, :, :3] != base[:, :, :3]):
        raise AssertionError("Eye mask makes no visible change: wrong donor, crop, or mask")
    if not np.any(mouth_frame[:, :, :3] != base[:, :, :3]):
        raise AssertionError("Mouth mask makes no visible change: wrong donor, crop, or mask")
    both_frame = eye_frame.copy()
    both_frame[mouth_allowed] = mouth_frame[mouth_allowed]
    if config["source_mouth_state"] == "closed":
        frames = {"idle": base.copy(), "blink": eye_frame, "talking": mouth_frame, "blink_talking": both_frame}
    elif config["source_mouth_state"] == "open":
        frames = {"idle": mouth_frame, "blink": both_frame, "talking": base.copy(), "blink_talking": eye_frame}
    else:
        raise ValueError(config["source_mouth_state"])

    protected_eye_checks = {}
    for eye_name, protected in protected_eye_components.items():
        per_state = {}
        for state_name, frame in frames.items():
            changed = np.any(frame[:, :, :3] != base[:, :, :3], axis=2)
            count = int(np.count_nonzero(changed & protected))
            per_state[state_name] = count
            if count:
                raise AssertionError(
                    f"{state_name}: {count} changed pixels inside protected {eye_name} hair/strand region"
                )
        protected_eye_checks[eye_name] = {
            "protected_source_pixels": int(np.count_nonzero(protected)),
            "changed_pixels_by_state": per_state,
        }

    allowed_masks = {"eye": eye_allowed, "mouth": mouth_allowed, "both": eye_allowed | mouth_allowed}
    reports = {}
    state_regions = {}
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
            raise AssertionError(f"{name}: {outside} changed pixels outside declared edit regions")
        reports[name] = {"changed_rgb_pixels": int(changed.sum()), "outside_declared_edit_regions": outside,
                         "alpha_identical": True}
        state_regions[name] = allowed
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

    review_images(out, base, eye_frame, mouth_frame, frames, eye,
                  corrected_eye_donor, eye_components, eye_preserve_mask, mouth,
                  config["source_mouth_state"], mouth_donor,
                  config["eye_box"], config["mouth_box"])
    report = {
        "expression": config["slug"],
        "source": config["source"],
        "source_git_blob_sha": git_blob_sha(src_path),
        "source_mouth_state": config["source_mouth_state"],
        "dimensions": [w, h],
        "source_alpha_preserved_for_all_states": True,
        "mask_within_donor_crop": True,
        "visual_quality_status": "UNREVIEWED — inspect each 20x donor/source/result/mask comparison and GIF",
        "eye_mask_pixels": int(np.count_nonzero(eye)),
        "eye_mask_sha256": hashlib.sha256((eye > 0).astype(np.uint8).tobytes()).hexdigest(),
        "eye_mask_region_sha256": {
            name: hashlib.sha256((mask > 0).astype(np.uint8).tobytes()).hexdigest()
            for name, mask in eye_components.items()
        },
        "eye_mask_region_pixels": {
            name: int(np.count_nonzero(mask)) for name, mask in eye_components.items()
        },
        "eye_mask_clip_y": {
            name: region.get("clip_y") for name, region in config["eye_regions"].items()
        },
        "eye_preserved_source_pixels": eye_preserved,
        "protected_eye_regions_unchanged": protected_eye_checks,
        "mouth_mask_pixels": int(np.count_nonzero(mouth)),
        "eye_donor_color": eye_color,
        "mouth_donor_color": mouth_color,
        "states": reports,
        "gifs": ["blink.gif", "talk.gif", "combined.gif"],
        "notes": config.get("notes", "")
    }
    (out / "QA.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    reviews = [name for name in (
        'left_eye_20x_review.png', 'right_eye_20x_review.png', 'mouth_20x_review.png',
        'eye_stages.png', 'mouth_stages.png',
    ) if (out/name).exists() and (not name.endswith('_stages.png') or config.get(name.split('_')[0]+'_layers') is not None)]
    if not config.get('defer_manifest', False):
        record_build(out, src_path, inputs=sorted((here/'assets').glob('*.png')),
                     scripts=[here/'build.py', Path(__file__), ROOT/'experiments/artwork_tools.py'],
                     regions=state_regions, reviews=reviews, notes=config.get('notes', ''))
    if print_report:
        print(json.dumps(report, indent=2))
    return report
