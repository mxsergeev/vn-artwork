# Published animation assets

Each expression folder contains four 1086×1448 RGBA states: `idle.png`, `blink.png`, `talking.png`, and `blink_talking.png`. The PNGs preserve the source sprite's alpha channel.

| Folder | State reused from the original sprite | GIF previews |
|---|---|---|
| `neutral/` | `idle.png` | `blink.gif`, `talk.gif` |
| `happy/` | `blink_talking.png` | `blink.gif`, `talk.gif`, `combined.gif` |
| `shocked/` | `idle.png` | `blink.gif`, `talk.gif`, `combined.gif` |

GIFs are preview files, flattened onto an opaque pale-gray background. GIF transparency cannot represent the sprites' antialiased alpha without edge artifacts. Use the PNG states when transparency is needed. Neutral's experiment does not produce a combined GIF, so none is included.

Build scripts write temporary frames, masks, GIFs, and QA files under the ignored experiment `output/` folders. These directories contain reproducible work products; this folder contains the reviewed, published copies.
