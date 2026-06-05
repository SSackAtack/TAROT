"""Read-only contract helpers for Stage 6 real-camera aggregate fixtures."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os


@dataclass(frozen=True)
class AggregateSample:
    sample_id: str
    session_id: str
    session_path: str
    scenario: str
    category: str
    expected_deck: str
    expected_card_id: str | None
    expected_orientation: str
    expected_behavior: str
    quality_expectation: str
    similarity_group: str | None
    notes: str
    resolved_session_path: str


@dataclass(frozen=True)
class AggregateFixture:
    fixture_id: str
    manifest_version: int
    capture_policy: str
    samples: tuple
    labels: dict


def stable_sample_id(session_id, scenario, category):
    identity = f"{session_id}|{scenario}|{category}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def load_aggregate(manifest_path, ground_truth_path):
    manifest = _read_json(manifest_path)
    ground_truth = _read_json(ground_truth_path)
    base_dir = os.path.dirname(os.path.abspath(manifest_path))
    samples = tuple(
        AggregateSample(
            **item,
            resolved_session_path=os.path.abspath(os.path.join(base_dir, item["session_path"])),
        )
        for item in manifest.get("samples", [])
    )
    return AggregateFixture(
        fixture_id=manifest.get("fixture_id"),
        manifest_version=manifest.get("manifest_version"),
        capture_policy=manifest.get("capture_policy"),
        samples=samples,
        labels=ground_truth.get("labels", {}),
    )


def session_fingerprint(session_path):
    digest = hashlib.sha256()
    if not os.path.isdir(session_path):
        return None
    for root, directories, files in os.walk(session_path):
        directories.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            relative = os.path.relpath(path, session_path).replace("\\", "/")
            digest.update(relative.encode("utf-8"))
            digest.update(str(os.path.getsize(path)).encode("ascii"))
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(65536), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def scenario_required_files(scenario):
    suffixes = {"empty": "0", "one_card": "1", "three_cards": "3"}
    suffix = suffixes.get(scenario)
    if suffix is None:
        return []
    return [
        f"analysis_frame_{suffix}.png",
        f"raw_frame_{suffix}.png",
        "payload.json",
        "metrics.json",
        "roi_diagnostics.json",
    ]


def _read_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)
