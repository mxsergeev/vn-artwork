#!/usr/bin/env python3
from pathlib import Path
import numpy as np
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from animation_builder import build
from angry_visual_blink import apply_to_states

published = Path(__file__).resolve().parents[2] / "static/animation/angry"
before_states = {
    state: np.asarray(Image.open(published / f"{state}.png").convert("RGBA"))
    for state in ("idle", "blink", "talking", "blink_talking")
}

build({
    "experiment": "14_angry_animation",
    "slug": "angry",
    "source": "static/sprites/05_angry.png",
    "source_mouth_state": "open",
    "eye_box": [460, 116, 606, 166],
    "mouth_box": [505, 174, 582, 219],
    "eye_regions": {
        "viewer_left": {
            "clip_y": [136, None],
            "polygons": [
                [(470,152),(472,144),(477,140),(484,138),(492,137),(500,138),(507,141),(512,145),(518,150),(517,155),(511,158),(503,159),(495,159),(487,158),(479,156),(473,154)],
                [(464,149),(465,143),(469,140),(474,140),(478,144),(477,150),(472,154),(468,155),(464,152)],  # angled lash tip on this angry donor
                [(464,147),(466,141),(472,137),(480,134),(488,132),(496,132),(504,134),(511,138),(516,143),(518,149),(512,148),(505,145),(497,143),(489,143),(481,145),(474,148),(468,150)],  # angry upper lash, traced below the brow
            ],
            "protect": [
                [(500,116),(502,116),(502,124),(503,130),(503,135),(502,137),(500,134),(500,127)],
            ],
            "feather": 1.0,
        },
        "viewer_right": {
            "clip_y": [132, 152],
            "polygons": [
                [(539,151),(540,142),(543,137),(549,133),(556,130),(564,128),(572,128),(578,129),(582,131),(584,134),(584,138),(582,143),(579,148),(574,152),(566,155),(557,156),(549,155),(544,153)],
                [(579,138),(581,135),(583,134),(584,137),(583,141),(581,144),(579,143)],  # outer lash tip ends at the protected hair edge
                [(538,149),(539,141),(542,135),(548,131),(555,127),(563,125),(571,125),(579,126),(583,129),(584,133),(580,134),(573,132),(565,132),(557,134),(550,138),(545,143),(541,150)],  # angry upper lash, ending before the protected strand
            ],
            "protect": [
                [(584,125),(588,126),(590,133),(590,143),(589,152),(586,155),(583,151),(584,140)],
            ],
            "feather": 0.95,
        },
    },
    "eye_preserve_dark": [{
        "polygon": [(545,135),(551,131),(558,128),(566,125),(574,122),(582,119),(589,118),(591,120),(584,122),(576,125),(568,128),(560,131),(553,134),(547,136)],
        "max_channel": 125,
    }],
    "mouth_polygon": [(520,182),(523,178),(531,176),(543,176),(555,179),(562,183),(564,190),(562,197),(557,202),(549,205),(539,204),(530,202),(524,198),(521,191)],
    "eye_sample_region": [460, 118, 606, 166],
    "mouth_sample_region": [515, 176, 570, 215],
    "notes": "Angry keeps the original teeth-baring expression for talking. The final blink uses a source-matched closed-eye donor, eye-local skin replacement, and separately restored source brow and hair foreground. Visual review is required; static mask checks do not establish quality.",
}, print_report=False)
apply_to_states(before_states)
