#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build

build({
    "experiment": "14_angry_animation",
    "slug": "angry",
    "source": "static/sprites/05_angry.png",
    "source_mouth_state": "open",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_polygons": [
        [(466,146),(467,141),(471,137),(479,136),(489,136),(498,138),(506,140),(512,143),(514,147),(511,151),(505,155),(496,156),(486,156),(477,153),(470,150)],
        [(538,138),(541,133),(547,129),(555,126),(564,127),(572,129),(579,132),(582,136),(580,141),(574,144),(565,146),(556,145),(548,142),(542,140)],
    ],
    "eye_protect": [[(501,116),(506,116),(512,137),(511,144),(506,143),(503,132)]],
    "mouth_polygon": [(520,182),(523,178),(531,176),(543,176),(555,179),(562,183),(564,190),(562,197),(557,202),(549,205),(539,204),(530,202),(524,198),(521,191)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 176, 570, 215],
    "notes": "The source's teeth-baring angry mouth is the talking state. The tight mouth donor supplies the closed-mouth idle.",
})
