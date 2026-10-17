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
        [(466,145),(468,140),(473,136),(482,136),(491,136),(500,138),(507,140),(511,144),(513,148),(510,152),(504,155),(495,157),(486,156),(477,153),(470,150)],
        [(538,139),(541,133),(547,129),(555,126),(564,126),(572,129),(579,133),(582,137),(580,141),(574,144),(565,146),(556,145),(548,143),(542,141)],
    ],
    "eye_protect": [[(501,116),(506,116),(512,137),(511,144),(506,143),(503,132)]],
    "mouth_polygon": [(520,190),(523,184),(529,181),(538,179),(548,180),(556,183),(561,188),(560,198),(556,205),(548,210),(539,210),(531,206),(525,202),(521,196)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 178, 570, 215],
    "notes": "The original downturned mouth remains idle; the image-edited donor opens it only slightly for subdued speech.",
})
