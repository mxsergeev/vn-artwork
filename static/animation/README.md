# Published animation assets

Each expression folder contains four 1086×1448 RGBA states: `idle.png`, `blink.png`, `talking.png`, and `blink_talking.png`. The PNGs preserve the source sprite's alpha channel. `preview.jpg` is a compact index of all eight idle expressions.

| Folder | State reused from the original sprite | GIF previews |
|---|---|---|
| `neutral/` | `idle.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `happy/` | `blink_talking.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `shocked/` | `idle.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `pouty/` | `idle.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `angry/` | `talking.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `embarrassed/` | `talking.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `sad/` | `idle.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `strained_smile/` | `talking.png` | `blink.gif`, `talk.gif`, `combined.gif` |

Each expression folder contains three full-resolution GIF previews (`blink.gif`, `talk.gif`, and `combined.gif`) at 1086×1448. `all_expressions.gif` shows all eight face animations together in a labeled 3×3 grid. GIFs are flattened onto an opaque pale-gray background because GIF transparency cannot represent the sprites' antialiased alpha without edge artifacts; use the PNG states when transparency is needed.

`python experiments/build_animation_previews.py` regenerates every published GIF from the four PNG states in these folders. Experiment scripts write temporary frames, masks, review GIFs, and QA files under the ignored experiment `output/` folders.

