# Shocked reference

| Status record | Current information |
|---|---|
| Master | `static/sprites/03_shocked.png` |
| Usable donors | `assets/eyes_closed_patch.png` and `assets/open_mouth_patch.png`; crop coordinates in build.py. |
| Status | Established Shocked reference. |
| Current build | Ignored `output/build.json` after the command below; published identity is recorded alongside the static assets. |
| Defects | No new defect assessment in this cleanup; read existing artwork before changing it. |
| Visual review | Historically reviewed; no fresh artwork acceptance performed in this cleanup. |
| User approval | Not recorded for a new candidate. |
| Next action | Build a candidate when needed and inspect its eye/mouth transitions. |

## Local method

Separate eye and mouth transplantation; original source is idle.

## Command

```sh
python experiments/12_shocked_animation/build.py
```

Writes the four standard PNG states, native GIFs, review images, declared regions, and a manifest to ignored `output/`. Historical output names remain available. Building does not publish.

Follow the shared [workflow](../../README.md) and [techniques](../../EDITING_TECHNIQUES.md). Previous iteration measurements belong to [history](../../HISTORY.md), not acceptance criteria.
