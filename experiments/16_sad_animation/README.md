# Experiment 16 — Sad blink and speech

Adds four source-anchored animation states to `static/sprites/07_sad.png`. The original downturned mouth remains idle; an image-edited slightly open donor supplies talking. The eye contour avoids the lower tearful shading, and both feature masks preserve the brows, hair, alpha, and untouched source pixels.

Run `python experiments/16_sad_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: an earlier left-eye keep-out crossed the source upper lashes. It was removed, then Sad's drooped upper-lash arcs and outer tips were traced per eye, with the lower boundary held above tearful shading. Brows and the right outer hair strand stay source-identical. Reviewed source, donor, result, mask overlay, and changed boundary at 22×, plus all four states at face scale. Current eye-mask pixel counts: 1,240 image-left and 1,189 image-right; protected hair pixels are unchanged in all four states.
