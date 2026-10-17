# Experiment 15 — Embarrassed blink and speech

Adds four source-anchored animation states to `static/sprites/06_embarrassed.png`. The original small open mouth is reused for talking; an image-edited closed-mouth donor supplies idle. The mask keeps the visible blush, raised brows, hair, cheek shading, and source alpha intact.

Run `python experiments/15_embarrassed_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: tightened the left lid contour to retain the fringe and under-eye skin, with a separate small outer-lash polygon. A tiny outer-corner patch removes the last source sclera pixel without reaching the brow. The eye mask fell from 1,433 to 1,304 pixels; inspect the generated 8x crop and changed-boundary overlay after rebuilding.