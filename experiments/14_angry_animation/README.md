# Angry — layered composition reference

| Status record | Current information |
|---|---|
| Master | `static/sprites/05_angry.png` |
| Usable donors | `assets/eyes_closed_angry_patch.png` for the selected blink; `mouth_variant_patch.png` for idle. The older eye crop remains an input to the legacy first pass. |
| Current build | `output/build.json` after building; current published identity is `static/animation/angry/build.json`. |
| Defects | Earlier mouth-state swap, lost first-eye repair, and stale review ordering were corrected in 0d5e99d. |
| Visual review | Source / previous / corrected result were compared at face scale and enlarged feature scale. |
| User approval | User accepted the corrected result on 2026-10-18: “Yeah, this looks better. Commit only THESE changes and push.” Approval applies to that result. |
| Next action | Use its layer separation as a reference; rebuild only when a candidate is needed. |

## Local method

The generic pass supplies the original speaking source and closed-mouth idle. `angry_visual_blink.py` then uses the source-matched eye crop at `(460,112,606,176)`: eye-local skin replacement, donor lid insertion, and source brows/crossing hair restored last. The second eye starts from the first eye's repaired result.

Apply those eye changes to idle for `blink.png` and to talking for `blink_talking.png`. Generate final reviews and GIFs before writing the manifest. `output/angry_layer_stages.png` shows the working layers. Reusable compositing/restoration operations come from `artwork_tools.py`; the geometry and tone-selection rules remain local.

```sh
python experiments/14_angry_animation/build.py
```

Writes candidates and review files to ignored `output/`. Historical before/after comparisons use current published frames only as a comparison baseline; they are not build inputs for the final states.

See the [workflow](../../README.md), [techniques](../../EDITING_TECHNIQUES.md), and explicit publication command there.
