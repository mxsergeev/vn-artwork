# Neutral blink reference

| Status record | Current information |
|---|---|
| Master | `static/sprites/01_neutral_worried.png` |
| Usable donors | `../04_source_anchored_animation/assets/eyes_closed_donor.png` and `approved_talking.png`. |
| Status | Established Neutral reference. |
| Current build | Ignored `output/build.json` after the command below; published identity is recorded alongside the static assets. |
| Visual review | See `static/animation/neutral/build.json`; inspect candidate PNGs and decoded GIFs before publication. |
| User approval | Talking artifact was historically approved; no blanket approval inferred. |

## Local method

Retains the approved speaking frame, with separate eyelid contours and a targeted lash-tip extension.

## Command

```sh
python experiments/10_neutral_blink_refined/build.py
```

Writes the four standard PNG states, native GIFs, review images, declared regions, and a manifest to ignored `output/`. Historical output names remain available. Building does not publish.

Follow the shared [workflow](../../README.md) and [techniques](../../EDITING_TECHNIQUES.md).
