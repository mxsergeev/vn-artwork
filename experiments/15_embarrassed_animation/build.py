#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "15_embarrassed_animation",
    "slug": "embarrassed",
    "source": "static/sprites/06_embarrassed.png",
    "source_mouth_state": "open",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_polygons": [
        [(470,151),(472,146),(477,142),(484,140),(492,140),(500,142),(506,145),(511,148),(512,152),(508,155),(501,157),(493,158),(485,157),(478,155),(473,153)],
        [(538,139),(541,133),(547,129),(555,126),(564,126),(572,129),(579,133),(582,137),(580,141),(574,144),(565,146),(556,145),(548,143),(542,141)],
        [(465,149),(470,146),(474,148),(474,153),(469,155),(465,153)],  # tiny, separate outer lash-tip continuation
        [(572,142),(575,138),(581,138),(584,142),(582,146),(578,147),(572,145)],  # tiny outer-corner patch removes source sclera below the brow
    ],
    "eye_protect": [[(501,116),(506,116),(512,137),(511,144),(506,143),(503,132)]],
    "mouth_polygon": [(523,188),(526,183),(532,181),(541,180),(551,181),(560,184),(564,188),(563,196),(560,201),(552,204),(541,203),(531,201),(526,197),(524,192)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 570, 215],
    "notes": "Redrew the left lid contour to preserve fringe and under-eye pixels; the outer lash-tip extension is separate. A tiny outer-corner patch removes the source sclera sliver without touching the brow. The source's small open mouth is reused for talking.",
})
