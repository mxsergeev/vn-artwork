# Experiment 14 — Angry blink and speech

Adds four source-anchored animation states to `static/sprites/05_angry.png`. The original teeth-baring expression is reused for talking; a small image-edited closed-mouth donor supplies idle. The closed-eye donor is kept separate, and both feature masks preserve the angry brows, hair, and source alpha.

Run `python experiments/14_angry_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: an earlier left-eye keep-out crossed the source upper lashes. That strip was removed, then Angry's down-angled upper-lash arcs were traced separately. The right-eye contour now ends before the outer hair strand; a narrow dark-pixel trace retains the angry brow above the closed eye. Reviewed source, donor, result, mask overlay, and changed boundary at 22×, plus all four states at face scale. Current eye-mask pixel counts: 1,160 image-left and 1,128 image-right; protected hair pixels are unchanged in all four states.
