"""Behavioral checks for layered edits, stale builds, and publication boundaries."""
import json
import runpy
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artwork_tools as art
import publish_artwork as pub
import numpy as np
from PIL import Image


class ArtworkWorkflowTests(unittest.TestCase):
    def setUp(self):
        parent = art.ROOT/'experiments/.workflow_checks'
        parent.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.folder = self.root/'candidate'
        self.folder.mkdir()
        self.source = np.full((12, 12, 4), (220, 175, 150, 255), np.uint8)
        self.source[4, 4, :3] = 20
        self.source_path = self.root/'source.png'
        Image.fromarray(self.source).save(self.source_path)
        self.regions = {}
        for state in art.STATES:
            region = np.zeros((12, 12), bool)
            region[4:8, 4:8] = True
            self.regions[state] = region
            Image.fromarray(self.source).save(self.folder/f'{state}.png')
        Image.new('RGB', (20, 10), '#eee').save(self.folder/'review.png')
        for name in art.GIFS:
            a, b = Image.fromarray(self.source).convert('RGB'), Image.new('RGB', (12, 12), '#cccccc')
            a.save(self.folder/name, save_all=True, append_images=[b], duration=[100, 100], loop=0)
        self.driver = self.root/'driver.py'
        self.driver.write_text('# original build\n')

    def record(self):
        return art.record_build(self.folder, self.source_path, scripts=[self.driver],
                                regions=self.regions, reviews=['review.png'])

    def review(self, approval='not_recorded'):
        data = self.record()
        data['visual_review'] = {'status': 'reviewed', 'reviewer': 'test',
                                 'artifact_set_sha256': data['artifact_set_sha256']}
        data['user_approval'] = {'status': approval, 'artwork_sha256': data['artwork_sha256']}
        art.write_json(self.folder/'build.json', data)
        return data

    def test_removal_and_insertion_have_independent_footprints(self):
        source = self.source.copy()
        source[2, 4, :3] = 10  # Foreground hair above an old eye.
        clean = np.full_like(source, (220, 175, 150, 255))
        donor = clean.copy()
        donor[6, 4:7, :3] = 35
        removal = np.zeros((12, 12), np.float32)
        removal[2:7, 4:7] = 1
        insertion = np.zeros_like(removal)
        insertion[6, 4:7] = 1
        foreground = np.zeros_like(removal)
        foreground[2, 4] = 1
        final, allowed, stages = art.compose_feature(source, donor, insertion,
            repair_image=clean, removal=removal, foreground=foreground)
        self.assertTrue(np.array_equal(final[4, 4], clean[4, 4]))  # Old eye removed outside insertion.
        self.assertTrue(np.array_equal(final[2, 4], source[2, 4]))  # Hair restored last.
        self.assertTrue(np.array_equal(final[6, 5], donor[6, 5]))
        self.assertTrue(np.array_equal(final[:, :, 3], source[:, :, 3]))
        self.assertFalse(np.any(np.any(final != source, axis=2) & ~allowed))
        self.assertIn('background repair', stages)

    def test_fractional_alignment_preserves_color_at_crop_boundary(self):
        donor = np.full((4, 4, 4), (180, 100, 60, 255), np.uint8)
        aligned, mask = art.align_feature(donor, np.ones((4, 4)), [[1, 0, 0.5], [0, 1, 0.5]], (6, 6))
        self.assertTrue(np.all(aligned[mask > 0] == donor[0, 0]))
        with self.assertRaises(ValueError):
            art.composite(donor, donor, np.full((4, 4), 255))

    def test_layered_builder_reviews_the_actual_donor_and_cleanup(self):
        import animation_builder as shared
        config = {}
        with patch.object(shared, 'build', side_effect=lambda value: config.update(value)):
            runpy.run_path(str(art.ROOT/'experiments/13_pouty_animation/build.py'))
        assets = self.root/'assets'
        assets.mkdir()
        for name in ('eyes_closed_patch.png', 'mouth_variant_patch.png'):
            shutil.copyfile(art.ROOT/'experiments/13_pouty_animation/assets'/name, assets/name)
        source = np.asarray(Image.open(art.ROOT/config['source']).convert('RGBA'))
        donor = source.copy()
        donor[147, 490, :3] = (20, 60, 110)
        insertion = np.zeros(source.shape[:2], np.float32)
        insertion[147, 490] = 1
        removal = np.zeros_like(insertion)
        removal[147, 491] = 1
        clean = source.copy()
        clean[147, 491, :3] = (220, 175, 150)
        config.update(experiment=self.root.relative_to(art.ROOT/'experiments').as_posix(),
                      defer_manifest=True, eye_layers={'donor': donor, 'insertion': insertion,
                                                       'removal': removal, 'repair_image': clean})
        with patch.object(shared, 'save_gif'), patch.object(shared, 'save_png_atomic'), \
                patch.object(shared, 'save_stage_review'), patch.object(shared, 'review_images') as review:
            shared.build(config, print_report=False)
        args = review.call_args.args
        self.assertTrue(np.array_equal(args[6], donor))  # Actual aligned donor in final reviews.
        self.assertTrue(args[5][147, 491])  # Cleanup/removal coverage is visible too.
        self.assertTrue(np.array_equal(args[4]['blink'][147, 490, :3], (20, 60, 110)))
        self.assertTrue(np.array_equal(args[4]['blink'][147, 491, :3], (220, 175, 150)))

    def test_containment_is_recomputed_from_declared_region(self):
        self.record()
        changed = self.source.copy()
        changed[0, 0, 0] = 0
        Image.fromarray(changed).save(self.folder/'blink.png')
        with self.assertRaisesRegex(ValueError, 'outside declared regions'):
            self.record()

    def test_stale_output_or_builder_is_rejected(self):
        self.record()
        self.driver.write_text('# changed build\n')
        with self.assertRaisesRegex(ValueError, 'Build input changed'):
            art.verify_manifest(self.folder)
        self.driver.write_text('# original build\n')
        Image.new('RGB', (20, 10), 'red').save(self.folder/'review.png')
        with self.assertRaisesRegex(ValueError, 'Stale or modified artifact'):
            art.verify_manifest(self.folder)

    def test_approval_survives_unchanged_build_only(self):
        self.review('approved')
        same = self.record()
        self.assertEqual(same['user_approval']['status'], 'approved')
        changed = self.source.copy()
        changed[4, 4, :3] = 180
        Image.fromarray(changed).save(self.folder/'blink.png')
        new = self.record()
        self.assertEqual(new['user_approval']['status'], 'not_recorded')
        self.assertEqual(new['visual_review']['status'], 'unreviewed')

    def test_publication_requires_current_review_and_respects_rejection(self):
        self.record()
        destination = self.root/'static/animation/example'
        with patch.object(pub, 'ROOT', self.root):
            with self.assertRaisesRegex(ValueError, 'visual review'):
                pub.publish(self.folder, destination)
            self.review('not_approved')
            with self.assertRaisesRegex(ValueError, 'NOT APPROVED'):
                pub.publish(self.folder, destination)
        self.assertFalse(destination.exists())

    def test_publication_keeps_review_evidence_without_copying_panels(self):
        original = self.review('approved')
        destination = self.root/'static/animation/example'
        with patch.object(pub, 'ROOT', self.root):
            pub.publish(self.folder, destination)
        final = json.loads((destination/'build.json').read_text())
        self.assertEqual(final['candidate_record']['build_id'], original['build_id'])
        self.assertEqual(final['artwork_sha256'], original['artwork_sha256'])
        self.assertIn('review.png', final['review_evidence'])
        self.assertFalse((destination/'review.png').exists())
        art.verify_manifest(destination)


if __name__ == '__main__':
    unittest.main()
