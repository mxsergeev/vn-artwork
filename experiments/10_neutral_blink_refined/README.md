# Experiment 10 — refined Neutral blink

Refines experiment 04 with eyelid-following masks and a very small left-lash tip patch. The tip is limited to the eye/skin edge so it does not repaint adjacent hair. Original under-eye shading and the approved talking frame are preserved.

Reuses both original donor files from `experiments/04_source_anchored_animation/assets/`. No duplicate asset copies.

Run: `python experiments/10_neutral_blink_refined/build.py`. Generated sprites, GIFs, mask and changed-boundary comparisons, and QA appear in ignored `output/`. Inspect those visually; pixel confinement alone is not approval.



After the 16x review, the earlier 9-pixel-wide lash patch was reduced to a 5-pixel contour around the visible tip. The generated 16x crop confirms the adjacent hair and the full eyelid remain intact; the final changed-pixel and alpha checks are in `output/qa.json`.
