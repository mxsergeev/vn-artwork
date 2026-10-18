# Angry — layered composition reference

| Status record | Current information |
|---|---|
| Master | `static/sprites/05_angry.png` |
| Usable donors | `assets/eyes_closed_angry_patch.png` for the selected blink; `mouth_variant_patch.png` for idle. The older eye crop remains an input to the legacy first pass. |
| Current build | `output/build.json` after building; current published identity is `static/animation/angry/build.json`. |
| Visual review | See `static/animation/angry/build.json`; inspect candidate PNGs and decoded GIFs before publication. |
| User approval | Recorded for the published result in `static/animation/angry/build.json`. |

## Local method

The generic pass supplies the original speaking source and closed-mouth idle. `angry_visual_blink.py` then uses the source-matched eye crop at `(460,112,606,176)`: eye-local skin replacement, donor lid insertion, and source brows/crossing hair restored last. The second eye starts from the first eye's repaired result.

Apply those eye changes to idle for `blink.png` and to talking for `blink_talking.png`. Generate final reviews and GIFs before writing the manifest. `output/angry_layer_stages.png` shows the working layers. Reusable compositing/restoration operations come from `artwork_tools.py`; the geometry and tone-selection rules remain local.

```sh
python experiments/14_angry_animation/build.py
```

Writes candidates and review files to ignored `output/`. Published frames supply the before/after comparison baseline; final states are built from the master and donors.

See the [workflow](../../README.md), [techniques](../../EDITING_TECHNIQUES.md), and explicit publication command there.
