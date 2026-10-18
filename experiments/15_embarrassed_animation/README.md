# Embarrassed animation

| Status record | Current information |
|---|---|
| Master | `static/sprites/06_embarrassed.png` |
| Usable donors | `assets/eyes_closed_patch.png` and `assets/mouth_variant_patch.png`; geometry in build.py. |
| Status | Existing default-pose set. |
| Current build | Ignored `output/build.json` after the command below; published identity is recorded alongside the static assets. |
| Visual review | See `static/animation/embarrassed/build.json`; inspect candidate PNGs and decoded GIFs before publication. |

## Local method

Original open mouth supplies talking. Preserve blush and brows while creating the closed-mouth idle state.

## Command

```sh
python experiments/15_embarrassed_animation/build.py
```

Writes the four standard PNG states, native GIFs, review images, declared regions, and a manifest to ignored `output/`. Historical output names remain available. Building does not publish.

Follow the [production manual](../../README.md).
