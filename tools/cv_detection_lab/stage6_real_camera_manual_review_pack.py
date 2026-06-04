"""Manual review pack generator for validated Stage 6 real-camera aggregates."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
import shutil

import cv2
import numpy as np

from tools.cv_detection_lab.stage6_real_camera_fixture import load_aggregate, scenario_required_files, session_fingerprint


def build_manual_review_pack(manifest_path, ground_truth_path, preflight_path, output_dir):
    with open(preflight_path, "r", encoding="utf-8") as handle:
        preflight = json.load(handle)
    if preflight.get("status") != "PASS":
        raise ValueError("Manual review pack requires PASS preflight.")
    aggregate = load_aggregate(manifest_path, ground_truth_path)
    before = {sample.session_id: session_fingerprint(sample.resolved_session_path) for sample in aggregate.samples}
    os.makedirs(os.path.join(output_dir, "samples"), exist_ok=True)
    shutil.copy2(manifest_path, os.path.join(output_dir, "manifest.json"))
    shutil.copy2(ground_truth_path, os.path.join(output_dir, "ground_truth.json"))
    shutil.copy2(preflight_path, os.path.join(output_dir, "preflight_report.json"))

    categories = defaultdict(list)
    similarities = defaultdict(list)
    for sample in aggregate.samples:
        label = aggregate.labels[sample.sample_id]
        _write_debug_sheet(sample, label, os.path.join(output_dir, "samples", f"{sample.sample_id}.png"))
        categories[sample.category].append(sample.sample_id)
        if sample.similarity_group:
            similarities[sample.similarity_group].append(sample.sample_id)
    _write_json(os.path.join(output_dir, "category_index.json"), categories)
    _write_json(os.path.join(output_dir, "similarity_groups.json"), similarities)
    _write_readme(output_dir, len(aggregate.samples))
    after = {sample.session_id: session_fingerprint(sample.resolved_session_path) for sample in aggregate.samples}
    if before != after:
        raise RuntimeError("Session content changed while generating manual review pack.")
    return {"sample_count": len(aggregate.samples), "category_count": len(categories)}


def _write_debug_sheet(sample, label, path):
    scenario_dir = os.path.join(sample.resolved_session_path, sample.scenario)
    analysis_name = next(name for name in scenario_required_files(sample.scenario) if name.startswith("analysis_frame_"))
    analysis_path = os.path.join(scenario_dir, analysis_name)
    if not hasattr(cv2, "imread") or not hasattr(np, "zeros"):
        shutil.copy2(analysis_path, path)
        metadata_dir = os.path.join(os.path.dirname(os.path.dirname(path)), "sample_metadata")
        os.makedirs(metadata_dir, exist_ok=True)
        _write_text_sheet(sample, label, os.path.join(metadata_dir, f"{sample.sample_id}.txt"))
        return
    image = cv2.imread(analysis_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Cannot read analysis frame for {sample.sample_id}")
    resized = cv2.resize(image, (480, 320), interpolation=cv2.INTER_AREA)
    panel = np.zeros((520, 900, 3), dtype=np.uint8)
    panel[:320, :480] = resized
    lines = [
        f"sample_id: {sample.sample_id}",
        f"session: {sample.session_id}",
        f"category: {sample.category}",
        f"expected: {label.get('expected_deck')} / {label.get('expected_card_id')}",
        f"orientation: {label.get('expected_orientation')}",
        f"behavior: {label.get('expected_behavior')}",
        f"quality: {sample.quality_expectation}",
        f"similarity_group: {sample.similarity_group}",
    ]
    for index, line in enumerate(lines):
        cv2.putText(panel, line, (500, 45 + index * 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (225, 225, 225), 1, cv2.LINE_AA)
    cv2.imwrite(path, panel)


def _write_text_sheet(sample, label, path):
    lines = [
        f"sample_id: {sample.sample_id}",
        f"session: {sample.session_id}",
        f"category: {sample.category}",
        f"expected: {label.get('expected_deck')} / {label.get('expected_card_id')}",
        f"orientation: {label.get('expected_orientation')}",
        f"behavior: {label.get('expected_behavior')}",
        f"quality: {sample.quality_expectation}",
        f"similarity_group: {sample.similarity_group}",
    ]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _write_readme(output_dir, count):
    text = (
        "# Stage 6 Real-Camera Manual Review Pack\n\n"
        f"Samples: `{count}`\n\n"
        "Review every sheet under `samples/`, then review category and similarity indexes.\n\n"
        "This pack does not approve runtime thresholds or runtime integration.\n"
    )
    with open(os.path.join(output_dir, "README_FOR_SUPERVISOR.md"), "w", encoding="utf-8") as handle:
        handle.write(text)


def _write_json(path, payload):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build Stage 6 real-camera manual review pack.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--ground-truth", required=True)
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    result = build_manual_review_pack(args.manifest, args.ground_truth, args.preflight, args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
