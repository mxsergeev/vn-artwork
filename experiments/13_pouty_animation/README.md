# Experiment 13 — Pouty blink and speech

Adds four source-anchored animation states to `static/sprites/04_pouty.png`. The original pout remains idle; image-edited closed-eye and open-mouth donors are cropped to the recorded source coordinates in `build.py` and transplanted through separate tight masks. Hair, brows, cheek shading, alpha, and all pixels outside those masks stay source-authoritative.

Run `python experiments/13_pouty_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: redrew the left lid contour around the eyelid, moved fringe and lower cheek pixels outside the mask, and kept the outer lash tip in its own small polygon. A tiny outer-corner patch removes the last source sclera pixel without reaching the brow. The eye mask fell from 1,420 to 1,239 pixels; inspect the generated 8x crop and changed-boundary overlay after rebuilding.