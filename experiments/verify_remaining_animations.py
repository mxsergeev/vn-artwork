#!/usr/bin/env python3
"""Verify the published experiment 13–17 PNG and GIF copies."""
from pathlib import Path
import json

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EXPRESSIONS = {
    "pouty": ("13_pouty_animation", "04_pouty"),
    "angry": ("14_angry_animation", "05_angry"),
    "embarrassed": ("15_embarrassed_animation", "06_embarrassed"),
    "sad": ("16_sad_animation", "07_sad"),
    "strained_smile": ("17_strained_smile_animation", "08_strained_smile"),
}
STATES = ("idle", "blink", "talking", "blink_talking")
GIFS = {"blink.gif": 5, "talk.gif": 5, "combined.gif": 9}
ALL_EXPRESSIONS = (
    "neutral", "happy", "shocked", "pouty", "angry", "embarrassed", "sad", "strained_smile"
)

# Check every published state, including the original Neutral/Happy/Shocked builds.
for slug in ALL_EXPRESSIONS:
    folder = ROOT / "static/animation" / slug
    reference_alpha = None
    for state in STATES:
        with Image.open(folder / f"{state}.png") as image:
            image.load()
            assert image.size == (1086, 1448) and image.mode == "RGBA", f"{slug}/{state}: bad PNG"
            alpha = np.asarray(image)[:, :, 3]
            if reference_alpha is None:
                reference_alpha = alpha.copy()
            else:
                assert np.array_equal(alpha, reference_alpha), f"{slug}/{state}: alpha differs from idle"
print("PASS all eight expressions: four full-size RGBA states with identical per-expression alpha")

for slug, (experiment, source_name) in EXPRESSIONS.items():
    source = np.asarray(Image.open(ROOT / "static/sprites" / f"{source_name}.png").convert("RGBA"))
    published = ROOT / "static/animation" / slug
    out = ROOT / "experiments" / experiment / "output"
    report = json.loads((out / "QA.json").read_text(encoding="utf-8"))
    assert report["source_alpha_preserved_for_all_states"] is True
    assert all(v["outside_feature_mask_pixels"] == 0 for v in report["states"].values())
    for state in STATES:
        src = out / f"{state}.png"
        dst = published / f"{state}.png"
        with Image.open(src) as image:
            image.load()
            assert image.size == (1086, 1448) and image.mode == "RGBA"
            source_state = np.asarray(image)
        with Image.open(dst) as image:
            image.load()
            assert image.size == (1086, 1448) and image.mode == "RGBA"
            final_state = np.asarray(image)
        assert np.array_equal(final_state, source_state), f"{slug}/{state}: published copy differs from build output"
        assert np.array_equal(final_state[:, :, 3], source[:, :, 3]), f"{slug}/{state}: source alpha changed"
    for filename, expected_frames in GIFS.items():
        with Image.open(published / filename) as gif:
            assert gif.size == (1086, 1448), f"{slug}/{filename}: unexpected size {gif.size}"
            assert gif.n_frames == expected_frames, f"{slug}/{filename}: unexpected frame count {gif.n_frames}"
            for frame_no in range(gif.n_frames):
                gif.seek(frame_no)
                gif.convert("RGB")
    print(f"PASS {slug}: 4 exact PNG copies, source alpha, 3 readable GIFs")

preview = ROOT / "static/animation/preview.jpg"
with Image.open(preview) as image:
    assert image.format == "JPEG" and image.size == (1280, 690)
print("PASS eight-expression index preview")

for slug in ("neutral", "happy", "shocked"):
    folder = ROOT / "static/animation" / slug
    for filename, expected_frames in GIFS.items():
        with Image.open(folder / filename) as gif:
            assert gif.size == (1086, 1448), f"{slug}/{filename}: unexpected size {gif.size}"
            assert gif.n_frames == expected_frames, f"{slug}/{filename}: unexpected frame count {gif.n_frames}"
            for frame_no in range(gif.n_frames):
                gif.seek(frame_no)
                gif.convert("RGB")
    print(f"PASS {slug}: 3 native-resolution GIFs")

all_expressions = ROOT / "static/animation/all_expressions.gif"
with Image.open(all_expressions) as gif:
    assert gif.size == (1284, 1416), f"all_expressions.gif: unexpected size {gif.size}"
    assert gif.n_frames == 8, f"all_expressions.gif: unexpected frame count {gif.n_frames}"
    for frame_no in range(gif.n_frames):
        gif.seek(frame_no)
        gif.convert("RGB")
print("PASS all-expression montage GIF")
