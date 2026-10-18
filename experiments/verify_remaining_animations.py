#!/usr/bin/env python3
"""Verify candidate or published records. Integrity never establishes visual approval."""
import argparse
import json
from pathlib import Path

from artwork_tools import ROOT, verify_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folders', type=Path, nargs='*', help='Candidate or published set folders')
    parser.add_argument('--check-inputs', action='store_true', help='Also require current builder/input hashes to match')
    args = parser.parse_args()
    folders = args.folders or sorted(path.parent for path in (ROOT/'static/animation').rglob('build.json'))
    if not folders:
        parser.error('No manifests found; build a candidate or supply an asset-set folder')
    failures = []
    for folder in folders:
        try:
            data = json.loads((folder/'build.json').read_text(encoding='utf-8'))
            report = verify_manifest(folder, data, check_inputs=args.check_inputs)
            review = data['visual_review'].get('status', 'unreviewed')
            approval = data['user_approval'].get('status', 'not_recorded')
            print(f'INTEGRITY PASS {folder}: containment={report["containment"]}; '
                  f'visual_review={review}; user_approval={approval}')
        except (OSError, ValueError, KeyError) as error:
            failures.append(f'{folder}: {error}')
    if failures:
        raise SystemExit('\n'.join(f'INTEGRITY FAIL {item}' for item in failures))
    print('Visual quality is assessed from the artwork; this command does not approve it.')


if __name__ == '__main__':
    main()
