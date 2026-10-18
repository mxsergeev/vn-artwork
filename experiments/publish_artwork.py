#!/usr/bin/env python3
"""Record review of an exact candidate, or explicitly publish its recorded files."""
import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path

from artwork_tools import (ROOT, STATES, GIFS, VISUAL_CRITERIA, digest, local_path,
                           verify_manifest, validate_visual_review, write_json)


def record_visual_review(data, reviewer, findings):
    if findings.get('artifact_set_sha256') != data['artifact_set_sha256']:
        raise ValueError('Review file belongs to different artifacts; regenerate the template and inspect this build')
    checks = findings.get('checks', {})
    statuses = {item.get('status') for item in checks.values()}
    verdict = 'failed' if 'fail' in statuses else 'uncertain' if 'uncertain' in statuses else 'passed'
    updated = copy.deepcopy(data)
    updated['visual_review'] = {'status': verdict, 'reviewer': reviewer,
                               'artifact_set_sha256': data['artifact_set_sha256'], 'checks': checks}
    validate_visual_review(updated)
    return updated


def publish(candidate, destination):
    candidate, destination = Path(candidate).resolve(), Path(destination).resolve()
    manifest = json.loads((candidate/'build.json').read_text(encoding='utf-8'))
    integrity = verify_manifest(candidate, manifest)
    review = manifest['visual_review']
    validate_visual_review(manifest, require_pass=True)
    if review.get('artifact_set_sha256') != manifest['artifact_set_sha256']:
        raise ValueError('Record visual review of these exact artifacts before publication')
    if manifest['user_approval'].get('status') == 'not_approved':
        raise ValueError('This artwork is explicitly NOT APPROVED')
    if set(manifest['states']) != set(STATES):
        raise ValueError('Publication requires all four named states')
    if any(name not in manifest['artifacts'] for name in GIFS):
        raise ValueError('Publication requires the three final GIF previews')
    if manifest['provenance'] != 'built' or integrity['containment'] != 'measured':
        raise ValueError('Build a candidate with declared edit regions before publication')
    if not destination.is_relative_to(ROOT/'static/animation') or destination == ROOT/'static/animation':
        raise ValueError('Destination must be a set inside static/animation/')
    if destination == candidate or destination.is_relative_to(candidate) or candidate.is_relative_to(destination):
        raise ValueError('Candidate and destination must be separate folders')
    # Keep large diagnostic panels in ignored candidate output. Preserve their
    # hashes and review binding in the publication record instead of copying them.
    candidate_record = {'build_id': manifest['build_id'], 'artifact_set_sha256': manifest['artifact_set_sha256'],
                         'artifacts': manifest['artifacts']}
    published = copy.deepcopy(manifest)
    names = set(manifest['deliverables']) | set(manifest['regions'].values())
    published['artifacts'] = {name: value for name, value in manifest['artifacts'].items() if name in names}
    published['candidate_record'] = candidate_record
    published['review_evidence'] = {name: manifest['artifacts'][name] for name in manifest['reviews']}
    published['reviews'] = []
    published['artifact_set_sha256'] = digest(published['artifacts'])
    published['build_id'] = digest({k: published[k] for k in ('source', 'inputs', 'scripts', 'artifacts', 'runtime')})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.publish-', dir=destination.parent) as temp:
        staging = Path(temp)
        for name in published['artifacts']:
            target = local_path(staging, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(local_path(candidate, name), target)
        write_json(staging/'build.json', published)
        verify_manifest(staging, published)
        destination.mkdir(parents=True, exist_ok=True)
        # Record is installed last; interrupted copies are detected as stale.
        for name in [*published['artifacts'], 'build.json']:
            target = local_path(destination, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            local_path(staging, name).replace(target)
    return published['build_id']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--reviewed-by', help='Record an actual visual review; does not publish')
    parser.add_argument('--review-file', type=Path, help='JSON with artifact_set_sha256 and six criterion findings')
    parser.add_argument('--review-template', type=Path, help='Write a blank review form for this exact candidate')
    approval = parser.add_mutually_exclusive_group()
    approval.add_argument('--approval-note', help='Record explicit user approval; quote or identify its evidence')
    approval.add_argument('--not-approved-note', help='Record rejection/unresolved artwork')
    args = parser.parse_args()
    folder = args.candidate.resolve()
    path = folder/'build.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    verify_manifest(folder, data)
    if args.review_template:
        if args.review_template.exists() or args.review_template.resolve() == path:
            parser.error('Review template destination must be a new file')
        if args.reviewed_by or args.review_file or args.destination or args.approval_note or args.not_approved_note:
            parser.error('--review-template is a separate operation')
        write_json(args.review_template, {'artifact_set_sha256': data['artifact_set_sha256'],
                   'checks': {name: {'status': 'uncertain', 'observation': '', 'evidence': []}
                              for name in VISUAL_CRITERIA}})
        print(f'Wrote blank visual review to {args.review_template}; inspect and complete all six criteria')
        return
    if bool(args.reviewed_by) != bool(args.review_file):
        parser.error('--reviewed-by and --review-file must be used together')
    if args.reviewed_by:
        data = record_visual_review(data, args.reviewed_by,
                                    json.loads(args.review_file.read_text(encoding='utf-8')))
    if args.approval_note or args.not_approved_note:
        data['user_approval'] = {'status': 'approved' if args.approval_note else 'not_approved',
                                 'note': args.approval_note or args.not_approved_note,
                                 'artwork_sha256': data['artwork_sha256']}
    if args.reviewed_by or args.approval_note or args.not_approved_note:
        write_json(path, data)
    if args.destination:
        print(f'Published build {publish(folder, args.destination)} to {args.destination}')
    else:
        print(f'Recorded build {data["build_id"]}; review={data["visual_review"]["status"]}; approval={data["user_approval"]["status"]}')


if __name__ == '__main__':
    main()
