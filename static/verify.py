#!/usr/bin/env python3
"""Regenerate archived static expressions in a temporary folder and compare RGBA pixels."""
from pathlib import Path
from tempfile import TemporaryDirectory
from subprocess import run
from shutil import copy2
from PIL import Image
import numpy as np

root=Path(__file__).resolve().parent
with TemporaryDirectory() as d:
    tmp=Path(d)
    for name in ('vn_expression_transplant.py', 'Melancholic Corporate Sci-Fi Officer.png', 'anime_character_expression_sheet_grid.png'):
        copy2(root/name, tmp/name)
    run(['python',str(tmp/'vn_expression_transplant.py')],cwd=tmp,check=True,capture_output=True,text=True)
    expected=sorted((root/'sprites').glob('*.png'))
    assert len(expected)==8, f'Expected 8 archived expression PNGs, found {len(expected)}'
    for original in expected:
        regenerated=tmp/'vn_expression_sprites'/original.name
        assert np.array_equal(np.asarray(Image.open(original).convert('RGBA')),
                              np.asarray(Image.open(regenerated).convert('RGBA'))), f'MISMATCH: {original.name}'
        print('PASS',original.name)
    base=root/'Melancholic Corporate Sci-Fi Officer.png'
    assert np.array_equal(np.asarray(Image.open(base).convert('RGBA')),
                          np.asarray(Image.open(tmp/'vn_expression_sprites/00_original_unchanged.png').convert('RGBA')))
    print('PASS original base')
print('All 9 files reproduced pixel-for-pixel.')
