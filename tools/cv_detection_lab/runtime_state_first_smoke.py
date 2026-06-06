"""Offline smoke check for the state-first diff runtime detector."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import cv2

from tarotvision.background_model import BackgroundModel
from tarotvision.change_detection import ChangeDetector


DEFAULT_FIXTURE_ROOT = Path("logs/live_fixtures/event_first_current_debug_verified")

FRAME_SPECS = {
    "empty": ("empty", "analysis_frame_0.png"),
    "one_card": ("one_card", "analysis_frame_1.png"),
    "three_cards": ("three_cards", "analysis_frame_3.png"),
}

EXPECTED_PAIRS = [
    ("empty", "empty", 0),
    ("empty", "one_card", 1),
    ("empty", "three_cards", 3),
    ("one_card", "three_cards", 2),
    ("one_card", "empty", 1),
    ("three_cards", "empty", 3),
]

EXPECTED_ANALYSIS_ROI_COUNTS = {
    "empty->empty": 0,
    "empty->one_card": 1,
    "empty->three_cards": 2,
    "one_card->three_cards": 2,
    "one_card->empty": 0,
    "three_cards->empty": 0,
}


def run_smoke(fixture_root=DEFAULT_FIXTURE_ROOT):
    fixture_root = Path(fixture_root)
    frames = _load_frames(fixture_root)
    background = BackgroundModel()
    background.capture(frames["empty"])
    detector = ChangeDetector()

    pairs = []
    for previous_name, current_name, expected_count in EXPECTED_PAIRS:
        result = detector.detect(
            frames[previous_name],
            frames[current_name],
            empty_reference=background,
        )
        actual_count = len(result.regions)
        pair_name = f"{previous_name}->{current_name}"
        analysis_roi_count = len(_analysis_roi_hints(result.regions))
        expected_analysis_roi_count = EXPECTED_ANALYSIS_ROI_COUNTS[pair_name]
        raw_status = "PASS" if actual_count == expected_count and not result.global_shift else "FAIL"
        analysis_status = (
            "PASS"
            if analysis_roi_count == expected_analysis_roi_count and not result.global_shift
            else "FAIL"
        )
        pairs.append({
            "pair": pair_name,
            "expected_count": expected_count,
            "actual_count": actual_count,
            "status": analysis_status,
            "raw_region_status": raw_status,
            "expected_analysis_roi_count": expected_analysis_roi_count,
            "analysis_roi_count": analysis_roi_count,
            "global_shift": result.global_shift,
            "mask_nonzero_ratio": result.mask_nonzero_ratio,
            "regions": [
                {
                    "kind": region.kind,
                    "bbox": list(region.bbox),
                    "area_ratio": region.area_ratio,
                    "previous_empty_ratio": region.previous_empty_ratio,
                    "current_empty_ratio": region.current_empty_ratio,
                }
                for region in result.regions
            ],
        })

    status = "PASS" if all(item["status"] == "PASS" for item in pairs) else "FAIL"
    return {
        "status": status,
        "fixture_root": str(fixture_root),
        "pairs": pairs,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture-root", default=str(DEFAULT_FIXTURE_ROOT))
    parser.add_argument("--output", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    report = run_smoke(args.fixture_root)
    text = json.dumps(report, indent=2)
    print(text)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    if args.strict and report["status"] != "PASS":
        return 1
    return 0


def _load_frames(fixture_root):
    frames = {}
    for name, (directory, filename) in FRAME_SPECS.items():
        path = fixture_root / directory / filename
        frame = cv2.imread(str(path))
        if frame is None:
            raise FileNotFoundError(f"Missing or unreadable fixture frame: {path}")
        frames[name] = frame
    return frames


def _analysis_roi_hints(regions):
    added = [region.bbox for region in regions if region.kind == "added"]
    if added:
        return added
    return [region.bbox for region in regions if region.kind == "moved_or_replaced"]


if __name__ == "__main__":
    sys.exit(main())
