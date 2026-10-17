#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "16_sad_animation",
    "slug": "sad",
    "source": "static/sprites/07_sad.png",
    "source_mouth_state": "closed",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_polygons": [
        [(470,150),(472,145),(478,141),(485,139),(493,139),(500,141),(506,144),(511,147),(513,151),(510,154),(503,156),(495,157),(487,156),(479,154),(473,152)],
        [(538,139),(541,133),(547,129),(555,126),(564,126),(572,129),(579,133),(582,137),(580,141),(574,144),(565,146),(556,145),(548,143),(542,141)],
        [(465,148),(470,145),(475,147),(474,152),(469,154),(465,152)],  # tiny, separate outer lash-tip continuation
        [(572,141),(575,137),(581,137),(584,141),(582,145),(578,147),(572,145)],  # tiny outer-corner patch removes source sclera below the brow
    ],
    "eye_protect": [[(501,116),(506,116),(512,137),(511,144),(506,143),(503,132)]],
    "mouth_polygon": [(520,190),(523,184),(529,181),(538,179),(548,180),(556,183),(561,188),(560,198),(556,205),(548,210),(539,210),(531,206),(525,202),(521,196)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 570, 215],
    "notes": "Redrew the left lid contour to preserve fringe and under-eye pixels; the outer lash-tip extension is separate. A tiny outer-corner patch removes the source sclera sliver without touching the brow. The original downturned mouth remains idle.",
})
