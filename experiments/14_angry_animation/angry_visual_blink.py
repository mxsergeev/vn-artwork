#!/usr/bin/env python3
"""Eye-only Angry blink reconstruction using a source-matched donor crop."""
from pathlib import Path
import hashlib
import json

import cv2
import numpy as np
from PIL import Image, ImageDraw
from artwork_tools import composite, restore_foreground, record_build, save_stage_review

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
        corrected = donor.astype(np.float32)
        corrected[:, :, :3] = np.clip(adjusted, 0, 255)
        return composite(base, corrected, alpha)

    left = polygon_mask(source.shape[1::-1], LEFT_REGION)
    right = polygon_mask(source.shape[1::-1], RIGHT_REGION)
    result = transfer_skin(source, left)
    result = transfer_skin(result, right)
    repaired = result.copy()

    # Place the closed lid lines over the repaired skin.
    lids = polygon_mask(source.shape[1::-1], LID_POLYGONS)
    hair = polygon_mask(source.shape[1::-1], HAIR_POLYGONS)
    lids &= ~hair
    alpha = np.minimum(lids.astype(np.float32),
                       cv2.GaussianBlur(lids.astype(np.float32), (3, 3), 0.55))
    a = alpha[:, :, None]
    result[:, :, :3] = np.rint(result[:, :, :3].astype(np.float32) * (1-a) +
                               donor[:, :, :3].astype(np.float32) * a).clip(0, 255).astype(np.uint8)

    # Restore source brow and hair last so their antialiased edges stay in front.
    for polygons, threshold in ((BROW_POLYGONS, 225), (HAIR_POLYGONS, 230)):
        traced = polygon_mask(source.shape[1::-1], polygons)
        dark = np.max(source[:, :, :3], axis=2) < threshold
        core = traced & dark
        grown = cv2.dilate(core.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        restore = grown & cv2.dilate(traced.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
        result = restore_foreground(result, source, restore.astype(np.float32))

    result[:, :, 3] = source[:, :, 3]
    save_stage_review(OUT/'angry_layer_stages.png',
                      {'source': source, 'donor': donor, 'skin repaired': repaired, 'final': result},
                      (460, 112, 606, 176), scale=6)
    return result


def _review_image(frames, before_states):
    """Create reproducible face, eye, and mouth comparisons for all four states."""
    OUT.mkdir(parents=True, exist_ok=True)
    bg = "#f0f0f0"

    def render(frame, box, scale):
        crop = Image.fromarray(frame, "RGBA").crop(box)
        matte = Image.new("RGBA", crop.size, bg)
        matte.alpha_composite(crop)
        return matte.convert("RGB").resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)

    reviews = (
        ("face", (434, 64, 640, 268), 2),
        ("eyes_8x", DONOR_BOX, 8),
        ("mouth_8x", (505, 174, 582, 219), 8),
    )
    for suffix, box, scale in reviews:
        w, h = (box[2] - box[0]) * scale, (box[3] - box[1]) * scale
        label_h = 26
        sheet = Image.new("RGB", (w * 2, (h + label_h) * len(frames)), bg)
        draw = ImageDraw.Draw(sheet)
        for row, (state, after) in enumerate(frames.items()):
            y = row * (h + label_h)
            draw.text((5, y + 5), f"{state} — before", fill="#111")
            draw.text((w + 5, y + 5), f"{state} — after", fill="#111")
            sheet.paste(render(before_states[state], box, scale), (0, y + label_h))
            sheet.paste(render(after, box, scale), (w, y + label_h))
        sheet.save(OUT / f"angry_before_after_{suffix}.png", optimize=True)


def _write_final_reviews(frames, source):
    """Refresh the eye and four-state reviews from the actual final frames."""
    donor = source.copy()
    patch = np.asarray(Image.open(DONOR).convert("RGB"))
    x0, y0, x1, y1 = DONOR_BOX
    donor[y0:y1, x0:x1, :3] = patch
    regions = (
        ("left", (466, 118, 526, 164), LEFT_REGION + BROW_POLYGONS[:1] + HAIR_POLYGONS[:1] + LID_POLYGONS[:1]),
        ("right", (530, 116, 596, 164), RIGHT_REGION + BROW_POLYGONS[1:] + HAIR_POLYGONS[1:] + LID_POLYGONS[1:]),
    )
    for side, box, polygons in regions:
        x0, y0, x1, y1 = box
        scale = 20
        panels = []
        for label, frame in (("SOURCE", source), ("CLOSED-EYE DONOR", donor), ("FINAL BLINK", frames["blink"])):
            crop = Image.fromarray(frame, "RGBA").crop(box)
            matte = Image.new("RGBA", crop.size, "#f0f0f0")
            matte.alpha_composite(crop)
            panels.append((label, matte.convert("RGB").resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)))
        overlay = source.copy()
        mask = polygon_mask(source.shape[1::-1], polygons)
        overlay[mask, :3] = np.rint(overlay[mask, :3].astype(np.float32) * .45 + np.array([25, 235, 60]) * .55).astype(np.uint8)
        crop = Image.fromarray(overlay, "RGBA").crop(box)
        matte = Image.new("RGBA", crop.size, "#f0f0f0")
        matte.alpha_composite(crop)
        panels.append(("EDIT / RESTORE REGIONS", matte.convert("RGB").resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)))
        panel_w, panel_h = panels[0][1].size
        label_h = 28
        board = Image.new("RGB", (panel_w * len(panels), panel_h + label_h), "#f0f0f0")
        draw = ImageDraw.Draw(board)
        for col, (label, panel) in enumerate(panels):
            draw.text((col * panel_w + 5, 6), label, fill="#111")
            board.paste(panel, (col * panel_w, label_h))
        board.save(OUT / f"{side}_eye_20x_review.png", optimize=True)

    # Rebuild the four-state contact sheet from the final frames.
    face_box = (434, 64, 640, 268)
    scale = 3
    box_w, box_h = (face_box[2] - face_box[0]) * scale, (face_box[3] - face_box[1]) * scale
    label_h = 28
    board = Image.new("RGB", (box_w * 4, box_h + label_h), "#f0f0f0")
    draw = ImageDraw.Draw(board)
    for col, (state, frame) in enumerate(frames.items()):
        crop = Image.fromarray(frame, "RGBA").crop(face_box)
        matte = Image.new("RGBA", crop.size, "#f0f0f0")
        matte.alpha_composite(crop)
        panel = matte.convert("RGB").resize((box_w, box_h), Image.Resampling.NEAREST)
        board.paste(panel, (col * box_w, label_h))
        draw.text((col * box_w + 5, 6), state, fill="#111")
    board.save(OUT / "four_states_face_comparison.png", optimize=True)


def apply_to_states(before_states=None) -> None:
    blink = make_closed_blink()
    source = np.asarray(Image.open(SOURCE).convert("RGBA"))
    idle = np.asarray(Image.open(OUT / "idle.png").convert("RGBA"))
    talking = np.asarray(Image.open(OUT / "talking.png").convert("RGBA"))
    changed = np.any(blink[:, :, :3] != source[:, :, :3], axis=2)
    # A blink preserves the idle mouth; blink_talking preserves the talking mouth.
    blink_idle = idle.copy()
    blink_idle[changed] = blink[changed]
    blink_talking = talking.copy()
    blink_talking[changed] = blink[changed]
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(blink, "RGBA").save(OUT / "angry_visual_blink.png")
    Image.fromarray(blink_idle, "RGBA").save(OUT / "angry_visual_blink_idle.png")
    Image.fromarray(blink_talking, "RGBA").save(OUT / "angry_visual_blink_talking.png")
    Image.fromarray(blink_idle, "RGBA").save(OUT / "blink.png")
    Image.fromarray(blink_talking, "RGBA").save(OUT / "blink_talking.png")
    frames = {
        "idle": idle,
        "blink": blink_idle,
        "talking": talking,
        "blink_talking": blink_talking,
    }
    _write_final_reviews(frames, source)
    if before_states is not None:
        _review_image(frames, before_states)

    # Record hashes and state-to-state checks only after all final frames exist.
    report_path = OUT / "QA.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    eye_polygons = LEFT_REGION + RIGHT_REGION + LID_POLYGONS
    eye_area = polygon_mask(source.shape[1::-1], eye_polygons)
    idle_changes = np.any(idle[:, :, :3] != source[:, :, :3], axis=2)
    allowed = eye_area | idle_changes
    protected_checks = {}
    for side, brow, hair in (("viewer_left", BROW_POLYGONS[:1], HAIR_POLYGONS[:1]),
                             ("viewer_right", BROW_POLYGONS[1:], HAIR_POLYGONS[1:])):
        protected = np.zeros(source.shape[:2], dtype=bool)
        for polygons, threshold in ((brow, 225), (hair, 230)):
            traced = polygon_mask(source.shape[1::-1], polygons)
            dark = np.max(source[:, :, :3], axis=2) < threshold
            core = traced & dark
            grown = cv2.dilate(core.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            protected |= grown & (cv2.dilate(traced.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
        changed_by_state = {}
        for name, frame in frames.items():
            changes = np.any(frame[:, :, :3] != source[:, :, :3], axis=2)
            changed_by_state[name] = int(np.count_nonzero(changes & protected))
            if changed_by_state[name]:
                raise AssertionError(f"{name}: source {side} brow/hair pixels changed")
        protected_checks[side] = {
            "protected_source_pixels": int(protected.sum()),
            "changed_pixels_by_state": changed_by_state,
        }
    final_states = {}
    for name, frame in frames.items():
        changes = np.any(frame[:, :, :3] != source[:, :, :3], axis=2)
        final_states[name] = {
            "changed_rgb_pixels": int(changes.sum()),
            "outside_declared_edit_regions": int(np.count_nonzero(changes & ~allowed)),
            "alpha_identical": bool(np.array_equal(frame[:, :, 3], source[:, :, 3])),
            "output_sha256": hashlib.sha256((OUT / f"{name}.png").read_bytes()).hexdigest(),
        }
    report["states"] = final_states
    report["eye_mask_pixels"] = int(eye_area.sum())
    report["source_alpha_preserved_for_all_states"] = all(
        item["alpha_identical"] for item in final_states.values()
    )
    report["protected_eye_regions_unchanged"] = protected_checks
    report["eye_mask_sha256"] = hashlib.sha256(eye_area.astype(np.uint8).tobytes()).hexdigest()
    eye_regions = {
        side: polygon_mask(source.shape[1::-1], polygons)
        for side, polygons in (("viewer_left", LEFT_REGION + LID_POLYGONS[:1]),
                               ("viewer_right", RIGHT_REGION + LID_POLYGONS[1:]))
    }
    report["eye_mask_region_sha256"] = {
        side: hashlib.sha256(mask.astype(np.uint8).tobytes()).hexdigest()
        for side, mask in eye_regions.items()
    }
    report["eye_mask_region_pixels"] = {
        side: int(mask.sum()) for side, mask in eye_regions.items()
    }
    x0, y0, x1, y1 = DONOR_BOX
    ys, xs = np.where(eye_area)
    report["mask_within_donor_crop"] = bool(
        len(xs) and xs.min() >= x0 and xs.max() < x1 and ys.min() >= y0 and ys.max() < y1
    )
    if not report["mask_within_donor_crop"]:
        raise AssertionError("Closed-eye feature mask extends beyond the source-matched donor crop")
    report["visual_quality_status"] = (
        "UNREVIEWED_BY_USER — final state comparisons regenerated; user sign-off is separate"
    )
    report["angry_visual_blink"] = {
        "final_states_written_after_composite": True,
        "state_mapping": {
            "blink": "closed eyes + idle mouth",
            "blink_talking": "closed eyes + talking mouth",
        },
        "alpha_matches_source": {
            name: bool(np.array_equal(frame[:, :, 3], source[:, :, 3]))
            for name, frame in frames.items()
        },
        "state_sha256": {
            name: hashlib.sha256((OUT / f"{name}.png").read_bytes()).hexdigest()
            for name in frames
        },
        "source_state_mouth_matches": {
            "blink": bool(np.array_equal(frames["blink"][174:219, 505:582], idle[174:219, 505:582])),
            "blink_talking": bool(np.array_equal(frames["blink_talking"][174:219, 505:582], talking[174:219, 505:582])),
        },
        "comparisons": [
            "angry_before_after_face.png",
            "angry_before_after_eyes_8x.png",
            "angry_before_after_mouth_8x.png",
            "left_eye_20x_review.png",
            "right_eye_20x_review.png",
            "four_states_face_comparison.png",
        ] if before_states is not None else [],
    }
    report["angry_visual_blink"]["review_sha256"] = {
        name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        for name in report["angry_visual_blink"]["comparisons"]
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("Final Angry state checks:")
    for name, checks in final_states.items():
        print(f"  {name}: alpha={checks['alpha_identical']}, "
              f"outside declared regions={checks['outside_declared_edit_regions']}, "
              f"changed pixels={checks['changed_rgb_pixels']}")

    # Regenerate previews from the final state mapping.
    from animation_builder import save_gif
    save_gif(OUT / "blink.gif", [idle, blink_idle, idle, blink_idle, idle],
             [1050, 130, 1250, 130, 1050])
    save_gif(OUT / "talk.gif", [idle, talking, idle, talking, idle],
             [260, 220, 220, 250, 900])
    save_gif(OUT / "combined.gif",
             [idle, talking, idle, blink_idle, idle, talking, blink_talking, talking, idle],
             [450, 220, 300, 130, 430, 220, 130, 240, 1100])
    # The mouth contour is declared by the builder, not inferred from changed pixels.
    mouth = polygon_mask(source.shape[1::-1], [[
        (520,182),(523,178),(531,176),(543,176),(555,179),(562,183),(564,190),
        (562,197),(557,202),(549,205),(539,204),(530,202),(524,198),(521,191),
    ]])
    record_build(OUT, SOURCE, inputs=sorted((HERE/'assets').glob('*.png')),
                 scripts=[HERE/'build.py', Path(__file__), ROOT/'experiments/animation_builder.py',
                          ROOT/'experiments/artwork_tools.py'],
                 regions={'idle': mouth, 'talking': np.zeros_like(mouth),
                          'blink': eye_area | mouth, 'blink_talking': eye_area},
                 reviews=['left_eye_20x_review.png', 'right_eye_20x_review.png',
                          'four_states_face_comparison.png', 'angry_layer_stages.png'],
                 notes='Layered Angry reference; record final artifacts after all postprocessing.')


if __name__ == "__main__":
    apply_to_states()
