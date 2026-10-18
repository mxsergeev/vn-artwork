"""Small compositing operations and artifact records. Geometry belongs to builders.

Masks passed to compositing functions are coverage in [0, 1], never 0/255.
Source-removal masks stay in source coordinates; only donor selections move.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.codex-python').is_dir():
    sys.path.insert(0, str(ROOT / '.codex-python'))

import cv2
import numpy as np
import PIL
from PIL import Image, ImageDraw

STATES = ('idle', 'blink', 'talking', 'blink_talking')
GIFS = ('blink.gif', 'talk.gif', 'combined.gif')
VISUAL_CRITERIA = ('geometry', 'source_removal', 'foreground', 'joins',
                   'expression_states', 'animation')


def validate_visual_review(data, *, require_pass=False):
    """Check review evidence and verdict consistency; cannot judge the pixels."""
    review = data.get('visual_review', {})
    if review.get('status') not in ('passed', 'failed', 'uncertain'):
        if require_pass:
            raise ValueError('Publication requires a structured visual review with a passing verdict')
        return
    checks = review.get('checks', {})
    if set(checks) != set(VISUAL_CRITERIA) or not str(review.get('reviewer', '')).strip():
        raise ValueError('Visual review requires a reviewer and all six criteria')
    evidence = {**data.get('artifacts', {}), **data.get('review_evidence', {})}
    for name, check in checks.items():
        if (check.get('status') not in ('pass', 'fail', 'uncertain')
                or not str(check.get('observation', '')).strip()
                or not isinstance(check.get('evidence'), list) or not check['evidence']):
            raise ValueError(f'{name}: provide pass/fail/uncertain, an observation, and artifact evidence')
        for item in check['evidence']:
            if not isinstance(item, str) or item not in evidence or Path(item).suffix.lower() not in ('.png', '.jpg', '.gif'):
                raise ValueError(f'{name}: evidence must name a recorded image: {item}')
            origin = data.get('candidate_record')
            if origin and origin.get('artifacts', {}).get(item) != evidence[item]:
                raise ValueError(f'{name}: published review evidence differs from the candidate')
    statuses = {check['status'] for check in checks.values()}
    expected = 'failed' if 'fail' in statuses else 'uncertain' if 'uncertain' in statuses else 'passed'
    if review['status'] != expected:
        raise ValueError('Visual verdict disagrees with its criterion results')
    if require_pass and expected != 'passed':
        raise ValueError('Visual review has failed or uncertain criteria; repair and review before publication')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def local_path(folder, name):
    path = (Path(folder) / name).resolve()
    if not path.is_relative_to(Path(folder).resolve()):
        raise ValueError(f'Path escapes artifact folder: {name}')
    return path


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def coverage(mask, shape):
    value = np.asarray(mask, dtype=np.float32)
    if value.shape != shape or not np.isfinite(value).all() or np.any((value < 0) | (value > 1)):
        raise ValueError('Coverage must match the canvas and lie in [0, 1]; convert 0/255 masks first')
    return value


def composite(canvas, donor, mask):
    """Blend RGB within explicit coverage, preserving canvas alpha exactly."""
    if canvas.shape != donor.shape or canvas.ndim != 3 or canvas.shape[2] != 4:
        raise ValueError('Composite expects two equally sized RGBA arrays')
    alpha = coverage(mask, canvas.shape[:2])[:, :, None]
    out = canvas.copy()
    out[:, :, :3] = np.rint(canvas[:, :, :3].astype(np.float32) * (1-alpha)
                            + donor[:, :, :3].astype(np.float32) * alpha).clip(0, 255).astype(np.uint8)
    return out


def restore_foreground(canvas, source, mask):
    """Restore identified source foreground last; do not select all dark pixels."""
    return composite(canvas, source, mask)


def repair_background(canvas, repair_image, removal):
    """Replace the complete old feature using an explicitly selected clean image."""
    return composite(canvas, repair_image, removal)


def align_feature(donor, selection, matrix, canvas_size):
    """Transform donor pixels and their selection together, returning valid support.

    Never pass a source-removal or source-foreground selection here.
    """
    transform = np.asarray(matrix, dtype=np.float32)
    if transform.shape != (2, 3) or not np.isfinite(transform).all():
        raise ValueError('Alignment requires a finite 2x3 affine matrix')
    mask = coverage(selection, donor.shape[:2])
    # Premultiply coverage to avoid black fringes at the edge of a crop.
    premultiplied = donor.astype(np.float32) * mask[:, :, None]
    warped_mask = cv2.warpAffine(mask, transform, tuple(canvas_size), flags=cv2.INTER_LINEAR)
    warped = cv2.warpAffine(premultiplied, transform, tuple(canvas_size), flags=cv2.INTER_LINEAR)
    valid = warped_mask > 0
    warped[valid] /= warped_mask[valid, None]
    return np.rint(warped).clip(0, 255).astype(np.uint8), warped_mask


def match_skin(source, donor, sample_mask, skin_mask, limit=12):
    """Estimate a median offset from caller-selected skin; change only that skin."""
    samples = coverage(sample_mask, source.shape[:2]) > 0
    selected = coverage(skin_mask, source.shape[:2]) > 0
    if source.shape != donor.shape or samples.sum() < 8:
        raise ValueError('Color matching requires matching canvases and at least eight skin samples')
    offset = np.median(source[:, :, :3][samples].astype(float) - donor[:, :, :3][samples], axis=0)
    offset = np.clip(offset, -limit, limit)
    out = donor.copy()
    out[selected, :3] = np.rint(donor[selected, :3].astype(float) + offset).clip(0, 255).astype(np.uint8)
    return out, offset.tolist()


def save_stage_review(path, stages, box, scale=8):
    """Save fixed-coordinate, nearest-neighbor crops with actual stage labels."""
    width, height = (box[2]-box[0])*scale, (box[3]-box[1])*scale
    board = Image.new('RGB', (width*len(stages), height+28), '#eeeeee')
    for index, (name, array) in enumerate(stages.items()):
        cut = Image.fromarray(array).crop(box).convert('RGBA')
        matte = Image.new('RGBA', cut.size, '#eeeeee')
        matte.alpha_composite(cut)
        board.paste(matte.convert('RGB').resize((width, height), Image.Resampling.NEAREST), (index*width, 28))
        ImageDraw.Draw(board).text((index*width+5, 6), name, fill='black')
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    board.save(path)


def region_effect(before, after, region):
    """Report whether an intended repair reached its target; never judge quality."""
    selected = coverage(region, before.shape[:2]) > 0
    changed = np.any(before[:, :, :3] != after[:, :, :3], axis=2)
    return {'target_pixels': int(selected.sum()), 'changed_target_pixels': int((selected & changed).sum()),
            'changed_outside_target': int((~selected & changed).sum())}


def compose_feature(source, donor, insertion, *, repair_image=None, removal=None,
                    foreground=None, cleanup=()):
    """Explicit layered path; no geometry or color heuristic is inferred here.

    cleanup is an ordered sequence of (repair_image, coverage) pairs, applied
    before foreground restoration. Returns final pixels, declared union, stages.
    """
    shape = source.shape[:2]
    allowed = coverage(insertion, shape) > 0
    stages = {'source': source.copy(), 'aligned donor': donor.copy()}
    canvas = source.copy()
    if removal is not None:
        if repair_image is None:
            raise ValueError('Source removal requires an explicit clean repair image')
        canvas = repair_background(canvas, repair_image, removal)
        allowed |= coverage(removal, shape) > 0
        stages['background repair'] = canvas.copy()
    canvas = composite(canvas, donor, insertion)
    stages['donor inserted'] = canvas.copy()
    for index, (image, mask) in enumerate(cleanup):
        canvas = repair_background(canvas, image, mask)
        allowed |= coverage(mask, shape) > 0
        stages[f'cleanup {index+1}'] = canvas.copy()
    if foreground is not None:
        canvas = restore_foreground(canvas, source, foreground)
        allowed |= coverage(foreground, shape) > 0
        stages['source foreground'] = canvas.copy()
    return canvas, allowed, stages


def file_records(paths):
    records = {}
    for item in sorted({Path(p).resolve() for p in paths}):
        records[item.relative_to(ROOT).as_posix()] = sha256(item)
    return records


def record_build(folder, source, *, inputs=(), scripts=(), regions=None,
                 reviews=(), extra_artifacts=(), notes='', provenance='built', states=None):
    """Record final artifacts only, after all postprocessing and GIF encoding.

    regions are independently declared boolean masks per state, never inferred
    from changed pixels. Missing historic regions stay explicitly unmeasured.
    """
    folder, source = Path(folder).resolve(), Path(source).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    state_files = states if states is not None else {s: f'{s}.png' for s in STATES}
    region_files = {}
    if regions is not None:
        for state, mask in regions.items():
            name = f'regions/{state}.png'
            path = local_path(folder, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.where(mask, 255, 0).astype(np.uint8)).save(path)
            region_files[state] = name
    names = list(state_files.values()) + list(region_files.values()) + list(reviews) + list(extra_artifacts)
    names += [name for name in GIFS if (folder / name).is_file()]
    artifacts = {name: sha256(local_path(folder, name)) for name in sorted(set(names))}
    deliverables = sorted(set(state_files.values()) | set(extra_artifacts)
                          | {name for name in GIFS if name in artifacts})
    artwork = {name: artifacts[name] for name in deliverables}
    manifest = {
        'schema_version': 1, 'provenance': provenance,
        'source': {'path': source.relative_to(ROOT).as_posix(), 'sha256': sha256(source)},
        'inputs': file_records([source, *inputs]), 'scripts': file_records(scripts),
        'runtime': {'python': platform.python_version(), 'pillow': PIL.__version__,
                    'numpy': np.__version__, 'opencv': cv2.__version__},
        'states': state_files, 'regions': region_files, 'reviews': list(reviews), 'deliverables': deliverables,
        'artifacts': artifacts, 'artifact_set_sha256': digest(artifacts),
        'artwork_sha256': digest(artwork), 'notes': notes,
    }
    manifest['build_id'] = digest({k: manifest[k] for k in ('source', 'inputs', 'scripts', 'artifacts', 'runtime')})
    manifest['visual_review'] = {'status': 'unreviewed'}
    manifest['user_approval'] = {'status': 'not_recorded'}
    old_path = folder / 'build.json'
    if old_path.exists():
        old = json.loads(old_path.read_text(encoding='utf-8'))
        if old.get('artifact_set_sha256') == manifest['artifact_set_sha256']:
            manifest['visual_review'] = old.get('visual_review', manifest['visual_review'])
        if old.get('artwork_sha256') == manifest['artwork_sha256']:
            manifest['user_approval'] = old.get('user_approval', manifest['user_approval'])
    manifest['integrity'] = verify_manifest(folder, manifest, check_inputs=False)
    write_json(old_path, manifest)
    return manifest


def verify_manifest(folder, manifest=None, *, check_inputs=True):
    """Recompute file integrity and containment, independently of visual status."""
    folder = Path(folder).resolve()
    data = manifest if manifest is not None else json.loads((folder/'build.json').read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported build manifest version')
    if digest(data['artifacts']) != data['artifact_set_sha256']:
        raise ValueError('Manifest artifact-set identity is inconsistent')
    identity = digest({k: data[k] for k in ('source', 'inputs', 'scripts', 'artifacts', 'runtime')})
    if identity != data['build_id']:
        raise ValueError('Manifest build identity is inconsistent')
    for name, expected in data['artifacts'].items():
        path = local_path(folder, name)
        if sha256(path) != expected:
            raise ValueError(f'Stale or modified artifact: {path}')
        if path.suffix.lower() in ('.png', '.jpg', '.gif'):
            with Image.open(path) as image:
                for index in range(getattr(image, 'n_frames', 1)):
                    image.seek(index)
                    image.load()
    source_path = local_path(ROOT, data['source']['path'])
    if sha256(source_path) != data['source']['sha256']:
        raise ValueError(f'Source identity changed: {source_path}')
    if check_inputs and data['provenance'] == 'built':
        for name, expected in {**data['inputs'], **data['scripts']}.items():
            if sha256(local_path(ROOT, name)) != expected:
                raise ValueError(f'Build input changed; rebuild candidate: {name}')
    source = np.asarray(Image.open(source_path).convert('RGBA'))
    for name in GIFS:
        if name in data['artifacts']:
            with Image.open(local_path(folder, name)) as gif:
                if gif.size != (source.shape[1], source.shape[0]) or gif.n_frames < 2:
                    raise ValueError(f'{name}: expected source-size animated GIF')
    checks = {}
    for state, name in data['states'].items():
        if name not in data['artifacts']:
            raise ValueError(f'Unhashed state: {name}')
        with Image.open(local_path(folder, name)) as im:
            if im.mode != 'RGBA' or im.size != (source.shape[1], source.shape[0]):
                raise ValueError(f'{name}: expected source-sized RGBA')
            array = np.asarray(im)
        if not np.array_equal(array[:, :, 3], source[:, :, 3]):
            raise ValueError(f'{name}: source alpha changed')
        region_name = data['regions'].get(state)
        outside = None
        if region_name:
            if region_name not in data['artifacts']:
                raise ValueError(f'Unhashed region: {region_name}')
            with Image.open(local_path(folder, region_name)) as im:
                allowed = np.asarray(im.convert('L')) > 0
            if allowed.shape != source.shape[:2]:
                raise ValueError(f'{region_name}: wrong dimensions')
            changed = np.any(array[:, :, :3] != source[:, :, :3], axis=2)
            outside = int((changed & ~allowed).sum())
            if outside:
                raise ValueError(f'{name}: {outside} edits outside declared regions')
        checks[state] = {'alpha_matches_source': True, 'outside_declared_regions': outside}
    for review in data['reviews']:
        if review not in data['artifacts']:
            raise ValueError(f'Unhashed review: {review}')
    artwork = {name: data['artifacts'][name] for name in data['deliverables']}
    if digest(artwork) != data['artwork_sha256']:
        raise ValueError('Manifest artwork identity is inconsistent')
    review = data.get('visual_review', {})
    if review.get('status') in ('reviewed', 'passed', 'failed', 'uncertain') and review.get('artifact_set_sha256') != data['artifact_set_sha256']:
        origin = data.get('candidate_record', {})
        if (review.get('artifact_set_sha256') != origin.get('artifact_set_sha256')
                or digest(origin.get('artifacts', {})) != origin.get('artifact_set_sha256')
                or any(origin['artifacts'].get(k) != v for k, v in data['artifacts'].items())):
            raise ValueError('Visual review belongs to different artifacts')
    validate_visual_review(data)
    approval = data.get('user_approval', {})
    if approval.get('status') in ('approved', 'not_approved') and approval.get('artwork_sha256') != data['artwork_sha256']:
        raise ValueError('User approval/rejection belongs to different artwork')
    return {'status': 'pass', 'states': checks,
            'containment': 'measured' if checks and all(s in data['regions'] for s in checks) else 'not_recorded',
            'visual_quality_certified': False}


def finish_animation(folder, source, frames, regions, *, inputs=(), scripts=(), reviews=(), notes=''):
    """Add standard state names, native GIFs, and traceability to a legacy builder."""
    folder = Path(folder)
    for name in STATES:
        Image.fromarray(frames[name]).save(folder / f'{name}.png')
    from build_animation_previews import render_state_gifs
    render_state_gifs(folder, folder)
    return record_build(folder, source, inputs=inputs, scripts=[*scripts, Path(__file__),
                        ROOT/'experiments/build_animation_previews.py'], regions=regions, reviews=reviews, notes=notes)
