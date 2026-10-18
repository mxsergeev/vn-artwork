# Pouty animation

| Status record | Current information |
|---|---|
| Master | `static/sprites/04_pouty.png` |
| Usable donors | `assets/eyes_closed_patch.png` and `assets/mouth_variant_patch.png`; geometry in build.py. |
| Status | Existing default-pose set. |
| Current build | Ignored `output/build.json` after the command below; published identity is recorded alongside the static assets. |
| Visual review | See `static/animation/pouty/build.json`; inspect candidate PNGs and decoded GIFs before publication. |

## Local method

Original pout remains idle; closed eyes and speaking mouth are transplanted separately.

## Command

```sh
python experiments/13_pouty_animation/build.py
```

Writes the four standard PNG states, native GIFs, review images, declared regions, and a manifest to ignored `output/`. Historical output names remain available. Building does not publish.

Follow the shared [workflow](../../README.md) and [techniques](../../EDITING_TECHNIQUES.md).
