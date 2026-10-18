# Experiment 17 — Strained-smile blink and speech

Adds four source-anchored animation states to `static/sprites/08_strained_smile.png`. The original toothy strained smile is reused for talking; an image-edited tight, closed-mouth variant supplies idle. The eye and mouth masks remain independent and avoid changing the character's tense expression, hair, alpha, or source pixels outside the features.

Run `python experiments/17_strained_smile_animation/build.py` from the repository root. Frames, GIFs, mask overlays, changed-boundary reviews, and QA are written to ignored `output/`.


Mask iteration: an earlier left-eye keep-out crossed the source upper lashes. It was removed, then Strained Smile's compressed upper-lash arcs and outer tips were traced separately per eye. The lower edge preserves under-eye skin, and the right outer hair strand stays source-identical. Reviewed source, donor, result, mask overlay, and changed boundary at 22×, plus all four states at face scale. Current eye-mask pixel counts: 1,210 image-left and 1,255 image-right; protected hair pixels are unchanged in all four states.
