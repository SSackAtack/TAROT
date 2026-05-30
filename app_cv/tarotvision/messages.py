"""Stable WebSocket payload builder for TarotVision.

Centralizes the construction of the JSON payload sent from the CV
backend to the AR frontend.  This ensures a consistent schema that
the frontend can rely on, regardless of which CV features are active.

The payload format is backward-compatible: the frontend uses
``data.cards || []`` and ignores unknown fields.
"""


import copy


def build_status_payload(cards, metrics=None, warnings=None,
                         debug=None, runtime=None, operator=None,
                         table=None, layout=None, studio=None):
    """Build a complete status payload for WebSocket broadcast.

    Args:
        cards:     list of confirmed card dicts (name, x, y, angle).
        metrics:   dict of rolling metric averages (fps, matching_ms, ...).
        warnings:  list of warning strings for the operator.
        debug:     dict of debug info (candidates, contour data, ...).
        runtime:   dict of runtime config (profile, camera settings, ...).
        operator:  dict of operator panel state (parameters, calibration, ...).
        table:     dict of ArUco table calibration status.
        layout:    dict of snapshot-first layout metadata.
        studio:    dict of recording studio state.

    Returns:
        dict ready for JSON serialization.
    """
    studio_dict = copy.deepcopy(studio) if studio is not None else {}
    if "director_mode" not in studio_dict:
        studio_dict["director_mode"] = "manual"
    if "director_scene" not in studio_dict:
        studio_dict["director_scene"] = "table"
    if "audio" not in studio_dict:
        studio_dict["audio"] = {
            "channels": {
                "mic": {"volume": 1.0, "muted": False},
                "bgm": {"volume": 0.5, "muted": False},
                "sfx": {"volume": 0.8, "muted": False},
                "master": {"volume": 1.0, "muted": False}
            },
            "peak_db": None
        }

    return {
        "schema_version": 1,
        "detected": len(cards) > 0,
        "cards": cards,
        "metrics": metrics or {},
        "warnings": warnings or [],
        "debug": debug or {},
        "runtime": runtime or {},
        "operator": operator or {},
        "table": table or {},
        "layout": layout or {},
        "studio": studio_dict,
    }
