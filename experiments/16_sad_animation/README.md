# Experiment 16 — Sad blink and speech

Adds four source-anchored animation states to `static/sprites/07_sad.png`. The original downturned mouth remains idle; an image-edited slightly open donor supplies talking. The eye contour avoids the lower tearful shading, and both feature masks preserve the brows, hair, alpha, and untouched source pixels.

Run `python experiments/16_sad_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: redrew the left lid contour to keep the fringe and cheek outside the blink mask, with a separate small outer-lash polygon. A tiny outer-corner patch removes the last source sclera pixel without reaching the brow. The eye mask fell from 1,388 to 1,306 pixels; inspect the generated 8x crop and changed-boundary overlay after rebuilding.