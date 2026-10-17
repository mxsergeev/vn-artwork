#!/usr/bin/env python3
"""Regenerate experiments 13–17 from their committed source-anchored donor crops."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENTS = [
    "13_pouty_animation",
    "14_angry_animation",
    "15_embarrassed_animation",
    "16_sad_animation",
    "17_strained_smile_animation",
]

for name in EXPERIMENTS:
    print(f"== {name} ==", flush=True)
    subprocess.run([sys.executable, str(ROOT / "experiments" / name / "build.py")],
                   cwd=ROOT, check=True)
