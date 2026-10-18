#!/usr/bin/env python3
"""Reproduce two established edits and render the manual's instructional figures.

Writes only to the requested example folder and optional illustration folder.
Neither example publishes artwork or records visual approval.
"""
from __future__ import annotations

import argparse
import importlib.util
import contextlib
import io
import json
import runpy
import shutil
import tempfile
from pathlib import Path

import artwork_tools as art  # Also locates the repository's optional Python dependencies.
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = art.ROOT


def rgba(path):
    return np.asarray(Image.open(path).convert('RGBA'))


def board(path, panels, box, *, columns=2, scale=4):
    width, height = (box[2]-box[0])*scale, (box[3]-box[1])*scale
    canvas = Image.new('RGB', (width*columns, (height+28)*((len(panels)+columns-1)//columns)), '#eeeeee')
    draw = ImageDraw.Draw(canvas)
    for index, (label, pixels) in enumerate(panels.items()):
        cut = Image.fromarray(pixels).crop(box).convert('RGBA')
        matte = Image.new('RGBA', cut.size, '#eeeeee')
        matte.alpha_composite(cut)
        x, y = index % columns * width, index // columns * (height+28)
        canvas.paste(matte.convert('RGB').resize((width, height), Image.Resampling.NEAREST), (x, y+28))
        draw.text((x+5, y+7), label, fill='black')
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)


def static_expression(output, illustrations):
    """Exact historic Happy transplant: recorded registration, broad patch, palette."""
    source = rgba(ROOT/'static/Melancholic Corporate Sci-Fi Officer.png')
    sheet = np.asarray(Image.open(ROOT/'static/anime_character_expression_sheet_grid.png').convert('RGB'))
    panel = sheet[:561, 350:700]  # Happy is the second portrait in the first row.
    height, width = source.shape[:2]
    matrix = np.array([[.6674, -.02563, 418.8], [.02563, .6674, -7.6]], np.float32)
    polygon = np.array([(144,147),(184,139),(233,143),(260,158),(272,182),
                        (276,225),(260,270),(242,294),(217,312),(184,314),
                        (153,297),(128,283),(105,265),(92,244),(86,218),
                        (83,187),(104,160)], np.int32)
    selection = np.zeros((561,350), np.uint8)
    cv2.fillPoly(selection, [polygon], 255)
    selection = cv2.GaussianBlur(selection, (0,0), 5)
    coverage = cv2.warpAffine(selection, matrix, (width,height), flags=cv2.INTER_LINEAR).astype(np.float32)/255
    aligned = cv2.warpAffine(panel, matrix, (width,height), flags=cv2.INTER_CUBIC)
    # These correspondences sample the neutral portrait and original source.
    samples = [(140,257),(162,277),(237,277),(182,310),(210,265),
               (178,181),(208,162),(153,245),(239,234),(206,272)]
    deltas = []
    for x,y in samples:
        dx,dy = np.round(matrix @ np.array([x,y,1])).astype(int)
        deltas.append(source[dy,dx,:3].astype(np.float32)-sheet[y,x,:3].astype(np.float32))
    offset = np.median(deltas, axis=0)
    matched = np.clip(aligned.astype(np.float32)+offset, 0,255)
    final = source.copy()
    # Preserve historical truncation, interpolation and palette arithmetic exactly.
    final[:,:,:3] = np.clip(source[:,:,:3].astype(np.float32)*(1-coverage[:,:,None])+
                            matched*coverage[:,:,None], 0,255).astype(np.uint8)
    with tempfile.TemporaryDirectory(dir=output.resolve()) as temp:
        temporary = Path(temp)
        for name in ('vn_expression_transplant.py', 'Melancholic Corporate Sci-Fi Officer.png',
                     'anime_character_expression_sheet_grid.png'):
            shutil.copy2(ROOT/'static'/name, temporary/name)
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(temporary/'vn_expression_transplant.py'))
        expected = rgba(temporary/'vn_expression_sprites/02_happy.png')
    if not np.array_equal(final, expected):
        raise AssertionError('Static example differs from the historical builder on this runtime')
    Image.fromarray(final).save(output/'static_happy.png')
    donor = source.copy(); donor[:,:,:3] = np.clip(aligned,0,255).astype(np.uint8)
    overlay = source.copy()
    active = coverage > .5
    overlay[active,:3] = np.rint(overlay[active,:3]*.5 + np.array([40,220,90])*.5).astype(np.uint8)
    board(output/'static_stages.png', {'Master':source, 'Aligned donor':donor,
          'Broad face selection (green)':overlay, 'Reproduced Happy':final}, (450,80,620,240), scale=3)
    if illustrations:
        Image.open(output/'static_stages.png').save(illustrations/'static_alignment.png')
    published = rgba(ROOT/'static/sprites/02_happy.png')
    return {'matches_historical_builder': True,
            'published_different_pixels': int(np.any(final!=published,axis=2).sum()),
            'published_max_channel_difference': int(np.abs(final.astype(int)-published.astype(int)).max()),
            'recorded_affine': matrix.tolist(),
            'skin_rgb_offset': offset.tolist()}


def layered_blink(output, illustrations):
    """Run the actual Angry compositor, capturing its actual intermediate stages."""
    path = ROOT/'experiments/14_angry_animation/angry_visual_blink.py'
    spec = importlib.util.spec_from_file_location('angry_worked_example', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = output
    captured = {}
    original_save = module.save_stage_review
    def capture(path, stages, box, scale):
        captured.update(stages)
        original_save(path, stages, box, scale)
    def capture_foreground(canvas, source, mask):
        captured.setdefault('before foreground', canvas.copy())
        return art.restore_foreground(canvas, source, mask)
    module.save_stage_review = capture
    module.restore_foreground = capture_foreground
    final = module.make_closed_blink()
    expected = rgba(ROOT/'static/animation/angry/blink_talking.png')
    if not np.array_equal(final, expected):
        raise AssertionError('Layered example differs from the established Angry blink_talking')
    Image.fromarray(final).save(output/'angry_blink.png')
    board(output/'layered_stages.png', {'Master: open eyes':captured['source'],
          'Donor skin and lids':captured['skin repaired'],
          'Lids inserted, before foreground':captured['before foreground'],
          'Final: source foreground restored':final}, (468,120,596,168))
    # Controlled failure examples derived from the established images, not failed experiments.
    source = captured['source']
    removal = module.polygon_mask(source.shape[1::-1], module.LEFT_REGION+module.RIGHT_REGION)
    ghosts = art.composite(final, source, removal.astype(np.float32)*.65)
    shifted_donor, shifted_mask = art.align_feature(final, removal.astype(np.float32),
                                                   [[1,0,6],[0,1,3]], source.shape[1::-1])
    misplaced = art.composite(source, shifted_donor, shifted_mask)
    board(output/'reject_examples.png', {'Reject: original eyes ghost through':ghosts,
          'Reject: lids shifted, old lines survive':misplaced,
          'Reference: one closed lid per eye':final,
          'Source: original open eyes':source}, (468,120,596,168))
    # Explicit selections, overlaid on the source, show that removal exceeds the lids.
    views = {}
    for name, polygons, color in (
            ('Removal / skin replacement', module.LEFT_REGION+module.RIGHT_REGION, [30,210,90]),
            ('Donor lid insertion', module.LID_POLYGONS, [255,130,30]),
            ('Source hair: foreground', module.HAIR_POLYGONS, [50,150,250]),
            ('Source brows: foreground', module.BROW_POLYGONS, [220,60,200])):
        mask = module.polygon_mask(source.shape[1::-1], polygons)
        view = source.copy()
        view[mask,:3] = np.rint(view[mask,:3]*.4+np.array(color)*.6).astype(np.uint8)
        views[name] = view
    board(output/'selection_roles.png', views, (468,120,596,168))
    if illustrations:
        for src,dst in [('layered_stages.png','layered_eye.png'), ('reject_examples.png','reject_examples.png'),
                        ('selection_roles.png','selection_roles.png')]:
            Image.open(output/src).save(illustrations/dst)
    return {'matches_established_blink_talking': True,
            'alpha_matches_source': bool(np.array_equal(final[:,:,3],source[:,:,3]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'experiments/.workflow_checks/examples')
    parser.add_argument('--illustrations', type=Path, help='Also write the four selected manual illustrations')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.illustrations:
        args.illustrations.mkdir(parents=True, exist_ok=True)
    report = {'static':static_expression(args.output,args.illustrations),
              'layered':layered_blink(args.output,args.illustrations)}
    (args.output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
