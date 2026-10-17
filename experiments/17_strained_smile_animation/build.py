#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "17_strained_smile_animation",
    "slug": "strained_smile",
    "source": "static/sprites/08_strained_smile.png",
    "source_mouth_state": "open",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_polygons": [
        [(470,151),(472,146),(478,142),(485,140),(493,140),(500,142),(506,145),(511,148),(513,152),(509,155),(502,157),(494,158),(486,157),(478,155),(473,153)],
        [(538,139),(541,133),(547,129),(555,126),(564,126),(572,129),(579,133),(582,137),(580,141),(574,144),(565,146),(556,145),(548,143),(542,141)],
        [(465,149),(470,146),(474,148),(474,153),(469,155),(465,153)],  # tiny, separate outer lash-tip continuation
        [(572,142),(575,138),(581,138),(584,142),(582,146),(578,147),(572,145)],  # tiny outer-corner patch removes source sclera below the brow
    ],
    "eye_protect": [[(501,116),(506,116),(512,137),(511,144),(506,143),(503,132)]],
    "mouth_polygon": [(507,188),(509,182),(515,179),(527,176),(542,176),(558,179),(570,183),(575,188),(573,195),(568,201),(559,205),(547,208),(535,208),(524,205),(515,202),(509,197)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [510, 176, 580, 215],
    "notes": "Redrew the left lid contour to preserve fringe and under-eye pixels; the outer lash-tip extension is separate. A tiny outer-corner patch removes the source sclera sliver without touching the brow. The toothy smile remains the talking state.",
})
