# Experiment 13 — Pouty blink and speech

Adds four source-anchored animation states to `static/sprites/04_pouty.png`. The original pout remains idle; image-edited closed-eye and open-mouth donors are cropped to the recorded source coordinates in `build.py` and transplanted through separate tight masks. Hair, brows, cheek shading, alpha, and all pixels outside those masks stay source-authoritative.

Run `python experiments/13_pouty_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: the earlier left-eye horizontal keep-out crossed the source upper lashes and left open-eye ink visible. It was removed, then Pouty's shallow upper-lash arcs and outer tips were traced separately for both eyes. The outer-right contour stops at its protected hair strand. Reviewed source, donor, result, mask overlay, and changed boundary at 22×, plus all four states at face scale. Current eye-mask pixel counts: 1,225 image-left and 1,174 image-right; protected hair pixels are unchanged in all four states.
