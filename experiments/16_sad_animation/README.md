# Sad animation

| Status record | Current information |
|---|---|
| Master | `static/sprites/07_sad.png` |
| Usable donors | `assets/eyes_closed_patch.png` and `assets/mouth_variant_patch.png`; geometry in build.py. |
| Status | Existing default-pose set. |
| Current build | Ignored `output/build.json` after the command below; published identity is recorded alongside the static assets. |
| Defects | No new defect assessment in this cleanup; read existing artwork before changing it. |
| Visual review | Prior README reports source/donor/result review at 22×; retained as historical evidence. |
| User approval | Not recorded for a new candidate. |
| Next action | Inspect the existing set before deciding whether any edit is necessary. |

## Local method

Original downturned mouth remains idle; eye contour retains intentional tearful shading.

## Command

```sh
python experiments/16_sad_animation/build.py
```

Writes the four standard PNG states, native GIFs, review images, declared regions, and a manifest to ignored `output/`. Historical output names remain available. Building does not publish.

Follow the shared [workflow](../../README.md) and [techniques](../../EDITING_TECHNIQUES.md). Previous iteration measurements belong to [history](../../HISTORY.md), not acceptance criteria.
