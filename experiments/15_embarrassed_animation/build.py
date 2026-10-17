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
        [(466,146),(468,140),(473,136),(482,136),(491,136),(500,138),(507,140),(511,144),(513,148),(510,152),(504,156),(495,158),(485,157),(476,154),(470,151)],
        [(538,139),(541,133),(547,129),(555,126),(564,126),(572,129),(579,133),(582,137),(580,141),(574,144),(565,146),(556,145),(548,143),(542,141)],
    ],
    "eye_protect": [[(501,116),(506,116),(512,137),(511,144),(506,143),(503,132)]],
    "mouth_polygon": [(523,188),(526,183),(532,181),(541,180),(551,181),(560,184),(564,188),(563,196),(560,201),(552,204),(541,203),(531,201),(526,197),(524,192)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 570, 215],
    "notes": "The source's small open embarrassed mouth is reused for talking; the donor closes only its inner-mouth opening for idle.",
})
