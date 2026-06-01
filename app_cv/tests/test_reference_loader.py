import json
import os
import tempfile
import unittest

import cv2
import numpy as np

from tarotvision.image_io import imwrite_unicode
from tarotvision.reference_loader import load_active_reference_cards


class ReferenceLoaderTest(unittest.TestCase):
    def _write_card(self, path):
        img = np.zeros((120, 70), dtype=np.uint8)
        cv2.rectangle(img, (10, 10), (60, 110), 255, 2)
        cv2.line(img, (10, 10), (60, 110), 255, 1)
        self.assertTrue(imwrite_unicode(path, img))

    def test_loads_polish_deck_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cv_dir = os.path.join(tmpdir, "biblioteka_talii", "światło_i_cień", "produkcja", "wzorce_cv")
            os.makedirs(cv_dir)
            self._write_card(os.path.join(cv_dir, "Światło_i_Cień_00.jpg"))
            manifest = {
                "version": 1,
                "decks": [{
                    "id": "swiatlo_i_cien",
                    "display_name": "Światło i Cień",
                    "prefix": "Światło_i_Cień",
                    "cv_path": "biblioteka_talii/światło_i_cień/produkcja/wzorce_cv",
                }],
            }
            active = {"version": 1, "active_decks": ["swiatlo_i_cien"]}
            manifest_path = os.path.join(tmpdir, "decks_manifest.json")
            active_path = os.path.join(tmpdir, "active_decks.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f)
            with open(active_path, "w", encoding="utf-8") as f:
                json.dump(active, f)

            orb = cv2.ORB_create(nfeatures=500)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            result = load_active_reference_cards(
                project_root=tmpdir,
                manifest_path=manifest_path,
                active_decks_path=active_path,
                fallback_deck_id="swiatlo_i_cien",
                orb=orb,
                clahe=clahe,
            )

        self.assertIn("Światło_i_Cień_00", result.cards)
        self.assertEqual(result.loaded_deck_ids, ["swiatlo_i_cien"])
        self.assertEqual(result.skipped_files, [])

    def test_skips_unreadable_file_with_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cv_dir = os.path.join(tmpdir, "deck", "cv")
            os.makedirs(cv_dir)
            bad_path = os.path.join(cv_dir, "Bad_00.jpg")
            with open(bad_path, "wb") as f:
                f.write(b"not a jpeg")
            manifest_path = os.path.join(tmpdir, "manifest.json")
            active_path = os.path.join(tmpdir, "active.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump({"decks": [{"id": "bad", "display_name": "Bad", "prefix": "Bad", "cv_path": "deck/cv"}]}, f)
            with open(active_path, "w", encoding="utf-8") as f:
                json.dump({"active_decks": ["bad"]}, f)

            result = load_active_reference_cards(
                project_root=tmpdir,
                manifest_path=manifest_path,
                active_decks_path=active_path,
                fallback_deck_id="bad",
                orb=cv2.ORB_create(nfeatures=500),
                clahe=cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)),
            )

        self.assertEqual(result.cards, {})
        self.assertEqual(len(result.skipped_files), 1)
        self.assertTrue(result.skipped_files[0].endswith("Bad_00.jpg"))


if __name__ == "__main__":
    unittest.main()
