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

The separate `document_reading/` set is a pose-specific variant. Its source pose is `static/poses/document_reading/neutral.png`; each expression folder contains the same four PNG states plus native-size `blink.gif`, `talk.gif`, and `combined.gif` (1086×1448). `document_reading/all_three_native.gif` places neutral, happy, and shocked side by side at 3306×1448 with combined blink-and-talk timing. These files do not replace the default pose assets above.

Build scripts write temporary frames, masks, GIFs, and QA files under the ignored experiment `output/` folders. These directories contain reproducible work products; this folder contains the reviewed, published copies.

