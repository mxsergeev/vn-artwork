# Experiment 14 — Angry blink and speech

Adds four source-anchored animation states to `static/sprites/05_angry.png`. The original teeth-baring expression is reused for talking; a small image-edited closed-mouth donor supplies idle. The closed-eye donor is kept separate, and both feature masks preserve the angry brows, hair, and source alpha.

Run `python experiments/14_angry_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: redrew the left lid around its visible lash and raised the right-eye upper contour below the angry brow. The central bang remains protected, and a separate tiny polygon retains the left outer lash tip. A tiny outer-corner patch removes the last source sclera pixel without reaching the brow. The eye mask fell from 1,367 to 913 pixels; inspect the generated 8x crop and changed-boundary overlay after rebuilding.