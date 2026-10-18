# Happy eye reference

| Status record | Current information |
|---|---|
| Master | `static/sprites/02_happy.png` |
| Usable donors | `../05_happy_animation/assets/ai_open_eyes_candidate.png` and `../09_happy_imagen_mouth/assets/closed_smile_patch.png`. |
| Status | Established Happy reference, using the mouth donor from 09. |
| Current build | Ignored `output/build.json` after the command below; published identity is recorded alongside the static assets. |
| Visual review | See `static/animation/happy/build.json`; inspect candidate PNGs and decoded GIFs before publication. |

## Local method

Independent eye contours, local tone matching, and a constrained outer-edge preservation rule. Source already supplies blink_talking.

## Command

```sh
python experiments/11_happy_eye_refined/build.py
```

Writes the four standard PNG states, native GIFs, review images, declared regions, and a manifest to ignored `output/`. Historical output names remain available. Building does not publish.

Follow the shared [workflow](../../README.md) and [techniques](../../EDITING_TECHNIQUES.md).
