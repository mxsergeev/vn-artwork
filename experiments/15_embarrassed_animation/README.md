# Experiment 15 — Embarrassed blink and speech

Adds four source-anchored animation states to `static/sprites/06_embarrassed.png`. The original small open mouth is reused for talking; an image-edited closed-mouth donor supplies idle. The mask keeps the visible blush, raised brows, hair, cheek shading, and source alpha intact.

Run `python experiments/15_embarrassed_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: an earlier left-eye keep-out crossed the source upper lashes. It was removed, then Embarrassed's raised-eye upper-lash arcs and lifted outer tips were traced separately per eye. The raised brows, hair, blush, and cheek shading remain outside the masks. Reviewed source, donor, result, mask overlay, and changed boundary at 22×, plus all four states at face scale. Current eye-mask pixel counts: 1,212 image-left and 1,179 image-right; protected hair pixels are unchanged in all four states.
