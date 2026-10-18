# Happy mouth reference

| Status record | Current information |
|---|---|
| Master | `static/sprites/02_happy.png` |
| Usable donors | Existing open-eye donor from experiment 05 and `assets/closed_smile_patch.png`. |
| Status | Reference for the closed-smile donor; experiment 11 supersedes its eye treatment. |
| Current build | Ignored `output/build.json` after the command below; published identity is recorded alongside the static assets. |
| Visual review | See `static/animation/happy/build.json`; inspect candidate PNGs and decoded GIFs before publication. |

## Local method

The generated closed smile replaces the earlier compressed mouth. The original closed eyes/open smile remain blink_talking.

## Command

```sh
python experiments/09_happy_imagen_mouth/build.py
```

Writes the four standard PNG states, native GIFs, review images, declared regions, and a manifest to ignored `output/`. Historical output names remain available. Building does not publish.

Follow the [production manual](../../README.md).
